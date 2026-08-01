import json
import time
from modules.llm_script_generator import generate_powerful_script

topics = [
    "Dark Psychology of Body Language", "How to tell if someone is lying", 
    "The Halo Effect Explained", "Why silence is powerful", 
    "How to read minds instantly", "The Baader-Meinhof Phenomenon",
    "Zeigarnik Effect - Why we can't forget", "Placebo Effect in real life",
    "How to win any argument", "The Dunning-Kruger Effect",
    "3 Signs of a genius", "Why smart people have fewer friends",
    "How to build extreme confidence", "The secret psychology of colors",
    "Bystander Effect explained", "Why we procrastinate",
    "Introverts vs Extroverts psychology", "How to rewire your brain",
    "Addiction psychology of TikTok", "High Emotional Intelligence signs",
    "The Mandela Effect", "Paradox of Choice", "Stockholm Syndrome",
    "Imposter Syndrome", "Confirmation Bias", "Cognitive Dissonance",
    "Pygmalion Effect", "Hawthorne Effect", "Halo vs Horn Effect",
    "Spotlight Effect"
]

with open("Google_Vids_30_Days_MasterPlan.txt", "w", encoding="utf-8") as f:
    f.write("🚀 30-DAY GOOGLE VIDS MASTER SCRIPT PLAN 🚀\n")
    f.write("================================================\n\n")

for i, topic in enumerate(topics):
    print(f"Generating day {i+1}...")
    try:
        script_data = generate_powerful_script(topic=topic, language="english")
        title = script_data.get('title', topic)
        scenes = script_data.get('scenes', [])
        
        full_text = " ".join([s['text'] for s in scenes])
        visual_prompt = scenes[0]['visual_prompt'] if scenes else "Cinematic hyperrealistic footage of characters."
        
        with open("Google_Vids_30_Days_MasterPlan.txt", "a", encoding="utf-8") as f:
            f.write(f"DAY {i+1}: {title}\n")
            f.write("-" * 40 + "\n")
            f.write(f"▶ GOOGLE VIDS PROMPT (Paste this in the main box):\n")
            f.write(f"Create a fast-paced viral YouTube Shorts vertical video about '{title}'. Visual Style: {visual_prompt} Use dark moody cinematic lighting, high-quality stock footage of humans, and engaging dynamic transitions.\n\n")
            f.write(f"▶ VOICEOVER SCRIPT (Paste this in the script/audio section):\n")
            f.write(f"{full_text}\n\n")
            f.write("=" * 60 + "\n\n")
        time.sleep(2)
    except Exception as e:
        print(f"Error on {topic}: {e}")

print("Done! Saved to Google_Vids_30_Days_MasterPlan.txt")
