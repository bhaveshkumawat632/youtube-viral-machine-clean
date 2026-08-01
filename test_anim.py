import sys
import os
import subprocess
sys.path.insert(0, '/home/junglee01/youtube-viral-machine')
from modules.animated_builder import build_animated_scene
import edge_tts, asyncio, tempfile

async def go():
    d = "/home/junglee01/youtube-viral-machine/output/vidrush"
    aud = os.path.join(d, "t.mp3")
    c = edge_tts.Communicate("नमस्ते! मैं पैसा भाई हूँ", "hi-IN-SwaraNeural")
    await c.save(aud)
    out = os.path.join(d, "test_animated2.mp4")
    build_animated_scene("नमस्ते", aud, out, 4.0, "host_neutral")

asyncio.run(go())
