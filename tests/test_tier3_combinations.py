import os
import json
import pytest
from unittest.mock import patch
from modules.voiceover import generate_voiceover, get_audio_duration
from modules.audio_mixer import mix_cinematic_audio
from vidrush_pipeline import (
    build_scene_visuals,
    assemble_final_video,
    run_qa_gate,
    log_asset,
    MANIFEST_FILE,
    ASSETS_DIR
)
import subprocess

def test_combination_voice_subtitles_sync(tmp_path):
    # Cross-feature: Voice TTS + word boundary timestamps
    vo_path = os.path.join(tmp_path, "combination_vo.mp3")
    script = "This is a cross feature test scenario verifying alignment"
    audio_path, boundaries_path, word_boundaries = generate_voiceover(script, vo_path)
    
    assert os.path.exists(audio_path)
    assert os.path.exists(boundaries_path)
    
    # Assert duration is greater than 0
    duration = get_audio_duration(audio_path)
    assert duration > 0.0
    
    # Assert last word boundary end time is close to the audio duration
    if word_boundaries:
        last_word_end = word_boundaries[-1]["end_ms"] / 1000.0
        assert abs(last_word_end - duration) <= 1.0  # within 1 second

def test_combination_audio_video_assembly(tmp_path):
    # Cross-feature: Audio mixer output mixed with video assembly
    vo = os.path.join(tmp_path, "vo.mp3")
    bgm = os.path.join(tmp_path, "bgm.mp3")
    from conftest import create_mock_audio, create_mock_video
    create_mock_audio(vo, duration=4.0)
    create_mock_audio(bgm, duration=4.0)
    
    mixed_audio = os.path.join(tmp_path, "mix.mp3")
    mix_cinematic_audio(vo, bgm_path=bgm, output_path=mixed_audio)
    assert os.path.exists(mixed_audio)
    
    # Generate 2 scenes of video
    v1 = os.path.join(tmp_path, "v1.mp4")
    v2 = os.path.join(tmp_path, "v2.mp4")
    create_mock_video(v1, duration=2.0)
    create_mock_video(v2, duration=2.0)
    
    # Assemble video using a scene list
    scenes_data = [
        {"text": "Scene 1", "audio": vo, "video": v1, "duration": 2.0},
        {"text": "Scene 2", "audio": vo, "video": v2, "duration": 2.0}
    ]
    
    final_output, total_dur = assemble_final_video(scenes_data)
    assert os.path.exists(final_output)
    assert abs(total_dur - 4.0) <= 0.5

def test_combination_fallback_cascade_to_local_loop():
    # Cross-feature: Visual sourcing cloud failure -> stock failure -> local loop success
    # Mock spaces to raise exception, Pexels to fail, Coverr to fail
    with patch("gradio_client.Client", side_effect=Exception("Cloud offline")):
        with patch.dict(os.environ, {"PEXELS_API_KEY": ""}):
            with patch("urllib.request.urlopen", side_effect=Exception("Coverr offline")):
                # When build_scene_visuals is called, it should fallback to local loops.
                # Let's ensure manifest is cleared first
                os.makedirs(ASSETS_DIR, exist_ok=True)
                if os.path.exists(MANIFEST_FILE):
                    os.remove(MANIFEST_FILE)
                    
                scene = {"text": "Test Scene", "suggested_visual_keyword": "neon light"}
                res = build_scene_visuals(scene, index=9, duration=3.0)
                
                assert os.path.exists(res)
                assert os.path.getsize(res) > 5000
                
                # Check manifest.json: source must be "local" or "ffmpeg_synthetic"
                assert os.path.exists(MANIFEST_FILE)
                with open(MANIFEST_FILE, "r") as f:
                    manifest = json.load(f)
                    assert len(manifest) >= 1
                    assert manifest[-1]["source"] in ["local", "ffmpeg_synthetic"]

@pytest.mark.anyio
async def test_combination_full_pipeline_dry_run():
    # Run the full pipeline in dry-run mode (using mock interfaces)
    import vidrush_pipeline
    
    # Clear manifest first
    if os.path.exists(MANIFEST_FILE):
        os.remove(MANIFEST_FILE)
        
    # Run pipeline main function with no-upload option
    with patch("sys.argv", ["vidrush_pipeline.py", "--no-upload"]):
        await vidrush_pipeline.main()
        
    # Verify outputs
    assert os.path.exists(vidrush_pipeline.LOG_FILE)
    assert os.path.exists(MANIFEST_FILE)
    
    # Check if VIDRUSH_MASTER.mp4 or a failed/success video exists
    master_path = os.path.join(vidrush_pipeline.OUTPUT_DIR, "VIDRUSH_MASTER.mp4")
    # If QA gate failed, it might be in failed directory
    if not os.path.exists(master_path):
        failed_files = os.listdir(vidrush_pipeline.FAILED_DIR)
        assert len(failed_files) >= 1
    else:
        assert os.path.exists(master_path)
