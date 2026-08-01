"""
YouTube Viral Machine - Subtitle Generator
Uses Whisper for transcription + creates styled ASS subtitles
"""
import os
import sys
import json
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    WHISPER_MODEL, WHISPER_DEVICE, WHISPER_COMPUTE_TYPE,
    SUBTITLE_FONT_SIZE, SUBTITLE_FONT_COLOR, SUBTITLE_HIGHLIGHT_COLOR,
    SUBTITLE_OUTLINE_COLOR, SUBTITLE_OUTLINE_WIDTH, SUBTITLE_POSITION,
    MAX_WORDS_PER_LINE, SHORTS_WIDTH, SHORTS_HEIGHT, TEMP_DIR,
    SUBTITLE_FONT_NAME, SUBTITLE_BG_OPACITY,
    DYNAMIC_SUBTITLES, SUBTITLE_ANIMATION, PRIMARY_TEXT_COLOR, HIGHLIGHT_TEXT_COLOR, OUTLINE_COLOR, BACK_COLOR
)


def hex_to_ass_color(hex_color):
    """Convert hex color (#RRGGBB) to ASS color (&HBBGGRR&)"""
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"&H00{b:02X}{g:02X}{r:02X}&"


def seconds_to_ass_time(seconds):
    """Convert seconds to ASS timestamp format (H:MM:SS.CC)"""
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def transcribe_audio(audio_path, language="hi"):
    """
    Transcribe audio using Whisper and return word-level timestamps.

    Args:
        audio_path: Path to audio file
        language: Language code (e.g., 'hi' for Hindi, 'en' for English)

    Returns:
        list of dicts: [{"text": "word", "start": 0.0, "end": 0.5}, ...]
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("❌ faster-whisper not installed. Run: pip install faster-whisper")
        import whisper
        print(f"🔄 Loading Whisper model (tiny for low RAM)...")
        # Load tiny model to avoid RAM crashes on 16GB systems without GPU
        model = whisper.load_model("tiny")
        print(f"🎧 Transcribing audio (language: {language})...")
        segments = model.transcribe(audio_path, language="hi" if language=="hindi" else "en", word_timestamps=True)["segments"]
        
        words = []
        for segment in segments:
            for word in segment.get("words", []):
                words.append({
                    "text": word["word"].strip(),
                    "start": word["start"],
                    "end": word["end"],
                })
        return words

    print(f"🔄 Loading Whisper model ({WHISPER_MODEL})...")
    model = WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE_TYPE)

    print(f"🎧 Transcribing audio (language: {language})...")
    segments, info = model.transcribe(audio_path, word_timestamps=True, language=language)

    words = []
    for segment in segments:
        if segment.words:
            for word in segment.words:
                words.append({
                    "text": word.word.strip(),
                    "start": word.start,
                    "end": word.end,
                })

    print(f"✅ Transcribed {len(words)} words")
    return words


def words_from_edge_tts(word_boundaries_json_path):
    """
    Load word timestamps from Edge TTS word boundaries JSON file.
    These are more accurate than Whisper for TTS-generated audio.
    """
    with open(word_boundaries_json_path, "r", encoding="utf-8") as f:
        boundaries = json.load(f)

    words = []
    for wb in boundaries:
        words.append({
            "text": wb["text"],
            "start": wb["start_ms"] / 1000.0,  # convert ms to seconds
            "end": wb["end_ms"] / 1000.0,
        })

    return words


def words_from_script_with_timestamps(script_text, audio_path, language="hi"):
    """
    Smart hybrid approach: Use Whisper for TIMESTAMPS only,
    but use the ORIGINAL script text for the actual words.

    This solves the Urdu script problem - Whisper may transcribe in
    wrong script, but we only need its timing data.

    Args:
        script_text: Original script text (Hindi/English)
        audio_path: Path to the audio file
        language: Language code for Whisper

    Returns:
        list of dicts: [{"text": "word", "start": 0.0, "end": 0.5}, ...]
    """
    # Get timestamps from Whisper
    whisper_words = transcribe_audio(audio_path, language=language)

    if not whisper_words:
        # Fallback: evenly distribute script words across audio duration
        return _evenly_distribute_words(script_text, audio_path)

    # Split original script into words
    import re
    script_words = [w for w in re.split(r'\s+', script_text.strip()) if w]

    # If word counts are similar, map 1:1
    if abs(len(script_words) - len(whisper_words)) <= len(script_words) * 0.3:
        # Map original text onto Whisper timestamps
        result = []
        for i, whisper_w in enumerate(whisper_words):
            if i < len(script_words):
                result.append({
                    "text": script_words[i],
                    "start": whisper_w["start"],
                    "end": whisper_w["end"],
                })
            else:
                # Extra whisper words - use whisper text
                result.append(whisper_w)

        # Add remaining script words if any (distribute in last segment)
        if len(script_words) > len(whisper_words) and whisper_words:
            last_end = whisper_words[-1]["end"]
            remaining = script_words[len(whisper_words):]
            time_per_word = 0.3
            for j, word in enumerate(remaining):
                result.append({
                    "text": word,
                    "start": last_end + j * time_per_word,
                    "end": last_end + (j + 1) * time_per_word,
                })

        print(f"✅ Mapped {len(result)} original script words to Whisper timestamps")
        return result
    else:
        # Word counts too different - use even distribution
        print(f"⚠️  Word count mismatch (script: {len(script_words)}, whisper: {len(whisper_words)})")
        print(f"   Using evenly distributed timestamps...")
        return _evenly_distribute_words(script_text, audio_path)


def _evenly_distribute_words(script_text, audio_path):
    """Fallback: Evenly distribute script words across audio duration"""
    import re, subprocess
    script_words = [w for w in re.split(r'\s+', script_text.strip()) if w]

    # Get audio duration
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", audio_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    duration = float(json.loads(result.stdout)["format"]["duration"])

    time_per_word = duration / len(script_words)
    words = []
    for i, word in enumerate(script_words):
        words.append({
            "text": word,
            "start": i * time_per_word,
            "end": (i + 1) * time_per_word,
        })

    print(f"✅ Evenly distributed {len(words)} words over {duration:.1f}s")
    return words


def group_words_into_lines(words, max_words_per_line=None):
    """Group words into subtitle lines"""
    max_words = max_words_per_line or MAX_WORDS_PER_LINE
    lines = []
    current_line = []

    for word in words:
        current_line.append(word)
        if len(current_line) >= max_words:
            lines.append(current_line)
            current_line = []

    if current_line:
        lines.append(current_line)

    return lines


KEYWORD_EMOJI_MAP = {
    "secret": "🤫",
    "brain": "🧠",
    "money": "💰",
    "life": "🌱",
    "planet": "🪐",
    "astronaut": "👨‍🚀",
    "time": "⏱️",
    "waiting": "⏳"
}

def map_word_to_emoji(word_text):
    import re
    clean_word = re.sub(r'[^\w\s]', '', word_text).lower()
    if clean_word in KEYWORD_EMOJI_MAP:
        return f"{word_text} {KEYWORD_EMOJI_MAP[clean_word]}"
    return word_text


def generate_ass_subtitles(words, output_path, video_width=None, video_height=None,
                           font_size=None, highlight=True, highlight_color=None):
    """
    Generate ASS subtitle file with word-by-word highlighting (karaoke style).

    Args:
        words: list of word dicts with 'text', 'start', 'end'
        output_path: path for output .ass file
        video_width: video width in pixels
        video_height: video height in pixels
        font_size: subtitle font size
        highlight: if True, highlight current word in gold
        highlight_color: hex highlight color (e.g. #FF0000)
    """
    # Map words to emoji (R1)
    mapped_words = []
    for w in words:
        new_w = w.copy()
        new_w["text"] = map_word_to_emoji(w["text"])
        mapped_words.append(new_w)
    words = mapped_words

    width = video_width or SHORTS_WIDTH
    height = video_height or SHORTS_HEIGHT
    fsize = font_size or SUBTITLE_FONT_SIZE

    primary_color = hex_to_ass_color(SUBTITLE_FONT_COLOR)
    h_color = highlight_color or SUBTITLE_HIGHLIGHT_COLOR
    highlight_color_ass = hex_to_ass_color(h_color)
    outline_color = hex_to_ass_color(SUBTITLE_OUTLINE_COLOR)

    # Position: center of screen for Shorts
    if SUBTITLE_POSITION == "center":
        alignment = 5  # Center-center
        margin_v = int(height * 0.1)
    elif SUBTITLE_POSITION == "bottom":
        alignment = 2  # Bottom-center
        margin_v = 60
    elif SUBTITLE_POSITION == "shorts_optimal":
        alignment = 8  # Top-center
        margin_v = 150  # Fixed pixel margin to avoid renderer capping
    else:  # top
        alignment = 8  # Top-center
        margin_v = 60

    # Background opacity
    bg_alpha = int((1 - SUBTITLE_BG_OPACITY) * 255)
    bg_color_ass = f"&H{bg_alpha:02X}000000&"

    # ASS Header
    ass_content = f"""[Script Info]
Title: YouTube Viral Machine Subtitles
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes
Collisions: Normal

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{SUBTITLE_FONT_NAME},{fsize},{PRIMARY_TEXT_COLOR},&H000000FF&,{OUTLINE_COLOR},{BACK_COLOR},-1,0,0,0,100,100,0,0,1,{SUBTITLE_OUTLINE_WIDTH},4,{alignment},40,40,{margin_v},1
Style: Highlight,{SUBTITLE_FONT_NAME},{fsize},{HIGHLIGHT_TEXT_COLOR},&H000000FF&,{OUTLINE_COLOR},{BACK_COLOR},-1,0,0,0,100,100,0,0,1,{SUBTITLE_OUTLINE_WIDTH},4,{alignment},40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    # Group words into lines
    lines = group_words_into_lines(words)

    for line_words in lines:
        if not line_words:
            continue

        line_start = line_words[0]["start"]
        line_end = line_words[-1]["end"]

        if highlight and len(line_words) > 1:
            # Create word-by-word highlight effect
            # Show each word highlighted one at a time
            for i, word in enumerate(line_words):
                word_start = word["start"]
                word_end = word["end"]

                # Build the text with current word highlighted
                text_parts = []
                for j, w in enumerate(line_words):
                    if j == i:
                        # Current word - color-based highlighting with no scale changes to prevent jittering
                        text_parts.append(
                            f"{{\\rHighlight}}{w['text']}{{\\rDefault}}"
                        )
                    else:
                        text_parts.append(w["text"])

                line_text = " ".join(text_parts)

                start_time = seconds_to_ass_time(word_start)
                end_time = seconds_to_ass_time(word_end)

                ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{line_text}\n"
        else:
            # Simple subtitle without highlighting
            line_text = " ".join([w["text"] for w in line_words])
            start_time = seconds_to_ass_time(line_start)
            end_time = seconds_to_ass_time(line_end)
            ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{line_text}\n"

    # Write file
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    print(f"✅ Subtitles generated: {output_path}")
    print(f"📊 Total lines: {len(lines)}, Total words: {len(words)}")

    return output_path


def generate_srt_subtitles(words, output_path):
    """Generate simple SRT subtitle file (for CapCut import)"""
    # Map words to emoji (R1)
    mapped_words = []
    for w in words:
        new_w = w.copy()
        new_w["text"] = map_word_to_emoji(w["text"])
        mapped_words.append(new_w)
    words = mapped_words

    lines = group_words_into_lines(words)

    srt_content = ""
    for i, line_words in enumerate(lines, 1):
        if not line_words:
            continue

        start = line_words[0]["start"]
        end = line_words[-1]["end"]

        # SRT timestamp format: HH:MM:SS,mmm
        start_h, start_m = int(start // 3600), int((start % 3600) // 60)
        start_s, start_ms = int(start % 60), int((start % 1) * 1000)
        end_h, end_m = int(end // 3600), int((end % 3600) // 60)
        end_s, end_ms = int(end % 60), int((end % 1) * 1000)

        start_str = f"{start_h:02d}:{start_m:02d}:{start_s:02d},{start_ms:03d}"
        end_str = f"{end_h:02d}:{end_m:02d}:{end_s:02d},{end_ms:03d}"

        text = " ".join([w["text"] for w in line_words])
        srt_content += f"{i}\n{start_str} --> {end_str}\n{text}\n\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    print(f"✅ SRT subtitles generated: {output_path}")
    return output_path


if __name__ == "__main__":
    print("📝 YouTube Viral Machine - Subtitle Generator")
    print("=" * 50)

    # Test with sample words
    test_words = [
        {"text": "Yeh", "start": 0.0, "end": 0.3},
        {"text": "sunke", "start": 0.3, "end": 0.7},
        {"text": "aapko", "start": 0.7, "end": 1.1},
        {"text": "yakeen", "start": 1.1, "end": 1.5},
        {"text": "nahi", "start": 1.5, "end": 1.8},
        {"text": "hoga", "start": 1.8, "end": 2.2},
        {"text": "ki", "start": 2.5, "end": 2.7},
        {"text": "aapka", "start": 2.7, "end": 3.1},
        {"text": "dimaag", "start": 3.1, "end": 3.5},
        {"text": "kitna", "start": 3.5, "end": 3.9},
        {"text": "powerful", "start": 3.9, "end": 4.4},
        {"text": "hai", "start": 4.4, "end": 4.7},
    ]

    os.makedirs(TEMP_DIR, exist_ok=True)
    ass_path = os.path.join(TEMP_DIR, "test_subs.ass")
    srt_path = os.path.join(TEMP_DIR, "test_subs.srt")

    generate_ass_subtitles(test_words, ass_path)
    generate_srt_subtitles(test_words, srt_path)
