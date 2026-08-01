import os
import sys
import time
import random
import textwrap
import asyncio
import subprocess
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modules.script_generator import READY_SCRIPTS_HINDI
import edge_tts
from modules.image_motion_generator import get_pollinations_image
from modules.youtube_uploader import get_authenticated_service
from googleapiclient.http import MediaFileUpload

# Working Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output", "auto_bot")
os.makedirs(OUTPUT_DIR, exist_ok=True)

async def generate_audio(text, output_path):
    # Using a good Hindi voice
    communicate = edge_tts.Communicate(text, "hi-IN-MadhurNeural", rate="+5%")
    await communicate.save(output_path)

def get_audio_duration(audio_path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    try:
        return float(result.stdout.decode().strip())
    except:
        return 4.0

async def process_scene(scene_id, text, image_prompt):
    print(f"\n🎬 Processing Scene {scene_id}...")
    
    audio_path = os.path.join(OUTPUT_DIR, f"scene_{scene_id}.mp3")
    image_path = os.path.join(OUTPUT_DIR, f"scene_{scene_id}.jpg")
    video_motion_path = os.path.join(OUTPUT_DIR, f"scene_{scene_id}_motion.mp4")
    video_final_path = os.path.join(OUTPUT_DIR, f"scene_{scene_id}_final.mp4")
    
    # 1. Generate Voiceover
    print(f"🎙️ Voiceover: {text[:30]}...")
    await generate_audio(text, audio_path)
    duration = get_audio_duration(audio_path)
    
    # 2. Generate Image
    print(f"🖼️ Generating Image for: {image_prompt}")
    get_pollinations_image(image_prompt, image_path)
    
    # 3. Ken Burns Zoom Effect
    print(f"🚀 Adding Motion (Duration: {duration:.2f}s)")
    fps = 30
    frames = int(duration * fps)
    
    # Randomize zoom direction (in or out)
    zoom_in = random.choice([True, False])
    zoom_expr = "min(zoom+0.0015,1.5)" if zoom_in else "max(1.5-0.0015*n,1.0)"
    
    cmd_motion = [
        "ffmpeg", "-y", "-loop", "1", "-i", image_path,
        "-vf", f"scale=1080x1920,zoompan=z='{zoom_expr}':d={frames}:x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2':s=1080x1920",
        "-t", str(duration), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", video_motion_path
    ]
    subprocess.run(cmd_motion, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 4. Burn Subtitles
    print(f"🧵 Burning Subtitles...")
    lines = textwrap.wrap(text, width=20)
    safe_text = "\\n".join(lines).replace("'", "\u2019").replace(":", "\:")
    
    cmd_stitch = [
        "ffmpeg", "-y", "-i", video_motion_path, "-i", audio_path,
        "-vf", f"drawtext=fontfile='/usr/share/fonts/truetype/noto/NotoSansMono-Bold.ttf':text='{safe_text}':fontcolor=yellow:fontsize=65:x=(w-text_w)/2:y=(h-text_h)/2:line_spacing=25:box=1:boxcolor=black@0.7:boxborderw=25:borderw=3:bordercolor=black",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
        "-map", "0:v:0", "-map", "1:a:0", "-shortest", video_final_path
    ]
    subprocess.run(cmd_stitch, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    return video_final_path

def upload_to_youtube(video_path, title, description, tags):
    print("\n=========================================================")
    print("🚀 LIVE YOUTUBE UPLOAD PROTOCOL INITIATED")
    print("=========================================================")
    
    youtube = get_authenticated_service()
    if not youtube:
        print("❌ Auth Failed. Please ensure token.pickle or client_secrets.json is valid.")
        return False
        
    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": "27"
        },
        "status": {
            "privacyStatus": "public",
            "madeForKids": False,
            "selfDeclaredMadeForKids": False
        }
    }
    
    media = MediaFileUpload(video_path, chunksize=1024*1024, resumable=True)
    request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)
    
    response = None
    print(f"📡 Uploading '{video_path}'...")
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                print(f"⏳ Uploading... {int(status.progress() * 100)}%")
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            return False

    print(f"\n✅ Upload Complete! Link: https://youtu.be/{response.get('id')}")
    return True

async def main():
    print("=========================================================")
    print("🤖 AUTOPILOT YOUTUBE BOT STARTED (ZERO TOUCH MODE)")
    print("=========================================================")
    
    # 1. Pick a random category and script
    category = random.choice(list(READY_SCRIPTS_HINDI.keys()))
    script_data = random.choice(READY_SCRIPTS_HINDI[category])
    
    full_text = script_data['hook'] + " " + script_data['body'] + " " + script_data['cta']
    sentences = [s.strip() for s in full_text.split('.') if len(s.strip()) > 5]
    
    print(f"📄 Selected Script: {script_data['title']} (Category: {category})")
    
    # 2. Process Scenes
    generated_clips = []
    for idx, sentence in enumerate(sentences):
        # Create a dynamic image prompt based on the sentence & category
        prompt = f"cinematic photography representing {script_data['title']}, dramatic lighting, highly detailed, 4k resolution, no text"
        
        # Process the scene
        clip_path = await process_scene(idx+1, sentence, prompt)
        generated_clips.append(clip_path)
        
    # 3. Final Stitch
    print("\n🎞️ Finalizing Master Timeline...")
    concat_list_path = os.path.join(OUTPUT_DIR, "concat_list.txt")
    with open(concat_list_path, "w") as f:
        for clip in generated_clips:
            f.write(f"file '{clip}'\n")
            
    master_output = os.path.join(OUTPUT_DIR, f"FINAL_UPLOAD_{int(time.time())}.mp4")
    
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path,
        "-c", "copy", master_output
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"✅ FINAL RENDER SUCCESSFUL: {master_output}")
    
    # 4. Upload to YouTube
    title = f"{script_data['title']} | Secret Revealed 🤯 #shorts #viral"
    desc = f"{script_data['hook']}\n\nDon't forget to Like & Subscribe!\n#shorts #motivation #facts"
    tags = ["shorts", "viral", "motivation", "facts", script_data['title'].replace(" ", "")]
    
    upload_success = upload_to_youtube(master_output, title, desc, tags)
    
    if upload_success:
        print("\n🎉 AUTOMATION CYCLE COMPLETED SUCCESSFULLY. SEE YOU TOMORROW!")
    else:
        print("\n⚠️ AUTOMATION FINISHED BUT UPLOAD FAILED. PLEASE CHECK LOGS.")

if __name__ == "__main__":
    asyncio.run(main())
