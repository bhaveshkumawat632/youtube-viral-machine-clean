import os
import sys
import time
import subprocess
import asyncio
import textwrap

from modules.image_motion_generator import get_pollinations_image
import edge_tts

scenes = [
    {
        "id": 1,
        "text": "The signal was traced to an abandoned server room beneath the city.",
        "image_prompt": "cyberpunk hacker in dark server room, glowing green code, hyperrealistic, 4k",
    },
    {
        "id": 2,
        "text": "Dust particles danced in the pale blue light of a single active monitor.",
        "image_prompt": "dust particles floating in pale blue light of a single active computer monitor, cinematic lighting, dark room",
    },
    {
        "id": 3,
        "text": "On the screen, a message blinked. They are coming.",
        "image_prompt": "close up of a retro computer monitor showing red text They are coming, suspenseful, dark cyberpunk aesthetic, hyperrealistic, 4k",
    }
]

TEST_DIR = "/home/junglee01/youtube-viral-machine/output"
os.makedirs(TEST_DIR, exist_ok=True)

async def generate_audio(text, output_path):
    communicate = edge_tts.Communicate(text, "en-US-GuyNeural", rate="-5%")
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
        return 4.0 # default fallback

async def process_scene(scene):
    print(f"\n🎬 --- DIRECTOR: Commencing Action on Scene {scene['id']} ---")
    
    audio_path = os.path.join(TEST_DIR, f"image_scene_{scene['id']}.mp3")
    image_path = os.path.join(TEST_DIR, f"image_scene_{scene['id']}_raw.jpg")
    video_motion_path = os.path.join(TEST_DIR, f"image_scene_{scene['id']}_motion.mp4")
    video_final_path = os.path.join(TEST_DIR, f"image_scene_{scene['id']}_final.mp4")
    
    print(f"🎙️ Audio Engineer: Synthesizing -> '{scene['text']}'")
    await generate_audio(scene['text'], audio_path)
    
    duration = get_audio_duration(audio_path)
    print(f"⏱️ Audio Duration: {duration:.2f} seconds")
    
    print(f"🖼️ Image Engineer: Fetching Cinematic Visual for '{scene['image_prompt']}'...")
    get_pollinations_image(scene['image_prompt'], image_path)
    
    print(f"🚀 Motion Engineer: Applying Ken Burns Zoom-Pan (Duration: {duration:.2f}s)...")
    # Convert Image to Motion Video with Zoompan
    fps = 30
    frames = int(duration * fps)
    cmd_motion = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-vf", f"zoompan=z='min(zoom+0.0015,1.5)':d={frames}:x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2':s=1080x1920",
        "-t", str(duration),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        video_motion_path
    ]
    subprocess.run(cmd_motion, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print(f"🧵 Subtitle Engineer: Overlaying Text & Audio...")
    lines = textwrap.wrap(scene['text'], width=24)
    safe_text = "\n".join(lines).replace("'", "\u2019").replace(":", "\:")
    
    cmd_stitch = [
        "ffmpeg", "-y",
        "-i", video_motion_path,
        "-i", audio_path,
        "-vf", f"drawtext=fontfile='/usr/share/fonts/truetype/noto/NotoSansMono-Bold.ttf':text='{safe_text}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2:line_spacing=25:box=1:boxcolor=black@0.6:boxborderw=20",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        video_final_path
    ]
    subprocess.run(cmd_stitch, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print(f"✅ Scene {scene['id']} locked and stored safely.")
    return video_final_path

async def main():
    print("=========================================================")
    print("🎬 AGHORI STUDIO: AI IMAGE & MOTION PIPELINE INITIALIZED")
    print("=========================================================")
    print("📡 Routing strictly to Pollinations Image API")
    print("🛠️ Dynamic Ken Burns Motion & Audio Sync")
    print("=========================================================\n")
    
    generated_clips = []
    for scene in scenes:
        final_scene = await process_scene(scene)
        generated_clips.append(final_scene)
        
    print("\n🎞️ Chief Editor: Finalizing Master Timeline Stitching...")
    concat_list_path = os.path.join(TEST_DIR, "image_concat_list.txt")
    with open(concat_list_path, "w") as f:
        for clip in generated_clips:
            f.write(f"file '{clip}'\n")
            
    master_output = os.path.join(TEST_DIR, f"FINAL_TEST_RENDER.mp4")
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_path,
        "-c", "copy",
        master_output
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print("=========================================================")
    print(f"🚀 FINAL EXPORT SUCCESSFUL: {master_output}")
    print("=========================================================")
    
    ans = input(f"🎥 Final test rendered successfully at {master_output}. Watch it now. Keep or Delete? (K/D): ")
    if ans.strip().lower() == 'd':
        print("\n🗑️ Deleting test render...")
        os.remove(master_output)
        print("✅ File deleted.")
    else:
        print("\n💾 File kept successfully.")

if __name__ == "__main__":
    asyncio.run(main())
