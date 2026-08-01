import os
import sys
import time
import subprocess

sys.path.insert(0, '/home/junglee01/youtube-viral-machine')
from modules.subtitle_generator import transcribe_audio, generate_ass_subtitles
from modules.video_maker import create_video_from_audio_and_subtitles
from config import OUTPUT_DIR, TEMP_DIR

def generate_real_fifa_video():
    print("🚀 Starting generation of Real FIFA Audio Short...")
    output_dir = os.path.join(OUTPUT_DIR, f"real_fifa_world_cup_{int(time.time())}")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    bg_video_original = "/home/junglee01/youtube-viral-machine/backgrounds/fifa_with_audio.mp4"
    bg_video_trimmed = os.path.join(TEMP_DIR, "fifa_60s_trimmed.mp4")
    temp_audio = os.path.join(TEMP_DIR, "real_fifa_audio.mp3")
    temp_ass = os.path.join(TEMP_DIR, "real_fifa_subtitles.ass")
    output_mp4 = os.path.join(output_dir, "real_fifa_iconic_moments.mp4")
    
    if not os.path.exists(bg_video_original):
        print(f"❌ Error: {bg_video_original} not found!")
        return

    print("✂️ Trimming original video to 60 seconds...")
    subprocess.run([
        "ffmpeg", "-y", "-ss", "00:00:30", "-i", bg_video_original, "-t", "60", 
        "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", bg_video_trimmed
    ], capture_output=True)

    print("🎵 Extracting audio from trimmed video...")
    subprocess.run([
        "ffmpeg", "-y", "-i", bg_video_trimmed, "-q:a", "0", "-map", "a", temp_audio
    ], capture_output=True)
    
    print("📝 Transcribing original commentator audio with Whisper...")
    # The commentary is in English or Spanish, we use 'en' as it's a global compilation
    words = transcribe_audio(temp_audio, language="en")
    
    if not words:
        print("⚠️ Whisper failed to detect any words in the real audio!")
        words = [{"text": "Iconic", "start": 0.0, "end": 2.0}, {"text": "Moment!", "start": 2.0, "end": 4.0}]
        
    generate_ass_subtitles(words, temp_ass)
    
    print("🎬 Rendering Final Video with Audiogram and Subtitles...")
    create_video_from_audio_and_subtitles(
        temp_audio, temp_ass, output_mp4,
        background_video=bg_video_trimmed,
        video_format="shorts"
    )
    print(f"✅ Finished! Video saved to: {output_mp4}")

if __name__ == "__main__":
    generate_real_fifa_video()
