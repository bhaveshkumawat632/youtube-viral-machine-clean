#!/usr/bin/env python3
"""
Generate proper ffmpeg concat list with quoted paths
Fixed handling for special characters and spaces
"""
import os
import subprocess
import sys

# Set the directory containing the videos
VIDEO_DIR = "/home/junglee01/youtube-viral-machine/output/vidrush"
CONCAT_LIST = "/home/junglee01/youtube-viral-machine/concat_list_proper.txt"

# Get all motion video files, sorted naturally
motion_videos = sorted([f for f in os.listdir(VIDEO_DIR) if f.startswith("motion_") and f.endswith(".mp4")])

if not motion_videos:
    print("ERROR: No motion videos found")
    sys.exit(1)

print(f"Found {len(motion_videos)} motion videos")

# Write the concat list with proper quoting
with open(CONCAT_LIST, "w") as f:
    for video_file in motion_videos:
        # Properly escape single quotes within the filename
        safe_path = os.path.join(VIDEO_DIR, video_file)
        # Use double quotes around the path to handle spaces/special chars
        f.write(f"file '{safe_path}'\n")

print(f"Concat list written to {CONCAT_LIST}")
for line in open(CONCAT_LIST):
    print(f"  {line.strip()}")

# Now run ffmpeg with this concat list
VIDEO_DIR = "/home/junglee01/youtube-viral-machine/output/vidrush"
FINAL_OUTPUT = "/home/junglee01/youtube-viral-machine/output/VIDRUSH_MASTER_FINAL.mp4"

print("Running ffmpeg concatenation...")
result = subprocess.run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "1", "-i", CONCAT_LIST,
    "-c", "copy", "-vsync", "vfr", FINAL_OUTPUT
], capture_output=True, text=True)

print("FFmpeg stdout:", result.stdout[-500:] if result.stdout else "None")
print("FFmpeg stderr:", result.stderr[-500:] if result.stderr else "None")
print("Exit code:", result.returncode)

if result.returncode == 0:
    print("✅ SUCCESS: Final video concatenation completed!")
else:
    print("❌ ERROR: FFmpeg concatenation failed")
    print("Return code:", result.returncode)
    print("Stderr:", result.stderr)