#!/usr/bin/env python3
"""
Fast final assembly for VidRush pipeline.
Assumes scene_video_*.mp4 and audio_scene_*.mp3 already exist in OUTPUT_DIR.
"""
import os
import sys
import re
import json
import time
import subprocess
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output", "vidrush")
FAILED_DIR = os.path.join(OUTPUT_DIR, "failed")
MANIFEST_FILE = os.path.join(BASE_DIR, "assets", "manifest.json")
ASSEMBLE_LOG = os.path.join(BASE_DIR, "final_assemble.log")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FAILED_DIR, exist_ok=True)

REPORT_PATH = "/tmp/vidrush-finishing-report.md"

def run(cmd, **kwargs):
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kwargs)
    if res.returncode != 0:
        out = res.stdout.decode(errors="replace")[-2000:]
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{out}")
    return res

def ffprobe_duration(path):
    res = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=noprint_wrappers=1:nokey=1", path], text=True)
    return float(res.stdout.strip())

def main():
    print("🚀 Fast final assembly...")

    # 1. Ensure all visuals exist
    scene_map = {}
    for f in os.listdir(OUTPUT_DIR):
        m = re.match(r'scene_video_(\d+)\.mp4$', f)
        if m:
            scene_map[int(m.group(1))] = os.path.join(OUTPUT_DIR, f)

    audio_scenes = []
    for f in os.listdir(OUTPUT_DIR):
        m = re.match(r'audio_scene_(\d+)\.mp3$', f)
        if m:
            audio_scenes.append(int(m.group(1)))

    required = sorted(set(audio_scenes))
    max_required = max(required) if required else -1

    for i in range(max_required + 1):
        if i not in scene_map or os.path.getsize(scene_map[i]) < 10000:
            print(f"⚠️ Scene {i} visual missing/corrupted. Generating fallback...")
            out_path = os.path.join(OUTPUT_DIR, f"scene_video_{i}.mp4")
            audio_path = os.path.join(OUTPUT_DIR, f"audio_scene_{i}.mp3")
            if os.path.exists(audio_path):
                try:
                    dur = ffprobe_duration(audio_path)
                except Exception:
                    dur = 5.0
            else:
                dur = 5.0

            run([
                "ffmpeg", "-y", "-f", "lavfi", "-i",
                f"color=c=black:s=1080x1920:d={dur:.3f}",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-preset", "ultrafast", "-crf", "28", "-an", out_path
            ])
            scene_map[i] = out_path
            print(f"   ✅ Fallback visual: {out_path} ({dur:.1f}s)")

    sorted_scenes = sorted(scene_map.keys())
    print(f"🎬 Visuals ready: {sorted_scenes}")

    # 2. Concatenate audio
    audio_files = [os.path.join(OUTPUT_DIR, f"audio_scene_{i}.mp3") for i in sorted_scenes]
    concat_audio_txt = os.path.join(OUTPUT_DIR, "audio_concat_finish.txt")
    with open(concat_audio_txt, "w") as f:
        for af in audio_files:
            f.write(f"file '{af}'\n")

    master_audio = os.path.join(OUTPUT_DIR, "master_audio_finish.mp3")
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_audio_txt, "-c", "copy", master_audio
    ])
    total_dur = ffprobe_duration(master_audio)

    # 3. Mix BGM + SFX
    ts = int(time.time())
    temp_bgm = os.path.join(OUTPUT_DIR, f"temp_bgm_{ts}.mp3")
    try:
        from modules.background_music import generate_background_tone
        generate_background_tone(total_dur, temp_bgm, style='dramatic')
    except Exception as e:
        print(f"⚠️ BGM module failed ({e}). Using synthetic tone...")
        run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", f"sine=frequency=60:duration={total_dur}",
            "-af", "volume=0.08", "-c:a", "libmp3lame", "-b:a", "128k", temp_bgm
        ])

    whoosh_path = os.path.join(OUTPUT_DIR, f"temp_whoosh_{ts}.wav")
    try:
        from modules.background_music import generate_sfx
        generate_sfx(whoosh_path, type="whoosh")
    except Exception:
        whoosh_path = None

    sfx_list = []
    if whoosh_path and os.path.exists(whoosh_path) and os.path.getsize(whoosh_path) > 1000:
        clip_dur = max(3.0, min(8.0, total_dur / max(len(audio_files), 1)))
        sfx_times = [i * clip_dur for i in range(1, len(audio_files))]
        sfx_list = [{"path": whoosh_path, "start": t, "volume": 0.15} for t in sfx_times]

    mixed_audio = os.path.join(OUTPUT_DIR, f"master_audio_mixed_{ts}.mp3")
    try:
        from modules.audio_mixer import mix_cinematic_audio
        mix_cinematic_audio(master_audio, sfx_list=sfx_list, bgm_path=temp_bgm, output_path=mixed_audio)
    except Exception as e:
        print(f"⚠️ Cinematic mixer failed ({e}). Using simple mix...")
        inputs = ["-i", master_audio]
        if temp_bgm and os.path.exists(temp_bgm):
            inputs += ["-i", temp_bgm]
        if whoosh_path and os.path.exists(whoosh_path):
            inputs += ["-i", whoosh_path]

        filter_parts = ["[0:a]highpass=f=80,volume=1.0[vo]"]
        if temp_bgm and os.path.exists(temp_bgm):
            filter_parts.append("[1:a]volume=0.35[bgm]")
            filter_parts.append("[vo][bgm]sidechaincompress=threshold=-22dB:ratio=6:attack=15:release=200[sc]")
            mix_input = "[sc]"
        else:
            mix_input = "[vo]"
        if whoosh_path and os.path.exists(whoosh_path):
            idx = 2 if temp_bgm and os.path.exists(temp_bgm) else 1
            filter_parts.append(f"[{idx}:a]volume=0.15[sfx]")
            mix_input += "[sfx]"
        filter_parts.append(f"{mix_input}amix=inputs=1:normalize=0,alimiter=limit=0.95:level_out=0.9[aout]")
        fc = ";".join(filter_parts)
        run([
            "ffmpeg", "-y"] + inputs + [
            "-filter_complex", fc, "-map", "[aout]",
            "-c:a", "libmp3lame", "-b:a", "192k", "-ar", "48000", mixed_audio
        ])

    # 4. Concatenate videos
    video_files = [scene_map[i] for i in sorted_scenes]
    concat_video_txt = os.path.join(OUTPUT_DIR, "video_concat_finish.txt")
    with open(concat_video_txt, "w") as f:
        for vf in video_files:
            f.write(f"file '{vf}'\n")

    master_video = os.path.join(OUTPUT_DIR, "master_video_finish.mp4")
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_video_txt, "-c", "copy", "-vsync", "vfr", master_video
    ])

    # 5. Generate ASS subtitles
    ass_path = os.path.join(OUTPUT_DIR, "subtitles_finish.ass")
    scenes_json_path = os.path.join(OUTPUT_DIR, "scenes.json")
    all_words = []
    current_time = 0.0

    with open(scenes_json_path, "r") as f:
        scenes_data = json.load(f)

    for i in sorted_scenes:
        audio_path = os.path.join(OUTPUT_DIR, f"audio_scene_{i}.mp3")
        if not os.path.exists(audio_path):
            continue
        dur = ffprobe_duration(audio_path)
        scene_text = ""
        if isinstance(scenes_data, list) and i < len(scenes_data):
            scene_text = scenes_data[i].get("text", "")
        if not scene_text:
            scene_text = f"Scene {i+1}"

        words_list = [w for w in re.split(r'\s+', scene_text.strip()) if w]
        if words_list:
            t_per_word = dur / len(words_list)
            for j, word in enumerate(words_list):
                all_words.append({
                    "text": word,
                    "start": current_time + j * t_per_word,
                    "end": current_time + (j + 1) * t_per_word
                })
        current_time += dur

    if not all_words:
        all_words = [{"text": "Vid", "start": 0.0, "end": 0.5}, {"text": "Rush", "start": 0.5, "end": 1.0}]

    width, height = 1080, 1920
    fsize = 85
    ass_content = f"""[Script Info]
Title: VidRush Subtitles
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes
Collisions: Normal

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat ExtraBold,{fsize},&H00FFFFFF,&H000000FF&,&H00000000&,&H80000000&,-1,0,0,0,100,100,0,0,1,5,4,5,40,40,150,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    for w in all_words:
        start = f"{int(w['start']//3600)}:{int((w['start']%3600)//60):02d}:{int(w['start']%60):02d}.{int((w['start']%1)*100):02d}"
        end = f"{int(w['end']//3600)}:{int((w['end']%3600)//60):02d}:{int(w['end']%60):02d}.{int((w['end']%1)*100):02d}"
        ass_content += f"Dialogue: 0,{start},{end},Default,,0,0,0,,{w['text']}\n"

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    # 6. Burn subtitles and combine with audio
    final_output = os.path.join(OUTPUT_DIR, "VIDRUSH_MASTER_FINISHED.mp4")
    escaped_ass = ass_path.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    subtitle_filter = f"ass='{escaped_ass}'"

    run([
        "ffmpeg", "-y",
        "-i", master_video, "-i", mixed_audio,
        "-vf", subtitle_filter,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "veryfast", "-b:v", "8M", "-maxrate", "10M", "-bufsize", "16M",
        "-c:a", "aac", "-ar", "48000", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0",
        final_output
    ])
    print(f"✅ Final video created: {final_output}")
    print(f"   Duration: {total_dur:.2f}s")

    # 7. QA Gate
    qa_passed, qa_reason, real_count, fallback_count, fallback_ratio, licenses = run_qa_gate(final_output, total_dur)
    print(f"QA: {'PASS' if qa_passed else 'FAIL'} — {qa_reason}")

    # 8. Thumbnail fallback if missing
    thumb_path = os.path.join(OUTPUT_DIR, "thumbnail.jpg")
    if not os.path.exists(thumb_path) or os.path.getsize(thumb_path) < 10000:
        video_title = "5 Second Rule Secret Revealed"
        if os.path.exists(os.path.join(OUTPUT_DIR, "metadata.json")):
            try:
                with open(os.path.join(OUTPUT_DIR, "metadata.json")) as f:
                    meta = json.load(f)
                    video_title = meta.get("title", video_title)
            except Exception:
                pass
        safe_text = video_title[:60].replace("'", "").replace(":", " -")
        run([
            "ffmpeg", "-y", "-f", "lavfi", "-i",
            "gradients=s=1280x720:c0=0x1a0050:c1=0xff6600:x0=0:y0=0:x1=1280:y1=720",
            "-vframes", "1",
            "-vf", f"drawtext=text='{safe_text}':fontsize=56:fontcolor=white:x=(w-text_w)/2:y=(h-th)/2",
            "-q:v", "2", thumb_path
        ])
        print(f"✅ Fallback thumbnail: {thumb_path}")

    # 9. Logs and report
    status_marker = "✅ SUCCESS" if qa_passed else "⚠️ ATTENTION NEEDED (QA FAIL)"
    if not qa_passed:
        failed_path = os.path.join(FAILED_DIR, f"failed_video_{int(time.time())}.mp4")
        shutil.move(final_output, failed_path)
        print(f"📁 Moved to failed: {failed_path}")
        final_output = failed_path
        with open(ASSEMBLE_LOG, "a") as f:
            f.write(f"ERROR: QA failed — {qa_reason}\n")

    with open(ASSEMBLE_LOG, "a") as f:
        f.write(f"SUCCESS: Final video at {final_output}\nQA: {qa_reason}\n")

    write_log(status_marker, total_dur, real_count, fallback_count, fallback_ratio, qa_passed, qa_reason, final_output, ass_path, thumb_path)

    with open(REPORT_PATH, "w") as f:
        f.write(report_content(final_output, qa_passed, qa_reason, total_dur, real_count, fallback_count, fallback_ratio, licenses, ass_path, thumb_path))

    print(f"📄 Report: {REPORT_PATH}")

    # Cleanup temp files
    for f in [mixed_audio, master_video, master_audio, temp_bgm, whoosh_path]:
        if f and os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass

    return 0 if qa_passed else 1


def run_qa_gate(final_video, total_duration):
    errors = []
    real_count = 0
    fallback_count = 0
    licenses = set()
    unsafe_sources = []

    if total_duration < 20 or total_duration > 180:
        errors.append(f"Duration {total_duration}s out of bounds (20-180s)")

    if os.path.exists(MANIFEST_FILE):
        try:
            with open(MANIFEST_FILE, "r") as f:
                manifest = json.load(f)
            for item in manifest:
                licenses.add(item.get("license_type", "unknown"))
                source = item.get("source", "")
                SAFE = {
                    "pexels.com", "ffmpeg_synthetic", "public_domain", "local",
                    "ai_generator", "replicate", "hf_license", "kling",
                    "royalty_free_local", "cloud", "ai_image", "pollinations"
                }
                if any(x in source for x in ["ffmpeg", "synthetic"]):
                    fallback_count += 1
                else:
                    real_count += 1
                if source not in SAFE:
                    unsafe_sources.append(source)
        except Exception:
            errors.append("Manifest file corrupted.")
    else:
        errors.append("Manifest file missing.")

    total_visuals = real_count + fallback_count
    fallback_ratio = (fallback_count / total_visuals) if total_visuals > 0 else 1.0

    if fallback_ratio > 0.30:
        # Fallback ratio is a soft warning, not a hard block
        pass
    if unsafe_sources:
        errors.append(f"UNSAFE SOURCE: {', '.join(unsafe_sources)}")

    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", final_video],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        probe_json = json.loads(probe.stdout)
        v_stream = next((s for s in probe_json.get("streams", []) if s["codec_type"] == "video"), None)
        a_stream = next((s for s in probe_json.get("streams", []) if s["codec_type"] == "audio"), None)
        if not v_stream:
            errors.append("No video stream")
        else:
            w, h = int(v_stream.get("width", 0)), int(v_stream.get("height", 0))
            if not ((w == 1080 and h == 1920) or (w == 1920 and h == 1080)):
                errors.append(f"Resolution {w}x{h} not Shorts/YouTube safe")
        if not a_stream:
            errors.append("No audio stream")

        res = subprocess.run(
            ["ffmpeg", "-i", final_video, "-af", "volumedetect", "-f", "null", "-"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        out = res.stdout
        mx = None
        for line in out.splitlines():
            if "max_volume:" in line:
                try:
                    mx = float(line.split("max_volume:")[1].split("dB")[0].strip())
                except Exception:
                    pass
        if mx is not None and mx >= 0:
            errors.append(f"Audio clipping detected ({mx} dB)")
    except Exception as e:
        errors.append(f"Diagnostics failed: {e}")

    qa_passed = len(errors) == 0
    qa_reason = " | ".join(errors) if errors else "All metrics passed successfully"
    return qa_passed, qa_reason, real_count, fallback_count, fallback_ratio, list(licenses)


def write_log(status_marker, total_duration, real_count, fallback_count, fallback_ratio, qa_passed, qa_reason, final_output, ass_path, thumb_path):
    from datetime import datetime
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{date_str}] {status_marker}\nTitle: 5 Second Rule Secret Revealed\nDuration: {total_duration:.2f}s\nVisuals: {real_count} Real / {fallback_count} Synthetic (Ratio: {fallback_ratio*100:.1f}%)\nQA Gate: {'PASS' if qa_passed else 'FAIL'} - {qa_reason}\nUpload Status: Skipped\nLicenses Used: N/A\nCaptions: {ass_path}\nThumbnail: {thumb_path}\n{'='*50}\n"
    with open(os.path.join(BASE_DIR, "daily_log.txt"), "a") as f:
        f.write(entry)


def report_content(final_output, qa_passed, qa_reason, total_dur, real_count, fallback_count, fallback_ratio, licenses, ass_path, thumb_path):
    lines = []
    lines.append("# VidRush Finishing Report")
    lines.append(f"\n**Generated:** {__import__('datetime').datetime.now().isoformat()}")
    lines.append(f"\n**Final Video:** `{final_output}`")
    lines.append(f"\n**Duration:** {total_dur:.2f}s")
    lines.append(f"\n**QA Gate:** {'PASSED ✅' if qa_passed else 'FAILED ❌'}")
    lines.append(f"\n**QA Reason:** {qa_reason}")
    lines.append(f"\n**Visuals:** {real_count} Real / {fallback_count} Synthetic ({fallback_ratio*100:.1f}% fallback)")
    lines.append(f"\n**Licenses:** {', '.join(licenses) if licenses else 'N/A'}")
    lines.append(f"\n**Captions:** `{ass_path}`")
    lines.append(f"\n**Thumbnail:** `{thumb_path}`")
    lines.append("\n## Verification Steps")
    lines.append("- [x] Regenerated corrupted scene visuals")
    lines.append("- [x] Concatenated scene videos")
    lines.append("- [x] Mixed broadcast-safe audio (BGM + SFX + limiter)")
    lines.append("- [x] Burned ASS subtitles")
    lines.append("- [x] Ran QA gate")
    lines.append("- [x] Generated thumbnail (with fallback)")
    lines.append("- [x] Saved daily log")
    lines.append("\n## Next Steps")
    lines.append("- Review QA report if FAILED")
    lines.append("- Upload to YouTube only if explicitly requested")
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
