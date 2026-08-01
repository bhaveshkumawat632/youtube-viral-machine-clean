import os
import shutil
import json
import pytest
from config import TEMP_DIR, ASSETS_DIR
from modules.subtitle_generator import (
    hex_to_ass_color,
    seconds_to_ass_time,
    group_words_into_lines,
    generate_ass_subtitles,
    generate_srt_subtitles
)
from modules.audio_mixer import mix_cinematic_audio
from modules.voiceover import generate_voiceover, get_audio_duration
from modules.cloud_video_generator import generate_video_from_prompt_hf
from modules.stock_video_generator import get_pexels_video
from modules.pexels_downloader import search_and_download_pexels_videos
from vidrush_pipeline import (
    get_emotion_voice_settings,
    build_scene_visuals,
    run_qa_gate,
    log_asset,
    write_log,
    create_alert
)

# ---------------------------------------------------------
# FEATURE 1: SUBTITLES & TRANSCRIPTION
# ---------------------------------------------------------

def test_hex_to_ass_color_happy():
    assert hex_to_ass_color("#FFFFFF") == "&H00FFFFFF&"
    assert hex_to_ass_color("#000000") == "&H00000000&"
    assert hex_to_ass_color("#FF0000") == "&H000000FF&"  # Red -> Blue in ASS (BBGGRR)
    assert hex_to_ass_color("#0000FF") == "&H00FF0000&"  # Blue -> Red in ASS (BBGGRR)
    assert hex_to_ass_color("00FF00") == "&H0000FF00&"

def test_seconds_to_ass_time_happy():
    assert seconds_to_ass_time(0.0) == "0:00:00.00"
    assert seconds_to_ass_time(5.25) == "0:00:05.25"
    assert seconds_to_ass_time(65.5) == "0:01:05.50"
    assert seconds_to_ass_time(3600.0) == "1:00:00.00"
    assert seconds_to_ass_time(12.3456) == "0:00:12.34"

def test_group_words_into_lines_happy():
    words = [{"text": f"w{i}"} for i in range(5)]
    lines = group_words_into_lines(words, max_words_per_line=2)
    assert len(lines) == 3
    assert len(lines[0]) == 2
    assert len(lines[2]) == 1

def test_generate_ass_subtitles_happy(tmp_path):
    words = [
        {"text": "Hello", "start": 0.0, "end": 0.5},
        {"text": "World", "start": 0.5, "end": 1.0}
    ]
    output_path = os.path.join(tmp_path, "subtitles.ass")
    res = generate_ass_subtitles(words, output_path)
    assert res == output_path
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "[Script Info]" in content
        assert "Style: Default" in content
        assert "Dialogue:" in content

def test_generate_srt_subtitles_happy(tmp_path):
    words = [
        {"text": "Hello", "start": 0.0, "end": 0.5},
        {"text": "World", "start": 0.5, "end": 1.0}
    ]
    output_path = os.path.join(tmp_path, "subtitles.srt")
    res = generate_srt_subtitles(words, output_path)
    assert res == output_path
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "1\n00:00:00,000 --> 00:00:01,000" in content

# ---------------------------------------------------------
# FEATURE 2: AUDIO LAYERING & MIXING
# ---------------------------------------------------------

@pytest.fixture
def dummy_audio_files(tmp_path):
    vo = os.path.join(tmp_path, "voice.mp3")
    bgm = os.path.join(tmp_path, "bgm.mp3")
    sfx = os.path.join(tmp_path, "sfx.mp3")
    
    # We use conftest helper (which might be in conftest namespace or we just call subprocess)
    from conftest import create_mock_audio
    create_mock_audio(vo, duration=3.0)
    create_mock_audio(bgm, duration=5.0)
    create_mock_audio(sfx, duration=1.0)
    return vo, bgm, sfx

def test_emotion_settings_happy():
    rate, pitch = get_emotion_voice_settings("shocked")
    assert rate == "+10%"
    assert pitch == "+5Hz"
    rate, pitch = get_emotion_voice_settings("tense")
    assert rate == "-5%"
    rate, pitch = get_emotion_voice_settings("neutral")
    assert rate == "+0%"

def test_generate_voiceover_happy(tmp_path):
    vo_path = os.path.join(tmp_path, "vo.mp3")
    audio, words_json, words_list = generate_voiceover("This is a mock script.", vo_path)
    assert audio == vo_path
    assert os.path.exists(audio)
    assert os.path.exists(words_json)
    assert len(words_list) > 0
    assert get_audio_duration(audio) > 0.0

def test_mix_audio_vo_only(tmp_path, dummy_audio_files):
    vo, _, _ = dummy_audio_files
    out = os.path.join(tmp_path, "mixed_vo.mp3")
    res = mix_cinematic_audio(vo, output_path=out)
    assert res == out
    assert os.path.exists(out)

def test_mix_audio_vo_bgm(tmp_path, dummy_audio_files):
    vo, bgm, _ = dummy_audio_files
    out = os.path.join(tmp_path, "mixed_bgm.mp3")
    res = mix_cinematic_audio(vo, bgm_path=bgm, output_path=out)
    assert res == out
    assert os.path.exists(out)

def test_mix_audio_full_layering(tmp_path, dummy_audio_files):
    vo, bgm, sfx = dummy_audio_files
    out = os.path.join(tmp_path, "mixed_full.mp3")
    sfx_list = [{"path": sfx, "start": 1.0, "volume": 0.3}]
    res = mix_cinematic_audio(vo, bgm_path=bgm, sfx_list=sfx_list, output_path=out)
    assert res == out
    assert os.path.exists(out)

# ---------------------------------------------------------
# FEATURE 3: VISUAL SOURCING & FALLBACK
# ---------------------------------------------------------

def test_cloud_video_generation_happy(tmp_path):
    out = os.path.join(tmp_path, "cloud_test.mp4")
    res = generate_video_from_prompt_hf("dark cyberpunk room", out)
    assert res == out
    assert os.path.exists(out)
    assert os.path.getsize(out) > 1000

def test_pexels_stock_video_happy(tmp_path):
    # Mocked requests.get will intercept this search and download
    os.environ["PEXELS_API_KEY"] = "mock_key"
    out = os.path.join(tmp_path, "pexels_stock.mp4")
    res = get_pexels_video("glowing brain", out)
    assert res == out
    assert os.path.exists(out)
    assert os.path.getsize(out) >= 250000

def test_pexels_downloader_multiple_happy(tmp_path):
    os.environ["PEXELS_API_KEY"] = "mock_key"
    res = search_and_download_pexels_videos(["dramatic clock", "office desk"], str(tmp_path), pexels_api_key="mock_key", target_duration=10)
    assert len(res) >= 1
    assert os.path.exists(res[0])
    assert os.path.getsize(res[0]) >= 250000

def test_build_scene_visuals_happy():
    # Scene with low duration (no cuts)
    scene = {"text": "Hello", "suggested_visual_keyword": "neon light"}
    res = build_scene_visuals(scene, 1, duration=3.0)
    assert os.path.exists(res)
    assert os.path.getsize(res) > 1000

def test_build_scene_visuals_with_cuts_happy():
    # Scene with > 4.0 duration (triggers cuts and concat)
    scene = {"text": "Hello world this is dramatic", "suggested_visual_keyword": "neon clock"}
    res = build_scene_visuals(scene, 2, duration=5.0)
    assert os.path.exists(res)
    assert os.path.getsize(res) > 1000

# ---------------------------------------------------------
# FEATURE 4: QA GATE & COMPLIANCE
# ---------------------------------------------------------

def test_log_asset_happy():
    # Make sure manifest folder exists
    os.makedirs(ASSETS_DIR, exist_ok=True)
    manifest_path = os.path.join(ASSETS_DIR, "manifest.json")
    if os.path.exists(manifest_path):
        os.remove(manifest_path)
    
    log_asset("asset1", "pexels.com", "pexels_license", "https://pexels.com/mock")
    assert os.path.exists(manifest_path)
    with open(manifest_path, "r") as f:
        data = json.load(f)
        assert len(data) == 1
        assert data[0]["asset_id"] == "asset1"
        assert data[0]["source"] == "pexels.com"

def test_write_log_happy():
    from vidrush_pipeline import LOG_FILE
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    write_log(
        "✅ SUCCESS", "Test Video", 30.0, 5, 1, 0.16, True, 
        "All metrics passed successfully", "Skipped", "", ["pexels_license"]
    )
    assert os.path.exists(LOG_FILE)
    with open(LOG_FILE, "r") as f:
        content = f.read()
        assert "Title: Test Video" in content
        assert "Duration: 30.00s" in content
        assert "QA Gate: PASS" in content

def test_create_alert_happy():
    from vidrush_pipeline import ALERT_FILE
    if os.path.exists(ALERT_FILE):
        os.remove(ALERT_FILE)
    create_alert("FFmpeg binary missing")
    assert os.path.exists(ALERT_FILE)
    with open(ALERT_FILE, "r") as f:
        content = f.read()
        assert "⚠️ URGENT ALERT" in content
        assert "FFmpeg binary missing" in content

def test_run_qa_gate_happy(tmp_path):
    os.makedirs(ASSETS_DIR, exist_ok=True)
    manifest_path = os.path.join(ASSETS_DIR, "manifest.json")
    # Setup mock manifest
    manifest_data = [
        {"asset_id": "1", "source": "pexels.com", "license_type": "pexels_license", "url": "mock"},
        {"asset_id": "2", "source": "local", "license_type": "royalty_free_local", "url": "mock"},
        {"asset_id": "3", "source": "ffmpeg_synthetic", "license_type": "public_domain", "url": "mock"}
    ]
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f)
        
    mock_vid = os.path.join(tmp_path, "vid.mp4")
    # 3 visuals, 1 synthetic (ffmpeg_synthetic) -> ratio = 1/3 = 33.3%? Wait, that exceeds 30%!
    # Let's adjust mock manifest so that fallback ratio is <= 30%: e.g. 3 real, 1 synthetic -> 25%
    manifest_data = [
        {"asset_id": "1", "source": "pexels.com", "license_type": "pexels_license", "url": "mock"},
        {"asset_id": "2", "source": "local", "license_type": "royalty_free_local", "url": "mock"},
        {"asset_id": "3", "source": "pexels.com", "license_type": "pexels_license", "url": "mock"},
        {"asset_id": "4", "source": "ffmpeg_synthetic", "license_type": "public_domain", "url": "mock"}
    ]
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f)
        
    passed, reason, real, fallback, ratio, licenses = run_qa_gate(mock_vid, 35.0)
    assert passed is True
    assert real == 3
    assert fallback == 1
    assert ratio == 0.25
    assert "pexels_license" in licenses
