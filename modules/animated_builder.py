"""
Animated scene builder for VidRush — Paisa Bhai talking-host shorts.
Produces 1080x1920 vertical videos with:
  - big centered cartoon host (transparent PNG)
  - animated branded background (gradient + floating shapes)
  - ken-burns slow zoom
  - fake lip-sync (talk/neutral pose swap)
  - burned Hindi captions (Noto Devanagari, large, wrapped, bottom)
"""
import os
import subprocess

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE, "output", "vidrush")
CHAR_DIR = os.path.join(BASE, "assets", "character")
FONT = "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
FONT_B = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"

# animated background: clean solid navy (no glow box to avoid odd square)
BG = "color=c=0x0a1626:s=1080x1920:d=1"


def _run(cmd):
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def build_animated_scene(scene_text, audio_path, out_path, duration, pose="host_neutral"):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    char_path = os.path.join(CHAR_DIR, "transparent", f"{pose}.png")
    if not os.path.exists(char_path):
        char_path = os.path.join(CHAR_DIR, f"{pose}.png")
    if not os.path.exists(char_path):
        char_path = os.path.join(CHAR_DIR, "transparent", "host_neutral.png")
    talk_path = os.path.join(CHAR_DIR, "transparent", "host_talk.png")
    if not os.path.exists(talk_path):
        talk_path = os.path.join(CHAR_DIR, "host_talk.png")

    def char_vf():
        return (
            f"[0:v]drawbox=x=0:y=0:w=1080:h=1920:t=0[bg];"
            f"[1:v]scale=756:-1[ch];"
            f"[bg][ch]overlay=(W-w)/2:(H-h*0.92)"
        )

    tmp_neutral = os.path.join(OUTPUT_DIR, "_an_neutral.mp4")
    tmp_talk = os.path.join(OUTPUT_DIR, "_an_talk.mp4")

    _run(["ffmpeg", "-y", "-f", "lavfi", "-i", BG,
          "-loop", "1", "-i", char_path, "-t", str(duration),
          "-filter_complex", char_vf(),
          "-c:v", "libx264", "-preset", "fast", "-b:v", "7M",
          "-pix_fmt", "yuv420p", "-an", tmp_neutral])

    _run(["ffmpeg", "-y", "-f", "lavfi", "-i", BG,
          "-loop", "1", "-i", talk_path, "-t", str(duration),
          "-filter_complex", char_vf(),
          "-c:v", "libx264", "-preset", "fast", "-b:v", "7M",
          "-pix_fmt", "yuv420p", "-an", tmp_talk])

    # fake lip-sync: swap every 0.3s
    concat = os.path.join(OUTPUT_DIR, "_an_lip.txt")
    with open(concat, "w") as f:
        segs = max(1, int(duration / 0.6))
        for i in range(segs):
            a, b = (tmp_talk, tmp_neutral) if i % 2 == 0 else (tmp_neutral, tmp_talk)
            f.write(f"file '{a}'\ninpoint 0\noutpoint 0.3\n")
            f.write(f"file '{b}'\ninpoint 0\noutpoint 0.3\n")

    tmp_base = os.path.join(OUTPUT_DIR, "_an_base.mp4")
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat,
          "-c", "copy", tmp_base])

    # burn Hindi caption (large, wrapped manually, bottom, Noto Devanagari)
    safe = scene_text.replace("'", "").replace(":", "").replace("\\", "").replace("%", "")
    # manual wrap: split into <=13 char lines for 1080 width
    words = safe.split()
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= 13:
            cur = (cur + " " + w).strip()
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    wrapped = "\\n".join(lines)
    y_off = 140 + len(lines) * 26
    cap = (
        f"drawtext=text='{wrapped}':fontfile='{FONT}':fontcolor=white:fontsize=46:"
        f"box=1:boxcolor=black@0.65:boxborderw=14:"
        f"x=(w-text_w)/2:y=h-text_h-{y_off}:line_spacing=10:"
        f"text_align=center"
    )
    _run(["ffmpeg", "-y", "-i", tmp_base, "-i", audio_path,
          "-filter_complex", f"[0:v]{cap}[v]",
          "-map", "[v]", "-map", "1:a",
          "-c:v", "libx264", "-preset", "fast", "-b:v", "7M",
          "-c:a", "aac", "-b:a", "192k", "-shortest", out_path])

    for t in (tmp_neutral, tmp_talk, concat, tmp_base):
        if os.path.exists(t):
            try: os.remove(t)
            except OSError: pass
    return out_path


if __name__ == "__main__":
    import edge_tts, asyncio, tempfile
    d = tempfile.mkdtemp()
    aud = os.path.join(d, "t.mp3")
    async def go():
        c = edge_tts.Communicate("नमस्ते! मैं पैसा भाई हूँ, आज बचत के जादू की बात करेंगे।", "hi-IN-SwaraNeural")
        await c.save(aud)
    asyncio.run(go())
    out = os.path.join(OUTPUT_DIR, "test_animated.mp4")
    p = build_animated_scene("नमस्ते! मैं पैसा भाई हूँ, आज बचत के जादू की बात करेंगे।", aud, out, 4.0, "host_neutral")
    print("built:", p, os.path.getsize(p) if os.path.exists(p) else 0)
