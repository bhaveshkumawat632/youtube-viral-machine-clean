"""
YouTube Viral Machine - Configuration
All settings in one place
"""
import os

# ============================================================
# DIRECTORIES
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Move heavy I/O and outputs to HDD to save SSD
HDD_PATH = "/run/media/junglee01/New Volume/testing"
OUTPUT_DIR = os.path.join(HDD_PATH, "output")
TEMP_DIR = os.path.join(HDD_PATH, "temp")

# Fallback if HDD is not mounted
if not os.path.exists("/run/media/junglee01/New Volume"):
    OUTPUT_DIR = os.path.join(BASE_DIR, "Testing", "output")
    TEMP_DIR = os.path.join(BASE_DIR, "Testing", "temp")
BACKGROUNDS_DIR = os.path.join(BASE_DIR, "backgrounds")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
SFX_DIR = os.path.join(ASSETS_DIR, "sfx")
BGM_DIR = os.path.join(ASSETS_DIR, "bgm")

# ============================================================
# CLOUD ORCHESTRATION CONFIG (FREE TIER)
# ============================================================
# We use Hugging Face free spaces via gradio_client instead of paid APIs or local GPU
HF_VIDEO_SPACE = "THUDM/CogVideoX-5B-Space" # Example free powerful video generation space

# Optional: Set this to your temporary Google Colab Gradio link (e.g., "https://xyz.gradio.live")
PRIVATE_API_URL = os.environ.get("PRIVATE_API_URL", "https://5d0d7b9cfdaf3ecc11.gradio.live/")

# ============================================================
# VIDEO SETTINGS
# ============================================================
# YouTube Shorts (9:16)
SHORTS_WIDTH = 1080
SHORTS_HEIGHT = 1920

# YouTube Video (16:9)
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080

# FPS
FPS = 30

# ============================================================
# VOICE SETTINGS (Edge TTS)
# ============================================================
VOICES = {
    "hindi_male": "hi-IN-MadhurNeural",
    "hindi_female": "hi-IN-SwaraNeural",
    "english_male": "en-US-ChristopherNeural",
    "english_female": "en-US-JennyNeural",
    "english_dramatic": "en-US-GuyNeural",
    "hindi_dramatic": "hi-IN-MadhurNeural",
}

DEFAULT_VOICE = "hindi_female"
SPEECH_RATE = "+10%"  # Faster, cuter voice

# ============================================================
# SUBTITLE SETTINGS
# ============================================================
SUBTITLE_FONT_SIZE = 85
SUBTITLE_FONT_COLOR = "#FFFFFF"
SUBTITLE_HIGHLIGHT_COLOR = "#00FFFF"  # Cyan highlight for current word
SUBTITLE_BG_COLOR = "#000000"
SUBTITLE_BG_OPACITY = 0.6
SUBTITLE_OUTLINE_COLOR = "#000000"
SUBTITLE_OUTLINE_WIDTH = 5
SUBTITLE_FONT_NAME = "Montserrat ExtraBold"
SUBTITLE_FONT_PATH = os.path.join(ASSETS_DIR, "fonts", "Montserrat-ExtraBold.ttf")
SUBTITLE_POSITION = "shorts_optimal"  # optimal position for shorts (40% from bottom)
SUBTITLE_POSITION = "shorts_optimal"  # optimal position for shorts (40% from bottom)
MAX_WORDS_PER_LINE = 2 # Punchy 1-2 words reveal for high retention shorts

# DYNAMIC CINEMATIC CAPTION SETTINGS
DYNAMIC_SUBTITLES = True
SUBTITLE_ANIMATION = "pop_in" # pop_in, bounce, slide
PRIMARY_TEXT_COLOR = "&H00FFFFFF" # ASS format White
HIGHLIGHT_TEXT_COLOR = "&H0000FF00" # ASS format Neon Green
OUTLINE_COLOR = "&H00000000"
BACK_COLOR = "&H80000000"

# ============================================================
# GRADIENT BACKGROUNDS (for script-to-video mode)
# ============================================================
GRADIENTS = {
    "dark_purple": ["#1a0033", "#4a0080", "#1a0033"],
    "midnight_blue": ["#0a0a2e", "#1a1a5e", "#0a0a2e"],
    "dark_red": ["#1a0000", "#4a0000", "#1a0000"],
    "forest_green": ["#001a00", "#004a00", "#001a00"],
    "sunset": ["#1a0a00", "#4a1a00", "#1a0a00"],
    "ocean": ["#000a1a", "#001a4a", "#000a1a"],
    "neon_dark": ["#0d0d0d", "#1a0033", "#0d0d0d"],
    "blood_moon": ["#0d0000", "#330000", "#1a0011"],
}

DEFAULT_GRADIENT = "neon_dark"

# ============================================================
# AUTO CLIPPER SETTINGS
# ============================================================
MIN_CLIP_DURATION = 15   # seconds
MAX_CLIP_DURATION = 59   # seconds (YouTube Shorts limit)
SILENCE_THRESHOLD = -35  # dB
SILENCE_MIN_DURATION = 0.5  # seconds

# ============================================================
# WHISPER SETTINGS
# ============================================================
WHISPER_MODEL = "tiny"  # tiny, base, small, medium, large
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"

# ============================================================
# CONTENT TEMPLATES
# ============================================================
VIRAL_HOOKS_HINDI = [
    "Yeh sunke aapko yakeen nahi hoga...",
    "99% log yeh galti karte hain...",
    "Yeh secret sirf 1% log jaante hain...",
    "Agar yeh nahi jaante toh bahut peeche reh jaoge...",
    "Duniya ka sabse {adjective} {topic}...",
    "Aaj main aapko woh baat bataunga jo koi nahi batata...",
    "Yeh video dekhne ke baad aapki zindagi badal jaegi...",
    "Last tak dekhna, sabse important baat end mein hai...",
    "Kya aapko pata hai {topic} ka asli sach?",
    "Warning: yeh video weak logon ke liye nahi hai...",
    "Sirf 30 second mein samjho {topic}...",
    "Maine {topic} ka sabse bada raaz khol diya...",
]

VIRAL_HOOKS_ENGLISH = [
    "You won't believe this...",
    "99% of people don't know this...",
    "This secret will blow your mind...",
    "Stop scrolling! You NEED to see this...",
    "The truth about {topic} nobody tells you...",
    "I discovered something insane about {topic}...",
    "Watch till the end, the best part is coming...",
    "This changed everything I knew about {topic}...",
    "POV: You just discovered {topic}...",
    "They don't want you to know this about {topic}...",
]

CTA_HINDI = [
    "Like karo, Share karo, aur Subscribe zaroor karo!",
    "Agar yeh video pasand aayi toh Like aur Subscribe karo!",
    "Comment mein batao aapko kya lagta hai!",
    "Notification bell dabao taaki koi video miss na ho!",
    "Aisi aur videos ke liye Subscribe karo!",
]

CTA_ENGLISH = [
    "Like, Share, and Subscribe!",
    "Hit that Subscribe button and turn on notifications!",
    "Drop a comment below, what do you think?",
    "Follow for more content like this!",
    "Subscribe for daily videos like this!",
]

# Niche-specific script categories
# Niche-specific script categories
NICHES = {
    "reddit_revenge": {
        "name_hi": "Reddit Revenge",
        "name_en": "Reddit Revenge",
        "topics": ["Pro revenge", "Petty revenge", "Nuclear revenge"],
    },
    "reddit_aita": {
        "name_hi": "Am I The Jerk?",
        "name_en": "Am I The Jerk?",
        "topics": ["Family drama AITA", "Wedding drama AITA", "Workplace AITA"],
    },
    "reddit_drama": {
        "name_hi": "Relationship Drama",
        "name_en": "Relationship Drama",
        "topics": ["Cheating stories", "Toxic in-laws", "Bad roommates"],
    },
}

# ============================================================
# SAFETY KILL SWITCH (COPYRIGHT GUARDRAIL)
# ============================================================
AUDIO_WHITELIST = ["youtube_audio_library", "royalty_free_local", "synthetic_ffmpeg"]
VISUAL_WHITELIST = ["pexels_api", "self_recorded_loop", "synthetic_gradient", "synthetic_ffmpeg"]
