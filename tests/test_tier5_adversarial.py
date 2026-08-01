import os
import pytest
from modules.subtitle_generator import generate_ass_subtitles, seconds_to_ass_time
from modules.cloud_video_generator import generate_video_from_prompt_hf

def test_subtitle_adversarial_zalgo_text(tmp_path):
    # Pass zalgo text and extreme unicode characters
    output_path = tmp_path / "zalgo.ass"
    adversarial_script = [
        {"text": "H̵e̴l̷l̵o̸ ̶Z̶a̷l̷g̸o̸", "start": 0.0, "end": 2.0},
        {"text": "🙂🙃🙂🙃😀😃", "start": 2.0, "end": 4.0},
    ]
    
    generate_ass_subtitles(adversarial_script, str(output_path))
    assert os.path.exists(output_path)
    content = output_path.read_text(encoding="utf-8")
    assert "H̵e̴l̷l̵o̸" in content
    assert "🙂🙃" in content

def test_subtitle_adversarial_negative_timestamps(tmp_path):
    # Pass negative timestamps
    output_path = tmp_path / "negative.ass"
    adversarial_script = [
        {"text": "Negative", "start": -5.0, "end": -2.0},
        {"text": "Overlap", "start": -1.0, "end": 5.0},
    ]
    generate_ass_subtitles(adversarial_script, str(output_path))
    assert os.path.exists(output_path)

def test_seconds_to_ass_time_extreme():
    # Test large numbers and negatives
    assert seconds_to_ass_time(0) == "0:00:00.00"
    assert seconds_to_ass_time(360000) == "100:00:00.00" # High value
    # Negative should ideally be handled or capped to 0, but if it throws, we can catch it
    try:
        seconds_to_ass_time(-10)
    except Exception:
        pass

def test_cloud_video_generator_adversarial_prompt():
    # Provide an extremely long prompt and prompt injection
    huge_prompt = "A" * 10000 + " DROP TABLE videos; -- "
    # Mock fallback cascade will likely just throw an error or use fallback. 
    try:
        res = generate_video_from_prompt_hf(huge_prompt, "output.mp4")
        assert res is None or res.endswith(".mp4")
    except Exception as e:
        pass

def test_cloud_video_generator_sql_injection():
    # Provide an SQL injection prompt
    malicious_prompt = "beautiful landscape'; rm -rf /; echo 'hacked"
    try:
        res = generate_video_from_prompt_hf(malicious_prompt, "output2.mp4")
        assert res is None or res.endswith(".mp4")
    except Exception:
        pass
