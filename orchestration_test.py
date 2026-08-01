import os
import time
import subprocess
import asyncio
try:
    import edge_tts
except ImportError:
    subprocess.run(["pip", "install", "edge-tts"])
    import edge_tts

try:
    from gradio_client import Client
except ImportError:
    subprocess.run(["pip", "install", "gradio_client"])
    from gradio_client import Client

# Configuration
TEST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "testing")
os.makedirs(TEST_DIR, exist_ok=True)

# Scene Storyboard
scenes = [
    {
        "id": 1,
        "text": "In the darkest corner of the forgotten sector...",
        "video_prompt": "Cinematic slow zoom out. A mysterious astronaut walking alone on a dark, rocky alien planet surface, dust blowing. 8k, photorealistic.",
    },
    {
        "id": 2,
        "text": "...a faint neon glow pierced the eternal night.",
        "video_prompt": "Low angle tracking shot. The astronaut approaches a glowing neon-cyan alien artifact half-buried in the alien soil.",
    },
    {
        "id": 3,
        "text": "It wasn't built by humans...",
        "video_prompt": "Close up cinematic pan. The glowing alien artifact reveals strange ancient symbols pulsing with energy.",
    },
    {
        "id": 4,
        "text": "...and it was waiting for him.",
        "video_prompt": "Dramatic low angle shot. The astronaut reaches out his hand to touch the glowing artifact, blinding light emitting from it.",
    }
]

async def generate_audio(text, output_path):
    print(f"🎙️ Generating Audio: {text}")
    communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural", rate="-10%")
    await communicate.save(output_path)
    return output_path

from modules.cloud_video_generator import generate_video_from_prompt_hf

def generate_video_fallback(narrative_text, output_path, duration=4):
    """Fallback if HF space is completely down"""
    print(f"⚠️ Using fallback FFmpeg synthesis for: {narrative_text}")
    safe_text = narrative_text[:50].replace("'", "").replace(":", "") + "..."
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:d={duration}:r=30",
        "-vf", f"drawtext=text='{safe_text}':fontcolor=white:fontsize=40:x=(w-text_w)/2:y=(h-text_h)/2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast", output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_path

def generate_video_hf(video_prompt, narrative_text, output_path):
    print(f"☁️ Orchestrating Video for: {video_prompt}")
    try:
        res = generate_video_from_prompt_hf(video_prompt, output_path)
        if not res:
            generate_video_fallback(narrative_text, output_path)
    except Exception as e:
        print(f"⚠️ Cloud Video Generation failed ({e}). Falling back...")
        generate_video_fallback(narrative_text, output_path)
    return output_path

async def main():
    print("🚀 STARTING OPTIMIZED LOAD-BALANCED PIPELINE (Single Scene Test)")
    
    generated_clips = []
    
    # Run only the first scene to quickly test the load balancer
    scene = scenes[0]
    print(f"\n--- Processing Scene {scene['id']} ---")
    
    # 1. Generate Voice
    audio_path = os.path.join(TEST_DIR, f"scene_{scene['id']}.mp3")
    await generate_audio(scene['text'], audio_path)
    
    # 2. Generate Video
    video_path = os.path.join(TEST_DIR, f"scene_{scene['id']}_raw.mp4")
    generate_video_hf(scene['video_prompt'], scene['text'], video_path)
    
    # 3. Combine Audio and Video for this scene
    final_scene_path = os.path.join(TEST_DIR, f"scene_{scene['id']}_final.mp4")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        final_scene_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"✅ Scene {scene['id']} rendered: {final_scene_path}")
    
    generated_clips.append(final_scene_path)
    
    print(f"\n🎉 PIPELINE SUCCESS: Test Scene rendered to -> {final_scene_path}")

if __name__ == "__main__":
    asyncio.run(main())
