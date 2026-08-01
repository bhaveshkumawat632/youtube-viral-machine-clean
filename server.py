import os
import re
import sys
import uuid
import time
import json
import subprocess
import traceback
try:
    import torch
except ImportError:
    torch = None
import shutil
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List
from openai import OpenAI

# Ensure project root is in path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from config import (
    OUTPUT_DIR, TEMP_DIR, VOICES, GRADIENTS,
    SHORTS_WIDTH, SHORTS_HEIGHT, VIDEO_WIDTH, VIDEO_HEIGHT
)
from modules.script_generator import generate_script
from modules.voiceover import generate_voiceover, get_audio_duration
from modules.subtitle_generator import (
    words_from_edge_tts,
    words_from_script_with_timestamps,
    generate_ass_subtitles,
    generate_srt_subtitles
)
from modules.video_maker import create_video_from_audio_and_subtitles
from modules.pexels_downloader import search_and_download_pexels_videos

app = FastAPI(title="YouTube Viral Machine API")

# Enable CORS — restricted to local development origins only
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ============================================================
# API Authentication
# ============================================================
API_SECRET_KEY = os.environ.get("API_SECRET_KEY", "")

async def verify_api_key(x_api_key: str = Header(None)):
    """Simple API key authentication for all endpoints."""
    if API_SECRET_KEY and x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return True

# Ensure folders exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Mount outputs as static files so they can be played in the UI
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

# Load Coqui TTS lazily
coqui_tts_instance = None

def get_coqui_tts():
    global coqui_tts_instance
    if coqui_tts_instance is None:
        print("[*] Initializing Coqui TTS locally...")
        os.environ["COQUI_TOS_AGREED"] = "1"
        from TTS.api import TTS
        device = "cuda" if torch and torch.cuda.is_available() else "cpu"
        print(f"[*] Coqui TTS loading on: {device}")
        coqui_tts_instance = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        print("[+] Coqui TTS loaded.")
    return coqui_tts_instance

class GradioUrlRequest(BaseModel):
    gradio_url: str

@app.post("/api/set-gradio-url")
async def set_gradio_url(req: GradioUrlRequest):
    url = req.gradio_url.strip()
    if not url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL format")
    
    print(f"[+] Setting PRIVATE_API_URL to: {url}")
    os.environ["PRIVATE_API_URL"] = url
    
    # Update config module
    try:
        import config
        config.PRIVATE_API_URL = url
    except Exception as e:
        print(f"[-] Failed to update config: {e}")
        
    # Update cloud_video_generator module
    try:
        import modules.cloud_video_generator
        modules.cloud_video_generator.PRIVATE_API_URL = url
    except Exception as e:
        print(f"[-] Failed to update modules.cloud_video_generator: {e}")
        
    # Write to .env file
    env_path = os.path.join(PROJECT_ROOT, '.env')
    try:
        content = ""
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                content = f.read()
        
        if "PRIVATE_API_URL=" in content:
            content = re.sub(r'PRIVATE_API_URL=.*', f'PRIVATE_API_URL={url}', content)
        else:
            content += f"\nPRIVATE_API_URL={url}\n"
            
        with open(env_path, 'w') as f:
            f.write(content)
        print("[+] .env file updated with new PRIVATE_API_URL.")
    except Exception as e:
        print(f"[-] Failed to update .env: {e}")
        
    return {"status": "success", "private_api_url": url}

class ScriptRequest(BaseModel):
    topic: str = Field(..., max_length=200)
    niche: str = Field(default="motivation", max_length=50)
    language: str = Field(default="hindi", max_length=20)

@app.post("/api/generate-script")
async def api_generate_script(req: ScriptRequest, auth: bool = Depends(verify_api_key)):
    """
    Generate script titles, script text (hook, body, cta), search terms, and description.
    """
    system_prompt = (
        "You are a viral YouTube Shorts/Videos growth hacker. "
        "Generate a highly engaging viral package for the user's topic in JSON format. "
        "Output ONLY valid JSON matching this schema: "
        '{"titles": ["Title 1", "Title 2", "Title 3"], '
        '"hook": "hook script...", '
        '"body": "body script...", '
        '"cta": "cta script...", '
        '"search_terms": ["term1", "term2", "term3", "term4", "term5"], '
        '"description": "description text with hashtags..."}'
    )
    user_prompt = f"Topic: {req.topic}\nNiche: {req.niche}\nLanguage: {req.language}"

    # 1. Try Groq API (Ultra-fast LLM <0.5s response)
    groq_api_key = os.environ.get("GROQ_API_KEY", "")
    if groq_api_key:
        try:
            client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_api_key, max_retries=0)
            c = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2048,
                timeout=4.0
            )
            response_text = c.choices[0].message.content.strip()
            if response_text.startswith("```json"):
                response_text = response_text.split("```json", 1)[1].rsplit("```", 1)[0].strip()
            elif response_text.startswith("```"):
                response_text = response_text.split("```", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(response_text)
        except Exception as e:
            print(f"⚠️ Groq API failed ({e}), trying fallback...")

    # 2. Try OpenRouter API
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
    if openrouter_key:
        try:
            client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=openrouter_key, max_retries=0)
            c = client.chat.completions.create(
                model="meta-llama/llama-3.3-70b-instruct:free",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2048,
                timeout=4.0
            )
            response_text = c.choices[0].message.content.strip()
            if response_text.startswith("```json"):
                response_text = response_text.split("```json", 1)[1].rsplit("```", 1)[0].strip()
            elif response_text.startswith("```"):
                response_text = response_text.split("```", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(response_text)
        except Exception as e:
            print(f"⚠️ OpenRouter API failed ({e}), trying fallback...")

    # 3. Fallback to local template generator (Instant <0.01s response)
    print("⚡ Using ultra-fast local script generator.")
    local_script = generate_script(req.niche, req.language, req.topic)
    terms = [req.topic, req.niche, "cinematic", "motivation", "viral"]
    titles = [
        f"The Untold Truth of {req.topic}",
        f"Why 99% Fail At {req.topic}",
        f"The Ultimate {req.topic} Secret"
    ]
    description = (
        f"🔴 {req.topic} | Secrets Revealed! 🤯\n\n"
        f"In this video we talk about {req.topic}. If you like this content, Subscribe!\n\n"
        f"#shorts #{req.niche} #viral #{req.topic.replace(' ', '')}"
    )
    return {
        "titles": titles,
        "hook": local_script.get("hook", f"Did you know this about {req.topic}?"),
        "body": local_script.get("body", f"Here is the secret about {req.topic} that most people never realize..."),
        "cta": local_script.get("cta", "Subscribe for more viral content!"),
        "search_terms": terms,
        "description": description
    }

@app.post("/api/generate-video")
async def api_generate_video(
    auth: bool = Depends(verify_api_key),
    topic: str = Form(...),
    hook: str = Form(...),
    body: str = Form(...),
    cta: str = Form(...),
    voice_key: str = Form("hindi_male"),
    video_format: str = Form("shorts"),
    highlight_color: str = Form("#FFE100"),
    background_type: str = Form("gradient"),
    gradient_name: str = Form("neon_dark"),
    pexels_api_key: Optional[str] = Form(None),
    search_terms: str = Form("[]"),
    voice_clone_file: Optional[UploadFile] = File(None)
):
    try:
        timestamp = int(time.time())
        # Secure sanitization — only allow alphanumeric, underscore, hyphen
        safe_topic = re.sub(r'[^a-zA-Z0-9_-]', '', topic.replace(' ', '_'))[:30]
        if not safe_topic:
            safe_topic = f"video_{timestamp}"
        
        # Input length validation
        if len(hook) > 2000 or len(body) > 10000 or len(cta) > 2000:
            raise HTTPException(status_code=400, detail="Input text too long")
        
        full_script = f"{hook}\n\n{body}\n\n{cta}"
        
        # Create unique file paths
        audio_path = os.path.join(TEMP_DIR, f"{safe_topic}_{timestamp}.mp3")
        
        # Use voice cloning or Edge TTS
        words_json_path = None
        if voice_clone_file:
            print("[*] Processing Voice Cloning Audio File...")
            # Save voice clone file to temp path
            ref_path = os.path.join(TEMP_DIR, f"ref_{timestamp}_{voice_clone_file.filename}")
            with open(ref_path, "wb") as f:
                shutil.copyfileobj(voice_clone_file.file, f)
                
            # Perform cloning locally
            tts = get_coqui_tts()
            lang_code = "hi" if "hi" in voice_key or "hindi" in voice_key else "en"
            
            print(f"[*] Synthesis of cloned voice using {ref_path}...")
            # XTTS writes to WAV file
            wav_output = audio_path.replace(".mp3", ".wav")
            tts.tts_to_file(
                text=full_script,
                speaker_wav=ref_path,
                language=lang_code,
                file_path=wav_output
            )
            
            # Convert WAV output to MP3 format for downstream compatibility
            subprocess.run(["ffmpeg", "-y", "-i", wav_output, "-codec:a", "libmp3lame", "-qscale:a", "2", audio_path], capture_output=True)
            try:
                os.remove(wav_output)
            except:
                pass
        else:
            # Standard Edge TTS voiceover
            audio_path, words_json_path, _ = generate_voiceover(
                full_script, audio_path, voice_key
            )
            
        duration = get_audio_duration(audio_path)
        
        # Process visual background
        bg_video = None
        if background_type == "stock_video" and pexels_api_key:
            parsed_terms = json.loads(search_terms)
            download_dir = os.path.join(TEMP_DIR, f"pexels_{timestamp}")
            downloaded = search_and_download_pexels_videos(
                search_terms=parsed_terms,
                output_dir=download_dir,
                pexels_api_key=pexels_api_key,
                video_format=video_format,
                target_duration=duration
            )
            if downloaded:
                bg_video = downloaded
        elif background_type == "anime":
            print("[*] Generating Anime Visuals using Pollinations AI...")
            raw_sentences = re.split(r'(?<=[.!?])\s+', full_script)
            sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 5]
            if not sentences:
                sentences = [full_script]
            
            anime_clips = []
            scene_duration = duration / len(sentences)
            from modules.image_motion_generator import get_pollinations_image
            
            for idx, sentence in enumerate(sentences):
                clean_sentence = re.sub(r'[^\w\s-]', '', sentence)
                prompt = f"Beautiful colorful anime style, vertical, highly detailed, makoto shinkai aesthetic: {clean_sentence}"
                image_path = os.path.join(TEMP_DIR, f"anime_img_{timestamp}_{idx}.jpg")
                temp_clip = os.path.join(TEMP_DIR, f"anime_clip_{timestamp}_{idx}.mp4")
                
                print(f"  -> Generating scene {idx+1}/{len(sentences)}: {clean_sentence[:50]}...")
                get_pollinations_image(prompt, image_path)
                
                fps = 30
                frames = int(scene_duration * fps)
                zoom_in = (idx % 2 == 0)
                zoom_expr = "min(zoom+0.0015,1.5)" if zoom_in else "max(1.5-0.0015*n,1.0)"
                
                cmd = [
                    "ffmpeg", "-y",
                    "-loop", "1",
                    "-i", image_path,
                    "-vf", f"scale=1200:2133,crop=w=1080:h=1920:x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2',setsar=1",
                    "-t", f"{scene_duration:.2f}",
                    "-c:v", "libx264", "-preset", "ultrafast",
                    "-pix_fmt", "yuv420p",
                    temp_clip
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                if os.path.exists(temp_clip):
                    anime_clips.append(temp_clip)
                    
            if anime_clips:
                concat_list = os.path.join(TEMP_DIR, f"anime_concat_{timestamp}.txt")
                with open(concat_list, "w") as f:
                    for clip in anime_clips:
                        f.write(f"file '{clip}'\n")
                        
                output_bg = os.path.join(TEMP_DIR, f"multi_bg_{timestamp}.mp4")
                cmd = [
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
                    "-c", "copy", output_bg
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                for clip in anime_clips:
                    try: os.remove(clip)
                    except: pass
                try: os.remove(concat_list)
                except: pass
                
                if os.path.exists(output_bg):
                    bg_video = output_bg
                
        # Subtitles
        lang_code = "hi" if "hi" in voice_key or "hindi" in voice_key else "en"
        words = []
        if words_json_path and os.path.exists(words_json_path):
            words = words_from_edge_tts(words_json_path)
            
        if not words:
            words = words_from_script_with_timestamps(
                full_script, audio_path, language=lang_code
            )
            
        # Determine subtitle resolution
        sub_w = SHORTS_WIDTH if video_format == "shorts" else VIDEO_WIDTH
        sub_h = SHORTS_HEIGHT if video_format == "shorts" else VIDEO_HEIGHT
        
        ass_path = os.path.join(TEMP_DIR, f"{safe_topic}_{timestamp}.ass")
        srt_path = os.path.join(OUTPUT_DIR, f"{safe_topic}_{timestamp}.srt")
        
        generate_ass_subtitles(words, ass_path, video_width=sub_w, video_height=sub_h, highlight_color=highlight_color)
        generate_srt_subtitles(words, srt_path)
        
        output_filename = f"{safe_topic}_{timestamp}.mp4"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        create_video_from_audio_and_subtitles(
            audio_path=audio_path,
            subtitle_path=ass_path,
            output_path=output_path,
            background_video=bg_video,
            gradient_name=gradient_name,
            video_format=video_format
        )
        
        # Clean up temp Pexels folder if created
        if bg_video and isinstance(bg_video, list):
            try:
                shutil.rmtree(os.path.dirname(bg_video[0]))
            except:
                pass
                
        if os.path.exists(output_path):
            return {
                "success": True,
                "video_url": f"/outputs/{output_filename}",
                "srt_url": f"/outputs/{safe_topic}_{timestamp}.srt",
                "duration": duration,
                "size_mb": os.path.getsize(output_path) / (1024 * 1024)
            }
        else:
            raise HTTPException(status_code=500, detail="Video rendering output missing.")
            
    except Exception as e:
        print(f"❌ Error during generation: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000, loop="asyncio")
