"""
YouTube Viral Machine - Auto Clipper
Automatically splits long videos into viral YouTube Shorts with subtitles
"""
import os
import sys
import subprocess
import json
import math
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    MIN_CLIP_DURATION, MAX_CLIP_DURATION,
    SILENCE_THRESHOLD, SILENCE_MIN_DURATION,
    SHORTS_WIDTH, SHORTS_HEIGHT,
    OUTPUT_DIR, TEMP_DIR, FPS
)
from modules.subtitle_generator import transcribe_audio, generate_ass_subtitles, generate_srt_subtitles
from modules.video_maker import crop_to_shorts, add_subtitles_to_video, _get_duration


def detect_silence_points(audio_or_video_path):
    """
    Detect silence points in audio/video to find natural break points.

    Returns:
        list of dicts: [{"start": 10.5, "end": 11.2}, ...]
    """
    cmd = [
        "ffmpeg", "-i", audio_or_video_path,
        "-af", f"silencedetect=noise={SILENCE_THRESHOLD}dB:d={SILENCE_MIN_DURATION}",
        "-f", "null", "-"
    ]

    print(f"🔍 Detecting silence points...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    silences = []
    silence_start = None

    for line in result.stderr.split('\n'):
        if 'silence_start:' in line:
            match = re.search(r'silence_start:\s*([\d.]+)', line)
            if match:
                silence_start = float(match.group(1))
        elif 'silence_end:' in line and silence_start is not None:
            match = re.search(r'silence_end:\s*([\d.]+)', line)
            if match:
                silence_end = float(match.group(1))
                silences.append({
                    "start": silence_start,
                    "end": silence_end,
                    "mid": (silence_start + silence_end) / 2,
                })
                silence_start = None

    print(f"✅ Found {len(silences)} silence points")
    return silences


def find_best_clip_points(total_duration, silences, min_dur=None, max_dur=None):
    """
    Find the best points to cut the video into clips.
    Uses silence points as natural break points.
    """
    min_d = min_dur or MIN_CLIP_DURATION
    max_d = max_dur or MAX_CLIP_DURATION

    clips = []
    current_start = 0.0

    # Sort silence points by time
    sorted_silences = sorted(silences, key=lambda x: x["mid"])

    while current_start < total_duration - min_d:
        best_end = None

        # Find a silence point that gives us a clip in the right duration range
        for silence in sorted_silences:
            clip_duration = silence["mid"] - current_start

            if min_d <= clip_duration <= max_d:
                best_end = silence["mid"]
                # Prefer clips closer to max duration for more content
                # But break if we find a good one

            elif clip_duration > max_d:
                # Past max duration, use previous best or force cut
                if best_end is None:
                    best_end = current_start + max_d
                break

        if best_end is None:
            # No good silence point found, check remaining duration
            remaining = total_duration - current_start
            if remaining >= min_d:
                best_end = min(current_start + max_d, total_duration)
            else:
                break

        clips.append({
            "start": round(current_start, 2),
            "end": round(best_end, 2),
            "duration": round(best_end - current_start, 2),
        })

        current_start = best_end

    print(f"✅ Generated {len(clips)} clip segments")
    return clips


def extract_clip(video_path, start, end, output_path, crop_to_vertical=True):
    """Extract a clip from a video and optionally crop to 9:16"""
    duration = end - start

    if crop_to_vertical:
        # Crop to vertical (Shorts format)
        vf = f"crop=ih*9/16:ih,scale={SHORTS_WIDTH}:{SHORTS_HEIGHT}"
    else:
        vf = f"scale=-2:720"  # Just scale down

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", video_path,
        "-t", str(duration),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def auto_clip_video(video_path, output_dir=None, add_subs=True, crop_vertical=True,
                    min_duration=None, max_duration=None):
    """
    Main auto-clipper function.
    Takes a long video and automatically creates viral Shorts from it.

    Args:
        video_path: Path to input video
        output_dir: Output directory for clips
        add_subs: Add auto-generated subtitles
        crop_vertical: Crop to 9:16 for Shorts
        min_duration: Minimum clip duration
        max_duration: Maximum clip duration

    Returns:
        list: Paths to generated clips
    """
    if not os.path.exists(video_path):
        print(f"❌ Video not found: {video_path}")
        return []

    out_dir = output_dir or os.path.join(OUTPUT_DIR, "auto_clips")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    # Get video info
    total_duration = _get_duration(video_path)
    video_name = os.path.splitext(os.path.basename(video_path))[0]

    print(f"\n{'='*60}")
    print(f"🎬 AUTO CLIPPER - YouTube Viral Machine")
    print(f"{'='*60}")
    print(f"📁 Input: {video_path}")
    print(f"⏱️  Duration: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)")
    print(f"✂️  Clip range: {min_duration or MIN_CLIP_DURATION}s - {max_duration or MAX_CLIP_DURATION}s")
    print(f"{'='*60}\n")

    # Step 1: Extract audio for analysis
    print("📥 Step 1: Extracting audio...")
    temp_audio = os.path.join(TEMP_DIR, "clipper_audio.wav")
    extract_audio_cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        temp_audio
    ]
    subprocess.run(extract_audio_cmd, capture_output=True, text=True)

    # Step 2: Detect silence points
    print("\n🔇 Step 2: Detecting natural break points...")
    silences = detect_silence_points(video_path)

    # Step 3: Find best clip segments
    print("\n✂️  Step 3: Finding best clip segments...")
    clips = find_best_clip_points(
        total_duration, silences,
        min_dur=min_duration, max_dur=max_duration
    )

    if not clips:
        print("⚠️  No suitable clips found. Splitting evenly...")
        clip_dur = max_duration or MAX_CLIP_DURATION
        num_clips = math.ceil(total_duration / clip_dur)
        clips = []
        for i in range(num_clips):
            start = i * clip_dur
            end = min((i + 1) * clip_dur, total_duration)
            if end - start >= (min_duration or MIN_CLIP_DURATION):
                clips.append({"start": start, "end": end, "duration": end - start})

    # Step 4: Transcribe audio (for subtitles)
    words = []
    if add_subs:
        print("\n🎧 Step 4: Transcribing audio for subtitles...")
        words = transcribe_audio(temp_audio)

    # Step 5: Extract clips
    print(f"\n🎬 Step 5: Extracting {len(clips)} clips...")
    output_paths = []

    for i, clip in enumerate(clips):
        clip_num = i + 1
        print(f"\n--- Clip {clip_num}/{len(clips)} [{clip['start']:.1f}s - {clip['end']:.1f}s] ({clip['duration']:.1f}s) ---")

        clip_filename = f"{video_name}_short_{clip_num:03d}.mp4"
        clip_path = os.path.join(out_dir, clip_filename)

        # Extract clip
        if add_subs and words:
            # First extract without subtitles
            temp_clip = os.path.join(TEMP_DIR, f"temp_clip_{clip_num}.mp4")
            success = extract_clip(video_path, clip['start'], clip['end'], temp_clip, crop_vertical)

            if success:
                # Filter words for this clip segment
                clip_words = [
                    {
                        "text": w["text"],
                        "start": w["start"] - clip["start"],
                        "end": w["end"] - clip["start"],
                    }
                    for w in words
                    if clip["start"] <= w["start"] < clip["end"]
                ]

                if clip_words:
                    # Adjust negative timestamps
                    clip_words = [w for w in clip_words if w["start"] >= 0]

                    # Generate subtitles
                    sub_width = SHORTS_WIDTH if crop_vertical else 1280
                    sub_height = SHORTS_HEIGHT if crop_vertical else 720
                    sub_path = os.path.join(TEMP_DIR, f"clip_{clip_num}_subs.ass")
                    generate_ass_subtitles(
                        clip_words, sub_path,
                        video_width=sub_width, video_height=sub_height
                    )

                    # Add subtitles to clip
                    add_subtitles_to_video(temp_clip, sub_path, clip_path)

                    # Also save SRT for CapCut
                    srt_path = os.path.join(out_dir, f"{video_name}_short_{clip_num:03d}.srt")
                    generate_srt_subtitles(clip_words, srt_path)
                else:
                    os.rename(temp_clip, clip_path)
            else:
                print(f"⚠️  Failed to extract clip {clip_num}")
                continue
        else:
            success = extract_clip(video_path, clip['start'], clip['end'], clip_path, crop_vertical)
            if not success:
                print(f"⚠️  Failed to extract clip {clip_num}")
                continue

        if os.path.exists(clip_path):
            size_mb = os.path.getsize(clip_path) / (1024 * 1024)
            print(f"✅ Clip {clip_num} saved: {clip_path} ({size_mb:.1f} MB)")
            output_paths.append(clip_path)

    # Summary
    print(f"\n{'='*60}")
    print(f"🎉 AUTO CLIPPER COMPLETE!")
    print(f"{'='*60}")
    print(f"📊 Total clips generated: {len(output_paths)}")
    print(f"📁 Output directory: {out_dir}")
    for p in output_paths:
        print(f"   ✅ {os.path.basename(p)}")
    print(f"{'='*60}")

    return output_paths


if __name__ == "__main__":
    print("✂️  YouTube Viral Machine - Auto Clipper")
    print("=" * 50)
    print("Usage: python auto_clipper.py <video_path>")
    print("This module is used by main.py")

    if len(sys.argv) > 1:
        video = sys.argv[1]
        auto_clip_video(video)
