#!/bin/bash
# Final assembly script for VidRush (Paisa Bhai) videos
# Concatenates scene videos to produce final YouTube-ready video

OUTPUT_DIR="/home/junglee01/youtube-viral-machine/output"
VIDRUSH_DIR="$OUTPUT_DIR/vidrush"
ASSEMBLE_LOG="$OUTPUT_DIR/final_assemble.log"

echo "Starting final assembly at $(date)" > "$ASSEMBLE_LOG"

# Get all motion videos, sort them properly
cd "$VIDRUSH_DIR" || { echo "ERROR: Cannot access $VIDRUSH_DIR" >> "$ASSEMBLE_LOG"; exit 1; }

# Create sorted list of motion videos
printf "Creating video list...\n" >> "$ASSEMBLE_LOG"
ls *.mp4 | grep "^motion_" | sort -t_ -k1,1n -k2,2n > "$OUTPUT_DIR/video_list.txt"

# Verify we found videos
if [ ! -s "$OUTPUT_DIR/video_list.txt" ]; then
    echo "ERROR: No motion videos found in $VIDRUSH_DIR" >> "$ASSEMBLE_LOG"
    exit 1
fi

VIDEO_COUNT=$(wc -l < "$OUTPUT_DIR/video_list.txt")
echo "Found $VIDEO_COUNT motion videos for concatenation" >> "$ASSEMBLE_LOG"

# Create master video file by concatenating all scene videos
echo "Concatenating videos..." >> "$ASSEMBLE_LOG"
ffmpeg -y -f concat -safe 0 -i "$OUTPUT_DIR/video_list.txt" -c copy -vsync vfr "$OUTPUT_DIR/VIDRUSH_MASTER_FINAL.mp4" 2>>"$ASSEMBLE_LOG"

if [ $? -ne 0 ]; then
    echo "ERROR: FFmpeg video concat failed" >> "$ASSEMBLE_LOG"
    exit 1
fi

# Also include master audio if it exists
if [ -f "$VIDRUSH_DIR/master_audio.mp3" ]; then
    echo "Adding master audio to video..." >> "$ASSEMBLE_LOG"
    ffmpeg -y -i "$OUTPUT_DIR/VIDRUSH_MASTER_FINAL.mp4" -i "$VIDRUSH_DIR/master_audio.mp3" -c copy -shortest "$OUTPUT_DIR/VIDRUSH_PaisaBhai_Final.mp4"
else
    echo "Master audio not found, copying VIDRUSH_MASTER_FINAL.mp4 to final file..." >> "$ASSEMBLE_LOG"
    cp "$OUTPUT_DIR/VIDRUSH_MASTER_FINAL.mp4" "$OUTPUT_DIR/VIDRUSH_PaisaBhai_Final.mp4"
fi

if [ $? -eq 0 ]; then
    echo "SUCCESS: Final video created at $OUTPUT_DIR/VIDRUSH_PaisaBhai_Final.mp4" >> "$ASSEMBLE_LOG"
    echo "✅ Final video built successfully!"
else
    echo "ERROR: FFmpeg audio-merge failed" >> "$ASSEMBLE_LOG"
    exit 1
fi