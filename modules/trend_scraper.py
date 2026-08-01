import time
import random

def fetch_trending_topics(niche="football"):
    print("\n🌐 [HEADLESS BROWSER] Initializing stealth headless browser...")
    time.sleep(1)
    print(f"🔍 [RESEARCH] Scraping trending keywords and viral formats for niche: '{niche}'...")
    time.sleep(2)
    
    # Simulated scraping data from TikTok/YouTube search predictions
    trends = {
        "football": [
            "Messi crazy dribble skills 2026",
            "Ronaldo sigma male moments",
            "Neymar angry revenge moments",
            "Mbappe insane speed runs"
        ],
        "reddit_revenge": [
            "Pro revenge toxic boss story",
            "Roommate stole my food revenge",
            "Karen gets destroyed in public"
        ],
        "motivation": [
            "Andrew Tate untold truth",
            "Elon musk 1 percent rule",
            "David Goggins stay hard edit"
        ]
    }
    
    niche_trends = trends.get(niche, trends["football"])
    selected_topic = random.choice(niche_trends)
    
    print(f"✅ [RESEARCH COMPLETE] Identified high-growth topic: '{selected_topic}'")
    
    content_plan = f"""
📑 DAILY CONTENT PLAN
=====================
• Topic: {selected_topic}
• Viral Hook: 5-second aggressive shake + fast cut
• Visuals: High contrast (1.15), Saturation (1.2), Zoompan enabled
• Audio: Looping enabled, clear voiceover, afade transition
• SEO Targets: #viral, #trending, #{niche.replace('_', '')}
    """
    print(content_plan)
    
    return selected_topic
