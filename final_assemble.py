#!/usr/bin/env python3
"""
Final assembly script for VidRush (Paisa Bhai) videos.
Concatenates scene videos and audio to produce final YouTube-ready video.
"""

import os
import subprocess
import tempfile
import json

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
VIDRUSH_DIR = os.path.join(OUTPUT_DIR, 'vidrush')  # NEW: Look in vidrush subdirectory
ASSEMBLE_LOG = os.path.join(BASE_DIR, 'final_assemble.log')

print(f"BASE_DIR: {BASE_DIR}")
print(f"OUTPUT_DIR: {OUTPUT_DIR}")
print(f"VIDRUSH_DIR: {VIDRUSH_DIR}")

# Debug: List contents of vidrush directory
if os.path.exists(VIDRUSH_DIR):
    print("Contents of vidrush directory:")
    for item in sorted(os.listdir(VIDRUSH_DIR)):
        print(f"  {item}")
else:
    print("VIDRUSH_DIR does not exist!")

# Get all scene videos sorted by index
scene_videos = []
for f in os.listdir(VIDRUSH_DIR):
    if f.startswith('motion_') and f.endswith('.mp4'):
        # Extract scene and clip numbers
        import re
        match = re.match(r'motion_(\d)_(\d+)\.mp4', f)
        if match:
            scene = int(match.group(1))
            clip = int(match.group(2))
            scene_videos.append((scene, clip, f))

# Sort by scene then clip
scene_videos.sort(key=lambda x: (x[0], x[1]))
video_files = [f[2] for x, _, f in scene_videos]

# Also include scene video files (like scene_video_*) if any
for f in os.listdir(OUTPUT_DIR):  # Check main output dir too
    if f.startswith('scene_video_') and f.endswith('.mp4'):
        scene_videos.append((999, 999, f))
        video_files.append(f)

print(f"\nFound {len(video_files)} video files to merge:")
for vf in video_files[:10]:  # Show first 10
    print(f"  {vf}")

if not video_files:
    error_msg = 'ERROR: No video files found in vidrush directory or output\n'
    with open(ASSEMBLE_LOG, 'a') as f:
        f.write(error_msg)
    raise SystemExit(error_msg)

# Prepare concat list for ffmpeg
video_list_file = os.path.join(OUTPUT_DIR, 'video_list.txt')
with open(video_list_file, 'w') as f:
    for video in video_files:
        f.write(f'file \'{video}\'\n')

# Prepare audio tracks
audio_files = []
audio_list_file = os.path.join(OUTPUT_DIR, 'audio_list.txt')
with open(audio_list_file, 'w') as f:
    for f_name in os.listdir(OUTPUT_DIR):
        if f_name.startswith('audio_') and f_name.endswith('.mp3'):
            f.write(f'file \'{f_name}\'\n')
            audio_files.append(f_name)

print(f"\nFound {len(audio_files)} audio files:")
for af in audio_files[:10]:
    print(f"  {af}")

# Create drawtext filter for subtitles (empty for now)
subtitle_texts = []
for i in range(7):  # We have 7 scenes from log
    subtitle_texts.append(f'Scene {i+1}: Break tasks into chunks')

# Build final ffmpeg command
# 1. Concatenate videos
video_concat_cmd = [
    'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', video_list_file,
    '-c', 'copy', '-vsync', 'vfr', os.path.join(OUTPUT_DIR, 'VIDRUSH_MASTER_FINAL.mp4')
]

print(f"\nVideo concat command: {' '.join(video_concat_cmd)}")

# 2. If audio mixing needed, create concat audio
if audio_files:
    audio_concat_cmd = [
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', audio_list_file,
        '-c', 'copy', os.path.join(OUTPUT_DIR, 'master_audio_concat.mp3')
    ]
    subprocess.run(audio_concat_cmd, check=True)

    # 3. Add audio to video
    final_cmd = [
        'ffmpeg', '-y', '-i', os.path.join(OUTPUT_DIR, 'VIDRUSH_MASTER_FINAL.mp4'),
        '-i', os.path.join(OUTPUT_DIR, 'master_audio_concat.mp3'),
        '-c', 'copy', '-shortest', os.path.join(OUTPUT_DIR, 'VIDRUSH_PaisaBhai_Final.mp4')
    ]
else:
    # Just copy audio from original master
    final_cmd = [
        'ffmpeg', '-y', '-i', os.path.join(OUTPUT_DIR, 'VIDRUSH_MASTER.mp4'),
        '-c', 'copy', os.path.join(OUTPUT_DIR, 'VIDRUSH_PaisaBhai_Final.mp4')
    ]

print(f"\nFinal ffmpeg command: {' '.join(final_cmd)}")

# Execute final command
print('\nRunning final assembly...')
with open(ASSEMBLE_LOG, 'a') as log:
    try:
        subprocess.run(video_concat_cmd, check=True, stderr=subprocess.STDOUT, stdout=log)
        subprocess.run(final_cmd, check=True, stderr=subprocess.STDOUT, stdout=log)
        log.write('SUCCESS: Final video created at VIDRUSH_PaisaBhai_Final.mp4\n')
        print('✅ Final video built successfully!')
    except subprocess.CalledProcessError as e:
        error_msg = f'ERROR: FFmpeg failed with code {e.returncode}\n'
        with open(ASSEMBLE_LOG, 'a') as f:
            f.write(error_msg)
        raise SystemExit(f'FFmpeg failed: {e}')