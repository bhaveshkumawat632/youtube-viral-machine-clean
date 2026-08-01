"""
Stress tests and boundary condition verifications for:
- R1 Auto-Thumbnail Generator (modules/thumbnail_generator.py)
- R3 Multi-Platform Export Formatter (modules/export_formatter.py)
"""
import os
import pytest
import tempfile
from PIL import Image
from modules.thumbnail_generator import render_thumbnail, render_3stop_gradient, hex_to_rgb
from modules.export_formatter import export_multiplatform, format_platform_metadata, normalize_tags


class TestR1ThumbnailGeneratorStress:
    """Stress tests for R1 Auto-Thumbnail Generator."""

    def test_extremely_long_title(self, tmp_path):
        """Test rendering with 200+ character title string."""
        long_title = "ULTIMATE VIRAL SHORTS GENERATOR " * 10  # ~320 chars
        out_file = str(tmp_path / "thumb_long_title.jpg")
        result = render_thumbnail(
            title=long_title,
            output_path=out_file,
            mode="gradient",
            gradient_name="fire",
            aspect_ratio="16:9"
        )
        assert os.path.exists(result)
        assert os.path.getsize(result) > 0
        img = Image.open(result)
        assert img.size == (1280, 720)

    def test_empty_string_title(self, tmp_path):
        """Test rendering with empty string and whitespace-only title."""
        out_file_empty = str(tmp_path / "thumb_empty.jpg")
        result_empty = render_thumbnail(
            title="",
            output_path=out_file_empty,
            mode="gradient"
        )
        assert os.path.exists(result_empty)
        assert os.path.getsize(result_empty) > 0

        out_file_space = str(tmp_path / "thumb_spaces.jpg")
        result_space = render_thumbnail(
            title="   \n \t  ",
            output_path=out_file_space,
            mode="gradient"
        )
        assert os.path.exists(result_space)
        assert os.path.getsize(result_space) > 0

    def test_special_characters_title(self, tmp_path):
        """Test rendering title with special characters, symbols, and formatting."""
        special_title = "!@#$%^&*()_+/<>:;\"'\\|[]{}~`\nLine2\tTabbed 🚀🔥"
        out_file = str(tmp_path / "thumb_special.jpg")
        result = render_thumbnail(
            title=special_title,
            output_path=out_file,
            mode="gradient",
            gradient_name="cyberpunk"
        )
        assert os.path.exists(result)
        assert os.path.getsize(result) > 0

    def test_invalid_gradient_name(self, tmp_path):
        """Test rendering with invalid / non-existent gradient preset name."""
        out_file = str(tmp_path / "thumb_invalid_grad.jpg")
        result = render_thumbnail(
            title="Invalid Gradient Test",
            output_path=out_file,
            mode="gradient",
            gradient_name="non_existent_super_duper_gradient_9999"
        )
        assert os.path.exists(result)
        assert os.path.getsize(result) > 0
        img = Image.open(result)
        assert img.size == (1280, 720)

    def test_non_existent_background_video_path(self, tmp_path):
        """Test rendering when non-existent background video path is passed in frame_extract mode."""
        fake_video_path = "/tmp/definitely_non_existent_video_path_999999.mp4"
        out_file = str(tmp_path / "thumb_fake_video.jpg")
        # Should gracefully fall back to gradient mode without raising exception
        result = render_thumbnail(
            title="Fake Video Fallback Test",
            output_path=out_file,
            mode="frame_extract",
            bg_path=fake_video_path,
            gradient_name="sunset"
        )
        assert os.path.exists(result)
        assert os.path.getsize(result) > 0

    def test_non_existent_background_image_path(self, tmp_path):
        """Test rendering when non-existent background image path is passed in image mode."""
        fake_img_path = "/tmp/definitely_non_existent_image_path_999999.png"
        out_file = str(tmp_path / "thumb_fake_img.jpg")
        # Should gracefully fall back to gradient mode
        result = render_thumbnail(
            title="Fake Image Fallback Test",
            output_path=out_file,
            mode="image",
            bg_path=fake_img_path
        )
        assert os.path.exists(result)
        assert os.path.getsize(result) > 0


class TestR3MultiPlatformExportFormatterStress:
    """Stress tests for R3 Multi-Platform Export Formatter."""

    def test_empty_metadata(self):
        """Test metadata formatting with completely empty metadata dict."""
        for platform in ["youtube_shorts", "tiktok", "instagram_reels"]:
            formatted = format_platform_metadata(platform, {})
            assert formatted["platform"] == platform
            assert "title" in formatted or "caption" in formatted
            assert "safe_zone" in formatted
            assert "encoding_profile" in formatted

    def test_invalid_platform_name_format_metadata(self):
        """Test format_platform_metadata with an unsupported platform name."""
        with pytest.raises(ValueError) as exc_info:
            format_platform_metadata("invalid_platform_123", {"title": "Test"})
        assert "Unsupported platform: invalid_platform_123" in str(exc_info.value)

    def test_non_existent_input_video_export(self, tmp_path):
        """Test export_multiplatform with non-existent input video file."""
        fake_input = str(tmp_path / "non_existent_input.mp4")
        out_dir = str(tmp_path / "exports")
        with pytest.raises(FileNotFoundError) as exc_info:
            export_multiplatform(
                input_video_path=fake_input,
                base_metadata={"title": "Test"},
                output_dir=out_dir
            )
        assert "Input video file not found" in str(exc_info.value)

    def test_export_with_unsupported_platform_list(self, tmp_path):
        """Test export_multiplatform when platforms list contains invalid platform name."""
        # Create dummy input video file
        dummy_video = str(tmp_path / "dummy_input.mp4")
        with open(dummy_video, "wb") as f:
            f.write(b"dummy content")

        out_dir = str(tmp_path / "exports")
        # Passing unsupported platform along with non-video dummy should fail on FFmpeg or skip unsupported
        # Let's test how export_multiplatform handles unsupported platform item in list
        results = export_multiplatform(
            input_video_path=dummy_video,
            base_metadata={"title": "Test"},
            output_dir=out_dir,
            platforms=["invalid_platform_xyz"]
        )
        assert results == {}  # invalid platform was skipped gracefully
