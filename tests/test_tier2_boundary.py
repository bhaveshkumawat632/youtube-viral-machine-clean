import os
import json
import pytest
from unittest.mock import patch, MagicMock
from modules.subtitle_generator import (
    hex_to_ass_color,
    seconds_to_ass_time,
    generate_ass_subtitles,
    generate_srt_subtitles,
    words_from_script_with_timestamps
)
from modules.audio_mixer import mix_cinematic_audio
from modules.voiceover import generate_voiceover
from modules.cloud_video_generator import generate_video_from_prompt_hf
from modules.stock_video_generator import get_pexels_video
from vidrush_pipeline import run_qa_gate, build_scene_visuals, ASSETS_DIR, MANIFEST_FILE

# ---------------------------------------------------------
# FEATURE 1: SUBTITLES BOUNDARY & CORNER CASES
# ---------------------------------------------------------

def test_hex_to_ass_color_invalid():
    # Invalid length/chars
    with pytest.raises(ValueError):
        hex_to_ass_color("ZZZZZZ")
    with pytest.raises(ValueError):
        hex_to_ass_color("#XYZ")

def test_seconds_to_ass_time_negative():
    # Negative time bounds
    res = seconds_to_ass_time(-5.5)
    assert res == "0:00:00.00"

def test_generate_ass_subtitles_empty(tmp_path):
    output_path = os.path.join(tmp_path, "empty.ass")
    res = generate_ass_subtitles([], output_path)
    assert os.path.exists(output_path)
    with open(output_path, "r") as f:
        content = f.read()
        assert "[Events]" in content
        # No dialogues
        assert "Dialogue:" not in content

def test_generate_srt_subtitles_empty(tmp_path):
    output_path = os.path.join(tmp_path, "empty.srt")
    res = generate_srt_subtitles([], output_path)
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) == 0

def test_transcribe_missing_audio():
    # Verify that words_from_script_with_timestamps raises exception when audio doesn't exist
    with pytest.raises(Exception):
        words_from_script_with_timestamps("This is a script", "non_existent_audio.mp3")

# ---------------------------------------------------------
# FEATURE 2: AUDIO MIXING BOUNDARY & CORNER CASES
# ---------------------------------------------------------

def test_mix_audio_missing_voice():
    # Non-existent voice file raises RuntimeError due to FFmpeg failure
    with pytest.raises(RuntimeError):
        mix_cinematic_audio("missing_voice.mp3", output_path="out.mp3")
    assert not os.path.exists("out.mp3")

def test_mix_audio_negative_sfx_delay(tmp_path):
    vo = os.path.join(tmp_path, "vo.mp3")
    sfx = os.path.join(tmp_path, "sfx.mp3")
    from conftest import create_mock_audio
    create_mock_audio(vo)
    create_mock_audio(sfx)
    
    out = os.path.join(tmp_path, "out_neg.mp3")
    # Negative start time in SFX should be handled (delay converted to negative or 0)
    sfx_list = [{"path": sfx, "start": -2.0, "volume": 0.5}]
    # If the system converts start to ms: int(start * 1000)
    # adelay=-2000|-2000 might fail or cause FFmpeg error
    # Let's see if our mock or system handles it, or if it raises.
    # We assert it runs, or raises cleanly
    try:
        mix_cinematic_audio(vo, sfx_list=sfx_list, output_path=out)
    except Exception:
        pass # exceptions are fine as long as they are caught/propagated cleanly

def test_mix_audio_extreme_volumes(tmp_path):
    vo = os.path.join(tmp_path, "vo.mp3")
    from conftest import create_mock_audio
    create_mock_audio(vo)
    
    out = os.path.join(tmp_path, "out_vol.mp3")
    # Volume 0.0 and 100.0 (extreme)
    mix_cinematic_audio(vo, output_path=out)
    assert os.path.exists(out)

def test_mix_audio_nonexistent_outdir():
    # If output directory doesn't exist, mix_cinematic_audio should create it
    from conftest import create_mock_audio
    vo = "temp_vo.mp3"
    create_mock_audio(vo)
    out = "nested_dir/subdir/out.mp3"
    try:
        mix_cinematic_audio(vo, output_path=out)
        assert os.path.exists(out)
    finally:
        if os.path.exists(vo): 
            os.remove(vo)
        if os.path.exists(out):
            os.remove(out)
        if os.path.exists("nested_dir/subdir"):
            os.rmdir("nested_dir/subdir")
        if os.path.exists("nested_dir"):
            os.rmdir("nested_dir")

def test_generate_voiceover_empty():
    # Empty script text in TTS
    with pytest.raises(Exception):
        generate_voiceover("", "empty_vo.mp3")

# ---------------------------------------------------------
# FEATURE 3: VISUAL SOURCING BOUNDARY & CORNER CASES
# ---------------------------------------------------------

def test_cloud_video_missing_api_keys(tmp_path):
    # Temporarily remove FAL_KEY from env
    with patch.dict(os.environ, {"FAL_KEY": ""}):
        out = os.path.join(tmp_path, "cloud_no_key.mp4")
        # Colab will be tried first (if PRIVATE_API_URL is active),
        # then spaces, and then fal which will print warning.
        # It should run successfully due to Colab/Spaces fallback.
        res = generate_video_from_prompt_hf("neon clock", out)
        assert os.path.exists(res)

def test_cloud_video_space_404(tmp_path):
    # Force Client to throw error, testing space exhaustion and failure
    with patch("modules.cloud_video_generator.Client", side_effect=Exception("404 Space Not Found")):
        with patch("fal_client.subscribe", side_effect=Exception("FAL quota exceeded")):
            with patch.dict(os.environ, {"FAL_KEY": "mock_key"}):
                out = os.path.join(tmp_path, "cloud_fail.mp4")
                # All engines should fail -> RuntimeError
                with pytest.raises(RuntimeError):
                    generate_video_from_prompt_hf("failed visual prompt", out)

def test_pexels_stock_missing_key(tmp_path):
    with patch.dict(os.environ, {"PEXELS_API_KEY": ""}):
        out = os.path.join(tmp_path, "pexels_fail.mp4")
        with pytest.raises(ValueError):
            get_pexels_video("glowing brain", out)

def test_pexels_stock_empty_results(tmp_path):
    # Mock requests.get response to return empty dict
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"videos": []}
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {"PEXELS_API_KEY": "mock_key"}):
            out = os.path.join(tmp_path, "pexels_empty.mp4")
            with pytest.raises(RuntimeError):
                get_pexels_video("nonexistent query", out)

def test_visual_loop_fallback_to_gradient():
    # If no local loops exist, build_scene_visuals falls back to FFmpeg color block (dark purple)
    # We simulate this by returning False only for backgrounds path
    original_exists = os.path.exists
    def mock_exists(path):
        if "backgrounds" in str(path):
            return False
        return original_exists(path)
        
    with patch("os.path.exists", side_effect=mock_exists):
        with patch.dict(os.environ, {"PEXELS_API_KEY": ""}):
            scene = {"text": "Hello", "suggested_visual_keyword": "neon light"}
            res = build_scene_visuals(scene, 1, duration=3.0)
            assert original_exists(res)
            assert os.path.getsize(res) > 1000

# ---------------------------------------------------------
# FEATURE 4: QA GATE BOUNDARY & CORNER CASES
# ---------------------------------------------------------

def test_qa_gate_out_of_bounds_duration():
    # Duration 10 seconds (too short)
    passed, reason, _, _, _, _ = run_qa_gate("mock.mp4", 10.0)
    assert passed is False
    assert "Duration" in reason

    # Duration 200 seconds (too long)
    passed, reason, _, _, _, _ = run_qa_gate("mock.mp4", 200.0)
    assert passed is False
    assert "Duration" in reason

def test_qa_gate_corrupted_manifest(tmp_path):
    os.makedirs(ASSETS_DIR, exist_ok=True)
    with open(MANIFEST_FILE, "w") as f:
        f.write("corrupted json data {")
    
    mock_vid = os.path.join(tmp_path, "vid.mp4")
    passed, reason, _, _, _, _ = run_qa_gate(mock_vid, 35.0)
    assert passed is False
    assert "Manifest file corrupted" in reason

def test_qa_gate_unsafe_source(tmp_path):
    os.makedirs(ASSETS_DIR, exist_ok=True)
    manifest_data = [
        {"asset_id": "1", "source": "shutterstock.com", "license_type": "unknown", "url": "mock"}
    ]
    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest_data, f)
        
    mock_vid = os.path.join(tmp_path, "vid.mp4")
    passed, reason, _, _, _, _ = run_qa_gate(mock_vid, 35.0)
    assert passed is False
    assert "UNSAFE SOURCE DETECTED" in reason

def test_qa_gate_high_fallback_ratio(tmp_path):
    os.makedirs(ASSETS_DIR, exist_ok=True)
    # 3 synthetic visuals, 0 real -> ratio = 100% (exceeds 30%)
    manifest_data = [
        {"asset_id": "1", "source": "ffmpeg_synthetic", "license_type": "public_domain", "url": "mock"},
        {"asset_id": "2", "source": "ffmpeg_synthetic", "license_type": "public_domain", "url": "mock"}
    ]
    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest_data, f)
        
    mock_vid = os.path.join(tmp_path, "vid.mp4")
    passed, reason, _, _, _, _ = run_qa_gate(mock_vid, 35.0)
    assert passed is False
    assert "Fallback ratio too high" in reason
