"""
Multi-Platform Export Formatter Module for VidRush Studio upgrade (R3).
Provides platform-specific video encoding parameters, safe zone pad margins,
and platform metadata generation for YouTube Shorts, TikTok, and Instagram Reels.
"""
import os
import sys
import json
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

PLATFORM_PROFILES = {
    "youtube_shorts": {
        "platform": "youtube_shorts",
        "name": "YouTube Shorts",
        "video": {
            "bitrate": "6M",
            "crf": 18,
            "h264_profile": "high",
            "aspect_ratio": "9:16",
            "width": 1080,
            "height": 1920,
        },
        "audio": {
            "codec": "aac",
            "bitrate": "192k",
            "sample_rate": 44100,
        },
        "safe_zone": {
            "top_margin": "15%",
            "bottom_margin": "20%",
            "left_margin": "5%",
            "right_margin": "5%",
        },
        "metadata_filename": "youtube_metadata.json",
    },
    "tiktok": {
        "platform": "tiktok",
        "name": "TikTok",
        "video": {
            "bitrate": "8M",
            "crf": 20,
            "h264_profile": "main",
            "aspect_ratio": "9:16",
            "width": 1080,
            "height": 1920,
        },
        "audio": {
            "codec": "aac",
            "bitrate": "128k",
            "sample_rate": 44100,
        },
        "safe_zone": {
            "top_margin": "10%",
            "bottom_margin": "25%",
            "left_margin": "5%",
            "right_margin": "15%",
        },
        "metadata_filename": "tiktok_metadata.json",
    },
    "instagram_reels": {
        "platform": "instagram_reels",
        "name": "Instagram Reels",
        "video": {
            "bitrate": "5M",
            "crf": 21,
            "h264_profile": "main",
            "aspect_ratio": "9:16",
            "width": 1080,
            "height": 1920,
        },
        "audio": {
            "codec": "aac",
            "bitrate": "160k",
            "sample_rate": 44100,
        },
        "safe_zone": {
            "top_margin": "12%",
            "bottom_margin": "18%",
            "left_margin": "5%",
            "right_margin": "5%",
        },
        "metadata_filename": "instagram_metadata.json",
    },
}


def normalize_tags(tags) -> list:
    """Normalize tags list into clean tag strings without '#'."""
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    elif not isinstance(tags, list):
        tags = []

    clean_tags = []
    for tag in tags:
        clean = str(tag).strip().lstrip("#")
        if clean and clean not in clean_tags:
            clean_tags.append(clean)
    return clean_tags


def format_platform_metadata(platform: str, base_metadata: dict) -> dict:
    """
    Generate platform-specific metadata dictionary with title, description,
    hashtag formatting, privacy settings, and interaction flags.
    """
    if platform not in PLATFORM_PROFILES:
        raise ValueError(f"Unsupported platform: {platform}. Supported: {list(PLATFORM_PROFILES.keys())}")

    profile = PLATFORM_PROFILES[platform]
    title = base_metadata.get("title", "Untitled Short")
    desc = base_metadata.get("description", "")
    raw_tags = base_metadata.get("tags", [])
    tags = normalize_tags(raw_tags)

    hashtag_list = [f"#{t}" for t in tags]

    if platform == "youtube_shorts":
        yt_title = title if "#Shorts" in title else f"{title} #Shorts"
        default_yt_hashtags = ["#Shorts", "#YouTubeShorts", "#Viral"]
        combined_hashtags = list(dict.fromkeys(hashtag_list + default_yt_hashtags))
        yt_desc = f"{desc}\n\n" + " ".join(combined_hashtags) if desc else " ".join(combined_hashtags)

        return {
            "platform": "youtube_shorts",
            "title": yt_title,
            "description": yt_desc.strip(),
            "tags": tags,
            "privacy_status": base_metadata.get("privacy_status", "public"),
            "category_id": base_metadata.get("category_id", "24"),
            "made_for_kids": base_metadata.get("made_for_kids", False),
            "self_declared_made_for_kids": base_metadata.get("self_declared_made_for_kids", False),
            "aspect_ratio": "9:16",
            "safe_zone": profile["safe_zone"],
            "encoding_profile": profile["video"],
        }

    elif platform == "tiktok":
        default_tt_hashtags = ["#fyp", "#viral", "#trending"]
        combined_hashtags = list(dict.fromkeys(hashtag_list + default_tt_hashtags))
        caption_str = f"{title} " + " ".join(combined_hashtags)
        if len(caption_str) > 2200:
            caption_str = caption_str[:2197] + "..."

        return {
            "platform": "tiktok",
            "caption": caption_str.strip(),
            "hashtags": combined_hashtags,
            "privacy_level": base_metadata.get("privacy_level", "PUBLIC_TO_EVERYONE"),
            "allow_duet": base_metadata.get("allow_duet", True),
            "allow_stitch": base_metadata.get("allow_stitch", True),
            "allow_comment": base_metadata.get("allow_comment", True),
            "brand_organic_toggle": base_metadata.get("brand_organic_toggle", False),
            "aspect_ratio": "9:16",
            "safe_zone": profile["safe_zone"],
            "encoding_profile": profile["video"],
        }

    elif platform == "instagram_reels":
        default_ig_hashtags = ["#reels", "#viral", "#trending"]
        combined_hashtags = list(dict.fromkeys(hashtag_list + default_ig_hashtags))
        ig_caption = f"{title}\n.\n.\n" + " ".join(combined_hashtags)

        return {
            "platform": "instagram_reels",
            "caption": ig_caption.strip(),
            "hashtags": combined_hashtags,
            "cover_frame_offset": base_metadata.get("cover_frame_offset", 1.0),
            "share_to_feed": base_metadata.get("share_to_feed", True),
            "audio_name": base_metadata.get("audio_name", title),
            "aspect_ratio": "9:16",
            "safe_zone": profile["safe_zone"],
            "encoding_profile": profile["video"],
        }


def encode_video_for_platform(input_video_path: str, output_video_path: str, profile: dict):
    """Re-encode input video using FFmpeg according to platform profile settings."""
    video_cfg = profile["video"]
    audio_cfg = profile["audio"]

    w, h = video_cfg["width"], video_cfg["height"]

    # Filter to scale and pad to 1080x1920 9:16 vertical format
    vf_filter = f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black"

    cmd = [
        "ffmpeg", "-y",
        "-i", input_video_path,
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", str(video_cfg["crf"]),
        "-b:v", video_cfg["bitrate"],
        "-profile:v", video_cfg["h264_profile"],
        "-c:a", audio_cfg["codec"],
        "-b:a", audio_cfg["bitrate"],
        "-ar", str(audio_cfg["sample_rate"]),
        "-pix_fmt", "yuv420p",
        output_video_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg encoding failed for platform '{profile['platform']}': {result.stderr}")


def export_multiplatform(
    input_video_path: str,
    base_metadata: dict,
    output_dir: str,
    platforms: list = None
) -> dict:
    """
    Export video and platform-specific metadata files for multiple target platforms.

    Args:
        input_video_path: Path to source video.
        base_metadata: Dict with title, description, tags, etc.
        output_dir: Root directory for output exports.
        platforms: List of platform names (defaults to ["youtube_shorts", "tiktok", "instagram_reels"]).

    Returns:
        Dict mapping platform name to export details (video_path, metadata_path, metadata).
    """
    if not os.path.exists(input_video_path):
        raise FileNotFoundError(f"Input video file not found: {input_video_path}")

    if platforms is None:
        platforms = ["youtube_shorts", "tiktok", "instagram_reels"]

    output_dir_abs = os.path.abspath(output_dir)
    os.makedirs(output_dir_abs, exist_ok=True)

    results = {}

    for platform in platforms:
        if platform not in PLATFORM_PROFILES:
            print(f"⚠️  Skipping unsupported platform: {platform}")
            continue

        profile = PLATFORM_PROFILES[platform]
        platform_dir = os.path.join(output_dir_abs, platform)
        os.makedirs(platform_dir, exist_ok=True)

        # Output video file paths
        video_filename = f"{platform}.mp4"
        video_out_path = os.path.join(platform_dir, video_filename)

        # Perform FFmpeg video re-encoding
        encode_video_for_platform(input_video_path, video_out_path, profile)

        # Also create video.mp4 symlink/copy for convenient reference
        default_video_path = os.path.join(platform_dir, "video.mp4")
        if not os.path.exists(default_video_path):
            with open(video_out_path, "rb") as f_src, open(default_video_path, "wb") as f_dst:
                f_dst.write(f_src.read())

        # Platform metadata formatting
        formatted_meta = format_platform_metadata(platform, base_metadata)

        # Write platform-specific metadata file (e.g. youtube_metadata.json)
        spec_meta_file = os.path.join(platform_dir, profile["metadata_filename"])
        with open(spec_meta_file, "w", encoding="utf-8") as f:
            json.dump(formatted_meta, f, indent=2)

        # Also write standard metadata.json
        std_meta_file = os.path.join(platform_dir, "metadata.json")
        with open(std_meta_file, "w", encoding="utf-8") as f:
            json.dump(formatted_meta, f, indent=2)

        results[platform] = {
            "video_path": video_out_path,
            "metadata_path": spec_meta_file,
            "standard_metadata_path": std_meta_file,
            "metadata": formatted_meta,
        }

        print(f"✅ Exported for {profile['name']}: {video_out_path}")

    return results
