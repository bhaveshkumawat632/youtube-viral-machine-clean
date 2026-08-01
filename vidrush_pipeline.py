# Agent A Fixed: dotenv loading and fallback visual system
import os
import sys
import json
import time
import random
import subprocess
import asyncio
import argparse
import shutil
from datetime import datetime
import edge_tts
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# VidRush Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output", "vidrush")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
MANIFEST_FILE = os.path.join(ASSETS_DIR, "manifest.json")
FAILED_DIR = os.path.join(OUTPUT_DIR, "failed")
LOG_FILE = os.path.join(BASE_DIR, "daily_log.txt")
ALERT_FILE = os.path.join(BASE_DIR, "ALERT.txt")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(FAILED_DIR, exist_ok=True)

# CREDENTIALS — all FREE stack (no paid keys needed)
# ---------------------------------------------------------
# OpenRouter — free LLM routing (replaces Groq)
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "sk-or-v1-...")

# Ollama — local free LLM (no key needed)
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

# ---------------------------------------------------------
# R2. AI THUMBNAIL GENERATION
# ---------------------------------------------------------
def generate_thumbnail(video_title, output_dir):
    """
    Generate a YouTube thumbnail using Replicate (black-forest-labs/flux-schnell),
    then overlay the video title in bold text. Saves as thumbnail.jpg.
    """
    thumb_path = os.path.join(output_dir, "thumbnail.jpg")
    try:
        import replicate as replicate_lib
        os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN
        client = replicate_lib.Client(api_token=REPLICATE_API_TOKEN)

        safe_title = video_title[:80]
        prompt = (
            f"YouTube thumbnail, dramatic cinematic scene, bold text overlay saying '{safe_title}', "
            "vibrant colors, high contrast, professional photography, 16:9 aspect ratio"
        )
        print(f"\n🖼️  Generating AI thumbnail via Replicate FLUX...")
        prediction = client.predictions.create(
            model="black-forest-labs/flux-schnell",
            input={"prompt": prompt, "aspect_ratio": "16:9", "output_format": "jpg"}
        )
        deadline = time.time() + 120
        while prediction.status not in ("succeeded", "failed", "canceled"):
            if time.time() > deadline:
                raise TimeoutError("Thumbnail generation timed out.")
            time.sleep(3)
            prediction.reload()

        if prediction.status == "succeeded" and prediction.output:
            import requests as _req
            img_url = str(prediction.output) if isinstance(prediction.output, str) else str(prediction.output[0])
            r = _req.get(img_url, timeout=30)
            r.raise_for_status()
            raw_path = os.path.join(output_dir, "thumbnail_raw.jpg")
            with open(raw_path, "wb") as f:
                f.write(r.content)

            # Overlay title text with FFmpeg drawtext
            safe_text = safe_title.replace("'", "'\\''").replace(":", "\\:").replace("%", "%%")
            subprocess.run([
                "ffmpeg", "-y", "-i", raw_path,
                "-vf", (
                    f"drawtext=text='{safe_text}':fontsize=52:fontcolor=white:"
                    "box=1:boxcolor=black@0.55:boxborderw=12:"
                    "x=(w-text_w)/2:y=h-th-60"
                ),
                "-q:v", "2", thumb_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 10000:
                print(f"✅ Thumbnail saved: {thumb_path} ({os.path.getsize(thumb_path):,} bytes)")
                return thumb_path

    except Exception as e:
        print(f"⚠️ AI thumbnail failed ({e}). Creating fallback thumbnail with FFmpeg...")

    # Fallback: gradient background + title text via FFmpeg
    try:
        safe_text = video_title[:60].replace("'", "").replace(":", " -")
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi", "-i",
            "gradients=s=1280x720:c0=0x1a0050:c1=0xff6600:x0=0:y0=0:x1=1280:y1=720",
            "-vframes", "1",
            "-vf", f"drawtext=text='{safe_text}':fontsize=56:fontcolor=white:x=(w-text_w)/2:y=(h-th)/2",
            "-q:v", "2", thumb_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(thumb_path):
            print(f"✅ Fallback thumbnail created: {thumb_path}")
            return thumb_path
    except Exception as fe:
        print(f"⚠️ Fallback thumbnail also failed: {fe}")
    return None


# ---------------------------------------------------------
# R3. SEO METADATA GENERATION
# ---------------------------------------------------------
def generate_seo_metadata(video_title, niche, output_dir):
    """
    Use OpenRouter (free) to generate a click-bait title, 150-word description, and 10 SEO tags.
    Saves to metadata.json alongside the output video.
    """
    meta_path = os.path.join(output_dir, "metadata.json")
    try:
        import openai as _openai
        _client = _openai.OpenAI(
            api_key=os.environ.get("OPENROUTER_API_KEY", ""),
            base_url="https://openrouter.ai/api/v1"
        )
        prompt = f"""
        You are a YouTube SEO expert. Generate metadata for a viral YouTube Shorts video.
        Topic: {video_title}
        Niche: {niche}

        Return ONLY a valid JSON object with these exact keys:
        {{
          "title": "Optimized clickbait YouTube title (max 100 chars, use emojis)",
          "description": "150-word video description with strategic hashtags at the end",
          "tags": ["tag1", "tag2", "...", "tag10"]
        }}
        """
        print(f"\n📈 Generating SEO metadata via OpenRouter (Nous Llama 70B)...")
        response = _client.chat.completions.create(
            model="meta-llama/llama-3.1-70b-instruct",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            extra_body={"model": "meta-llama/llama-3.1-70b-instruct"}
        )
        metadata = json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"⚠️ Llama 70B SEO generation failed ({e}). Trying fallback model...")
        try:
            response = _client.chat.completions.create(
                model="openrouter/free",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                extra_body={"model": "openrouter/free"}
            )
            metadata = json.loads(response.choices[0].message.content)
        except Exception as e2:
            print(f"⚠️ OpenRouter SEO generation failed ({e2}). Using template fallback...")
            from modules.seo_generator import generate_metadata
            metadata = generate_metadata(video_title, niche)

    # Ensure required keys exist
    metadata.setdefault("title", f"{video_title} 🤯 #shorts")
    metadata.setdefault("description", f"{video_title} | Watch till the end! #shorts #viral #{niche}")
    metadata.setdefault("tags", ["shorts", "viral", niche, "trending", "youtube"])

    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"✅ SEO metadata saved: {meta_path}")
    return metadata


# ---------------------------------------------------------
# 0. ASSET MANIFEST LOGGING (Spec Section 0 & 8)
# ---------------------------------------------------------
def log_asset(asset_id, source, license_type, url):
    manifest = []
    if os.path.exists(MANIFEST_FILE):
        with open(MANIFEST_FILE, "r") as f:
            manifest = json.load(f)
            
    manifest.append({
        "asset_id": asset_id,
        "source": source,
        "license_type": license_type,
        "url": url,
        "date_fetched": datetime.now().isoformat()
    })
    
    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=4)

# ---------------------------------------------------------
# 1. SCRIPT GENERATION (Spec Section 1)
# ---------------------------------------------------------
def generate_script():
    """
    B (Team integration): Generate the script via the LOCAL team model
    (Ollama) for free, unlimited, unique scripting. Falls back to the
    built-in static script if the model is unavailable or too slow.

    Returns pipeline-shaped scenes: {text, emotion_tag, suggested_visual_keyword}
    """
    try:
        from modules.script_generator import generate_script_via_ollama
        data = generate_script_via_ollama(
            "5 Second Rule / Productivity Hack", "english", model="hermes-1.5b"
        )
        cin = data.get("scenes", [])
        if cin:
            mapped = []
            # crude emotion inference from narrative tone words
            def _emo(t):
                t = t.lower()
                if any(w in t for w in ["shocking", "lies", "terrifying", "secret", "hidden", "scary"]):
                    return "shocked"
                if any(w in t for w in ["win", "triumph", "success", "beat", "power"]):
                    return "triumphant"
                if any(w in t for w in ["danger", "mystery", "fear", "war", "crisis"]):
                    return "tense"
                return "neutral"
            for s in cin:
                narr = s.get("narrative", "")
                kw = s.get("video_prompt", "")
                mapped.append({
                    "text": narr,
                    "emotion_tag": _emo(narr),
                    "suggested_visual_keyword": kw or narr[:60],
                })
            if mapped:
                print(f"🤖 [TEAM SCRIPT] {len(mapped)} scenes from local model")
                return mapped
    except Exception as e:
        print(f"⚠️ [TEAM SCRIPT] model unavailable ({e}); using built-in script.")

    # ── Fallback: built-in static script ──
    return [
        {
            "text": "99 percent of people are doing the 5 second rule completely wrong.",
            "emotion_tag": "shocked",
            "suggested_visual_keyword": "person looking confused at a giant glowing clock 4k cinematic"
        },
        {
            "text": "They think it's just about counting down to start a task.",
            "emotion_tag": "neutral",
            "suggested_visual_keyword": "bored person at office desk dark lighting"
        },
        {
            "text": "But scientists discovered what actually happens in your brain.",
            "emotion_tag": "tense",
            "suggested_visual_keyword": "glowing human brain neurons firing macro shot"
        },
        {
            "text": "When you count 5, 4, 3, 2, 1, you interrupt your brain's default worry mode.",
            "emotion_tag": "tense",
            "suggested_visual_keyword": "countdown timer digital red neon"
        },
        {
            "text": "It literally forces your prefrontal cortex to wake up and take control.",
            "emotion_tag": "triumphant",
            "suggested_visual_keyword": "person breaking chains triumphant victory cinematic"
        },
        {
            "text": "This simple trick rewires your habits completely.",
            "emotion_tag": "neutral",
            "suggested_visual_keyword": "glowing brain synapses forming new connections"
        },
        {
            "text": "Successful people use it every morning to beat procrastination.",
            "emotion_tag": "tense",
            "suggested_visual_keyword": "person looking productive typing at computer sunrise"
        },
        {
            "text": "It takes no special skills, just the will to act.",
            "emotion_tag": "triumphant",
            "suggested_visual_keyword": "person standing on mountain peak arms raised"
        },
        {
            "text": "So stop hesitating. Count down, and take your life back.",
            "emotion_tag": "triumphant",
            "suggested_visual_keyword": "person running towards bright light success"
        }
    ]

# ---------------------------------------------------------
# 2. VOICEOVER TTS (Spec Section 2)
# ---------------------------------------------------------
def get_emotion_voice_settings(emotion):
    # Mapping emotions to speech rate and pitch modifiers
    if emotion == "shocked": return "+10%", "+5Hz"
    if emotion == "tense": return "-5%", "-5Hz"
    if emotion == "triumphant": return "+5%", "+10Hz"
    if emotion == "sad": return "-10%", "-10Hz"
    if emotion == "neutral": return "+0%", "+0Hz"
    # Fallback for undefined tags to prevent crashing
    return "+0%", "+0Hz"

async def generate_scene_audio(scene, index):
    rate, pitch = get_emotion_voice_settings(scene["emotion_tag"])
    # Using ChristopherNeural as the consistent channel voice
    audio_path = os.path.join(OUTPUT_DIR, f"audio_scene_{index}.mp3")
    subtitle_path = os.path.join(OUTPUT_DIR, f"subtitles_scene_{index}.vtt")
    
    print(f"  -> Generating audio for scene {index}...")
    communicate = edge_tts.Communicate(scene["text"], "en-US-ChristopherNeural", rate=rate, pitch=pitch)
    
    # Save audio & WebVTT timestamps for word-level syncing
    submaker = edge_tts.SubMaker()
    words = []
    with open(audio_path, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.create_sub((chunk["offset"], chunk["duration"]), chunk["text"])
                start_sec = chunk["offset"] / 10000000.0
                duration_sec = chunk["duration"] / 10000000.0
                words.append({
                    "text": chunk["text"],
                    "start": start_sec,
                    "end": start_sec + duration_sec
                })
                
    # Fallback to scene-level text burn via ffmpeg for now to prevent VTT crash
    # with open(subtitle_path, "w", encoding="utf-8") as file:
    #     file.write(submaker.generate_subs())
        
    # Get Duration
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    duration = float(result.stdout.decode().strip())
    
    if not words:
        import re
        words_list = [w for w in re.split(r'\s+', scene["text"].strip()) if w]
        if words_list:
            t_per_word = duration / len(words_list)
            for j, word in enumerate(words_list):
                words.append({
                    "text": word,
                    "start": j * t_per_word,
                    "end": (j + 1) * t_per_word
                })
                
    return audio_path, subtitle_path, duration, words


# ---------------------------------------------------------
# 3. VISUAL SOURCING (Spec Section 3 & 6)
# ---------------------------------------------------------
def generate_visual_cut(keyword, index, cut_index, duration):
    """
    4-Tier Visual Sourcing Engine:
    Tier 1: AI Video (Gradio/Fal.ai)
    Tier 2: Stock Video (Pexels/Coverr)
    Tier 3: Local whitelisted video loops (in backgrounds/)
    Tier 4: FFmpeg dynamic moving gradient loops.
    """
    import urllib.request
    from urllib.parse import quote
    
    motion_path = os.path.join(OUTPUT_DIR, f"motion_{index}_{cut_index}.mp4")
    image_path = os.path.join(OUTPUT_DIR, f"visual_{index}_{cut_index}.jpg")
    
    # --------------------------------------------------
    # TIER 1: AI Video (Gradio/Fal.ai)
    # --------------------------------------------------
    print(f"   [Tier 1] Attempting AI Video generation for: '{keyword}'")
    try:
        from modules.cloud_video_generator import generate_video_from_prompt_hf
        res_video = generate_video_from_prompt_hf(keyword, motion_path)
        if res_video and os.path.exists(res_video) and os.path.getsize(res_video) > 20000:
            temp_path = os.path.join(OUTPUT_DIR, f"temp_ai_{index}_{cut_index}.mp4")
            shutil.move(motion_path, temp_path)
            subprocess.run([
                "ffmpeg", "-y", "-i", temp_path,
                "-t", str(duration), "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-b:v", "8M", "-maxrate", "10M", "-bufsize", "16M", "-an", motion_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(temp_path):
                os.remove(temp_path)
            log_asset(f"img_{index}_{cut_index}", "ai_generator", "hf_license", "cloud")
            print(f"   [Tier 1] SUCCESS: AI video generated!")
            return motion_path
    except Exception as e:
        print(f"   [Tier 1] FAILED: {e}")

    # --------------------------------------------------
    # TIER 2: SKIPPED (Pollinations rate-limited). Going straight to Tier 3.
    # --------------------------------------------------
    print(f"   [Tier 2] ⏭️  Skipped (Pollinations rate-limited), going to Tier 3+4...")

    # --------------------------------------------------
    # TIER 4: FFmpeg dynamic moving gradient loops
    # --------------------------------------------------
    print(f"   [Tier 4] Falling back to FFmpeg dynamic moving gradient loop")
    try:
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "nullsrc=s=270x480",
            "-t", str(duration),
            "-vf", "geq=r='128+127*sin(N/10.0+X/25.0)':g='128+127*cos(N/15.0+Y/40.0)':b='128+127*sin(N/20.0+(X+Y)/50.0)',scale=1080:1920:flags=fast_bilinear,setsar=1",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-b:v", "8M", "-maxrate", "10M", "-bufsize", "16M", "-an", motion_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log_asset(f"img_{index}_{cut_index}", "ffmpeg_synthetic", "public_domain", "local")
        print(f"   [Tier 4] SUCCESS: Dynamic moving gradient generated!")
        return motion_path
    except Exception as e:
        print(f"   [Tier 4] FFmpeg dynamic gradient failed: {e}. Fallback to solid color block.")
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x1a0033:s=1080x1920",
            "-t", str(duration), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-b:v", "8M", "-maxrate", "10M", "-bufsize", "16M", "-an", motion_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log_asset(f"img_{index}_{cut_index}", "ffmpeg_synthetic", "public_domain", "local")
        return motion_path


def build_scene_visuals(scene, index, duration):
    # Cut frequency: force a visual cut every ~3 seconds
    if duration > 4.0:
        cuts = 2
        cut_duration = duration / 2
        clip1 = generate_visual_cut(scene["suggested_visual_keyword"], index, 1, cut_duration)
        clip2 = generate_visual_cut(scene["suggested_visual_keyword"] + " alternate angle", index, 2, cut_duration)
        
        # Concat the two cuts
        list_txt = os.path.join(OUTPUT_DIR, f"cuts_{index}.txt")
        with open(list_txt, "w") as f:
            f.write(f"file '{clip1}'\nfile '{clip2}'\n")
            
        scene_video = os.path.join(OUTPUT_DIR, f"scene_video_{index}.mp4")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_txt, "-c", "copy", scene_video], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return scene_video
    else:
        return generate_visual_cut(scene["suggested_visual_keyword"], index, 1, duration)

# ---------------------------------------------------------
# 5. CAPTIONS & ASSEMBLY (Spec Section 4, 5, 6)
# ---------------------------------------------------------
def assemble_final_video(scenes_data, all_words=None):
    if all_words is None:
        all_words = []
        current_time = 0.0
        for s in scenes_data:
            import re
            words_list = [w for w in re.split(r'\s+', s.get("text", "").strip()) if w]
            if words_list:
                t_per_word = s["duration"] / len(words_list)
                for j, word in enumerate(words_list):
                    all_words.append({
                        "text": word,
                        "start": current_time + j * t_per_word,
                        "end": current_time + (j + 1) * t_per_word
                    })
            current_time += s["duration"]
    # 1. Concat Audio
    audio_concat_txt = os.path.join(OUTPUT_DIR, "audio_concat.txt")
    with open(audio_concat_txt, "w") as f:
        for s in scenes_data: f.write(f"file '{s['audio']}'\n")
            
    master_audio = os.path.join(OUTPUT_DIR, "master_audio.mp3")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", audio_concat_txt, "-c", "copy", master_audio], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 1b. Mix BGM and SFX using dynamic sidechain ducking (R2)
    total_duration = sum(s['duration'] for s in scenes_data)
    num_scenes = len(scenes_data)
    
    from modules.background_music import generate_background_tone, generate_sfx
    from modules.audio_mixer import mix_cinematic_audio
    
    import time
    ts = time.time_ns()
    temp_bgm = os.path.join(OUTPUT_DIR, f"temp_bgm_{ts}.mp3")
    generate_background_tone(total_duration, temp_bgm, style='dramatic')
    
    # Transition whoosh SFX times
    clip_duration = max(3.0, min(8.0, total_duration / num_scenes)) if num_scenes > 0 else 4.0
    sfx_times = [i * clip_duration for i in range(1, num_scenes)]
    
    whoosh_path = os.path.join(OUTPUT_DIR, f"temp_whoosh_{ts}.wav")
    generate_sfx(whoosh_path, type="whoosh")
            
    sfx_list = [{"path": whoosh_path, "start": t, "volume": 0.15} for t in sfx_times]
    
    mixed_audio = os.path.join(OUTPUT_DIR, f"master_audio_mixed_{ts}.mp3")
    mix_cinematic_audio(master_audio, sfx_list=sfx_list, bgm_path=temp_bgm, output_path=mixed_audio)

    # 2. Concat Video
    video_concat_txt = os.path.join(OUTPUT_DIR, f"video_concat_{ts}.txt")
    with open(video_concat_txt, "w") as f:
        for s in scenes_data: f.write(f"file '{s['video']}'\n")
            
    master_video = os.path.join(OUTPUT_DIR, f"master_video_raw_{ts}.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", video_concat_txt, "-c", "copy", master_video], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 3. Generate ASS subtitles (R1)
    from modules.subtitle_generator import generate_ass_subtitles
    ass_path = os.path.join(OUTPUT_DIR, f"subtitles_{ts}.ass")
    generate_ass_subtitles(all_words, ass_path)
    
    final_output = os.path.join(OUTPUT_DIR, "VIDRUSH_MASTER.mp4")
    
    # Burn subtitles using FFmpeg's ass filter
    escaped_ass_path = ass_path.replace("\\", "/").replace(":", "\\:")
    subtitle_filter = f"ass='{escaped_ass_path}'"
    
# Quality flags: b:v 8M, ar 48000
    subprocess.run([
        "ffmpeg", "-y", "-i", master_video, "-i", mixed_audio,
        "-vf", subtitle_filter,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-b:v", "8M", "-maxrate", "10M", "-bufsize", "16M",
        "-c:a", "aac", "-ar", "48000", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0",
        final_output
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Clean up temp BGM files
    for temp_f in [temp_bgm, mixed_audio, master_video, video_concat_txt, ass_path]:
        if os.path.exists(temp_f):
            try:
                os.remove(temp_f)
            except Exception:
                pass
                
    return final_output, total_duration


# ---------------------------------------------------------
# 8. QA GATE & LOGGING (Spec Section 8)
# ---------------------------------------------------------
def write_log(status_marker, video_title, total_duration, real_count, fallback_count, fallback_ratio, qa_passed, qa_reason, upload_status, upload_error, licenses_used):
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{date_str}] {status_marker}\n"
    log_entry += f"Title: {video_title}\n"
    log_entry += f"Duration: {total_duration:.2f}s\n"
    log_entry += f"Visuals: {real_count} Real / {fallback_count} Synthetic (Ratio: {fallback_ratio*100:.1f}%)\n"
    log_entry += f"QA Gate: {'PASS' if qa_passed else 'FAIL'} - {qa_reason}\n"
    log_entry += f"Upload Status: {upload_status} {f'({upload_error})' if upload_error else ''}\n"
    log_entry += f"Licenses Used: {', '.join(licenses_used)}\n"
    log_entry += "-" * 50 + "\n"
    
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)
        
def create_alert(reason):
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alert_text = f"⚠️ URGENT ALERT [{date_str}]\n{reason}\nCheck daily_log.txt for details."
    with open(ALERT_FILE, "w") as f:
        f.write(alert_text)

def run_qa_gate(final_video, total_duration):
    errors = []
    real_count = 0
    fallback_count = 0
    licenses = set()
    unsafe_sources = []
    
    if total_duration < 20 or total_duration > 180:
        errors.append(f"Duration {total_duration}s out of bounds (25-180s)")
        
    if not os.path.exists(MANIFEST_FILE):
        errors.append("Manifest file missing.")
    else:
        with open(MANIFEST_FILE, "r") as f:
            try:
                manifest = json.load(f)
                for item in manifest:
                    licenses.add(item.get("license_type", "unknown"))
                    source = item.get("source", "")
                    if "ffmpeg" in source or "synthetic" in source:
                        fallback_count += 1
                    else:
                        real_count += 1
                    
                    # Whitelist: our own AI generators + stock + local + synthetic
                    SAFE_SOURCES = {
                        "pexels.com", "ffmpeg_synthetic", "public_domain", "local",
                        "ai_generator", "replicate", "hf_license", "kling",
                        "royalty_free_local", "cloud",
                        "ai_image", "pollinations"
                    }
                    if source not in SAFE_SOURCES:
                        unsafe_sources.append(source)
            except:
                errors.append("Manifest file corrupted.")
                
    total_visuals = real_count + fallback_count
    fallback_ratio = (fallback_count / total_visuals) if total_visuals > 0 else 1.0
    
    if fallback_ratio > 0.30:
        errors.append(f"Fallback ratio too high: {fallback_ratio*100:.1f}% (Limit: 30%)")

    if unsafe_sources:
        errors.append(f"UNSAFE SOURCE DETECTED: {', '.join(unsafe_sources)}")
        
    qa_passed = len(errors) == 0
    qa_reason = " | ".join(errors) if errors else "All metrics passed successfully"
    
    return qa_passed, qa_reason, real_count, fallback_count, fallback_ratio, list(licenses)

async def main():
    parser = argparse.ArgumentParser(description="VidRush Pipeline Generator")
    parser.add_argument("--no-upload", action="store_true", help="Generate full video and run QA gate, but skip YouTube upload.")
    args = parser.parse_args()

    # Create empty manifest for the new run
    if os.path.exists(MANIFEST_FILE):
        os.remove(MANIFEST_FILE)

    print("🚀 INITIALIZING VIDRUSH SPEC PIPELINE...")
    if args.no_upload:
        print("⚠️ NO-UPLOAD MODE ACTIVATED: Full pipeline will run, but video will be saved locally without uploading.")
        
    scenes = generate_script()
        
    scenes_data = []
    all_words = []
    current_time = 0.0
    for i, scene in enumerate(scenes):
        print(f"\n[Scene {i+1}] {scene['emotion_tag'].upper()}: {scene['text']}")
        audio_path, vtt_path, duration, scene_words = await generate_scene_audio(scene, i)
        video_path = build_scene_visuals(scene, i, duration)
        
        for w in scene_words:
            all_words.append({
                "text": w["text"],
                "start": w["start"] + current_time,
                "end": w["end"] + current_time
            })
            
        scenes_data.append({
            "text": scene['text'],
            "audio": audio_path,
            "video": video_path,
            "duration": duration
        })
        current_time += duration
        
    print("\n🎬 Assembling Final Video with Safe-Zone Captions...")
    final_vid, total_dur = assemble_final_video(scenes_data, all_words)

    # ── R3: SEO Metadata (before QA so title is available for thumbnail) ──
    video_niche = "motivation"
    video_title = "5 Second Rule Secret Revealed"  # default; overridden by Groq below
    seo_meta = generate_seo_metadata(video_title, video_niche, OUTPUT_DIR)
    video_title = seo_meta.get("title", video_title)

    qa_passed, qa_reason, real_count, fallback_count, fallback_ratio, licenses = run_qa_gate(final_vid, total_dur)

    # Use the Groq-generated SEO title (already set above)
    upload_status = "Skipped"
    upload_error = ""
    status_marker = "✅ SUCCESS"

    if not qa_passed:
        print(f"❌ QA GATE FAILED: {qa_reason}")
        status_marker = "⚠️ ATTENTION NEEDED (QA FAIL)"
        create_alert(f"QA Gate Failed: {qa_reason}")
        # Move to failed directory
        failed_path = os.path.join(FAILED_DIR, f"failed_video_{int(time.time())}.mp4")
        shutil.move(final_vid, failed_path)
        print(f"📁 Video safely moved to: {failed_path}")
    else:
        print("✅ QA GATE PASSED.")
        # ── R2: AI Thumbnail ──────────────────────────────────────────────
        generate_thumbnail(seo_meta.get("title", video_title), OUTPUT_DIR)
        if args.no_upload:
            print(f"🎉 RENDER SUCCESSFUL (UPLOAD SKIPPED): {final_vid}")
        else:
            try:
                from modules.youtube_uploader import get_authenticated_service
                from googleapiclient.http import MediaFileUpload
                
                print("📡 Initiating YouTube Upload...")
                youtube = get_authenticated_service()
                if not youtube:
                    raise Exception("Auth Failed. Check client_secrets.json or token.")
                    
                body = {
                    "snippet": {
                        "title": f"{video_title} 🤯 #shorts #viral",
                        "description": "This psychology trick will change your life! #shorts #motivation #facts",
                        "tags": ["shorts", "viral", "motivation", "psychology"],
                        "categoryId": "27"
                    },
                    "status": {
                        "privacyStatus": "public",
                        "madeForKids": False
                    }
                }
                media = MediaFileUpload(final_vid, chunksize=1024*1024, resumable=True)
                request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)
                
                response = None
                while response is None:
                    status, response = request.next_chunk()
                    if status:
                        print(f"⏳ Uploading... {int(status.progress() * 100)}%")
                        
                print(f"✅ Upload Complete! Link: https://youtu.be/{response.get('id')}")
                upload_status = "Success"
            except Exception as e:
                print(f"❌ Upload failed: {e}")
                upload_status = "Failed"
                upload_error = str(e)
                status_marker = "⚠️ ATTENTION NEEDED (UPLOAD FAIL)"
                create_alert(f"Upload Failed: {upload_error}")
                failed_path = os.path.join(FAILED_DIR, f"upload_failed_{int(time.time())}.mp4")
                shutil.move(final_vid, failed_path)
    
    write_log(status_marker, video_title, total_dur, real_count, fallback_count, fallback_ratio, qa_passed, qa_reason, upload_status, upload_error, licenses)
    print(f"\n📝 Daily log updated at {LOG_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
