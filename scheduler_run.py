import os
import sys
import time
import asyncio
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_production import scenes, TEST_DIR, generate_audio, fallback_synthesis, qa_inspection
from modules.youtube_uploader import upload_video

# 8 Hours in seconds
WAIT_TIME = 0

def countdown(t):
    print("=========================================================")
    print("⏳ SCHEDULER ENGAGED: 8-Hour No-Stress Mode Activated")
    print("=========================================================")
    while t > 0:
        mins, secs = divmod(t, 60)
        hours, mins = divmod(mins, 60)
        timer = f'{hours:02d}:{mins:02d}:{secs:02d}'
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ⏳ Countdown: {timer} remaining...")
        
        # Sleep in 60-second chunks to keep terminal logs clean and readable
        time.sleep(60)
        t -= 60
        
    print("\n⏰ Timer complete! Engaging automated production...")

async def no_stress_production():
    print("\n=========================================================")
    print("🎬 AGHORI STUDIO: NO-STRESS MORNING PRODUCTION RUN")
    print("=========================================================")
    print("📡 Mode: 100% Local Fallback (Slate Gray Cinematic)")
    print("=========================================================\n")
    
    generated_clips = []
    
    for scene in scenes:
        print(f"\n🎬 Processing Scene {scene['id']}...")
        audio_path = os.path.join(TEST_DIR, f"morning_scene_{scene['id']}.mp3")
        video_raw_path = os.path.join(TEST_DIR, f"morning_scene_{scene['id']}_raw.mp4")
        video_final_path = os.path.join(TEST_DIR, f"morning_scene_{scene['id']}_final.mp4")
        
        # Audio
        await generate_audio(scene['text'], audio_path)
        
        # Bypass Cloud completely -> Force Fallback Synthesis
        fallback_synthesis(scene['text'], video_raw_path, scene['duration'])
        
        # QA Check
        if qa_inspection(scene['id'], video_raw_path):
            print("🧵 Stitching Audio & Slate Video Canvas...")
            cmd = [
                "ffmpeg", "-y",
                "-i", video_raw_path,
                "-i", audio_path,
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-shortest",
                video_final_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            generated_clips.append(video_final_path)
            print(f"✅ Scene {scene['id']} successfully rendered.")
        else:
            print(f"❌ QA Failed on Scene {scene['id']}. Skipping...")

    if generated_clips:
        print("\n🎞️ Chief Editor: Stitching Master Timeline...")
        concat_list_path = os.path.join(TEST_DIR, "morning_concat_list.txt")
        with open(concat_list_path, "w") as f:
            for clip in generated_clips:
                f.write(f"file '{clip}'\n")
                
        master_output = os.path.join(TEST_DIR, f"AGHORI_MORNING_SHORT_{int(time.time())}.mp4")
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_list_path, "-c", "copy", master_output
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("\n🚀 INITIATING PUBLIC YOUTUBE UPLOAD...")
        meta = {
            "title": "Escape The Matrix: The Secret 1% Rule Exposed! 👁️🔥 #shorts #motivation",
            "description": "Stop scrolling. Start building. Awaken from the simulation.\\n\\n🎬 Produced perfectly by Aghori Studio AI.\\n#EscapeTheMatrix #Awakening #Motivation",
            "tags": ["Escape The Matrix", "Awakening", "Motivation", "Shorts", "Viral", "Cyberpunk", "Aghori Studio"],
            "category_id": "27"
        }
        
        success = upload_video(master_output, meta)
        
        if success:
            print("\n=========================================================")
            print("✅ AUTOMATED MORNING RUN FULLY COMPLETE & UPLOADED LIVE!")
            print("=========================================================")
        else:
            print("\n❌ Upload failed. Video safely locked in Testing/output.")
    else:
        print("\n❌ Critical Failure: No scenes were generated.")

if __name__ == "__main__":
    countdown(WAIT_TIME)
    asyncio.run(no_stress_production())
