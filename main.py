#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║           🎬 YOUTUBE VIRAL MACHINE 🎬                       ║
║     Free Auto-Clipper + Video Generator for YouTube          ║
║                                                              ║
║  Features:                                                   ║
║   1. Script-to-Video: Topic → Script → Voice → Subtitles → Video ║
║   2. Auto-Clipper: Long video → Multiple viral Shorts        ║
║   3. Add Subtitles: Add animated subtitles to any video      ║
║   4. Voiceover Only: Generate AI voice from text             ║
╚══════════════════════════════════════════════════════════════╝
"""
import os
import sys
import time
import json

# Ensure project root is in path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from config import (
    OUTPUT_DIR, TEMP_DIR, VOICES, GRADIENTS,
    SHORTS_WIDTH, SHORTS_HEIGHT, VIDEO_WIDTH, VIDEO_HEIGHT
)
from modules.script_generator import generate_script, get_all_scripts, list_niches, READY_SCRIPTS_HINDI, READY_SCRIPTS_ENGLISH
from modules.voiceover import generate_voiceover, list_available_voices, get_audio_duration
from modules.subtitle_generator import (
    transcribe_audio, words_from_edge_tts,
    words_from_script_with_timestamps,
    generate_ass_subtitles, generate_srt_subtitles
)
from modules.video_maker import (
    create_video_from_audio_and_subtitles,
    add_subtitles_to_video, crop_to_shorts
)
from modules.auto_clipper import auto_clip_video
from modules.batch_generator import batch_generate
from modules.seo_generator import generate_metadata
from modules.background_music import generate_background_tone, mix_audio

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')


def print_banner():
    banner = """
\033[95m╔══════════════════════════════════════════════════════════════╗
║\033[93m           🎬  YOUTUBE VIRAL MACHINE  🎬                     \033[95m║
║\033[96m       Free Video Generator for YouTube Domination            \033[95m║
╠══════════════════════════════════════════════════════════════╣
║\033[92m  💰 100% FREE  |  🚫 No Watermark  |  🎯 Viral Ready       \033[95m║
╚══════════════════════════════════════════════════════════════╝\033[0m
"""
    print(banner)


def print_menu():
    menu = """
\033[96m┌──────────────────────────────────────────┐
│           MAIN MENU                      │
├──────────────────────────────────────────┤\033[0m
│                                          │
│  \033[93m[1]\033[0m 🎬 Script → Video (Full Auto)       │
│      Topic do, video lo!                 │
│                                          │
│  \033[93m[2]\033[0m ✂️  Auto Clipper                     │
│      Long video → Viral Shorts           │
│                                          │
│  \033[93m[3]\033[0m 🔤 Add Subtitles to Video            │
│      Kisi bhi video mein subtitles dalo  │
│                                          │
│  \033[93m[4]\033[0m 🎤 Voiceover Only                    │
│      Text se AI voice banao              │
│                                          │
│  \033[93m[5]\033[0m 📝 Browse Scripts                    │
│      Ready-made viral scripts dekho      │
│                                          │
│  \033[93m[6]\033[0m ⚙️  Settings                         │
│                                          │
│  \033[93m[7]\033[0m 🚀 Batch Generate                    │
│      Ek saath kai videos banao           │
│                                          │
│  \033[93m[8]\033[0m 📊 SEO Metadata Generator            │
│      YouTube tags and titles             │
│                                          │
│  \033[91m[0]\033[0m ❌ Exit                              │
│                                          │
\033[96m└──────────────────────────────────────────┘\033[0m
"""
    print(menu)


def mode_script_to_video():
    """Mode 1: Generate complete video from script"""
    print(f"\n\033[95m{'='*60}\033[0m")
    print(f"\033[93m🎬 SCRIPT → VIDEO (Full Automatic)\033[0m")
    print(f"\033[95m{'='*60}\033[0m")

    # Choose language
    print("\n\033[96mLanguage:\033[0m")
    print("  [1] Hindi (Recommended for Indian audience)")
    print("  [2] English")
    lang_choice = input("\n👉 Choose (1/2): ").strip()
    language = "english" if lang_choice == "2" else "hindi"

    # Choose niche
    niches = list_niches()
    print(f"\n\033[96mNiche/Category:\033[0m")
    for i, niche in enumerate(niches, 1):
        emoji_map = {"motivation": "💪", "facts": "🧠", "horror": "👻", "tech": "💻", "money": "💰"}
        emoji = emoji_map.get(niche, "📌")
        print(f"  [{i}] {emoji} {niche.title()}")
    print(f"  [{len(niches)+1}] ✏️  Custom Topic")

    niche_choice = input(f"\n👉 Choose (1-{len(niches)+1}): ").strip()

    custom_topic = None
    try:
        idx = int(niche_choice) - 1
        if idx == len(niches):
            custom_topic = input("\n✏️  Apna topic likho: ").strip()
            niche = "motivation"
        elif 0 <= idx < len(niches):
            niche = niches[idx]
        else:
            niche = "motivation"
    except ValueError:
        niche = "motivation"

    # Choose script or generate
    scripts_db = READY_SCRIPTS_HINDI if language == "hindi" else READY_SCRIPTS_ENGLISH
    niche_scripts = scripts_db.get(niche, scripts_db.get("motivation", []))

    if not custom_topic and niche_scripts:
        print(f"\n\033[96mAvailable Scripts for {niche.title()}:\033[0m")
        for i, s in enumerate(niche_scripts, 1):
            print(f"  [{i}] {s['title']}")
            print(f"      🎣 {s['hook'][:70]}...")
        print(f"  [{len(niche_scripts)+1}] 🎲 Random script")

        script_choice = input(f"\n👉 Choose (1-{len(niche_scripts)+1}): ").strip()
        try:
            s_idx = int(script_choice) - 1
            if 0 <= s_idx < len(niche_scripts):
                selected = niche_scripts[s_idx]
                script_data = {
                    "title": selected["title"],
                    "hook": selected["hook"],
                    "body": selected["body"],
                    "cta": selected["cta"],
                    "full_script": f"{selected['hook']}\n\n{selected['body']}\n\n{selected['cta']}",
                }
            else:
                script_data = generate_script(niche, language)
        except ValueError:
            script_data = generate_script(niche, language)
    else:
        script_data = generate_script(niche, language, custom_topic)

    # Show script
    print(f"\n\033[93m{'─'*60}\033[0m")
    print(f"\033[93m📝 SCRIPT: {script_data['title']}\033[0m")
    print(f"\033[93m{'─'*60}\033[0m")
    print(f"\n\033[92m🎣 HOOK:\033[0m\n{script_data['hook']}")
    print(f"\n\033[96m📖 BODY:\033[0m\n{script_data['body']}")
    print(f"\n\033[95m📢 CTA:\033[0m\n{script_data['cta']}")
    print(f"\033[93m{'─'*60}\033[0m")

    proceed = input("\n\033[92m✅ Is script se video banana hai? (y/n): \033[0m").strip().lower()
    if proceed != 'y' and proceed != 'yes' and proceed != '':
        print("❌ Cancelled.")
        return

    # Choose voice
    print(f"\n\033[96mVoice:\033[0m")
    voice_keys = list(VOICES.keys())
    for i, vk in enumerate(voice_keys, 1):
        print(f"  [{i}] {vk} ({VOICES[vk]})")

    voice_choice = input(f"\n👉 Choose (1-{len(voice_keys)}) [default: 1]: ").strip()
    try:
        v_idx = int(voice_choice) - 1
        voice_key = voice_keys[v_idx] if 0 <= v_idx < len(voice_keys) else voice_keys[0]
    except (ValueError, IndexError):
        voice_key = "hindi_male" if language == "hindi" else "english_male"

    # Choose video format
    print(f"\n\033[96mVideo Format:\033[0m")
    print("  [1] 📱 YouTube Shorts (9:16) - Recommended!")
    print("  [2] 🖥️  YouTube Video (16:9)")
    format_choice = input("\n👉 Choose (1/2) [default: 1]: ").strip()
    video_format = "video" if format_choice == "2" else "shorts"

    # Choose gradient background
    print(f"\n\033[96mBackground:\033[0m")
    grad_keys = list(GRADIENTS.keys())
    for i, gk in enumerate(grad_keys, 1):
        print(f"  [{i}] 🎨 {gk}")
    print(f"  Or enter path to background video/image")

    bg_choice = input(f"\n👉 Choose (1-{len(grad_keys)}) or file path: ").strip()
    gradient_name = DEFAULT_GRADIENT = "neon_dark"
    bg_video = None
    bg_image = None

    if os.path.isfile(bg_choice):
        ext = os.path.splitext(bg_choice)[1].lower()
        if ext in ('.mp4', '.mkv', '.avi', '.mov', '.webm'):
            bg_video = bg_choice
        elif ext in ('.jpg', '.jpeg', '.png', '.webp'):
            bg_image = bg_choice
    else:
        try:
            g_idx = int(bg_choice) - 1
            if 0 <= g_idx < len(grad_keys):
                gradient_name = grad_keys[g_idx]
        except (ValueError, IndexError):
            pass

    # Generate!
    print(f"\n\033[93m{'='*60}\033[0m")
    print(f"\033[92m🚀 GENERATING VIDEO...\033[0m")
    print(f"\033[93m{'='*60}\033[0m\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    timestamp = int(time.time())
    safe_title = script_data['title'].replace(' ', '_').replace('/', '_')[:30]

    # Step 1: Generate voiceover
    print("🎤 Step 1/3: Generating AI voiceover...")
    audio_path = os.path.join(TEMP_DIR, f"{safe_title}_{timestamp}.mp3")
    audio_path, words_json_path, word_boundaries = generate_voiceover(
        script_data["full_script"], audio_path, voice_key
    )
    duration = get_audio_duration(audio_path)
    print(f"   ✅ Voiceover: {duration:.1f}s, {len(word_boundaries)} words\n")

    # Step 2: Generate subtitles
    print("🔤 Step 2/3: Generating animated subtitles...")

    # Try Edge TTS word boundaries first
    words = words_from_edge_tts(words_json_path)
    if not words:
        # Use hybrid approach: Whisper timestamps + original script text
        # This ensures subtitles show in correct script (Hindi not Urdu)
        print("   Using smart hybrid approach (Whisper timing + original script text)...")
        lang_code = "hi" if language == "hindi" else "en"
        words = words_from_script_with_timestamps(
            script_data["full_script"], audio_path, language=lang_code
        )

    if video_format == "shorts":
        sub_w, sub_h = SHORTS_WIDTH, SHORTS_HEIGHT
    else:
        sub_w, sub_h = VIDEO_WIDTH, VIDEO_HEIGHT

    ass_path = os.path.join(TEMP_DIR, f"{safe_title}_{timestamp}.ass")
    srt_path = os.path.join(OUTPUT_DIR, f"{safe_title}_{timestamp}.srt")

    if words:
        generate_ass_subtitles(words, ass_path, video_width=sub_w, video_height=sub_h)
        generate_srt_subtitles(words, srt_path)
        print(f"   ✅ Subtitles generated ({len(words)} words)\n")
    else:
        print("   ⚠️  No words detected, video will be without subtitles\n")
        # Create empty subtitle file
        with open(ass_path, "w") as f:
            f.write("[Script Info]\nTitle: Empty\nScriptType: v4.00+\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")


    # Step 3: Create video
    print("🎬 Step 3/3: Creating final video...")
    output_filename = f"{safe_title}_{timestamp}.mp4"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    create_video_from_audio_and_subtitles(
        audio_path=audio_path,
        subtitle_path=ass_path,
        output_path=output_path,
        background_video=bg_video,
        background_image=bg_image,
        gradient_name=gradient_name,
        video_format=video_format,
    )

    # Done!
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"\n\033[92m{'='*60}\033[0m")
        print(f"\033[92m🎉 VIDEO GENERATED SUCCESSFULLY!\033[0m")
        print(f"\033[92m{'='*60}\033[0m")
        print(f"\n📁 Video: {output_path}")
        print(f"📏 Size: {file_size:.1f} MB")
        print(f"⏱️  Duration: {duration:.1f} seconds")
        print(f"📝 SRT (for CapCut): {srt_path}")
        print(f"\n\033[93m💡 TIP: Import the .srt file into CapCut for trendy subtitle effects!\033[0m")
    else:
        print(f"\n\033[91m❌ Video generation failed. Check the errors above.\033[0m")

    input("\n\033[96mPress Enter to continue...\033[0m")


def mode_auto_clipper():
    """Mode 2: Auto clip long video into Shorts"""
    print(f"\n\033[95m{'='*60}\033[0m")
    print(f"\033[93m✂️  AUTO CLIPPER - Long Video → Viral Shorts\033[0m")
    print(f"\033[95m{'='*60}\033[0m")

    video_path = input("\n📁 Video file path: ").strip().strip('"').strip("'")

    if not os.path.exists(video_path):
        print(f"\033[91m❌ File not found: {video_path}\033[0m")
        input("\nPress Enter to continue...")
        return

    print("\n\033[96mOptions:\033[0m")
    add_subs = input("  🔤 Add subtitles? (y/n) [default: y]: ").strip().lower() != 'n'
    crop_vert = input("  📱 Crop to Shorts (9:16)? (y/n) [default: y]: ").strip().lower() != 'n'

    min_dur = input(f"  ⏱️  Min clip duration (seconds) [default: {MIN_CLIP_DURATION}]: ").strip()
    max_dur = input(f"  ⏱️  Max clip duration (seconds) [default: {MAX_CLIP_DURATION}]: ").strip()

    try:
        min_dur = int(min_dur) if min_dur else None
    except ValueError:
        min_dur = None
    try:
        max_dur = int(max_dur) if max_dur else None
    except ValueError:
        max_dur = None

    print(f"\n\033[92m🚀 Starting Auto Clipper...\033[0m\n")
    clips = auto_clip_video(
        video_path,
        add_subs=add_subs,
        crop_vertical=crop_vert,
        min_duration=min_dur,
        max_duration=max_dur,
    )

    if clips:
        print(f"\n\033[93m💡 TIP: Import these clips + .srt files into CapCut for final polish!\033[0m")

    input("\n\033[96mPress Enter to continue...\033[0m")


def mode_add_subtitles():
    """Mode 3: Add subtitles to existing video"""
    print(f"\n\033[95m{'='*60}\033[0m")
    print(f"\033[93m🔤 ADD SUBTITLES TO VIDEO\033[0m")
    print(f"\033[95m{'='*60}\033[0m")

    video_path = input("\n📁 Video file path: ").strip().strip('"').strip("'")
    if not os.path.exists(video_path):
        print(f"\033[91m❌ File not found: {video_path}\033[0m")
        input("\nPress Enter to continue...")
        return

    print("\n🔄 Extracting audio and transcribing...")
    os.makedirs(TEMP_DIR, exist_ok=True)

    # Extract audio
    temp_audio = os.path.join(TEMP_DIR, "sub_audio.wav")
    os.system(f'ffmpeg -y -i "{video_path}" -vn -acodec pcm_s16le -ar 16000 -ac 1 "{temp_audio}" 2>/dev/null')

    # Transcribe
    words = transcribe_audio(temp_audio)

    if not words:
        print("\033[91m❌ No speech detected in video.\033[0m")
        input("\nPress Enter to continue...")
        return

    # Get video dimensions
    probe_cmd = f'ffprobe -v quiet -print_format json -show_streams "{video_path}"'
    import subprocess
    result = subprocess.run(probe_cmd, shell=True, capture_output=True, text=True)
    streams = json.loads(result.stdout)
    vid_w, vid_h = 1920, 1080
    for s in streams.get("streams", []):
        if s.get("codec_type") == "video":
            vid_w = int(s.get("width", 1920))
            vid_h = int(s.get("height", 1080))
            break

    # Generate subtitles
    timestamp = int(time.time())
    ass_path = os.path.join(TEMP_DIR, f"subs_{timestamp}.ass")
    generate_ass_subtitles(words, ass_path, video_width=vid_w, video_height=vid_h)

    # Also generate SRT
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    srt_path = os.path.join(OUTPUT_DIR, f"{video_name}_subtitles.srt")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    generate_srt_subtitles(words, srt_path)

    # Burn subtitles
    output_path = os.path.join(OUTPUT_DIR, f"{video_name}_with_subs.mp4")
    add_subtitles_to_video(video_path, ass_path, output_path)

    if os.path.exists(output_path):
        print(f"\n\033[92m✅ Video with subtitles: {output_path}\033[0m")
        print(f"📝 SRT file (for CapCut): {srt_path}")

    input("\n\033[96mPress Enter to continue...\033[0m")


def mode_voiceover():
    """Mode 4: Generate voiceover only"""
    print(f"\n\033[95m{'='*60}\033[0m")
    print(f"\033[93m🎤 AI VOICEOVER GENERATOR\033[0m")
    print(f"\033[95m{'='*60}\033[0m")

    print("\n\033[96mVoice:\033[0m")
    voice_keys = list(VOICES.keys())
    for i, vk in enumerate(voice_keys, 1):
        print(f"  [{i}] {vk} ({VOICES[vk]})")

    voice_choice = input(f"\n👉 Choose voice (1-{len(voice_keys)}): ").strip()
    try:
        v_idx = int(voice_choice) - 1
        voice_key = voice_keys[v_idx] if 0 <= v_idx < len(voice_keys) else "hindi_male"
    except (ValueError, IndexError):
        voice_key = "hindi_male"

    print(f"\n✏️  Text likhiye (Enter 2 baar dabao finish karne ke liye):")
    lines = []
    empty_count = 0
    while True:
        line = input()
        if line == "":
            empty_count += 1
            if empty_count >= 2:
                break
            lines.append("")
        else:
            empty_count = 0
            lines.append(line)
    text = "\n".join(lines).strip()

    if not text:
        print("\033[91m❌ No text provided.\033[0m")
        input("\nPress Enter to continue...")
        return

    rate = input("\n⚡ Speed (e.g., +10%, -20%, or Enter for normal): ").strip()
    if not rate:
        rate = "+0%"

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = int(time.time())
    output_path = os.path.join(OUTPUT_DIR, f"voiceover_{timestamp}.mp3")

    print(f"\n🔊 Generating voiceover...")
    audio_path, words_path, words = generate_voiceover(text, output_path, voice_key, rate)
    duration = get_audio_duration(audio_path)

    print(f"\n\033[92m✅ Voiceover generated!\033[0m")
    print(f"📁 Audio: {audio_path}")
    print(f"⏱️  Duration: {duration:.1f} seconds")
    print(f"📝 Word timestamps: {words_path}")

    input("\n\033[96mPress Enter to continue...\033[0m")


def mode_browse_scripts():
    """Mode 5: Browse and view viral scripts"""
    print(f"\n\033[95m{'='*60}\033[0m")
    print(f"\033[93m📝 VIRAL SCRIPTS LIBRARY\033[0m")
    print(f"\033[95m{'='*60}\033[0m")

    print("\n\033[96mLanguage:\033[0m")
    print("  [1] Hindi")
    print("  [2] English")
    lang_choice = input("\n👉 Choose (1/2): ").strip()
    language = "english" if lang_choice == "2" else "hindi"

    scripts_db = READY_SCRIPTS_HINDI if language == "hindi" else READY_SCRIPTS_ENGLISH

    for niche, scripts in scripts_db.items():
        emoji_map = {"motivation": "💪", "facts": "🧠", "horror": "👻", "tech": "💻", "money": "💰"}
        emoji = emoji_map.get(niche, "📌")
        print(f"\n\033[93m{'─'*60}\033[0m")
        print(f"\033[93m{emoji} {niche.upper()}\033[0m")
        print(f"\033[93m{'─'*60}\033[0m")

        for i, s in enumerate(scripts, 1):
            print(f"\n  \033[96m[{i}] {s['title']}\033[0m")
            print(f"      🎣 {s['hook'][:80]}...")
            word_count = len(s['body'].split())
            approx_duration = word_count / 2.5  # rough estimate
            print(f"      📊 ~{word_count} words | ~{approx_duration:.0f}s video")

    print(f"\n\033[93m{'─'*60}\033[0m")
    print(f"\n💡 Use option [1] from main menu to create a video from any script!")

    input("\n\033[96mPress Enter to continue...\033[0m")


def mode_settings():
    """Mode 6: Settings"""
    print(f"\n\033[95m{'='*60}\033[0m")
    print(f"\033[93m⚙️  CURRENT SETTINGS\033[0m")
    print(f"\033[95m{'='*60}\033[0m")

    print(f"\n\033[96m📁 Paths:\033[0m")
    print(f"   Output: {OUTPUT_DIR}")
    print(f"   Temp:   {TEMP_DIR}")

    print(f"\n\033[96m📱 Video (Shorts):\033[0m {SHORTS_WIDTH}x{SHORTS_HEIGHT}")
    print(f"\033[96m🖥️  Video (Normal):\033[0m {VIDEO_WIDTH}x{VIDEO_HEIGHT}")
    print(f"\033[96m🎞️  FPS:\033[0m {FPS}")

    print(f"\n\033[96m🎤 Available Voices:\033[0m")
    print(list_available_voices())

    print(f"\n\033[96m🎨 Available Gradients:\033[0m")
    for gk in GRADIENTS:
        print(f"   {gk}: {' → '.join(GRADIENTS[gk])}")

    print(f"\n\033[93m💡 Edit config.py to change settings!\033[0m")

    input("\n\033[96mPress Enter to continue...\033[0m")

def mode_batch_generate():
    """Mode 7: Batch Generation"""
    print(f"\n\033[95m{'='*60}\033[0m")
    print(f"\033[93m🚀 BATCH VIDEO GENERATOR\033[0m")
    print(f"\033[95m{'='*60}\033[0m")
    
    print("\n\033[96mLanguage:\033[0m")
    print("  [1] Hindi")
    print("  [2] English")
    lang_choice = input("\n👉 Choose (1/2): ").strip()
    language = "english" if lang_choice == "2" else "hindi"
    
    print("\n\033[96mNiche:\033[0m")
    niche_map = {"1": "reddit_revenge", "2": "reddit_aita", "3": "reddit_drama"}
    for k, v in niche_map.items():
        print(f"  [{k}] {v.replace('_', ' ').title()}")
    n_idx = input("\n👉 Choose niche (1-3): ").strip()
    niche = niche_map.get(n_idx, "reddit_revenge")
    
    try:
        count = int(input("\n👉 How many videos to generate? (e.g. 3): ").strip())
    except ValueError:
        count = 1
        
    print("\n\033[96mUpload to YouTube?\033[0m")
    upload_choice = input("👉 Auto-upload after generation? (y/N): ").strip().lower()
    upload_to_youtube = upload_choice == 'y'
        
    voice_key = "hindi_male" if language == "hindi" else "english_male"
    gradient = "neon_dark"
    
    batch_generate(niche, language, count, voice_key, gradient, upload_to_youtube=upload_to_youtube)
    
    input("\n\033[96mPress Enter to continue...\033[0m")


def mode_seo_generator():
    """Mode 8: SEO Generator"""
    print(f"\n\033[95m{'='*60}\033[0m")
    print(f"\033[93m📊 YOUTUBE SEO GENERATOR\033[0m")
    print(f"\033[95m{'='*60}\033[0m")
    
    title = input("\n👉 Enter video topic/title: ").strip()
    if not title:
        return
        
    print("\n\033[96mLanguage:\033[0m")
    print("  [1] Hindi")
    print("  [2] English")
    lang_choice = input("\n👉 Choose (1/2): ").strip()
    language = "english" if lang_choice == "2" else "hindi"
    
    print("\n\033[96mNiche:\033[0m")
    niche_map = {"1": "reddit_revenge", "2": "reddit_aita", "3": "reddit_drama"}
    for k, v in niche_map.items():
        print(f"  [{k}] {v.replace('_', ' ').title()}")
    n_idx = input("\n👉 Choose niche (1-3): ").strip()
    niche = niche_map.get(n_idx, "reddit_revenge")
    
    meta = generate_metadata(title, niche, language)
    
    print("\n\033[92m=== OPTIMIZED TITLE ===\033[0m")
    print(meta['title'])
    
    print("\n\033[92m=== DESCRIPTION ===\033[0m")
    print(meta['description'])
    
    print("\n\033[92m=== TAGS (Comma separated) ===\033[0m")
    print(", ".join(meta['tags']))
    
    input("\n\033[96mPress Enter to continue...\033[0m")


def main():
    """Main entry point"""
    while True:
        clear_screen()
        print_banner()
        print_menu()

        choice = input("\033[93m👉 Choose option (0-8): \033[0m").strip()

        if choice == "1":
            mode_script_to_video()
        elif choice == "2":
            mode_auto_clipper()
        elif choice == "3":
            mode_add_subtitles()
        elif choice == "4":
            mode_voiceover()
        elif choice == "5":
            mode_browse_scripts()
        elif choice == "6":
            mode_settings()
        elif choice == "7":
            mode_batch_generate()
        elif choice == "8":
            mode_seo_generator()
        elif choice == "0":
            print("\n\033[92m👋 Bye! YouTube par dhamaal machao!\033[0m\n")
            break
        else:
            print("\033[91m❌ Invalid choice. Try again.\033[0m")
            time.sleep(1)


if __name__ == "__main__":
    main()
