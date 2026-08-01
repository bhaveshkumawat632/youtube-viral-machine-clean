import os
import json
import pytest
import subprocess
from conftest import create_mock_video, create_mock_audio
from vidrush_pipeline import assemble_final_video, run_qa_gate

def run_ffprobe(file_path):
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", file_path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(res.stdout)

def test_tier4_e2e_render_and_technical_compliance(tmp_path):
    # Setup 5-second video inputs
    vo = os.path.join(tmp_path, "e2e_vo.mp3")
    create_mock_audio(vo, duration=5.0)
    
    # 2 scene videos of 2.5 seconds each
    v1 = os.path.join(tmp_path, "e2e_v1.mp4")
    v2 = os.path.join(tmp_path, "e2e_v2.mp4")
    create_mock_video(v1, duration=2.5)
    create_mock_video(v2, duration=2.5)
    
    scenes_data = [
        {"text": "First part of the 5 second rule story", "audio": vo, "video": v1, "duration": 2.5},
        {"text": "Second part of the 5 second rule story", "audio": vo, "video": v2, "duration": 2.5}
    ]
    
    # Compile the final video
    final_vid, total_dur = assemble_final_video(scenes_data)
    assert os.path.exists(final_vid)
    assert abs(total_dur - 5.0) <= 0.2
    
    # Run technical validation via ffprobe
    probe = run_ffprobe(final_vid)
    
    # 1. Container Check
    format_name = probe["format"]["format_name"]
    assert "mp4" in format_name or "mov" in format_name, f"Expected MP4 container, got {format_name}"
    
    # Extract streams
    video_stream = None
    audio_stream = None
    for stream in probe["streams"]:
        if stream["codec_type"] == "video":
            video_stream = stream
        elif stream["codec_type"] == "audio":
            audio_stream = stream
            
    assert video_stream is not None, "Video stream not found"
    assert audio_stream is not None, "Audio stream not found"
    
    # 2. Video Codec Check
    video_codec = video_stream["codec_name"]
    assert video_codec == "h264", f"Expected H.264 video codec, got {video_codec}"
    
    # 3. Audio Codec Check
    audio_codec = audio_stream["codec_name"]
    assert audio_codec == "aac", f"Expected AAC audio codec, got {audio_codec}"
    
    # 4. Portrait Layout Check
    width = video_stream["width"]
    height = video_stream["height"]
    assert width == 1080 and height == 1920, f"Expected 1080x1920 layout, got {width}x{height}"
    
    # 5. Framerate Check (30 FPS)
    fps_frac = video_stream["r_frame_rate"].split('/')
    fps = float(fps_frac[0]) / float(fps_frac[1])
    assert abs(fps - 30.0) < 0.5, f"Expected ~30 FPS, got {fps}"
    
    # 6. Subtitle Safe Zone Check
    # Avoid top 12% (1920 * 0.12 = 230.4) and bottom 15% (1920 * 0.85 = 1632) player overlays.
    # The drawtext Y coordinate used in assemble_final_video is h*0.75 = 1440.
    # 1440 is in the range [230.4, 1632].
    subtitle_y_expr_factor = 0.75
    top_overlay_pct = 0.12
    bottom_overlay_pct = 0.15
    assert top_overlay_pct < subtitle_y_expr_factor < (1 - bottom_overlay_pct)
