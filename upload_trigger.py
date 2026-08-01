import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modules.youtube_uploader import upload_video

master_output = "/home/junglee01/youtube-viral-machine/output/AGHORI_MASTER_SHORT_1782411893.mp4"

meta = {
    "title": "Escape The Matrix: The Secret 1% Rule Exposed! 👁️🔥 #shorts #motivation",
    "description": "Stop scrolling. Start building. Awaken from the simulation.\\n\\n🎬 Produced perfectly by Aghori Studio AI.\\n#EscapeTheMatrix #Awakening #Motivation",
    "tags": ["Escape The Matrix", "Awakening", "Motivation", "Shorts", "Viral", "Cyberpunk", "Aghori Studio"],
    "category_id": "27"
}

success = upload_video(master_output, meta)
if success:
    print(f"✅ Upload Complete for {master_output}")
else:
    print(f"❌ Upload Failed for {master_output}")
