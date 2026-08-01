import os
import sys
import time
import subprocess
import json

sys.path.insert(0, '/home/junglee01/youtube-viral-machine')
from modules.voiceover import generate_voiceover, get_audio_duration
from modules.subtitle_generator import transcribe_audio, generate_ass_subtitles
from config import OUTPUT_DIR, TEMP_DIR

def create_production_videos():
    print("🎬 Starting Production Engine (Episode 1: Antarctica Mystery)...")
    
    script_text = "You have been completely lied to about Antarctica, and what they just found is terrifying. In 2026, classified satellite imaging captured something that global governments have been trying to hide from the public for decades. Deep within the unexplored, frozen wasteland, a massive, unnaturally perfect circular opening was discovered. This isn't just a sinkhole or a cave. It plunges miles beneath the icy surface, emitting a strange, pulsating electromagnetic frequency. This mysterious energy is so powerful that it completely scrambles all airplane instruments and navigation systems within a fifty-mile radius. Former military whistleblowers have recently come forward, claiming this is the legendary Hollow Earth Gateway, a direct entrance to an ancient subterranean world that is still highly active today. Who, or what, is living down there in the dark? As elite military black-ops teams secretly secure the perimeter and prepare to descend, the truth about human history is about to be exposed to the world. If you want to know exactly what they find inside the ice cave in Part 2, you need to hit that subscribe button right now, before this video gets taken down!"
    
    print("🎙️ Generating AI Voiceover...")
    audio_path, words_path, words = generate_voiceover(script_text, voice_key="english_dramatic", rate="-5%")
    duration = get_audio_duration(audio_path)
    
    # Subtitles
    whisper_words = transcribe_audio(audio_path, language="en")
    
    temp_ass_9x16 = os.path.join(TEMP_DIR, "prod_9x16.ass")
    generate_ass_subtitles(whisper_words, temp_ass_9x16, video_width=1080, video_height=1920, highlight=True, highlight_color="#FF00FF")
    
    temp_ass_16x9 = os.path.join(TEMP_DIR, "prod_16x9.ass")
    generate_ass_subtitles(whisper_words, temp_ass_16x9, video_width=1920, video_height=1080, highlight=True, highlight_color="#00FFFF")
    
    # Hardcoded artifact paths from generation
    images_9x16 = [
        "/home/junglee01/.gemini/antigravity-cli/brain/4bfc2762-27a8-4b63-8827-c98153292e42/prod_ant_1_9x16_1782254171226.jpg",
        "/home/junglee01/.gemini/antigravity-cli/brain/4bfc2762-27a8-4b63-8827-c98153292e42/prod_ant_2_9x16_1782254182521.jpg",
        "/home/junglee01/.gemini/antigravity-cli/brain/4bfc2762-27a8-4b63-8827-c98153292e42/prod_ant_3_9x16_1782254193989.jpg",
        "/home/junglee01/.gemini/antigravity-cli/brain/4bfc2762-27a8-4b63-8827-c98153292e42/prod_ant_4_9x16_1782254203836.jpg"
    ]
    
    images_16x9 = [
        "/home/junglee01/.gemini/antigravity-cli/brain/4bfc2762-27a8-4b63-8827-c98153292e42/prod_ant_1_16x9_1782254215165.jpg",
        "/home/junglee01/.gemini/antigravity-cli/brain/4bfc2762-27a8-4b63-8827-c98153292e42/prod_ant_2_16x9_1782254224914.jpg",
        "/home/junglee01/.gemini/antigravity-cli/brain/4bfc2762-27a8-4b63-8827-c98153292e42/prod_ant_3_16x9_1782254241504.jpg",
        "/home/junglee01/.gemini/antigravity-cli/brain/4bfc2762-27a8-4b63-8827-c98153292e42/prod_ant_4_16x9_1782254253281.jpg"
    ]
    
    img_duration = duration / 4.0
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_9x16 = os.path.join(OUTPUT_DIR, f"prod_ant_9x16_{int(time.time())}.mp4")
    out_16x9 = os.path.join(OUTPUT_DIR, f"prod_ant_16x9_{int(time.time())}.mp4")
    
    def render(images, temp_ass, width, height, out_file):
        filter_chains = []
        for i in range(len(images)):
            # Dynamic zoompan to keep it engaging
            chain = f"[{i}:v]scale={width}x{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,zoompan=z='1.0+0.001*in':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(img_duration*30)}:s={width}x{height}:fps=30[v{i}];"
            filter_chains.append(chain)
        
        concat_str = "".join([f"[v{i}]" for i in range(len(images))]) + f"concat=n={len(images)}:v=1:a=0[cv];"
        
        watermark = "drawtext=text='Aghori Studio':fontcolor=white@0.10:fontsize=72:x=w-tw-40:y=h-th-40"
        final_chain = f"[cv]eq=contrast=1.1:saturation=1.2:brightness=0.01,unsharp=3:3:0.5:3:3:0.5,{watermark},subtitles={temp_ass}[outv]"
        
        filter_complex = "".join(filter_chains) + concat_str + final_chain
        
        cmd = ["ffmpeg", "-y"]
        for img in images:
            cmd.extend(["-loop", "1", "-t", str(img_duration), "-i", img])
        cmd.extend(["-i", audio_path])
        cmd.extend(["-filter_complex", filter_complex, "-map", "[outv]", "-map", f"{len(images)}:a"])
        cmd.extend(["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-profile:v", "high", "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-t", str(duration), out_file])
        
        subprocess.run(cmd)
        
    print("🎞️ Rendering 9:16 Video...")
    render(images_9x16, temp_ass_9x16, 1080, 1920, out_9x16)
    
    print("🎞️ Rendering 16:9 Video...")
    render(images_16x9, temp_ass_16x9, 1920, 1080, out_16x9)
    
    print(f"\n✅ Production Videos Rendered:\n9x16: {out_9x16}\n16x9: {out_16x9}")
    
    # Save paths to env for QA script
    with open("/home/junglee01/youtube-viral-machine/latest_prod.json", "w") as f:
        json.dump({"9x16": out_9x16, "16x9": out_16x9}, f)

if __name__ == "__main__":
    create_production_videos()
