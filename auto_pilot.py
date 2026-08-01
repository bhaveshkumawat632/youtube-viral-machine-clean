#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║        🚀 YOUTUBE VIRAL MACHINE — AUTO PILOT v2.0           ║
║                                                              ║
║   Ek command. Sab automatic.                                 ║
║   Topic → Script → Voice → Video → SEO → Upload             ║
║                                                              ║
║   Usage:                                                     ║
║     python3 auto_pilot.py                     (1 video)      ║
║     python3 auto_pilot.py --count 3           (3 videos)     ║
║     python3 auto_pilot.py --niche motivation  (specific)     ║
║     python3 auto_pilot.py --language english                 ║
║     python3 auto_pilot.py --no-upload         (skip upload)  ║
║     python3 auto_pilot.py --daemon            (daily auto)   ║
╚══════════════════════════════════════════════════════════════╝
"""
import os
import re
import sys
import time
import json
import random
import asyncio
import argparse
import subprocess
import traceback
from datetime import datetime, timedelta

# Ensure project root is in path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from config import (
    OUTPUT_DIR, TEMP_DIR, VOICES, GRADIENTS,
    SHORTS_WIDTH, SHORTS_HEIGHT, FPS, NICHES
)
from modules.script_generator import (
    generate_script, READY_SCRIPTS_HINDI, READY_SCRIPTS_ENGLISH
)
from modules.voiceover import generate_voiceover, get_audio_duration
from modules.subtitle_generator import (
    words_from_edge_tts,
    words_from_script_with_timestamps,
    generate_ass_subtitles, generate_srt_subtitles
)
from modules.video_maker import create_video_from_audio_and_subtitles
from modules.seo_generator import generate_metadata
from modules.youtube_uploader import upload_video
from modules.image_motion_generator import get_pollinations_image
from modules.background_music import generate_background_tone, mix_audio
from modules.llm_script_generator import generate_powerful_script
from modules.cloud_video_generator import generate_video_from_prompt_hf

# ============================================================
# LOGGING
# ============================================================
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(LOG_DIR, exist_ok=True)


def log(msg, level="INFO"):
    """Log message to console and file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level}] {msg}"
    print(line)
    log_file = os.path.join(LOG_DIR, f"autopilot_{datetime.now().strftime('%Y-%m-%d')}.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def print_banner():
    print("""
\033[96m╔══════════════════════════════════════════════════════════════╗
║\033[93m        🚀 AUTO PILOT v2.0 — ZERO TOUCH MODE                \033[96m║
║\033[92m        Topic → Script → Voice → Video → Upload              \033[96m║
╚══════════════════════════════════════════════════════════════╝\033[0m
""")


# ============================================================
# STEP 1: PICK TOPIC & SCRIPT
# ============================================================
def pick_script(niche=None, language="english"):
    """
    Generate a powerful viral script using LLM instead of templates.
    Returns dict with: title, hook, body, cta, niche
    """
    import random
    VIRAL_US_TOPICS = [
        "Dark Psychology Secrets",
        "How to Read Anyone Instantly",
        "Manipulative Mind Control Tricks",
        "The Psychology of Silence",
        "Cognitive Biases that Control Your Life",
        "Signs Someone is Secretly Attracted to You",
        "The Power of Eye Contact",
        "How to Detect a Liar Instantly",
        "Psychological Tricks to Gain Respect",
        "Why People Pleasing is Ruining You"
    ]
    
    if not niche or niche == "random":
        chosen_topic = random.choice(VIRAL_US_TOPICS) if language == "english" else "Mind Blowing Psychological Facts"
        niche_val = "psychology"
    else:
        chosen_topic = niche
        niche_val = niche
    
    # Try using the LLM for high quality content
    try:
        script_data = generate_powerful_script(topic=chosen_topic, language=language)
        script_data["niche"] = niche_val
        log(f"📄 High-Retention Script generated: \"{script_data.get('title')}\"")
        return script_data
    except Exception as e:
        log(f"⚠️ LLM Script generation failed ({e}), using fallback.", "WARN")
        return {
            "title": "5 Mind-Blowing Psychological Facts",
            "scenes": [
                {
                    "text": "Did you know that your brain can easily create false memories?",
                    "visual_prompt": "A close up of a glowing neural network pulsing.",
                    "youtube_search_query": "brain neurons firing"
                },
                {
                    "text": "If you tell yourself you slept well, your brain actually believes it.",
                    "visual_prompt": "A person waking up happily in a bright bedroom.",
                    "youtube_search_query": "waking up happy"
                }
            ],
            "niche": "psychology"
        }


# ============================================================
# STEP 2: GENERATE VOICEOVER
# ============================================================
def generate_voice(script_data, voice_key="hindi_male", timestamp_id=None):
    """
    Generate AI voiceover from script.
    Returns: (audio_path, words_json_path, duration)
    """
    ts = timestamp_id or int(time.time())
    
    # NEW SCHEMA: array of scenes
    full_script = "\n\n".join([scene["text"] for scene in script_data["scenes"]])

    safe_title = re.sub(r'[^a-zA-Z0-9_-]', '', script_data['title'].replace(' ', '_'))[:30]
    audio_path = os.path.join(TEMP_DIR, f"{safe_title}_{ts}.mp3")

    log(f"🎙️ Generating voiceover ({voice_key})...")
    audio_path, words_json_path, words = generate_voiceover(
        full_script, audio_path, voice_key
    )
    duration = get_audio_duration(audio_path)
    log(f"✅ Audio ready: {duration:.1f}s, {len(words)} words")

    return audio_path, words_json_path, duration, full_script


# ============================================================
# STEP 3: GENERATE SUBTITLES
# ============================================================
def generate_subs(full_script, audio_path, words_json_path, voice_key, timestamp_id=None):
    """
    Generate ASS (for video burn-in) and SRT (for YouTube) subtitles.
    Returns: (ass_path, srt_path)
    """
    ts = timestamp_id or int(time.time())
    lang_code = "en" # Script is exclusively English now, even if spoken with Indian accent

    # Get word-level timestamps
    words = []
    if words_json_path and os.path.exists(words_json_path):
        words = words_from_edge_tts(words_json_path)

    if not words:
        log("⚠️ Edge TTS words not available, using Whisper fallback...")
        words = words_from_script_with_timestamps(full_script, audio_path, language=lang_code)

    safe_name = f"autopilot_{ts}"
    ass_path = os.path.join(TEMP_DIR, f"{safe_name}.ass")
    srt_path = os.path.join(OUTPUT_DIR, f"{safe_name}.srt")

    log(f"🔤 Generating subtitles ({len(words)} words)...")
    generate_ass_subtitles(words, ass_path, video_width=SHORTS_WIDTH, video_height=SHORTS_HEIGHT)
    generate_srt_subtitles(words, srt_path)

    return ass_path, srt_path


# ============================================================
# FETCH RELEVANT STOCK VIDEO BACKGROUND
# ============================================================
def fetch_dynamic_background_video(script_data, duration, timestamp_id, is_anime=False):
    """
    Generates high-end AI videos for each specific scene using top-tier models (LTX Video).
    If AI fails, fetches exact character-driven stock footage from YouTube per scene.
    Returns a list of video paths to be stitched together for perfectly synced cuts.
    """
    import glob
    import subprocess
    ts = timestamp_id or int(time.time())
    title = script_data.get('title', 'Video')
    scenes = script_data.get('scenes', [])
    
    log(f"🧠 CLOUD AI ORCHESTRATION: Generating custom character role-play scenes for: '{title}'...")
    
    downloaded_files = []
    used_coverr_urls = []
    for i, scene in enumerate(scenes):
        base_prompt = scene.get('visual_prompt', '')
        
        if is_anime:
            log(f"🎨 Generating Anime Visual scene {i+1}/{len(scenes)}: {base_prompt[:50]}...")
            prompt = f"Beautiful colorful anime style, vertical, highly detailed, makoto shinkai aesthetic: {base_prompt}"
            from modules.image_motion_generator import get_pollinations_image
            
            image_path = os.path.join(TEMP_DIR, f"anime_img_{ts}_{i}.jpg")
            get_pollinations_image(prompt, image_path)
            
            # Convert to video with zoompan Ken Burns
            scene_duration = max(3.0, min(8.0, duration / len(scenes))) if len(scenes) > 0 else 4.0
            temp_clip = os.path.join(TEMP_DIR, f"anime_clip_{ts}_{i}.mp4")
            
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", image_path,
                "-vf", f"scale=1200:2133,crop=w=1080:h=1920:x='60+50*sin(2*PI*t/4.0)':y='106+80*cos(2*PI*t/4.0)',setsar=1",
                "-t", f"{scene_duration:.2f}",
                "-c:v", "libx264", "-preset", "ultrafast",
                "-pix_fmt", "yuv420p",
                temp_clip
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(temp_clip):
                downloaded_files.append(temp_clip)
            else:
                log(f"⚠️ Failed to create anime clip for scene {i+1}", "WARN")
            continue

        search_query = scene.get('youtube_search_query', 'cinematic character stock footage')
        prompt = f"A hyperrealistic cinematic shot of characters roleplaying: {base_prompt}, expressive acting, dark moody lighting, 4k resolution, smooth motion."
        
        log(f"🎬 Generating LTX Video AI scene {i+1}/{len(scenes)}: {base_prompt[:50]}...")
        vid_path = None
        try:
            vid_path = generate_video_from_prompt_hf(prompt, os.path.join(TEMP_DIR, f"ai_bg_{ts}_{i}.mp4"))
        except Exception as e:
            log(f"⚠️ AI video generation failed for scene {i+1}: {e}", "WARN")
            
        if vid_path and os.path.exists(vid_path) and os.path.getsize(vid_path) > 200000:
            downloaded_files.append(vid_path)
        else:
            # High quality fallback: Search Coverr.co for 100% copyright-free stock footage
            log(f"🔍 AI Failed or returned static image. Fetching Copyright-Free Clip from Coverr.co: '{search_query}'...")
            output_template = os.path.join(TEMP_DIR, f"dynamic_bg_{ts}_{i}.mp4")
            
            # Simple python based scraper for Coverr
            def fetch_coverr(query, exclude_urls=None):
                import urllib.request
                import re
                try:
                    url = f"https://coverr.co/s?q={urllib.parse.quote(query)}"
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
                    links = re.findall(r'https://cdn\.coverr\.co/videos/[^"]*1080p\.mp4', html)
                    if exclude_urls and links:
                        for l in links:
                            if l not in exclude_urls:
                                return l
                    return links[0] if links else None
                except Exception:
                    return None
                    
            video_url = fetch_coverr(search_query, used_coverr_urls)
            if not video_url:
                # Build a smarter fallback query by cleaning out stop words
                stop_words = ["a", "an", "the", "in", "on", "of", "with", "is", "are", "to", "and", "close-up", "shot", "showing", "shown", "characters", "roleplaying", "representing", "representing:", "animated", "animation", "against", "themselves", "versus", "trying", "some", "footage"]
                words = [w.strip(":,.;!?") for w in search_query.split() if w.lower().strip(":,.;!?") not in stop_words]
                
                # Try combining first two words, then first word
                fallback_query = None
                if len(words) >= 2:
                    fallback_query = f"{words[0]} {words[1]}"
                elif words:
                    fallback_query = words[0]
                else:
                    fallback_query = "people"
                
                print(f"🔄 Search failed, trying fallback query: '{fallback_query}'")
                video_url = fetch_coverr(fallback_query, used_coverr_urls)
                if not video_url:
                    video_url = fetch_coverr("cinematic", used_coverr_urls)
            
            if video_url:
                try:
                    # Download the specific 1080p video directly
                    subprocess.run(["wget", "-q", "-O", output_template, video_url], check=True)
                    if os.path.exists(output_template) and os.path.getsize(output_template) > 200000:
                        # Trim to 8 seconds max to match previous behavior
                        trimmed_template = os.path.join(TEMP_DIR, f"trim_bg_{ts}_{i}.mp4")
                        subprocess.run(["ffmpeg", "-y", "-i", output_template, "-t", "8", "-c", "copy", trimmed_template, "-loglevel", "quiet"])
                        os.replace(trimmed_template, output_template)
                        downloaded_files.append(output_template)
                        used_coverr_urls.append(video_url)
                    else:
                        log(f"⚠️ Coverr clip too small for scene {i+1}.", "WARN")
                except Exception as e:
                    log(f"⚠️ Failed to download Coverr clip for scene {i+1}: {e}", "WARN")
            else:
                log(f"⚠️ No Coverr clips found for scene {i+1}.", "WARN")
            
    if downloaded_files:
        log(f"✅ Gathered {len(downloaded_files)} premium character video clips!")
        return downloaded_files
    
    return None

# ============================================================
# STEP 4: RENDER VIDEO (Direct FFmpeg — 3x FASTER)
# ============================================================
def render_video(audio_path, ass_path, script_data, duration, timestamp_id=None, is_anime=False):
    """
    Render final video with dynamic video background + subtitles.
    """
    ts = timestamp_id or int(time.time())

    # Fetch a relevant stock video background for THIS specific script
    bg_video_path = fetch_dynamic_background_video(script_data, duration, ts, is_anime=is_anime)
        
    output_filename = f"autopilot_{ts}.mp4"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    if bg_video_path:
        log(f"🎬 Rendering video with topic-relevant video clip...")
    else:
        log(f"🎬 Rendering video with fallback background...")
        
    start_time = time.time()

    create_video_from_audio_and_subtitles(
        audio_path=audio_path,
        subtitle_path=ass_path,
        output_path=output_path,
        background_video=bg_video_path,
        video_format="shorts"
    )

    elapsed = time.time() - start_time
    if os.path.exists(output_path):
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        log(f"✅ Video rendered: {output_path} ({size_mb:.1f}MB in {elapsed:.0f}s)")
    else:
        log("❌ Video rendering failed!", "ERROR")
        return None

    return output_path


# ============================================================
# STEP 5: GENERATE SEO METADATA
# ============================================================
def generate_seo(script_data, language="hindi"):
    """Generate optimized title, description, tags for YouTube."""
    metadata = generate_metadata(
        title=script_data["title"],
        niche=script_data.get("niche", "motivation"),
        language=language
    )
    log(f"📊 SEO generated: \"{metadata['title'][:60]}...\"")
    return metadata


# ============================================================
# STEP 6: UPLOAD TO YOUTUBE
# ============================================================
def upload_to_youtube(video_path, metadata):
    """Upload video to YouTube with SEO metadata."""
    log(f"🚀 Uploading to YouTube: \"{metadata['title'][:50]}...\"")

    upload_metadata = {
        "title": metadata["title"][:100],
        "description": metadata["description"],
        "tags": metadata["tags"],
        "category_id": "22"  # People & Blogs
    }

    try:
        success = upload_video(video_path, upload_metadata)
        if success:
            log("✅ Upload successful!")
        else:
            log("❌ Upload failed", "ERROR")
        return success
    except Exception as e:
        log(f"❌ Upload error: {e}", "ERROR")
        return False


# ============================================================
# 🚀 FULL PIPELINE — One Click Magic
# ============================================================
def run_full_pipeline(niche=None, language="hindi", voice_key=None,
                      gradient=None, do_upload=True, is_anime=False):
    """
    Complete automated pipeline:
    Topic → Script → Voice → Subtitles → Video → SEO → Upload
    
    Returns: dict with status and details
    """
    pipeline_start = time.time()
    ts = int(time.time())

    # Auto-select voice if not specified
    if voice_key is None:
        voice_key = "hindi_male" if language == "hindi" else "english_male"

    result = {
        "success": False,
        "video_path": None,
        "srt_path": None,
        "title": None,
        "timestamp": ts,
    }

    try:
        # STEP 1: Pick Script
        log("=" * 60)
        log(f"🎯 STEP 1/6 — Picking Script (niche: {niche or 'random'})...")
        script_data = pick_script(niche=niche, language=language)
        result["title"] = script_data["title"]

        # STEP 2: Generate Voice
        log(f"🎯 STEP 2/6 — Generating Voiceover...")
        # Reduce speech rate slightly to make it less robotic
        voice_key = "hindi_male" if language == "hindi" else "english_male"
        audio_path, words_json_path, duration, full_script = generate_voice(
            script_data, voice_key=voice_key, timestamp_id=ts
        )

        # Mix with Background Music to hide robotic tone
        log(f"🎵 Bypassing Background Music for Maximum Voice Clarity...")
        # We no longer mix audio so the TTS voice remains 100% crystal clear
        # audio_path is used directly

        # STEP 3: Generate Subtitles
        log(f"🎯 STEP 3/6 — Generating Subtitles...")
        ass_path, srt_path = generate_subs(
            full_script, audio_path, words_json_path, voice_key, timestamp_id=ts
        )
        result["srt_path"] = srt_path

        # STEP 4: Render Video
        log(f"🎯 STEP 4/6 — Rendering Video...")
        video_path = render_video(audio_path, ass_path, script_data, duration, timestamp_id=ts, is_anime=is_anime)
        if not video_path:
            log("❌ Pipeline failed at video rendering", "ERROR")
            return result
        result["video_path"] = video_path

        # STEP 5: Generate SEO
        log(f"🎯 STEP 5/6 — Generating SEO Metadata...")
        metadata = generate_seo(script_data, language=language)

        # STEP 6: Upload
        if do_upload:
            log(f"🎯 STEP 6/6 — Uploading to YouTube...")
            uploaded = upload_to_youtube(video_path, metadata)
            result["uploaded"] = uploaded
        else:
            log(f"⏩ STEP 6/6 — Upload skipped (--no-upload)")
            result["uploaded"] = False

        # Done!
        elapsed = time.time() - pipeline_start
        result["success"] = True
        log("=" * 60)
        log(f"🎉 PIPELINE COMPLETE in {elapsed:.0f}s!")
        log(f"   📄 Title: {script_data['title']}")
        log(f"   🎬 Video: {video_path}")
        log(f"   📝 SRT:   {srt_path}")
        log("=" * 60)

    except Exception as e:
        log(f"❌ Pipeline failed: {e}", "ERROR")
        traceback.print_exc()

    return result


# ============================================================
# 🔁 DAEMON MODE — Auto Daily Scheduler
# ============================================================
def run_daemon(count_per_day=3, niche=None, language="hindi",
               voice_key=None, do_upload=True, is_anime=False):
    """
    Runs the pipeline automatically every day.
    Generates 'count_per_day' videos with gaps between them.
    """
    log("🤖 DAEMON MODE ACTIVATED — Auto Daily Video Generation")
    log(f"   Videos per day: {count_per_day}")
    log(f"   Niche: {niche or 'random'}")
    log(f"   Language: {language}")
    log(f"   Upload: {'Yes' if do_upload else 'No'}")

    while True:
        day_start = datetime.now()
        log(f"\n{'='*60}")
        log(f"📅 NEW DAY: {day_start.strftime('%Y-%m-%d %H:%M:%S')}")
        log(f"{'='*60}")

        # Calculate gap between videos (spread across waking hours ~8AM-10PM)
        gap_seconds = (14 * 3600) // max(count_per_day, 1)  # 14 hours spread

        for i in range(count_per_day):
            log(f"\n🎬 Video {i+1}/{count_per_day} for today...")

            result = run_full_pipeline(
                niche=niche,
                language=language,
                voice_key=voice_key,
                do_upload=do_upload,
                is_anime=is_anime
            )

            if result["success"]:
                log(f"✅ Video {i+1} done: {result.get('title', 'N/A')}")
            else:
                log(f"⚠️ Video {i+1} failed, continuing...", "WARN")

            # Wait between videos (skip wait after last one)
            if i < count_per_day - 1:
                wait_min = gap_seconds // 60
                log(f"⏳ Waiting {wait_min} minutes before next video...")
                time.sleep(gap_seconds)

        # Calculate when to start next day
        next_day = (day_start + timedelta(days=1)).replace(hour=8, minute=0, second=0)
        sleep_seconds = (next_day - datetime.now()).total_seconds()

        if sleep_seconds > 0:
            log(f"\n😴 Day complete! Sleeping until tomorrow {next_day.strftime('%H:%M')}...")
            log(f"   ({sleep_seconds/3600:.1f} hours)")
            time.sleep(sleep_seconds)
        else:
            # Already past 8 AM next day, start immediately
            log("⚡ Starting next cycle immediately...")


# ============================================================
# MAIN
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="🚀 YouTube Viral Machine — Auto Pilot v2.0"
    )
    parser.add_argument("--count", type=int, default=1,
                        help="Number of videos to generate (default: 1)")
    parser.add_argument("--niche", type=str, default=None,
                        help="Specific niche (motivation, facts, horror, etc.)")
    parser.add_argument("--language", type=str, default="english",
                        choices=["hindi", "english"],
                        help="Script language (default: english)")
    parser.add_argument("--voice", type=str, default="english_dramatic",
                        help="Voice key (english_dramatic, english_male, etc.)")
    parser.add_argument("--gradient", type=str, default=None,
                        help="Background gradient name")
    parser.add_argument("--no-upload", action="store_true",
                        help="Skip YouTube upload")
    parser.add_argument("--daemon", action="store_true",
                        help="Run in daemon mode (daily auto-generation)")
    parser.add_argument("--per-day", type=int, default=3,
                        help="Videos per day in daemon mode (default: 3)")
    parser.add_argument("--anime", action="store_true",
                        help="Generate anime-style video using Pollinations AI")

    args = parser.parse_args()

    print_banner()

    # Ensure output dirs exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    if args.daemon:
        # DAEMON MODE: Auto daily generation
        run_daemon(
            count_per_day=args.per_day,
            niche=args.niche,
            language=args.language,
            voice_key=args.voice,
            do_upload=not args.no_upload,
            is_anime=args.anime
        )
    else:
        # SINGLE RUN: Generate specified number of videos
        results = []
        for i in range(args.count):
            if args.count > 1:
                log(f"\n{'='*60}")
                log(f"📹 VIDEO {i+1}/{args.count}")
                log(f"{'='*60}")

            result = run_full_pipeline(
                niche=args.niche,
                language=args.language,
                voice_key=args.voice,
                gradient=args.gradient,
                do_upload=not args.no_upload,
                is_anime=args.anime
            )
            results.append(result)

            # Small gap between videos
            if i < args.count - 1:
                log("⏳ 10s gap before next video...")
                time.sleep(10)

        # Summary
        success_count = sum(1 for r in results if r["success"])
        log(f"\n{'='*60}")
        log(f"📊 SUMMARY: {success_count}/{args.count} videos generated successfully")
        for r in results:
            status = "✅" if r["success"] else "❌"
            log(f"   {status} {r.get('title', 'N/A')} → {r.get('video_path', 'Failed')}")
        log(f"{'='*60}")


if __name__ == "__main__":
    main()
