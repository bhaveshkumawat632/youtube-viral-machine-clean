"""
Thumbnail Generator Module for VidRush Studio / YouTube Viral Machine.
Provides dynamic 3-stop gradient backgrounds, video frame extraction via FFmpeg,
custom image backgrounds, dynamic font scaling, text stroke/outline, drop shadow,
and semi-transparent rounded pill box backgrounds.
"""
import os
import sys
import subprocess
import tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from config import GRADIENTS, ASSETS_DIR
except ImportError:
    GRADIENTS = {}
    ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# Default 3-stop gradient presets
GRADIENT_PRESETS = {
    "neon_dark": ["#0d0d0d", "#1a0033", "#0d0d0d"],
    "fire": ["#ffe100", "#ff3300", "#4a0000"],
    "cyberpunk": ["#ff007f", "#7f00ff", "#000033"],
    "sunset": ["#ffaa00", "#d6006e", "#2c003e"],
    "ocean": ["#00d2ff", "#0033aa", "#000a22"],
    "dark_purple": ["#1a0033", "#4a0080", "#1a0033"],
    "midnight_blue": ["#0a0a2e", "#1a1a5e", "#0a0a2e"],
    "forest_green": ["#001a00", "#004a00", "#001a00"],
    "blood_moon": ["#0d0000", "#330000", "#1a0011"],
}


def hex_to_rgb(hex_str: str) -> tuple:
    """Convert hex string (e.g. #FFE100 or FFE100) to RGB tuple."""
    hex_clean = hex_str.lstrip("#")
    if len(hex_clean) == 3:
        hex_clean = "".join([c * 2 for c in hex_clean])
    return (
        int(hex_clean[0:2], 16),
        int(hex_clean[2:4], 16),
        int(hex_clean[4:6], 16),
    )


def render_3stop_gradient(width: int, height: int, colors: list) -> Image.Image:
    """
    Render a 3-stop smooth linear gradient across image height using NumPy.
    Colors can be a list of 3 hex strings or RGB tuples.
    """
    if len(colors) < 3:
        colors = colors + [colors[-1]] * (3 - len(colors))

    rgb_colors = [hex_to_rgb(c) if isinstance(c, str) else c for c in colors[:3]]
    c1, c2, c3 = np.array(rgb_colors[0]), np.array(rgb_colors[1]), np.array(rgb_colors[2])

    t = np.linspace(0.0, 1.0, height).reshape(height, 1, 1)
    t = np.repeat(t, width, axis=1)

    # First half (0.0 to 0.5): blend c1 -> c2
    # Second half (0.5 to 1.0): blend c2 -> c3
    first_half = (0.5 - t) / 0.5
    second_half = (t - 0.5) / 0.5

    mask = t <= 0.5

    arr = np.where(
        mask,
        c1 * first_half + c2 * (1.0 - first_half),
        c2 * (1.0 - second_half) + c3 * second_half
    )

    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def extract_frame_ffmpeg(video_path: str, timestamp: str = "00:00:02") -> Image.Image:
    """Extract a frame from video file at specified timestamp using FFmpeg."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        cmd = [
            "ffmpeg", "-y",
            "-ss", timestamp,
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            tmp_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
            img = Image.open(tmp_path).convert("RGB")
            img.load()
            return img
        else:
            raise RuntimeError(f"FFmpeg frame extraction failed: {result.stderr}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def resize_and_crop_cover(img: Image.Image, target_width: int, target_height: int) -> Image.Image:
    """Resize and center crop PIL image to cover target width and height."""
    src_w, src_h = img.size
    src_aspect = src_w / src_h
    tgt_aspect = target_width / target_height

    if src_aspect > tgt_aspect:
        # Source is wider: scale height to match target, crop width
        new_h = target_height
        new_w = int(target_height * src_aspect)
    else:
        # Source is taller: scale width to match target, crop height
        new_w = target_width
        new_h = int(target_width / src_aspect)

    img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    left = (new_w - target_width) // 2
    top = (new_h - target_height) // 2
    right = left + target_width
    bottom = top + target_height

    return img_resized.crop((left, top, right, bottom))


def resolve_font(font_path: str = None, font_size: int = 40) -> ImageFont.FreeTypeFont:
    """Try resolving a TrueType font, falling back gracefully to system fonts or default font."""
    candidate_paths = []
    if font_path:
        candidate_paths.append(font_path)

    # Check assets directory font
    assets_font = os.path.join(ASSETS_DIR, "fonts", "Montserrat-ExtraBold.ttf")
    candidate_paths.append(assets_font)

    # Common Linux system fonts
    candidate_paths.extend([
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ])

    for path in candidate_paths:
        if path and os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=font_size)
            except Exception:
                continue

    # Fallback to default
    try:
        return ImageFont.load_default(size=font_size)
    except TypeError:
        return ImageFont.load_default()


def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int, draw: ImageDraw.ImageDraw) -> list:
    """Wrap text into multiple lines so that no line exceeds max_width."""
    lines = []
    paragraphs = text.split("\n")

    for paragraph in paragraphs:
        words = paragraph.split()
        if not words:
            continue

        current_line = []
        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_w = bbox[2] - bbox[0]
            if line_w <= max_width or not current_line:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

    return lines if lines else [text]


def get_text_metrics(lines: list, font: ImageFont.ImageFont, draw: ImageDraw.ImageDraw, line_spacing_ratio: float = 0.25):
    """Calculate total width, total height, line metrics for wrapped lines."""
    line_bboxes = [draw.textbbox((0, 0), line, font=font) for line in lines]
    line_widths = [b[2] - b[0] for b in line_bboxes]
    line_heights = [max(b[3] - b[1], font.size if hasattr(font, 'size') else 20) for b in line_bboxes]

    max_line_width = max(line_widths) if line_widths else 0
    single_line_h = max(line_heights) if line_heights else 20
    line_spacing = int(single_line_h * line_spacing_ratio)

    total_height = sum(line_heights) + line_spacing * max(0, len(lines) - 1)
    return max_line_width, total_height, line_heights, line_spacing


def render_thumbnail(
    title: str,
    output_path: str,
    mode: str = "gradient",
    bg_path: str = None,
    gradient_name: str = "neon_dark",
    aspect_ratio: str = "16:9",
    primary_color: str = "#FFE100",
    outline_color: str = "#000000",
    outline_width: int = 8,
    add_box_bg: bool = True,
    font_path: str = None
) -> str:
    """
    Render a high-impact auto-thumbnail with dynamic font scaling, background modes,
    text stroke, drop shadow, and rounded pill background box.

    Returns the absolute output file path.
    """
    # 1. Canvas Dimensions
    if aspect_ratio == "9:16":
        width, height = 1080, 1920
    elif aspect_ratio == "16:9":
        width, height = 1920, 1080
    elif isinstance(aspect_ratio, (list, tuple)) and len(aspect_ratio) == 2:
        width, height = int(aspect_ratio[0]), int(aspect_ratio[1])
    elif ":" in str(aspect_ratio):
        parts = str(aspect_ratio).split(":")
        try:
            w_ratio, h_ratio = float(parts[0]), float(parts[1])
            if h_ratio > w_ratio:
                width, height = 1080, 1920
            else:
                width, height = 1280, 720
        except ValueError:
            width, height = 1280, 720
    else:
        width, height = 1280, 720

    # 2. Render Background
    canvas = None
    is_video_bg = bg_path and bg_path.lower().endswith((".mp4", ".mov", ".avi", ".mkv", ".webm"))

    if (mode == "frame_extract" or is_video_bg) and bg_path and os.path.exists(bg_path):
        try:
            raw_frame = extract_frame_ffmpeg(bg_path, timestamp="00:00:02")
            canvas = resize_and_crop_cover(raw_frame, width, height)
        except Exception as e:
            print(f"⚠️  Frame extraction failed ({e}), falling back to gradient.")
            canvas = None

    if canvas is None and (mode == "image" or (bg_path and os.path.exists(bg_path) and not is_video_bg)):
        try:
            img = Image.open(bg_path).convert("RGB")
            canvas = resize_and_crop_cover(img, width, height)
        except Exception as e:
            print(f"⚠️  Image load failed ({e}), falling back to gradient.")
            canvas = None

    if canvas is None:
        # Gradient mode fallback
        preset = GRADIENTS.get(gradient_name) or GRADIENT_PRESETS.get(gradient_name) or GRADIENT_PRESETS["neon_dark"]
        canvas = render_3stop_gradient(width, height, preset)

    # Ensure canvas is in RGBA mode for alpha compositing
    canvas = canvas.convert("RGBA")

    # 3. Dynamic Font Scaling & Text Wrapping
    max_text_width = int(width * 0.85)
    max_text_height = int(height * 0.70)

    # Initial font size based on aspect ratio
    font_size = 140 if aspect_ratio == "9:16" else 110
    min_font_size = 20

    dummy_draw = ImageDraw.Draw(canvas)
    best_font = None
    best_lines = []
    best_metrics = None

    title_clean = title.strip()

    while font_size >= min_font_size:
        test_font = resolve_font(font_path, font_size=font_size)
        lines = wrap_text(title_clean, test_font, max_text_width, dummy_draw)
        max_w, total_h, line_hs, line_spacing = get_text_metrics(lines, test_font, dummy_draw)

        if max_w <= max_text_width and total_h <= max_text_height:
            best_font = test_font
            best_lines = lines
            best_metrics = (max_w, total_h, line_hs, line_spacing)
            break
        font_size -= 4

    if best_font is None:
        best_font = resolve_font(font_path, font_size=min_font_size)
        best_lines = wrap_text(title_clean, best_font, max_text_width, dummy_draw)
        best_metrics = get_text_metrics(best_lines, best_font, dummy_draw)

    max_w, total_h, line_hs, line_spacing = best_metrics

    # 4. Text Bounding Box & Pill Background Box
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    start_y = (height - total_h) // 2

    if add_box_bg:
        box_pad_x = int(font_size * 0.4)
        box_pad_y = int(font_size * 0.3)

        box_x1 = max(0, (width - max_w) // 2 - box_pad_x)
        box_y1 = max(0, start_y - box_pad_y)
        box_x2 = min(width, (width + max_w) // 2 + box_pad_x)
        box_y2 = min(height, start_y + total_h + box_pad_y)

        overlay_draw.rounded_rectangle(
            [box_x1, box_y1, box_x2, box_y2],
            radius=int(font_size * 0.3),
            fill=(0, 0, 0, 160)
        )

    # 5. Drop Shadow and Main Text with Outline
    shadow_offset = max(4, outline_width // 2 + 3)
    curr_y = start_y

    for line, line_h in zip(best_lines, line_hs):
        bbox = overlay_draw.textbbox((0, 0), line, font=best_font)
        line_w = bbox[2] - bbox[0]
        line_x = (width - line_w) // 2

        # Draw Drop Shadow
        overlay_draw.text(
            (line_x + shadow_offset, curr_y + shadow_offset),
            line,
            font=best_font,
            fill=(0, 0, 0, 220),
            stroke_width=outline_width,
            stroke_fill=(0, 0, 0, 220)
        )

        # Draw Primary Text with Outline
        overlay_draw.text(
            (line_x, curr_y),
            line,
            font=best_font,
            fill=primary_color,
            stroke_width=outline_width,
            stroke_fill=outline_color
        )

        curr_y += line_h + line_spacing

    # 6. Composite & Save Output
    final_img = Image.alpha_composite(canvas, overlay).convert("RGB")

    output_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(output_dir, exist_ok=True)

    final_img.save(output_path, quality=95, subsampling=0, optimize=True)
    print(f"✅ Thumbnail rendered successfully: {output_path} ({width}x{height})")
    return os.path.abspath(output_path)
