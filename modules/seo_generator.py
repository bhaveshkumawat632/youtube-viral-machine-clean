import random

POWER_WORDS_HI = ["SECRET", "SHOCKING", "99% Logon Ko Nahi Pata", "Asli Sach", "Chamatkar", "Warning", "Khulasa", "Zindagi Badal Dega"]
POWER_WORDS_EN = ["SECRET", "SHOCKING", "Nobody Tells You", "99% Don't Know", "Mind-Blowing", "Warning", "Exposed", "Life Changing"]

def generate_metadata(title, niche, language="hindi"):
    """
    Generate optimized YouTube SEO metadata.
    """
    power_words = POWER_WORDS_HI if language == "hindi" else POWER_WORDS_EN
    p_word = random.choice(power_words)
    
    # Title
    seo_title = f"🔴 {title} | {p_word} 🤯"
    if len(seo_title) > 100:
        seo_title = f"{title} | {p_word}"[:100]

    # Tags - comprehensive niche-specific tags
    base_tags = ["shorts", "youtubeshorts", "viral", "trending", niche]
    niche_tags = {
        "motivation": ["motivation", "success", "mindset", "quotes", "inspiration", "selfimprovement", "grindset"],
        "facts": ["facts", "amazingfacts", "knowledge", "didyouknow", "interesting", "science", "mindblown"],
        "horror": ["horror", "scary", "ghost", "mystery", "creepy", "truestory", "paranormal"],
        "tech": ["tech", "technology", "gadgets", "future", "ai", "coding", "innovation"],
        "money": ["money", "earning", "business", "finance", "wealth", "investing", "sidehustle"],
        "psychology": ["psychology", "darkpsychology", "mindset", "humanbehavior", "alpha", "mentalhealth"],
        "reddit_revenge": ["reddit", "revenge", "prorevenge", "pettyrevenge", "redditstories", "storytime", "drama", "justice"],
        "reddit_aita": ["reddit", "aita", "amithejerk", "redditstories", "storytime", "drama", "relationship", "family"],
        "reddit_drama": ["reddit", "drama", "redditstories", "storytime", "relationship", "toxicfamily", "inlaws", "marriage"],
    }
    
    # Extract clean words from title for tags
    title_words = [w.lower().strip("()[]{}!?.,") for w in title.split() if len(w) > 2 and w.lower() not in ("the", "and", "for", "with", "from")]
    tags = base_tags + niche_tags.get(niche, []) + title_words[:5]
    tags = list(set([t.lower().replace(" ", "") for t in tags if t]))[:30]
    
    # Hashtags - more strategic
    niche_specific = niche_tags.get(niche, [])[:2]
    hashtags = " ".join([f"#{t}" for t in ["shorts", "youtubeshorts", "viral"] + niche_specific])
    
    # Description - language-aware
    if language == "hindi":
        desc = f"""{seo_title}

Is video mein hum baat karenge: {title}. Agar aapko yeh {niche} content pasand aaya toh Like aur Subscribe zaroor karein!

{hashtags}

Queries Solved:
- {title} kya hai
- {niche} secrets 2026
- {p_word} facts
- Hindi {niche} stories
- Best {niche} videos 2026

Thanks for watching! 🙏
Subscribe for daily content! 🔔
"""
    else:
        desc = f"""{seo_title}

In this video we cover: {title}. If you enjoyed this {niche} content, hit Like and Subscribe!

{hashtags}

Related Topics:
- {title} explained
- {niche} secrets 2026
- {p_word} facts
- Best {niche} content 2026
- Must-watch {niche} videos

Thanks for watching! 🙏
Subscribe for daily content! 🔔
"""
    return {
        "title": seo_title,
        "description": desc,
        "tags": tags,
        "hashtags": hashtags
    }

def generate_thumbnail_text(title):
    words = title.split()
    if len(words) <= 3:
        return title
    return " ".join(words[:3]) + "..."
