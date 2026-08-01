import os
import sys
import pytest
import subprocess
import json
import runpy
from unittest.mock import MagicMock, patch

# Ensure project root is in Python PATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import SHORTS_WIDTH, SHORTS_HEIGHT, TEMP_DIR
from modules.video_maker import (
    create_gradient_background,
    check_copyright_killswitch,
    mix_voice_bgm_and_sfx,
    create_video_from_audio_and_subtitles,
    _prepare_background_video,
    _prepare_multi_background_videos,
    _prepare_background_image,
    _get_duration,
    add_subtitles_to_video,
    crop_to_shorts
)

# ============================================================
# SUBPROCESS MOCK REGISTRY
# ============================================================
class MockSubprocessRun:
    def __init__(self):
        self.returncode = 0
        self.stdout = ""
        self.stderr = ""
        self.called_commands = []
        self.duration_map = {}

    def __call__(self, cmd, *args, **kwargs):
        self.called_commands.append(cmd)
        
        if isinstance(cmd, list) and len(cmd) > 0:
            if "ffprobe" in cmd:
                # Intercept ffprobe duration lookup
                file_path = cmd[-1]
                duration = self.duration_map.get(file_path, "10.0")
                stdout_data = json.dumps({"format": {"duration": str(duration)}})
                return subprocess.CompletedProcess(cmd, 0, stdout=stdout_data, stderr="")
            
            # Intercept ffmpeg output commands and write dummy file to satisfy os.path.exists
            try:
                output_file = str(cmd[-1])
                if not output_file.startswith("-") and not output_file.startswith("/dev/null"):
                    parent = os.path.dirname(output_file)
                    if parent:
                        os.makedirs(parent, exist_ok=True)
                    if not os.path.exists(output_file):
                        with open(output_file, "wb") as f:
                            f.write(b"\0" * 1000)
            except Exception:
                pass
                        
        return subprocess.CompletedProcess(cmd, self.returncode, stdout=self.stdout, stderr=self.stderr)

# ============================================================
# 1. create_gradient_background TESTS
# ============================================================
def test_create_gradient_background_pillow_success(tmp_path):
    output_video = os.path.join(tmp_path, "grad_pillow.mp4")
    mock_run = MockSubprocessRun()
    with patch("subprocess.run", side_effect=mock_run):
        res = create_gradient_background(output_video, duration=3.0, gradient_name="dark_purple")
        assert res == output_video
        # PNG bg should be saved and then converted using ffmpeg
        assert os.path.exists(output_video.replace('.mp4', '_bg.png'))
        assert any("-loop" in cmd for cmd in mock_run.called_commands)

def test_create_gradient_background_pillow_success_ffmpeg_fail(tmp_path):
    output_video = os.path.join(tmp_path, "grad_pillow_fail.mp4")
    called_commands = []
    
    def mock_run(cmd, *args, **kwargs):
        called_commands.append(cmd)
        if isinstance(cmd, list) and "-loop" in cmd:
            # First conversion command fails
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="Mock loop fail")
        # Solid color fallback succeeds
        with open(cmd[-1], "wb") as f:
            f.write(b"\0")
        return subprocess.CompletedProcess(cmd, 0)

    with patch("subprocess.run", side_effect=mock_run):
        res = create_gradient_background(output_video, duration=3.0)
        assert res == output_video
        assert len(called_commands) == 2
        assert "-loop" in called_commands[0]
        assert "lavfi" in called_commands[1]

def test_create_gradient_background_pillow_import_failure(tmp_path):
    output_video = os.path.join(tmp_path, "grad_fallback.mp4")
    mock_run = MockSubprocessRun()
    
    # Remove PIL from sys.modules to force re-import inside the function
    removed_modules = {}
    for mod in list(sys.modules.keys()):
        if mod == "PIL" or mod.startswith("PIL."):
            removed_modules[mod] = sys.modules.pop(mod)
            
    # Intercept imports to simulate environment without Pillow (PIL)
    import builtins
    original_import = builtins.__import__
    def mock_import(name, *args, **kwargs):
        if "PIL" in name:
            raise ImportError("Mocked PIL import failure")
        return original_import(name, *args, **kwargs)
        
    try:
        with patch("builtins.__import__", side_effect=mock_import), \
             patch("subprocess.run", side_effect=mock_run):
             
            res = create_gradient_background(output_video, duration=3.0, gradient_name="dark_red")
            assert res == output_video
            # Verify fallback solid color command was called
            assert any("color=c=0x" in " ".join(cmd) for cmd in mock_run.called_commands if isinstance(cmd, list))
    finally:
        sys.modules.update(removed_modules)

# ============================================================
# 2. check_copyright_killswitch TESTS
# ============================================================
def test_copyright_killswitch_scenarios():
    # Path A: Allow
    assert check_copyright_killswitch("royalty_free_local", "pexels_api") is True
    # Path B: Audio block
    assert check_copyright_killswitch("unauthorized_audio", "pexels_api") is False
    # Path C: Visual block
    assert check_copyright_killswitch("royalty_free_local", "unauthorized_visual") is False

# ============================================================
# 3. mix_voice_bgm_and_sfx TESTS
# ============================================================
def test_mix_voice_bgm_and_sfx_with_sfx_generation(tmp_path):
    vo_path = os.path.join(tmp_path, "vo.mp3")
    out_path = os.path.join(tmp_path, "mixed.mp3")
    with open(vo_path, "wb") as f: f.write(b"\0")
        
    def mock_exists(path):
        # Trigger generate_sfx whoosh fallback branch
        if "whooshes.mp3" in path or "temp_whoosh.wav" in path:
            return False
        return True

    with patch("modules.background_music.generate_background_tone") as mock_bgm, \
         patch("modules.background_music.generate_sfx") as mock_sfx, \
         patch("os.path.exists", side_effect=mock_exists), \
         patch("subprocess.run") as mock_run:
         
        mock_run.return_value = subprocess.CompletedProcess([], 0)
        res = mix_voice_bgm_and_sfx(vo_path, out_path, total_duration=10.0, num_scenes=3)
        assert res == out_path
        mock_bgm.assert_called_once()
        mock_sfx.assert_called_once_with(os.path.join(TEMP_DIR, "temp_whoosh.wav"), type="whoosh")
        mock_run.assert_called_once()

def test_mix_voice_bgm_and_sfx_no_sfx_needed(tmp_path):
    vo_path = os.path.join(tmp_path, "vo.mp3")
    out_path = os.path.join(tmp_path, "mixed.mp3")
    with open(vo_path, "wb") as f: f.write(b"\0")
        
    # Covers num_scenes = 1 (no whoosh delayed tracks in filter chain)
    with patch("modules.background_music.generate_background_tone"), \
         patch("subprocess.run") as mock_run:
         
        mock_run.return_value = subprocess.CompletedProcess([], 0)
        res = mix_voice_bgm_and_sfx(vo_path, out_path, total_duration=5.0, num_scenes=1)
        assert res == out_path
        # Check command has simple 2-input mix chain
        complex_filter = mock_run.call_args[0][0][mock_run.call_args[0][0].index("-filter_complex")+1]
        assert "inputs=2" in complex_filter

def test_mix_voice_bgm_and_sfx_cleanup_exception(tmp_path):
    vo_path = os.path.join(tmp_path, "vo.mp3")
    out_path = os.path.join(tmp_path, "mixed.mp3")
    with open(vo_path, "wb") as f: f.write(b"\0")
        
    def mock_remove(path):
        raise OSError("Removal error")
        
    with patch("modules.background_music.generate_background_tone"), \
         patch("os.path.exists", return_value=True), \
         patch("os.remove", side_effect=mock_remove), \
         patch("subprocess.run"):
         
        # Should complete successfully despite os.remove throwing exception
        res = mix_voice_bgm_and_sfx(vo_path, out_path, total_duration=5.0, num_scenes=1)
        assert res == out_path

# ============================================================
# 4. create_video_from_audio_and_subtitles TESTS
# ============================================================
def test_create_video_killswitch_active():
    with patch("modules.video_maker.check_copyright_killswitch", return_value=False):
        res = create_video_from_audio_and_subtitles("audio.mp3", "subs.ass", "out.mp4")
        assert res is False

def test_create_video_format_video(tmp_path):
    audio_path = os.path.join(tmp_path, "vo.mp3")
    sub_path = os.path.join(tmp_path, "sub.ass")
    out_path = os.path.join(tmp_path, "final.mp4")
    with open(audio_path, "wb") as f: f.write(b"\0")
    with open(sub_path, "wb") as f: f.write(b"\0")
        
    mock_run = MockSubprocessRun()
    with patch("modules.video_maker.check_copyright_killswitch", return_value=True), \
         patch("modules.video_maker._get_duration", return_value=5.0), \
         patch("modules.video_maker.mix_voice_bgm_and_sfx"), \
         patch("os.path.getsize", return_value=1024*1024), \
         patch("subprocess.run", side_effect=mock_run):
         
        create_video_from_audio_and_subtitles(audio_path, sub_path, out_path, video_format="video")
        # Verify 1920x1080 resolution is compiled into scaling parameters (1960:1120 for crop box padding)
        final_cmd = " ".join(mock_run.called_commands[-1])
        assert "scale=1960:1120" in final_cmd

def test_create_video_background_modes(tmp_path):
    audio_path = os.path.join(tmp_path, "vo.mp3")
    sub_path = os.path.join(tmp_path, "sub.ass")
    out_path = os.path.join(tmp_path, "final.mp4")
    with open(audio_path, "wb") as f: f.write(b"\0")
    with open(sub_path, "wb") as f: f.write(b"\0")
        
    # Test single background video preparation mapping
    with patch("modules.video_maker.check_copyright_killswitch", return_value=True), \
         patch("modules.video_maker._get_duration", return_value=5.0), \
         patch("modules.video_maker._prepare_background_video", return_value="prep_vid.mp4") as mock_prep, \
         patch("modules.video_maker.mix_voice_bgm_and_sfx"), \
         patch("os.path.getsize", return_value=1024*1024), \
         patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0)):
         
        create_video_from_audio_and_subtitles(audio_path, sub_path, out_path, background_video="single_vid.mp4")
        mock_prep.assert_called_once_with("single_vid.mp4", SHORTS_WIDTH, SHORTS_HEIGHT, 6.0)

    # Test single background image preparation mapping
    with patch("modules.video_maker.check_copyright_killswitch", return_value=True), \
         patch("modules.video_maker._get_duration", return_value=5.0), \
         patch("modules.video_maker._prepare_background_image", return_value="prep_img.mp4") as mock_prep_img, \
         patch("modules.video_maker.mix_voice_bgm_and_sfx"), \
         patch("os.path.getsize", return_value=1024*1024), \
         patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0)):
         
        create_video_from_audio_and_subtitles(audio_path, sub_path, out_path, background_image="image.jpg")
        mock_prep_img.assert_called_once_with("image.jpg", SHORTS_WIDTH, SHORTS_HEIGHT, 6.0)

def test_create_video_bg_list_fails_to_gradient(tmp_path):
    audio_path = os.path.join(tmp_path, "vo.mp3")
    sub_path = os.path.join(tmp_path, "sub.ass")
    out_path = os.path.join(tmp_path, "final.mp4")
    with open(audio_path, "wb") as f: f.write(b"\0")
    with open(sub_path, "wb") as f: f.write(b"\0")
        
    # Multi list returns None -> Falls back to gradient generator
    with patch("modules.video_maker.check_copyright_killswitch", return_value=True), \
         patch("modules.video_maker._get_duration", return_value=5.0), \
         patch("modules.video_maker._prepare_multi_background_videos", return_value=None), \
         patch("modules.video_maker.create_gradient_background") as mock_grad, \
         patch("modules.video_maker.mix_voice_bgm_and_sfx"), \
         patch("os.path.getsize", return_value=1024*1024), \
         patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0)):
         
        create_video_from_audio_and_subtitles(audio_path, sub_path, out_path, background_video=["v1.mp4"])
        mock_grad.assert_called_once()

def test_create_video_primary_ffmpeg_fails_fallback_success(tmp_path):
    audio_path = os.path.join(tmp_path, "vo.mp3")
    sub_path = os.path.join(tmp_path, "sub.ass")
    out_path = os.path.join(tmp_path, "final.mp4")
    with open(audio_path, "wb") as f: f.write(b"\0")
    with open(sub_path, "wb") as f: f.write(b"\0")
        
    called_commands = []
    def mock_run(cmd, *args, **kwargs):
        called_commands.append(cmd)
        if isinstance(cmd, list) and "-filter_complex" in cmd:
            # Primary complex filter fails
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="Complex filter error")
        # Fallback command succeeds
        with open(out_path, "wb") as f: f.write(b"\0")
        return subprocess.CompletedProcess(cmd, 0)
        
    def mock_mix(voiceover_path, output_path, total_duration, num_scenes):
        with open(output_path, "wb") as f:
            f.write(b"\0")
            
    with patch("modules.video_maker.check_copyright_killswitch", return_value=True), \
         patch("modules.video_maker._get_duration", return_value=5.0), \
         patch("modules.video_maker.mix_voice_bgm_and_sfx", side_effect=mock_mix), \
         patch("os.path.getsize", return_value=1024*1024), \
         patch("subprocess.run", side_effect=mock_run):
         
        res = create_video_from_audio_and_subtitles(audio_path, sub_path, out_path)
        assert res == out_path
        # There are 3 commands: 1 for gradient background, 1 for primary video render, 1 for fallback video render
        assert len(called_commands) == 3
        
        # Verify the primary command (index 1) had -filter_complex filter
        cmd1 = called_commands[1]
        assert "-filter_complex" in cmd1
        
        # Verify the fallback command (index 2) had aspect ratio scaling
        cmd2 = called_commands[2]
        assert "-vf" in cmd2
        assert "force_original_aspect_ratio=decrease" in cmd2[cmd2.index("-vf") + 1]

def test_create_video_all_ffmpeg_fail(tmp_path):
    audio_path = os.path.join(tmp_path, "vo.mp3")
    sub_path = os.path.join(tmp_path, "sub.ass")
    out_path = os.path.join(tmp_path, "final.mp4")
    with open(audio_path, "wb") as f: f.write(b"\0")
    with open(sub_path, "wb") as f: f.write(b"\0")
        
    def mock_mix(voiceover_path, output_path, total_duration, num_scenes):
        with open(output_path, "wb") as f:
            f.write(b"\0")
            
    def mock_remove(path):
        raise OSError("Permission denied")
        
    with patch("modules.video_maker.check_copyright_killswitch", return_value=True), \
         patch("modules.video_maker._get_duration", return_value=5.0), \
         patch("modules.video_maker.mix_voice_bgm_and_sfx", side_effect=mock_mix), \
         patch("os.path.getsize", return_value=1024*1024), \
         patch("os.remove", side_effect=mock_remove), \
         patch("subprocess.run", return_value=subprocess.CompletedProcess([], 1, stderr="Hard error")):
         
        res = create_video_from_audio_and_subtitles(audio_path, sub_path, out_path)
        assert res == out_path

# ============================================================
# 5. _prepare_background_video TESTS
# ============================================================
def test_prepare_background_video_loop(tmp_path):
    video_path = os.path.join(tmp_path, "input.mp4")
    with patch("modules.video_maker._get_duration", return_value=2.0), \
         patch("subprocess.run") as mock_run:
         
        mock_run.return_value = subprocess.CompletedProcess([], 0)
        _prepare_background_video(video_path, width=1080, height=1920, duration=5.0)
        assert "-stream_loop" in mock_run.call_args[0][0]
         
def test_prepare_background_video_no_loop(tmp_path):
    video_path = os.path.join(tmp_path, "input.mp4")
    with patch("modules.video_maker._get_duration", return_value=10.0), \
         patch("subprocess.run") as mock_run:
         
        mock_run.return_value = subprocess.CompletedProcess([], 0)
        _prepare_background_video(video_path, width=1080, height=1920, duration=5.0)
        assert "-stream_loop" not in mock_run.call_args[0][0]

# ============================================================
# 6. _prepare_multi_background_videos TESTS
# ============================================================
def test_prepare_multi_background_videos_all_videos(tmp_path):
    # Pass 5 paths to trigger the total_time >= duration break on the 5th iteration
    video_paths = [os.path.join(tmp_path, f"v_{i}.mp4") for i in range(5)]
    for p in video_paths:
        with open(p, "wb") as f: f.write(b"\0")
            
    called_commands = []
    def mock_run(cmd, *args, **kwargs):
        called_commands.append(cmd)
        out_clip = cmd[-1]
        with open(out_clip, "wb") as f: f.write(b"\0")
        return subprocess.CompletedProcess(cmd, 0)
        
    with patch("subprocess.run", side_effect=mock_run), \
         patch("os.path.exists", return_value=True):
         
        res = _prepare_multi_background_videos(video_paths, width=1080, height=1920, duration=10.0)
        assert res is not None
        # Check scale/crop filter is mapped
        assert any("force_original_aspect_ratio=increase" in " ".join(c) for c in called_commands if isinstance(c, list))
        # Check concat command is run
        assert any("concat=" in " ".join(c) for c in called_commands if isinstance(c, list))

def test_prepare_multi_background_videos_short_duration_break(tmp_path):
    # Pass 4 paths and duration 9.5 to trigger this_dur < 1.0 break on the 4th iteration (this_dur will be 0.5)
    video_paths = [os.path.join(tmp_path, f"v_{i}.mp4") for i in range(4)]
    for p in video_paths:
        with open(p, "wb") as f: f.write(b"\0")
            
    called_commands = []
    def mock_run(cmd, *args, **kwargs):
        called_commands.append(cmd)
        out_clip = cmd[-1]
        with open(out_clip, "wb") as f: f.write(b"\0")
        return subprocess.CompletedProcess(cmd, 0)
        
    with patch("subprocess.run", side_effect=mock_run), \
         patch("os.path.exists", return_value=True):
         
        res = _prepare_multi_background_videos(video_paths, width=1080, height=1920, duration=9.5)
        assert res is not None

def test_prepare_multi_background_videos_empty_result(tmp_path):
    # Make os.path.exists return False for temp clips so they are not collected, returning None
    video_paths = [os.path.join(tmp_path, "v_fail.mp4")]
    with open(video_paths[0], "wb") as f: f.write(b"\0")
        
    with patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0)), \
         patch("os.path.exists", return_value=False):
         
        res = _prepare_multi_background_videos(video_paths, width=1080, height=1920, duration=5.0)
        assert res is None

def test_prepare_multi_background_videos_with_images_cloud_success(tmp_path):
    image_paths = [os.path.join(tmp_path, "img_1.png")]
    for p in image_paths:
        with open(p, "wb") as f: f.write(b"\0")
            
    called_commands = []
    def mock_run(cmd, *args, **kwargs):
        called_commands.append(cmd)
        out_clip = cmd[-1]
        with open(out_clip, "wb") as f: f.write(b"\0")
        return subprocess.CompletedProcess(cmd, 0)
        
    mock_video_path = os.path.join(tmp_path, "cloud_gen.mp4")
    with open(mock_video_path, "wb") as f: f.write(b"\0")
        
    with patch("modules.video_maker.generate_video_from_prompt_hf", return_value=mock_video_path) as mock_cloud, \
         patch("subprocess.run", side_effect=mock_run), \
         patch("os.path.exists", return_value=True):
         
        res = _prepare_multi_background_videos(image_paths, width=1080, height=1920, duration=5.0)
        assert res is not None
        mock_cloud.assert_called_once()
        # The path has changed to mock_video_path (not ending with png/jpg)
        # So it uses video formatting filter mapping rather than zoompan
        prep_cmd = " ".join(called_commands[0])
        assert "force_original_aspect_ratio=increase" in prep_cmd
        assert "zoompan" not in prep_cmd

def test_prepare_multi_background_videos_with_images_cloud_fail(tmp_path):
    image_paths = [os.path.join(tmp_path, "img_1.png")]
    for p in image_paths:
        with open(p, "wb") as f: f.write(b"\0")
            
    called_commands = []
    def mock_run(cmd, *args, **kwargs):
        called_commands.append(cmd)
        out_clip = cmd[-1]
        with open(out_clip, "wb") as f: f.write(b"\0")
        return subprocess.CompletedProcess(cmd, 0)
        
    with patch("modules.video_maker.generate_video_from_prompt_hf", return_value=None) as mock_cloud, \
         patch("subprocess.run", side_effect=mock_run), \
         patch("os.path.exists", return_value=True):
         
        res = _prepare_multi_background_videos(image_paths, width=1080, height=1920, duration=5.0)
        assert res is not None
        mock_cloud.assert_called_once()
        # The path remains png -> triggers zoompan image filter
        prep_cmd = " ".join(called_commands[0])
        assert "zoompan=z=" in prep_cmd
        assert "force_original_aspect_ratio" not in prep_cmd

def test_prepare_multi_background_videos_cleanup_error(tmp_path):
    video_paths = [os.path.join(tmp_path, "v1.mp4")]
    with open(video_paths[0], "wb") as f: f.write(b"\0")
        
    def mock_run(cmd, *args, **kwargs):
        out_clip = cmd[-1]
        with open(out_clip, "wb") as f: f.write(b"\0")
        return subprocess.CompletedProcess(cmd, 0)
        
    def mock_remove(path):
        raise OSError("Access denied")
        
    with patch("subprocess.run", side_effect=mock_run), \
         patch("os.path.exists", return_value=True), \
         patch("os.remove", side_effect=mock_remove):
         
        # Verification that cleanup failure does not interrupt the program
        res = _prepare_multi_background_videos(video_paths, width=1080, height=1920, duration=5.0)
        assert res is not None

# ============================================================
# 7. OTHER HELPER TESTS
# ============================================================
def test_prepare_background_image(tmp_path):
    img_path = os.path.join(tmp_path, "img.jpg")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess([], 0)
        res = _prepare_background_image(img_path, width=1080, height=1920, duration=5.0)
        assert res == os.path.join(TEMP_DIR, "bg_from_image.mp4")

def test_get_duration():
    mock_run = MagicMock()
    mock_run.return_value = subprocess.CompletedProcess([], 0, stdout='{"format": {"duration": "12.34"}}')
    with patch("subprocess.run", mock_run):
        dur = _get_duration("dummy.mp4")
        assert dur == 12.34

def test_add_subtitles_to_video_both_cases():
    # Case 1: Success
    with patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0)):
        res = add_subtitles_to_video("v.mp4", "s.ass", "out.mp4")
        assert res == "out.mp4"
    # Case 2: Failure
    with patch("subprocess.run", return_value=subprocess.CompletedProcess([], 1, stderr="Err")):
        res = add_subtitles_to_video("v.mp4", "s.ass", "out.mp4")
        assert res == "out.mp4"

def test_crop_to_shorts_both_cases():
    # Case 1: Success
    with patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0)):
        res = crop_to_shorts("v.mp4", "out.mp4")
        assert res == "out.mp4"
    # Case 2: Failure
    with patch("subprocess.run", return_value=subprocess.CompletedProcess([], 1, stderr="Err")):
        res = crop_to_shorts("v.mp4", "out.mp4")
        assert res == "out.mp4"

# ============================================================
# 8. SCRIPT ENTRY POINT (__main__) COVERAGE
# ============================================================
def test_video_maker_main_block():
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../modules/video_maker.py"))
    # Executes the raw module in runpy with __main__ environment namespace
    with patch("builtins.print") as mock_print:
        runpy.run_path(file_path, run_name="__main__")
        # Confirm it outputted the entry logs
        assert any("YouTube Viral Machine" in call[0][0] for call in mock_print.call_args_list)
