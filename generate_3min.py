import os
import sys
import time
import subprocess
import shutil

sys.path.insert(0, '/home/junglee01/youtube-viral-machine')
from modules.subtitle_generator import transcribe_audio, generate_ass_subtitles
from modules.quality_review import run_quality_review
from modules.upload_manager import upload_to_youtube, track_daily_metrics
from config import OUTPUT_DIR, TEMP_DIR

def create_story_video(aspect_ratio="9:16"):
    print(f"🚀 Rendering the 3-Minute Story Masterpiece ({aspect_ratio})...")
    output_dir = os.path.join(OUTPUT_DIR, f"story_{aspect_ratio.replace(':', 'x')}_{int(time.time())}")
    os.makedirs(output_dir, exist_ok=True)
    
    raw_video = "/home/junglee01/youtube-viral-machine/backgrounds/fifa_with_audio.mp4"
    
    if aspect_ratio == "9:16":
        width, height = 1080, 1920
    else:
        width, height = 1920, 1080
        
    duration = 180  # 3 minutes
    
    temp_audio = os.path.join(TEMP_DIR, f"story_audio_{aspect_ratio.replace(':', 'x')}.mp3")
    temp_ass = os.path.join(TEMP_DIR, f"story_subtitles_{aspect_ratio.replace(':', 'x')}.ass")
    output_mp4 = os.path.join(output_dir, f"full_story_{aspect_ratio.replace(':', 'x')}.mp4")
    
    if os.path.exists(temp_audio):
        os.remove(temp_audio)
        
    print("Extracting Audio...")
    res = subprocess.run(["ffmpeg", "-y", "-i", raw_video, "-t", str(duration), "-q:a", "0", "-map", "a", temp_audio], capture_output=True)
    if not os.path.exists(temp_audio):
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", str(duration), "-q:a", "0", temp_audio], capture_output=True)
    
    print("Transcribing...")
    words = transcribe_audio(temp_audio, language="en")
    if not words:
        words = [{"text": "UNBELIEVABLE!", "start": 0.0, "end": 2.0}]
        
    # Auto-correct common Whisper AI Typos
    for w in words:
        txt = w["text"].lower()
        if "missy" in txt or "messi" in txt:
            w["text"] = "Messi"
        elif "leonardo" in txt:
            w["text"] = "Lionel"
        elif "minutes" in txt:
            w["text"] = "menace"
        elif "for" == txt:
            w["text"] = "forward"
        elif "i'm" in txt or "i’m" in txt:
            w["text"] = "And"
            
    # Add Suspense Hooks
    # Part 1 Hook (around 85s - 90s)
    words.append({"text": "Wait", "start": 85.0, "end": 86.0})
    words.append({"text": "for", "start": 86.0, "end": 86.5})
    words.append({"text": "Part", "start": 86.5, "end": 87.5})
    words.append({"text": "2...", "start": 87.5, "end": 88.5})
    words.append({"text": "You", "start": 88.5, "end": 89.0})
    words.append({"text": "won't", "start": 89.0, "end": 89.5})
    words.append({"text": "believe", "start": 89.5, "end": 90.0})
    words.append({"text": "what", "start": 90.0, "end": 90.5})
    words.append({"text": "happens", "start": 90.5, "end": 91.0})
    words.append({"text": "next!", "start": 91.0, "end": 92.0})

    # Part 2 Hook (around 175s - 180s)
    words.append({"text": "Subscribe", "start": 175.0, "end": 176.0})
    words.append({"text": "for", "start": 176.0, "end": 177.0})
    words.append({"text": "the", "start": 177.0, "end": 178.0})
    words.append({"text": "next", "start": 178.0, "end": 179.0})
    words.append({"text": "episode!", "start": 179.0, "end": 180.0})
    
    # Sort words by start time
    words = sorted(words, key=lambda k: k['start'])

    print("Generating ASS Subtitles...")
    generate_ass_subtitles(words, temp_ass, video_width=width, video_height=height, highlight=True, highlight_color="#00FFFF")
    
    fps = 30
    zoom_expr = f"if(lte(time,1), 1.4-0.4*time, 1.0)"
    shake_x = "iw/2-ow/2+15*sin(t*20)*exp(-t*4)"
    shake_y = "ih/2-oh/2+15*cos(t*25)*exp(-t*4)"
    pad_w = int(width * 1.1)
    pad_h = int(height * 1.1)
    
    # Fast rendering settings for a 3 min video
    preset = "veryfast"
    crf = "23"
    
    filter_complex = (
        f"[0:v]scale={width*2}:{height*2}:force_original_aspect_ratio=increase,"
        f"zoompan=z='{zoom_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={pad_w}x{pad_h}:fps={fps},"
        f"crop={width}:{height}:'{shake_x}':'{shake_y}',"
        f"colorlevels=rimin=0.8:gimin=0.8:bimin=0.8:enable='between(t,0,0.2)',"
        f"eq=contrast=1.15:saturation=1.2:brightness=0.02,"
        f"unsharp=3:3:0.5:3:3:0.5,"
        f"subtitles={temp_ass}[v];"
        f"[1:a]afade=t=out:st=178.5:d=1.5[a]"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-i", raw_video,
        "-i", temp_audio,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "[a]",
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", preset,
        "-crf", crf,
        "-profile:v", "high",
        "-level", "4.1",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        output_mp4
    ]
    
    print(f"🎬 Rendering Video for {aspect_ratio}...")
    subprocess.run(cmd)
    print(f"✅ {aspect_ratio} Story Generated: {output_mp4}")
    return output_mp4

if __name__ == "__main__":
    print("Initiating 3-Minute Story Mode...")
    
    video_9_16 = create_story_video("9:16")
    passed_9_16 = run_quality_review(video_9_16)
    if passed_9_16:
        upload_to_youtube(video_9_16, niche="football", title_hint="Full Story Part 1 & 2")
    
    video_16_9 = create_story_video("16:9")
    passed_16_9 = run_quality_review(video_16_9)
    if passed_16_9:
        upload_to_youtube(video_16_9, niche="football", title_hint="Full Story Part 1 & 2 (Widescreen)")
