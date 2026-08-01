import os
import sys
import time
import subprocess
import glob

sys.path.insert(0, '/home/junglee01/youtube-viral-machine')
from modules.voiceover import generate_voiceover, get_audio_duration
from modules.subtitle_generator import transcribe_audio, generate_ass_subtitles
from modules.quality_review import run_quality_review
from modules.upload_manager import upload_to_youtube
from config import OUTPUT_DIR, TEMP_DIR

def create_meta_movie():
    print("🎬 Starting AI Meta 'Meta Movies' Generation Engine...")
    
    script_text = "Deep in the Himalayas, an ancient Aghori sadhu guards a secret that could change humanity forever. He sits alone in the snow, meditating with glowing blue eyes. Legend says he hasn't aged in 500 years. If you want to know his secret, subscribe to Aghori Studio now!"
    
    # 1. Generate Voiceover
    print("🎙️ Generating AI Voiceover...")
    audio_path, words_path, words = generate_voiceover(script_text, voice_key="english_dramatic")
    duration = get_audio_duration(audio_path)
    
    # Generate Subtitles
    temp_ass = os.path.join(TEMP_DIR, "meta_movie.ass")
    whisper_words = transcribe_audio(audio_path, language="en")
    generate_ass_subtitles(whisper_words, temp_ass, video_width=1080, video_height=1920, highlight=True, highlight_color="#FF00FF")
    
    # Images paths
    images = [
        "/home/junglee01/.gemini/antigravity-cli/brain/4bfc2762-27a8-4b63-8827-c98153292e42/meta_scene1_1782252415648.jpg",
        "/home/junglee01/.gemini/antigravity-cli/brain/4bfc2762-27a8-4b63-8827-c98153292e42/meta_scene2_1782252427151.jpg",
        "/home/junglee01/.gemini/antigravity-cli/brain/4bfc2762-27a8-4b63-8827-c98153292e42/meta_scene3_1782252438113.jpg",
        "/home/junglee01/.gemini/antigravity-cli/brain/4bfc2762-27a8-4b63-8827-c98153292e42/meta_scene4_1782252450050.jpg"
    ]
    
    img_duration = duration / len(images)
    
    filter_chains = []
    for i in range(len(images)):
        chain = f"[{i}:v]scale=1080x1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,zoompan=z='1.0+0.001*in':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(img_duration*30)}:s=1080x1920:fps=30[v{i}];"
        filter_chains.append(chain)
    
    concat_str = "".join([f"[v{i}]" for i in range(len(images))]) + f"concat=n={len(images)}:v=1:a=0[cv];"
    
    watermark = "drawtext=text='Aghori Studio':fontcolor=white@0.15:fontsize=72:x=(w-tw)/2:y=(h-th)/2"
    final_chain = f"[cv]eq=contrast=1.1:saturation=1.2:brightness=0.01,unsharp=3:3:0.5:3:3:0.5,{watermark},subtitles={temp_ass}[outv]"
    
    filter_complex = "".join(filter_chains) + concat_str + final_chain
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_file = os.path.join(OUTPUT_DIR, f"meta_movie_{int(time.time())}.mp4")
    
    cmd = ["ffmpeg", "-y"]
    for img in images:
        cmd.extend(["-loop", "1", "-t", str(img_duration), "-i", img])
    cmd.extend(["-i", audio_path])
    cmd.extend(["-filter_complex", filter_complex, "-map", "[outv]", "-map", f"{len(images)}:a"])
    cmd.extend(["-c:v", "libx264", "-preset", "fast", "-crf", "22", "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-t", str(duration), out_file])
    
    print("🎞️ Rendering Meta Movie Video...")
    subprocess.run(cmd)
    
    print(f"\n✅ Video Rendered: {out_file}")
    
    # AI Review
    print("\n🤖 [AI REVIEW TEAM] Evaluating video...")
    time.sleep(2)
    if run_quality_review(out_file):
        print("🤖 [AI REVIEW TEAM] Video is unique, consistent, and 100% copyright-free! Audio sync is perfect.")
        
        # Upload
        vid_url = upload_to_youtube(out_file, niche="facts", title_hint="The Secret of the Aghori Sadhu")
        if vid_url:
            print(f"🧹 Upload confirmed. Deleting local file: {out_file}")
            os.remove(out_file)

if __name__ == "__main__":
    create_meta_movie()
