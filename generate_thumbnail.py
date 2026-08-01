#!/usr/bin/env python3
"""
CLI script for Auto-Thumbnail Generator (VidRush Studio Upgrade R1).
"""
import argparse
import sys
import os

# Ensure modules directory can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.thumbnail_generator import render_thumbnail


def main():
    parser = argparse.ArgumentParser(description="Auto-Thumbnail Generator for YouTube Shorts & Videos")
    parser.add_argument("--title", type=str, default="HOW TO DOMINATE YOUTUBE IN 2026", help="Thumbnail text title")
    parser.add_argument("--output", type=str, default="output/test_thumbnail.jpg", help="Output image file path")
    parser.add_argument("--mode", type=str, default="gradient", choices=["gradient", "image", "frame_extract"], help="Background rendering mode")
    parser.add_argument("--gradient", type=str, default="neon_dark", help="3-stop gradient preset name")
    parser.add_argument("--aspect-ratio", type=str, default="16:9", help="Canvas aspect ratio ('16:9' or '9:16')")
    parser.add_argument("--bg-path", type=str, default=None, help="Background image or video file path")
    parser.add_argument("--primary-color", type=str, default="#FFE100", help="Primary text color hex")
    parser.add_argument("--outline-color", type=str, default="#000000", help="Text stroke outline color hex")
    parser.add_argument("--outline-width", type=int, default=8, help="Text stroke width in pixels")
    parser.add_argument("--font-path", type=str, default=None, help="Custom TrueType font path")
    parser.add_argument("--no-box-bg", action="store_false", dest="add_box_bg", help="Disable semi-transparent pill box background")

    args = parser.parse_args()

    out_path = render_thumbnail(
        title=args.title,
        output_path=args.output,
        mode=args.mode,
        bg_path=args.bg_path,
        gradient_name=args.gradient,
        aspect_ratio=args.aspect_ratio,
        primary_color=args.primary_color,
        outline_color=args.outline_color,
        outline_width=args.outline_width,
        add_box_bg=args.add_box_bg,
        font_path=args.font_path
    )
    print(f"Thumbnail created successfully: {out_path}")


if __name__ == "__main__":
    main()
