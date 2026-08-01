import os
import sys
import time
import subprocess

sys.path.insert(0, '/home/junglee01/youtube-viral-machine')
from modules.subtitle_generator import transcribe_audio, generate_ass_subtitles
from config import OUTPUT_DIR, TEMP_DIR

def get_words_for_segment(raw_video, duration):
    temp_audio = os.path.join(TEMP_DIR, f"demo_audio.mp3")
    if os.path.exists(temp_audio):
        os.remove(temp_audio)
        
    subprocess.run(["ffmpeg", "-y", "-ss", "0", "-i", raw_video, "-t", str(duration), "-q:a", "0", "-map", "a", temp_audio], capture_output=True)
    words = transcribe_audio(temp_audio, language="en")
    return words, temp_audio

def create_demo_16x9(raw_video, duration, output_dir):
    width, height = 1920, 1080
    temp_ass = os.path.join(TEMP_DIR, "demo_16x9.ass")
    output_mp4 = os.path.join(output_dir, "demo_30s_16x9.mp4")
    
    words, temp_audio = get_words_for_segment(raw_video, duration)
    generate_ass_subtitles(words, temp_ass, video_width=width, video_height=height, highlight=True, highlight_color="#00FFFF")
    
    watermark = "drawtext=text='Aghori Studio':fontcolor=white@0.15:fontsize=72:x=(w-tw)/2:y=(h-th)/2"
    
    filter_complex = (
        f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},eq=contrast=1.15:saturation=1.2:brightness=0.02,"
        f"unsharp=3:3:0.5:3:3:0.5,{watermark},"
        f"subtitles={temp_ass}[v]"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-i", raw_video,
        "-i", temp_audio,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "1:a",
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        output_mp4
    ]
    subprocess.run(cmd)
    return output_mp4

def create_demo_9x16(raw_video, duration, output_dir):
    width, height = 1080, 1920
    temp_ass = os.path.join(TEMP_DIR, "demo_9x16.ass")
    output_mp4 = os.path.join(output_dir, "demo_30s_9x16.mp4")
    
    words, temp_audio = get_words_for_segment(raw_video, duration)
    generate_ass_subtitles(words, temp_ass, video_width=width, video_height=height, highlight=True, highlight_color="#FF00FF")
    
    watermark = "drawtext=text='Aghori Studio':fontcolor=white@0.15:fontsize=96:x=(w-tw)/2:y=(h-th)/2"
    
    filter_complex = (
        f"[0:v]scale={width*2}:{height*2}:force_original_aspect_ratio=increase,"
        f"zoompan=z='if(lte(time,1), 1.4-0.4*time, 1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={width}x{height}:fps=30,"
        f"eq=contrast=1.2:saturation=1.25:brightness=0.03,"
        f"unsharp=3:3:0.5:3:3:0.5,{watermark},"
        f"subtitles={temp_ass}[v]"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-ss", "0",
        "-i", raw_video,
        "-i", temp_audio,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "1:a",
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        output_mp4
    ]
    subprocess.run(cmd)
    return output_mp4

if __name__ == "__main__":
    raw_video = "/home/junglee01/youtube-viral-machine/backgrounds/fifa_with_audio.mp4"
    output_dir = os.path.join(OUTPUT_DIR, "demo")
    os.makedirs(output_dir, exist_ok=True)
    
    print("Generating 16:9 Demo...")
    create_demo_16x9(raw_video, 30, output_dir)
    print("Generating 9:16 Demo...")
    create_demo_9x16(raw_video, 30, output_dir)
    print("Done!")
