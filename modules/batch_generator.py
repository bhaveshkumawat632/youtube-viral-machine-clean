import os
import time
import json
from config import OUTPUT_DIR, TEMP_DIR, SHORTS_WIDTH, SHORTS_HEIGHT, BACKGROUNDS_DIR
from modules.script_generator import get_all_scripts
from modules.voiceover import generate_voiceover, get_audio_duration
from modules.subtitle_generator import words_from_edge_tts, words_from_script_with_timestamps, generate_ass_subtitles, generate_srt_subtitles
from modules.video_maker import create_video_from_audio_and_subtitles
from modules.seo_generator import generate_metadata

def batch_generate(niche, language, count, voice_key, gradient_name, upload_to_youtube=False):
    """
    Generate multiple videos in batch and optionally upload to YouTube.
    """
    print(f"\n🚀 Starting Batch Generation: {count} videos for '{niche}' in '{language}'")
    
    batch_dir = os.path.join(OUTPUT_DIR, f"batch_{int(time.time())}")
    os.makedirs(batch_dir, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    from modules.script_generator import READY_SCRIPTS_HINDI, READY_SCRIPTS_ENGLISH
    
    scripts_db = READY_SCRIPTS_HINDI if language == "hindi" else READY_SCRIPTS_ENGLISH
    raw_scripts = scripts_db.get(niche, [])
    
    if not raw_scripts:
        print(f"❌ No scripts found for {niche} in {language}")
        return
        
    # Limit to requested count
    scripts = []
    for s in raw_scripts[:count]:
        full_text = f"{s['hook']}\n\n{s['body']}\n\n{s['cta']}"
        word_count = len(full_text.split())
        
        # If script is too long for a single YouTube Short (approx > 120 words = ~60s)
        if word_count > 120:
            sentences = [line.strip() for line in full_text.split('.') if line.strip()]
            midpoint = len(sentences) // 2
            
            part1_text = ". ".join(sentences[:midpoint]) + ".\n\nLike and Subscribe for Part 2!"
            part2_text = "Part 2 of the story:\n\n" + ". ".join(sentences[midpoint:]) + ".\n\nSubscribe for more!"
            
            scripts.append({
                "title": f"{s['title']} (Part 1)",
                "full_script": part1_text
            })
            scripts.append({
                "title": f"{s['title']} (Part 2)",
                "full_script": part2_text
            })
        else:
            scripts.append({
                "title": s["title"],
                "full_script": full_text
            })
            
    actual_count = len(scripts)
    
    print(f"Found {actual_count} scripts (including multi-parts). Let's go!")
    
    metadata_list = []
    
    for i, script_data in enumerate(scripts):
        print(f"\n" + "="*50)
        print(f"🎬 Generating Video {i+1}/{actual_count}: {script_data['title']}")
        print("="*50)
        
        safe_title = "".join([c if c.isalnum() else "_" for c in script_data['title']]).strip("_")
        base_name = f"video_{i+1}_{safe_title}"
        
        # 1. Voiceover
        audio_path = os.path.join(TEMP_DIR, f"{base_name}_audio.mp3")
        audio_path, words_json_path, _ = generate_voiceover(
            script_data["full_script"], audio_path, voice_key
        )
        
        # 2. Subtitles
        words = words_from_edge_tts(words_json_path)
        if not words:
            lang_code = "hi" if language == "hindi" else "en"
            words = words_from_script_with_timestamps(
                script_data["full_script"], audio_path, language=lang_code
            )
            
        ass_path = os.path.join(TEMP_DIR, f"{base_name}.ass")
        srt_path = os.path.join(batch_dir, f"{base_name}.srt")
        if words:
            generate_ass_subtitles(words, ass_path, video_width=SHORTS_WIDTH, video_height=SHORTS_HEIGHT)
            generate_srt_subtitles(words, srt_path)
        else:
            with open(ass_path, "w") as f:
                f.write("[Script Info]\nTitle: Empty\nScriptType: v4.00+\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
                
        # 2.5 Background Music & Loop SFX (Secret Sauce for Virality)
        music_path = os.path.join(TEMP_DIR, f"{base_name}_music.m4a")
        sfx_path = os.path.join(TEMP_DIR, f"whoosh.m4a")
        
        style = "dramatic" if niche in ["horror", "psychology"] else "ambient"
        duration = get_audio_duration(audio_path)
        
        from modules.background_music import generate_background_tone, mix_audio, generate_sfx
        generate_background_tone(duration + 1, music_path, style)
        
        # SFX Selection: Try to pick random SFX from assets/sfx/ if it exists, else generate synthetic
        from config import ASSETS_DIR
        sfx_dir = os.path.join(ASSETS_DIR, "sfx")
        if os.path.exists(sfx_dir) and [f for f in os.listdir(sfx_dir) if f.endswith(('.mp3', '.wav', '.m4a'))]:
            import random
            sfx_files = [os.path.join(sfx_dir, f) for f in os.listdir(sfx_dir) if f.endswith(('.mp3', '.wav', '.m4a'))]
            sfx_path = random.choice(sfx_files)
            print(f"🪄 Using random SFX from library: {os.path.basename(sfx_path)}")
        else:
            sfx_path = os.path.join(TEMP_DIR, "synthetic_whoosh.m4a")
            generate_sfx(sfx_path, "whoosh")
            
        # Mix Audio
        mixed_audio_path = os.path.join(TEMP_DIR, f"{base_name}_mixed.mp3")
        end_time = words[-1]["end"] if words else 5.0
        
        import subprocess
        cmd = [
            "ffmpeg", "-y",
            "-i", audio_path,
            "-i", music_path,
            "-i", sfx_path,
            "-filter_complex", 
            f"[1:a]volume=0.2[bg];"
            f"[2:a]volume=0.8[sfx1];"
            f"[2:a]adelay={int(end_time*1000)}|{int(end_time*1000)},volume=0.8[sfx2];"
            f"[0:a][bg][sfx1][sfx2]amix=inputs=4:duration=first:dropout_transition=2[a]",
            "-map", "[a]",
            "-c:a", "libmp3lame", "-b:a", "192k",
            mixed_audio_path
        ]
        subprocess.run(cmd, capture_output=True)
        
        # 3. Video Background Selection
        output_path = os.path.join(batch_dir, f"{base_name}.mp4")
        
        # New Contextual Scene Generation Logic
        print("🖼️ Generating contextual scene images via AI...")
        import urllib.request
        import urllib.parse
        
        # Split script into lines/sentences
        script_lines = [line.strip() for line in script_data['full_script'].split('.') if line.strip()]
        if not script_lines:
            script_lines = [script_data['title']]
            
        # Distribute time among lines roughly
        line_duration = duration / len(script_lines)
        
        # Disable AI image generation - Use high action background videos instead
        contextual_bg = None

        if contextual_bg:
            print("🎬 Using Contextual AI Story Images...")
            create_video_from_audio_and_subtitles(
                mixed_audio_path, ass_path, output_path, 
                background_video=contextual_bg,
                video_format="shorts"
            )
        else:
            print("🎬 Using Code-Generated Audiogram Background...")
            create_video_from_audio_and_subtitles(
                mixed_audio_path, ass_path, output_path, 
                gradient_name=gradient_name, 
                video_format="shorts"
            )
        # 4. SEO & YouTube Upload
        meta = generate_metadata(script_data["title"], niche, language)
        meta["file"] = f"{base_name}.mp4"
        metadata_list.append(meta)
        
        print(f"✅ Video {i+1} rendered!")
        
        # 5. Optional Upload
        if upload_to_youtube:
            print("\n" + "-"*30)
            print("🚀 PUSHING TO YOUTUBE...")
            from modules.youtube_uploader import upload_video
            
            # Map niche to YouTube category (Education=27, Entertainment=24, Science/Tech=28, People/Blogs=22)
            cat_id = "22"
            if niche == "tech": cat_id = "28"
            elif niche == "facts" or niche == "psychology": cat_id = "27"
            elif niche == "horror" or niche == "money": cat_id = "24"
            
            upload_meta = {
                "title": meta["title"],
                "description": meta["description"],
                "tags": meta["tags"],
                "category_id": cat_id
            }
            upload_video(output_path, upload_meta)
            
    # Save metadata
    meta_path = os.path.join(batch_dir, "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata_list, f, indent=4, ensure_ascii=False)
        
    print(f"\n🎉 BATCH GENERATION COMPLETE!")
    print(f"📁 All {actual_count} videos saved to: {batch_dir}")
    print(f"📄 SEO Metadata saved to: {meta_path}")
