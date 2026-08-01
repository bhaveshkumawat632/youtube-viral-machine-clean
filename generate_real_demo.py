import os
import sys
import time
import subprocess
import json

sys.path.insert(0, '/home/junglee01/youtube-viral-machine')
from modules.voiceover import generate_voiceover, get_audio_duration
from modules.subtitle_generator import transcribe_audio, generate_ass_subtitles
from config import OUTPUT_DIR, TEMP_DIR

def create_demo_videos():
    print("🎬 Starting Real Meta Movies Engine...")
    
    script_text = "Deep in the Himalayas, an ancient Aghori sadhu guards a secret that could change humanity forever. He sits alone in the freezing snow, meditating peacefully with glowing blue eyes, deeply connected to the universe. Legend says he hasn't aged a single day in over five hundred years. Many have tried to find him, but only the worthy can see his true form. If you want to know his ancient secret and unlock the mysteries of the universe, you must listen closely. Subscribe to Aghori Studio right now, and join the journey into the unknown!"
    
    print("🎙️ Generating AI Voiceover...")
    audio_path, words_path, words = generate_voiceover(script_text, voice_key="english_dramatic", rate="-10%")
    duration = get_audio_duration(audio_path)
    
    padded_audio = os.path.join(TEMP_DIR, "padded_audio.mp3")
    subprocess.run(["ffmpeg", "-y", "-i", audio_path, "-af", f"apad,atrim=0:30", padded_audio])
    duration = 30.0
    
    whisper_words = transcribe_audio(padded_audio, language="en")
    
    temp_ass_9x16 = os.path.join(TEMP_DIR, "meta_movie_9x16.ass")
    generate_ass_subtitles(whisper_words, temp_ass_9x16, video_width=1080, video_height=1920, highlight=True, highlight_color="#FF00FF")
    
    temp_ass_16x9 = os.path.join(TEMP_DIR, "meta_movie_16x9.ass")
    generate_ass_subtitles(whisper_words, temp_ass_16x9, video_width=1920, video_height=1080, highlight=True, highlight_color="#00FFFF")
    
    images_9x16 = [
        "/home/junglee01/.gemini/antigravity-cli/brain/4bfc2762-27a8-4b63-8827-c98153292e42/meta_scene1_1782252415648.jpg",
        "/home/junglee01/.gemini/antigravity-cli/brain/4bfc2762-27a8-4b63-8827-c98153292e42/meta_scene2_1782252427151.jpg",
        "/home/junglee01/.gemini/antigravity-cli/brain/4bfc2762-27a8-4b63-8827-c98153292e42/meta_scene3_1782252438113.jpg",
        "/home/junglee01/.gemini/antigravity-cli/brain/4bfc2762-27a8-4b63-8827-c98153292e42/meta_scene4_1782252450050.jpg"
    ]
    
    images_16x9 = [
        "/home/junglee01/.gemini/antigravity-cli/brain/4bfc2762-27a8-4b63-8827-c98153292e42/meta_16x9_1_1782253165926.jpg",
        "/home/junglee01/.gemini/antigravity-cli/brain/4bfc2762-27a8-4b63-8827-c98153292e42/meta_16x9_2_1782253177741.jpg",
        "/home/junglee01/.gemini/antigravity-cli/brain/4bfc2762-27a8-4b63-8827-c98153292e42/meta_16x9_3_1782253189938.jpg",
        "/home/junglee01/.gemini/antigravity-cli/brain/4bfc2762-27a8-4b63-8827-c98153292e42/meta_16x9_4_1782253199490.jpg"
    ]
    
    img_duration = 30.0 / 4.0
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_9x16 = os.path.join(OUTPUT_DIR, f"real_demo_9x16_{int(time.time())}.mp4")
    out_16x9 = os.path.join(OUTPUT_DIR, f"real_demo_16x9_{int(time.time())}.mp4")
    
    def render(images, temp_ass, width, height, out_file):
        filter_chains = []
        for i in range(len(images)):
            chain = f"[{i}:v]scale={width}x{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,zoompan=z='1.0+0.0015*in':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(img_duration*30)}:s={width}x{height}:fps=30[v{i}];"
            filter_chains.append(chain)
        
        concat_str = "".join([f"[v{i}]" for i in range(len(images))]) + f"concat=n={len(images)}:v=1:a=0[cv];"
        
        watermark = "drawtext=text='Aghori Studio':fontcolor=white@0.15:fontsize=72:x=w-tw-40:y=h-th-40"
        final_chain = f"[cv]eq=contrast=1.1:saturation=1.2:brightness=0.01,unsharp=3:3:0.5:3:3:0.5,{watermark},subtitles={temp_ass}[outv]"
        
        filter_complex = "".join(filter_chains) + concat_str + final_chain
        
        cmd = ["ffmpeg", "-y"]
        for img in images:
            cmd.extend(["-loop", "1", "-t", str(img_duration), "-i", img])
        cmd.extend(["-i", padded_audio])
        cmd.extend(["-filter_complex", filter_complex, "-map", "[outv]", "-map", f"{len(images)}:a"])
        cmd.extend(["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-profile:v", "high", "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-t", "30", out_file])
        
        t0 = time.time()
        subprocess.run(cmd)
        return time.time() - t0
        
    print("🎞️ Rendering 9:16 Video...")
    t_9x16 = render(images_9x16, temp_ass_9x16, 1080, 1920, out_9x16)
    
    print("🎞️ Rendering 16:9 Video...")
    t_16x9 = render(images_16x9, temp_ass_16x9, 1920, 1080, out_16x9)
    
    print(f"\n✅ Videos Rendered:\n9x16: {out_9x16}\n16x9: {out_16x9}")
    
    def qa_check(file_path):
        cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", file_path]
        res = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(res.stdout)
        v_stream = next(s for s in data["streams"] if s["codec_type"] == "video")
        a_stream = next(s for s in data["streams"] if s["codec_type"] == "audio")
        
        return {
            "format": data["format"]["format_name"],
            "duration": float(data["format"]["duration"]),
            "size": int(data["format"]["size"]),
            "bitrate": int(data["format"].get("bit_rate", data["format"].get("bitrate", 0))),
            "v_codec": v_stream["codec_name"],
            "fps": eval(v_stream["r_frame_rate"]),
            "width": v_stream["width"],
            "height": v_stream["height"],
            "a_codec": a_stream["codec_name"]
        }
        
    qa_9x16 = qa_check(out_9x16)
    qa_16x9 = qa_check(out_16x9)
    
    with open(os.path.join(OUTPUT_DIR, "qa_report.json"), "w") as f:
        json.dump({"9x16": qa_9x16, "16x9": qa_16x9, "t_9x16": t_9x16, "t_16x9": t_16x9}, f)

if __name__ == "__main__":
    create_demo_videos()
