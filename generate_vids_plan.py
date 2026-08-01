import json

topics = [
    "5 Mind-Blowing Psychological Facts About Attraction",
    "The Dark Truth About Dopamine Detox",
    "How to Read Anyone's Mind in 5 Seconds",
    "3 Signs You Are Secretly a Genius",
    "The FBI Body Language Trick (Mirroring)",
    "Why Silence is the Most Powerful Weapon",
    "The Baader-Meinhof Phenomenon Explained",
    "3 Habits That Are Destroying Your Brain",
    "How to Win Any Argument Instantly",
    "The Mandela Effect: Is Reality Broken?",
    "Why 99% of People Fail in Life",
    "The Secret Psychology of Colors",
    "How to Tell if Someone is Lying to You",
    "The Law of Attraction: Does it Actually Work?",
    "3 Things Your Dreams Reveal About You",
    "The Halo Effect: Why Looks Matter",
    "How to Stop Overthinking in 60 Seconds",
    "The Dark Psychology of Manipulation",
    "Why Smart People Have Fewer Friends",
    "The Placebo Effect: Your Mind Can Heal You",
    "3 Signs Someone is Secretly Jealous of You",
    "The Bystander Effect: Why No One Helps",
    "How to Build Unbreakable Confidence",
    "The Zeigarnik Effect: Why We Forget",
    "3 Psychological Tricks to Make Anyone Like You",
    "Why We Procrastinate (And How to Stop)",
    "The Truth About Introverts vs Extroverts",
    "How to Rewire Your Brain for Success",
    "The Psychology of Addictive TikToks",
    "3 Signs You Have High Emotional Intelligence"
]

with open("30_Days_Google_Vids_Plan.md", "w") as f:
    f.write("# 🚀 30-Day Google Vids Master Plan (Viral YouTube Shorts)\n\n")
    f.write("Welcome to the Ultimate Google Vids Content Calendar. Copy and paste the **Google Vids Master Prompt** and the **Voiceover Script** into Google Vids for each day.\n\n")
    
    for i, topic in enumerate(topics):
        day = i + 1
        prompt = f"Create a highly engaging, fast-paced vertical video about '{topic}'. Use premium cinematic stock footage of human characters and abstract elements. Dark, moody, and hyper-realistic style. Add dynamic transitions and text overlays for every sentence."
        
        script = f"""1. "Did you know that..." (Start with a strong hook about {topic})
2. "Studies show that..." (Provide the core mind-blowing fact)
3. "This happens because..." (Explain the psychology briefly)
4. "But the crazy part is..." (Give the twist or practical application)
5. "Subscribe for more psychological secrets!" (Call to action)"""

        f.write(f"## Day {day}: {topic}\n")
        f.write(f"**Google Vids Master Prompt (Paste this in the main prompt box):**\n> {prompt}\n\n")
        f.write(f"**Voiceover Script (Paste this in the script section):**\n```text\n{script}\n```\n\n")
        f.write("---\n\n")

print("Generated 30_Days_Google_Vids_Plan.md")
