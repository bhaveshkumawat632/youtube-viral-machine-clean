"""
Pytest unit and integration test suite for VidRush Studio Backend Architecture Upgrade.
Validates Requirement R1 (Auto-Thumbnail Generator) and Requirement R3 (Multi-Platform Export Formatter).
"""
import os
import sys
import json
import pytest
import subprocess
from PIL import Image

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from modules.thumbnail_generator import render_thumbnail
from modules.export_formatter import (
    export_multiplatform,
    format_platform_metadata,
    PLATFORM_PROFILES,
)


# ============================================================
# R1: THUMBNAIL GENERATOR TESTS
# ============================================================

def test_thumbnail_generator_gradient(tmp_path):
    """Test 16:9 thumbnail generation with gradient background."""
    output_file = str(tmp_path / "thumb_gradient.jpg")
    result_path = render_thumbnail(
        title="HOW TO DOMINATE YOUTUBE IN 2026",
        output_path=output_file,
        mode="gradient",
        gradient_name="neon_dark",
        aspect_ratio="16:9",
        primary_color="#FFE100",
        outline_color="#000000",
        outline_width=8,
        add_box_bg=True
    )

    assert os.path.exists(result_path)
    assert os.path.getsize(result_path) > 0

    with Image.open(result_path) as img:
        assert img.format in ("JPEG", "PNG")
        assert img.size == (1280, 720)


def test_thumbnail_generator_vertical_aspect(tmp_path):
    """Test 9:16 vertical thumbnail generation (1080x1920)."""
    output_file = str(tmp_path / "thumb_9_16.jpg")
    result_path = render_thumbnail(
        title="VERTICAL SHORTS THUMBNAIL",
        output_path=output_file,
        aspect_ratio="9:16",
        gradient_name="fire"
    )

    assert os.path.exists(result_path)

    with Image.open(result_path) as img:
        assert img.size == (1080, 1920)


def test_thumbnail_generator_frame_extract(tmp_path):
    """Test thumbnail rendering with video frame extraction background."""
    sample_video = os.path.join(BASE_DIR, "test_color.mp4")
    assert os.path.exists(sample_video), "test_color.mp4 sample video required for frame extract test"

    output_file = str(tmp_path / "thumb_frame.jpg")
    result_path = render_thumbnail(
        title="FRAME EXTRACTION TEST",
        output_path=output_file,
        mode="frame_extract",
        bg_path=sample_video,
        aspect_ratio="16:9"
    )

    assert os.path.exists(result_path)

    with Image.open(result_path) as img:
        assert img.size == (1280, 720)


def test_thumbnail_generator_dynamic_font_scaling(tmp_path):
    """Test dynamic font scaling with an extremely long title."""
    long_title = (
        "THIS IS AN EXTREMELY LONG TITLE THAT MUST SCALE DOWN DRAMATICALLY "
        "TO FIT INSIDE THE CANVAS BOUNDS WITHOUT OVERFLOWING OR CAUSING ERRORS"
    )
    output_file = str(tmp_path / "thumb_long_title.jpg")

    result_path = render_thumbnail(
        title=long_title,
        output_path=output_file,
        aspect_ratio="16:9"
    )

    assert os.path.exists(result_path)

    with Image.open(result_path) as img:
        assert img.size == (1280, 720)


# ============================================================
# R3: MULTI-PLATFORM EXPORT FORMATTER TESTS
# ============================================================

def test_format_platform_metadata_youtube():
    """Test YouTube Shorts metadata schema generation."""
    base_meta = {
        "title": "Build AI Apps Fast",
        "description": "Learn to code AI apps in minutes.",
        "tags": ["ai", "coding", "viral"]
    }

    meta = format_platform_metadata("youtube_shorts", base_meta)

    assert meta["platform"] == "youtube_shorts"
    assert "#Shorts" in meta["title"]
    assert "privacy_status" in meta and meta["privacy_status"] == "public"
    assert meta["category_id"] == "24"
    assert meta["made_for_kids"] is False
    assert meta["self_declared_made_for_kids"] is False
    assert "safe_zone" in meta
    assert "encoding_profile" in meta


def test_format_platform_metadata_tiktok():
    """Test TikTok metadata schema generation."""
    base_meta = {
        "title": "TikTok Trend 2026",
        "tags": ["tiktok", "viral", "challenge"]
    }

    meta = format_platform_metadata("tiktok", base_meta)

    assert meta["platform"] == "tiktok"
    assert "caption" in meta
    assert meta["privacy_level"] == "PUBLIC_TO_EVERYONE"
    assert meta["allow_duet"] is True
    assert meta["allow_stitch"] is True
    assert meta["allow_comment"] is True
    assert meta["brand_organic_toggle"] is False
    assert "#fyp" in meta["hashtags"]


def test_format_platform_metadata_instagram():
    """Test Instagram Reels metadata schema generation."""
    base_meta = {
        "title": "Reel Magic",
        "tags": ["reels", "insta", "magic"]
    }

    meta = format_platform_metadata("instagram_reels", base_meta)

    assert meta["platform"] == "instagram_reels"
    assert "caption" in meta
    assert meta["cover_frame_offset"] == 1.0
    assert meta["share_to_feed"] is True
    assert meta["audio_name"] == "Reel Magic"


def test_export_multiplatform_end_to_end(tmp_path):
    """End-to-end multiplatform export test re-encoding video and checking file output structure."""
    sample_video = os.path.join(BASE_DIR, "test_color.mp4")
    assert os.path.exists(sample_video), "test_color.mp4 sample video required for export test"

    output_dir = str(tmp_path / "multiplatform_export")
    base_meta = {
        "title": "Test Multi-Platform Vid",
        "description": "Integration test for YouTube, TikTok, and Instagram export.",
        "tags": ["test", "multiplatform", "viral"]
    }

    platforms = ["youtube_shorts", "tiktok", "instagram_reels"]
    results = export_multiplatform(
        input_video_path=sample_video,
        base_metadata=base_meta,
        output_dir=output_dir,
        platforms=platforms
    )

    # 1. Verify all target platform results returned
    for p in platforms:
        assert p in results

        platform_dir = os.path.join(output_dir, p)
        assert os.path.isdir(platform_dir)

        # Check encoded video existence
        encoded_video = results[p]["video_path"]
        assert os.path.exists(encoded_video)
        assert os.path.getsize(encoded_video) > 0

        # Probe encoded video using ffprobe
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,codec_name",
            "-of", "json",
            encoded_video
        ]
        probe_res = subprocess.run(probe_cmd, capture_output=True, text=True)
        assert probe_res.returncode == 0
        probe_data = json.loads(probe_res.stdout)
        stream_info = probe_data["streams"][0]
        assert stream_info["codec_name"] == "h264"
        assert stream_info["width"] == 1080
        assert stream_info["height"] == 1920

        # Check metadata JSON files existence & validity
        metadata_file = results[p]["metadata_path"]
        std_metadata_file = results[p]["standard_metadata_path"]

        assert os.path.exists(metadata_file)
        assert os.path.exists(std_metadata_file)

        with open(metadata_file, "r", encoding="utf-8") as f:
            meta_json = json.load(f)
            assert meta_json["platform"] == p
            assert "safe_zone" in meta_json
            assert "encoding_profile" in meta_json
