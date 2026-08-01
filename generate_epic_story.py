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

def get_words_for_segment(raw_video, start_time, duration, hook_text=None):
    temp_audio = os.path.join(TEMP_DIR, f"temp_audio_{start_time}.mp3")
    if os.path.exists(temp_audio):
        os.remove(temp_audio)
        
    subprocess.run(["ffmpeg", "-y", "-ss", str(start_time), "-i", raw_video, "-t", str(duration), "-q:a", "0", "-map", "a", temp_audio], capture_output=True)
    if not os.path.exists(temp_audio):
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", str(duration), "-q:a", "0", temp_audio], capture_output=True)
    
    words = transcribe_audio(temp_audio, language="en")
    if not words:
        words = [{"text": "UNBELIEVABLE!", "start": 0.0, "end": 2.0}]
        
    for w in words:
        txt = w["text"].lower()
        if "missy" in txt or "messi" in txt:
            w["text"] = "Messi"
            
    if hook_text:
        # hook at the end of duration
        start_hook = duration - 5.0
        words.append({"text": hook_text, "start": start_hook, "end": start_hook + 4.0})
        words = sorted(words, key=lambda k: k['start'])
        
    return words, temp_audio

def create_long_form_video(raw_video, total_duration, output_dir):
    print("🚀 Rendering 16:9 Long-Form Masterpiece...")
    width, height = 1920, 1080
    temp_ass = os.path.join(TEMP_DIR, "long_form_subtitles.ass")
    output_mp4 = os.path.join(output_dir, "long_form_epic_story_16x9.mp4")
    
    words, temp_audio = get_words_for_segment(raw_video, 0, total_duration)
    generate_ass_subtitles(words, temp_ass, video_width=width, video_height=height, highlight=True, highlight_color="#00FFFF")
    
    fps = 30
    zoom_expr = "1.0"
    shake_x = "iw/2-ow/2"
    shake_y = "ih/2-oh/2"
    pad_w = int(width * 1.05)
    pad_h = int(height * 1.05)
    
    filter_complex = (
        f"[0:v]scale={width*2}:{height*2}:force_original_aspect_ratio=increase,"
        f"zoompan=z='{zoom_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={pad_w}x{pad_h}:fps={fps},"
        f"crop={width}:{height}:'{shake_x}':'{shake_y}',"
        f"eq=contrast=1.15:saturation=1.2:brightness=0.02,"
        f"unsharp=3:3:0.5:3:3:0.5,"
        f"subtitles={temp_ass}[v]"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-i", raw_video,
        "-i", temp_audio,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "1:a",
        "-t", str(total_duration),
        "-c:v", "libx264", "-preset", "faster", "-crf", "24",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        output_mp4
    ]
    subprocess.run(cmd)
    print(f"✅ Long Form Generated: {output_mp4}")
    return output_mp4

def create_short_part(raw_video, start_time, duration, part_num, hook_text, output_dir):
    print(f"🚀 Rendering 9:16 Short Part {part_num}...")
    width, height = 1080, 1920
    temp_ass = os.path.join(TEMP_DIR, f"short_part{part_num}_subtitles.ass")
    output_mp4 = os.path.join(output_dir, f"short_part{part_num}_9x16.mp4")
    
    words, temp_audio = get_words_for_segment(raw_video, start_time, duration, hook_text)
    generate_ass_subtitles(words, temp_ass, video_width=width, video_height=height, highlight=True, highlight_color="#FF00FF")
    
    fps = 30
    zoom_expr = f"if(lte(time,1), 1.4-0.4*time, 1.0)"
    shake_x = "iw/2-ow/2+10*sin(t*20)*exp(-t*4)"
    shake_y = "ih/2-oh/2+10*cos(t*25)*exp(-t*4)"
    pad_w = int(width * 1.1)
    pad_h = int(height * 1.1)
    
    filter_complex = (
        f"[0:v]scale={width*2}:{height*2}:force_original_aspect_ratio=increase,"
        f"zoompan=z='{zoom_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={pad_w}x{pad_h}:fps={fps},"
        f"crop={width}:{height}:'{shake_x}':'{shake_y}',"
        f"colorlevels=rimin=0.8:gimin=0.8:bimin=0.8:enable='between(t,0,0.2)',"
        f"eq=contrast=1.2:saturation=1.25:brightness=0.03,"
        f"unsharp=3:3:0.5:3:3:0.5,"
        f"subtitles={temp_ass}[v]"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_time),
        "-i", raw_video,
        "-i", temp_audio,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "1:a",
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "faster", "-crf", "24",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        output_mp4
    ]
    subprocess.run(cmd)
    print(f"✅ Short Part {part_num} Generated: {output_mp4}")
    return output_mp4

if __name__ == "__main__":
    print("Initiating Epic Story Process...")
    raw_video = "/home/junglee01/youtube-viral-machine/backgrounds/fifa_with_audio.mp4"
    output_dir = os.path.join(OUTPUT_DIR, f"epic_story_{int(time.time())}")
    os.makedirs(output_dir, exist_ok=True)
    
    # 6-minute total story (360 seconds)
    total_duration = 360
    
    # 1. Generate Long-Form 16:9
    long_video = create_long_form_video(raw_video, total_duration, output_dir)
    if run_quality_review(long_video):
        vid_url = upload_to_youtube(long_video, niche="football", title_hint="The Ultimate Football Epic Story (Full Video)")
        if vid_url:
            print(f"🧹 Upload confirmed. Deleting local file: {long_video}")
            os.remove(long_video)
        
    # 2. Generate Shorts (Part 1 and Part 2) in 9:16
    # Part 1 (0 to 180s)
    part1_video = create_short_part(raw_video, 0, 180, part_num=1, hook_text="Wait for Part 2! You won't believe what happens next...", output_dir=output_dir)
    if run_quality_review(part1_video):
        vid_url = upload_to_youtube(part1_video, niche="football", title_hint="Football Epic Story - Part 1")
        if vid_url:
            print(f"🧹 Upload confirmed. Deleting local file: {part1_video}")
            os.remove(part1_video)
        
    # Part 2 (180s to 360s)
    part2_video = create_short_part(raw_video, 180, 180, part_num=2, hook_text="Subscribe for more epic stories!", output_dir=output_dir)
    if run_quality_review(part2_video):
        vid_url = upload_to_youtube(part2_video, niche="football", title_hint="Football Epic Story - Part 2")
        if vid_url:
            print(f"🧹 Upload confirmed. Deleting local file: {part2_video}")
            os.remove(part2_video)
        
    print("🎉 Epic Story Complete!")
