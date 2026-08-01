#!/usr/bin/env python3
"""
CLI script for Multi-Platform Export Formatter (VidRush Studio Upgrade R3).
"""
import argparse
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.export_formatter import export_multiplatform, PLATFORM_PROFILES


def main():
    parser = argparse.ArgumentParser(description="Multi-Platform Export Formatter for YouTube Shorts, TikTok & Instagram Reels")
    parser.add_argument("--input-video", type=str, required=True, help="Input video file path")
    parser.add_argument("--output-dir", type=str, required=True, help="Output export root directory")
    parser.add_argument("--title", type=str, default="Viral Shorts Challenge 2026", help="Base title for metadata")
    parser.add_argument("--description", type=str, default="Watch how to dominate social media with AI tools in 2026.", help="Base description for metadata")
    parser.add_argument("--tags", type=str, default="viral,trending,2026,shorts", help="Comma-separated tags")
    parser.add_argument("--platforms", type=str, default=None, help="Comma-separated platform list (youtube_shorts,tiktok,instagram_reels)")

    args = parser.parse_args()

    platform_list = None
    if args.platforms:
        platform_list = [p.strip() for p in args.platforms.split(",") if p.strip()]

    tags_list = [t.strip() for t in args.tags.split(",") if t.strip()]

    base_metadata = {
        "title": args.title,
        "description": args.description,
        "tags": tags_list
    }

    results = export_multiplatform(
        input_video_path=args.input_video,
        base_metadata=base_metadata,
        output_dir=args.output_dir,
        platforms=platform_list
    )

    print("\n--- Multi-Platform Export Complete ---")
    for platform, details in results.items():
        print(f"Platform: {platform}")
        print(f"  Video: {details['video_path']}")
        print(f"  Metadata: {details['metadata_path']}")


if __name__ == "__main__":
    main()
