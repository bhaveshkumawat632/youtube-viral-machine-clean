import os
import pytest
import subprocess
from unittest.mock import patch, MagicMock

from modules.audio_mixer import mix_cinematic_audio
from vidrush_pipeline import assemble_final_video, generate_visual_cut
from conftest import create_mock_audio, create_mock_video

def test_sidechaincompress_filter_present(tmp_path, monkeypatch):
    vo = os.path.join(tmp_path, "vo.mp3")
    bgm = os.path.join(tmp_path, "bgm.mp3")
    create_mock_audio(vo, duration=3.0)
    create_mock_audio(bgm, duration=5.0)
    out = os.path.join(tmp_path, "mixed.mp3")
    
    run_calls = []
    original_run = subprocess.run
    
    def mock_run(cmd, *args, **kwargs):
        run_calls.append(cmd)
        return original_run(cmd, *args, **kwargs)
        
    monkeypatch.setattr(subprocess, "run", mock_run)
    
    mix_cinematic_audio(vo, bgm_path=bgm, output_path=out)
    
    # Assert that a subprocess run call contains sidechaincompress
    found = False
    for cmd in run_calls:
        cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
        if "sidechaincompress" in cmd_str:
            found = True
            break
            
    assert found, "Expected FFmpeg command to contain 'sidechaincompress' when BGM is present"

def test_ass_filter_present_during_assembly(tmp_path, monkeypatch):
    vo = os.path.join(tmp_path, "vo.mp3")
    v1 = os.path.join(tmp_path, "v1.mp4")
    create_mock_audio(vo, duration=3.0)
    create_mock_video(v1, duration=3.0)
    
    scenes_data = [
        {"text": "Hello secret brain", "audio": vo, "video": v1, "duration": 3.0}
    ]
    
    run_calls = []
    original_run = subprocess.run
    
    def mock_run(cmd, *args, **kwargs):
        run_calls.append(cmd)
        if isinstance(cmd, list) and any("ass=" in arg for arg in cmd):
            # mock the final video creation to prevent heavy rendering in testing
            out_file = cmd[-1]
            create_mock_video(out_file, duration=3.0)
            return subprocess.CompletedProcess(cmd, 0, stdout=b"", stderr=b"")
        return original_run(cmd, *args, **kwargs)
        
    monkeypatch.setattr(subprocess, "run", mock_run)
    
    all_words = [
        {"text": "Hello", "start": 0.0, "end": 1.0},
        {"text": "secret", "start": 1.0, "end": 2.0},
        {"text": "brain", "start": 2.0, "end": 3.0}
    ]
    
    with patch("modules.background_music.generate_background_tone") as mock_bgm:
        def side_effect_bgm(duration, output_path, style='ambient'):
            create_mock_audio(output_path, duration=duration)
            return output_path
        mock_bgm.side_effect = side_effect_bgm
        
        assemble_final_video(scenes_data, all_words)
    
    found_ass = False
    for cmd in run_calls:
        cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
        if "ass=" in cmd_str:
            found_ass = True
            break
            
    assert found_ass, "Expected FFmpeg command to use 'ass' filter to burn subtitles"

def test_4_tier_fallback_logic(tmp_path, monkeypatch):
    motion_path = os.path.join(tmp_path, "motion_0_1.mp4")
    
    # 1. Tier 1: AI Video (succeeds)
    with patch("modules.cloud_video_generator.generate_video_from_prompt_hf") as mock_ai:
        def side_effect_ai(prompt, output_path):
            create_mock_video(output_path, duration=2.0)
            return output_path
        mock_ai.side_effect = side_effect_ai
        
        res = generate_visual_cut("glowing brain", 0, 1, 2.0)
        assert os.path.exists(res)
        mock_ai.assert_called_once()
        
    # 2. Tier 2: Stock Video (AI fails, Stock succeeds)
    with patch("modules.cloud_video_generator.generate_video_from_prompt_hf", side_effect=RuntimeError("AI Failed")), \
         patch("modules.stock_video_generator.get_pexels_video") as mock_stock:
         
        def side_effect_stock(query, output_path):
            create_mock_video(output_path, duration=2.0)
            return output_path
        mock_stock.side_effect = side_effect_stock
        
        res = generate_visual_cut("glowing brain", 0, 1, 2.0)
        assert os.path.exists(res)
        mock_stock.assert_called_once()
        
    # 3. Tier 3: Local Loops (AI fails, Stock fails, Local loop exists)
    local_loop_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backgrounds", "test_bg.mp4")
    os.makedirs(os.path.dirname(local_loop_path), exist_ok=True)
    create_mock_video(local_loop_path, duration=10.0)
    
    with patch("modules.cloud_video_generator.generate_video_from_prompt_hf", side_effect=RuntimeError("AI Failed")), \
         patch("modules.stock_video_generator.get_pexels_video", side_effect=RuntimeError("Stock Failed")):
         
         res = generate_visual_cut("glowing brain", 0, 1, 2.0)
         assert os.path.exists(res)
         
    # 4. Tier 4: FFmpeg dynamic moving gradient loops (All previous fail)
    original_exists = os.path.exists
    def mock_exists_no_bg(path):
        if "backgrounds" in str(path):
            return False
        return original_exists(path)
        
    with patch("modules.cloud_video_generator.generate_video_from_prompt_hf", side_effect=RuntimeError("AI Failed")), \
         patch("modules.stock_video_generator.get_pexels_video", side_effect=RuntimeError("Stock Failed")), \
         patch("os.path.exists", side_effect=mock_exists_no_bg):
         
         res = generate_visual_cut("glowing brain", 0, 1, 2.0)
         assert os.path.exists(res)
