"""
YouTube Viral Machine - Voiceover Engine
Uses Edge TTS for free, high-quality AI voiceover
"""
import asyncio
import os
import sys
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import VOICES, DEFAULT_VOICE, SPEECH_RATE, TEMP_DIR

try:
    import edge_tts
except ImportError:
    print("❌ edge-tts not installed. Run: pip install edge-tts")
    sys.exit(1)


async def _generate_voiceover(text, output_path, voice_key=None, rate=None):
    """Internal async function to generate voiceover with word timestamps using JARVIS UnifiedRouter"""
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    try:
        from jarvis_universal.core.api_router import UnifiedRouter
        router = UnifiedRouter()
        
        voice_preference = "male"
        if voice_key and "female" in voice_key.lower():
            voice_preference = "female"
            
        print("🎙️ Generating Voiceover via JARVIS UnifiedRouter...")
        audio_path, boundaries_path, word_boundaries = router.tts(text, output_path, voice_preference)
        return audio_path, boundaries_path, word_boundaries
        
    except Exception as e:
        print(f"⚠️ UnifiedRouter TTS failed: {e}. Falling back to basic Edge-TTS...")
        # Deep fallback to standard edge-tts if router is fully broken
        voice_name = VOICES.get(voice_key or DEFAULT_VOICE, VOICES[DEFAULT_VOICE])
        speech_rate = rate or SPEECH_RATE

        communicate = edge_tts.Communicate(text, voice_name, rate=speech_rate)
        submaker = edge_tts.SubMaker()

        # Collect word boundaries for subtitle sync
        word_boundaries = []
        audio_chunks = []

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.feed(chunk)
                word_boundaries.append({
                    "text": chunk["text"],
                    "offset": chunk["offset"],       # in ticks (100 nanoseconds)
                    "duration": chunk["duration"],    # in ticks
                    "start_ms": chunk["offset"] / 10000,      # convert to ms
                    "end_ms": (chunk["offset"] + chunk["duration"]) / 10000,
                })

        # Write audio file
        with open(output_path, "wb") as f:
            for chunk in audio_chunks:
                f.write(chunk)

        # Save word boundaries for subtitle generation
        boundaries_path = output_path.replace(".mp3", "_words.json")
        with open(boundaries_path, "w", encoding="utf-8") as f:
            json.dump(word_boundaries, f, ensure_ascii=False, indent=2)

        return output_path, boundaries_path, word_boundaries


def generate_voiceover(text, output_path=None, voice_key=None, rate=None):
    """
    Generate voiceover from text using Edge TTS.

    Args:
        text: The text to convert to speech
        output_path: Path for output MP3 file (auto-generated if None)
        voice_key: Key from VOICES dict (e.g., 'hindi_male', 'english_female')
        rate: Speech rate (e.g., '+10%', '-20%')

    Returns:
        tuple: (audio_path, word_boundaries_path, word_boundaries_list)
    """
    if output_path is None:
        os.makedirs(TEMP_DIR, exist_ok=True)
        output_path = os.path.join(TEMP_DIR, f"voiceover_{int(time.time())}.mp3")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    import nest_asyncio
    nest_asyncio.apply()
    result = asyncio.run(
        _generate_voiceover(text, output_path, voice_key, rate)
    )

    return result


def get_audio_duration(audio_path):
    """Get duration of an audio file using ffprobe"""
    import subprocess
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", audio_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(result.stdout)
    return float(info["format"]["duration"])


def list_available_voices():
    """List all available Edge TTS voices"""
    voices_info = []
    for key, name in VOICES.items():
        voices_info.append(f"  {key:20s} → {name}")
    return "\n".join(voices_info)


async def _list_all_voices():
    """List ALL available Edge TTS voices"""
    voices = await edge_tts.list_voices()
    return voices


def list_all_voices(language_filter=None):
    """List all Edge TTS voices, optionally filtered by language"""
    voices = asyncio.run(_list_all_voices())
    if language_filter:
        voices = [v for v in voices if language_filter.lower() in v["Locale"].lower()]
    return voices


if __name__ == "__main__":
    print("🎤 YouTube Viral Machine - Voiceover Engine")
    print("=" * 50)
    print("\nAvailable voices:")
    print(list_available_voices())
    print("\n🔊 Generating test voiceover...")

    test_text = "Yeh sunke aapko yakeen nahi hoga. Duniya ka sabse powerful computer aapke dimaag mein hai."
    audio_path, words_path, words = generate_voiceover(
        test_text,
        os.path.join(TEMP_DIR, "test_voice.mp3"),
        "hindi_male"
    )
    duration = get_audio_duration(audio_path)
    print(f"✅ Audio generated: {audio_path}")
    print(f"⏱️  Duration: {duration:.1f} seconds")
    print(f"📝 Word timestamps: {words_path}")
    print(f"📊 Total words: {len(words)}")
