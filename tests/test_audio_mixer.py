import os
import time
import runpy
import subprocess
import pytest
from unittest.mock import patch, MagicMock
from config import TEMP_DIR
from modules.audio_mixer import mix_cinematic_audio

# --- FIXTURES ---

@pytest.fixture
def mock_ffmpeg_success():
    """Provides a patched subprocess.run returning exit code 0."""
    with patch("subprocess.run") as mock_run:
        mock_completed = MagicMock(spec=subprocess.CompletedProcess)
        mock_completed.returncode = 0
        mock_completed.stdout = b"success"
        mock_completed.stderr = b""
        mock_run.return_value = mock_completed
        yield mock_run

@pytest.fixture
def mock_ffmpeg_failure():
    """Provides a patched subprocess.run returning exit code 1."""
    with patch("subprocess.run") as mock_run:
        mock_completed = MagicMock(spec=subprocess.CompletedProcess)
        mock_completed.returncode = 1
        mock_completed.stdout = b""
        mock_completed.stderr = b"FFmpeg filter graph compilation error"
        mock_run.return_value = mock_completed
        yield mock_run

# --- TEST CASES ---

def test_mix_audio_output_path_none(mock_ffmpeg_success):
    """Path coverage: tests auto-generation of output_path when set to None."""
    voice_path = "voice.mp3"
    
    # We mock os.makedirs to avoid polluting the workspace
    with patch("os.makedirs") as mock_makedirs:
        result = mix_cinematic_audio(voice_path, output_path=None)
        
        # Verify output path structure
        assert result.startswith(TEMP_DIR)
        assert result.endswith(".mp3")
        assert "cinematic_mix_" in result
        
        # Verify TEMP_DIR creation was requested
        mock_makedirs.assert_any_call(TEMP_DIR, exist_ok=True)

def test_mix_audio_sfx_missing_optional_keys(mock_ffmpeg_success):
    """Path coverage: tests fallback defaults in sfx list elements when start/volume keys are absent."""
    voice_path = "voice.mp3"
    sfx_list = [
        {"path": "sfx_default.mp3"}  # Both start and volume are missing
    ]
    
    mix_cinematic_audio(voice_path, sfx_list=sfx_list, output_path="out.mp3")
    
    # Inspect arguments passed to subprocess.run
    mock_ffmpeg_success.assert_called_once()
    cmd = mock_ffmpeg_success.call_args[0][0]
    
    # Verify filter complex details
    # The default volume should be 0.5, and start delay 0
    # Formula uses: adelay=0|0,volume=0.5
    filter_complex = cmd[cmd.index("-filter_complex") + 1]
    assert "adelay=0|0,volume=0.5" in filter_complex

def test_mix_audio_no_parent_dir(mock_ffmpeg_success):
    """Branch coverage: tests behavior when the output path does not contain a parent directory component."""
    voice_path = "voice.mp3"
    flat_output = "flat_out.mp3" # No slashes or path directory parts
    
    with patch("os.makedirs") as mock_makedirs:
        result = mix_cinematic_audio(voice_path, output_path=flat_output)
        assert result == flat_output
        
        # Since there is no parent directory, os.makedirs(parent_dir) should not be triggered.
        # Ensure it was not called with empty string or other directory paths
        for call in mock_makedirs.call_args_list:
            assert call[0][0] != ""

def test_mix_audio_ffmpeg_failure(mock_ffmpeg_failure):
    """Error coverage: tests raising of RuntimeError when subprocess returns non-zero code."""
    voice_path = "voice.mp3"
    
    with pytest.raises(RuntimeError) as exc_info:
        mix_cinematic_audio(voice_path, output_path="out.mp3")
        
    assert "FFmpeg audio mixing failed" in str(exc_info.value)
    assert "FFmpeg filter graph compilation error" in str(exc_info.value)

def test_audio_mixer_main_block():
    """Branch coverage: executes the if __name__ == '__main__' script block of the module."""
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../modules/audio_mixer.py"))
    # We patch print to verify output and capture execution of line 93
    with patch("builtins.print") as mock_print:
        # run_path executes the Python file under '__main__' scope
        runpy.run_path(file_path, run_name="__main__")
        mock_print.assert_any_call("Testing Cinematic Audio Mixer...")

def test_mix_audio_ffmpeg_command_structure(mock_ffmpeg_success):
    """Structural coverage: verifies exact formatting of commands, inputs, and compressor/limiter settings."""
    voice_path = "voice.mp3"
    bgm_path = "bgm.mp3"
    sfx_list = [
        {"path": "sfx0.mp3", "start": 1.5, "volume": 0.3},
        {"path": "sfx1.mp3", "start": 0.5, "volume": 0.8}
    ]
    output_path = "nested/out.mp3"
    
    with patch("os.makedirs") as mock_makedirs:
        mix_cinematic_audio(voice_path, sfx_list=sfx_list, bgm_path=bgm_path, output_path=output_path)
        
        # Verify folder creation
        mock_makedirs.assert_any_call("nested", exist_ok=True)
        
        mock_ffmpeg_success.assert_called_once()
        cmd = mock_ffmpeg_success.call_args[0][0]
        
        # Verify inputs matching: voice, bgm, sfx0, sfx1
        assert cmd[cmd.index("-i") + 1] == voice_path
        assert cmd[cmd.index("-i", cmd.index(voice_path)) + 1] == bgm_path
        assert cmd[cmd.index("-i", cmd.index(bgm_path)) + 1] == "sfx0.mp3"
        assert cmd[cmd.index("-i", cmd.index("sfx0.mp3")) + 1] == "sfx1.mp3"
        
        # Verify audio ducking filters built in order
        filter_complex = cmd[cmd.index("-filter_complex") + 1]
        
        # Voice compressor must be mapped to input 0
        assert "[0:a]acompressor" in filter_complex
        # BGM volume must be mapped to input 1
        assert "[1:a]volume=0.3" in filter_complex
        # Sidechain compress ducking BGM using voice comp
        assert "[bgm_init][voice_comp]sidechaincompress" in filter_complex
        # SFX0 must delay by 1500ms and scale by 0.3 volume
        assert "[2:a]adelay=1500|1500,volume=0.3" in filter_complex
        # SFX1 must delay by 500ms and scale by 0.8 volume
        assert "[3:a]adelay=500|500,volume=0.8" in filter_complex
        # amix must combine all 4 layers
        assert "amix=inputs=4" in filter_complex
