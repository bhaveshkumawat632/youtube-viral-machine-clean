import time
import random
from duckduckgo_search import DDGS

def get_live_seo_data(topic, niche):
    print("\n🌐 [WEB SCRAPER] Connecting to live web to search for trending hashtags and titles...")
    time.sleep(1)
    
    query = f"trending {niche} youtube shorts hashtags titles {time.strftime('%Y')}"
    print(f"🔍 Searching: '{query}'")
    
    results = []
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
    except Exception as e:
        print(f"⚠️ Web search failed: {e}. Falling back to internal generator.")
        
    # Extract some words from search results to simulate dynamic tags
    dynamic_tags = []
    if results:
        for res in results:
            words = res.get('body', '').split()
            tags = [w.strip('.,!?"\'') for w in words if len(w) > 4]
            dynamic_tags.extend(tags)
            
    # Clean up and select the best ones
    dynamic_tags = list(set([t.lower() for t in dynamic_tags if t.isalpha()]))
    
    # Mix with essential tags
    essential_tags = ['viral', 'trending', 'shorts', 'youtubeshorts', niche.replace('_', '')]
    final_tags = essential_tags + random.sample(dynamic_tags, min(5, len(dynamic_tags)))
    
    # Generate dynamic description
    description = f"🔥 Watch the latest viral {niche} moment: {topic}!\n\n"
    if results:
        description += f"Based on trending data, this is exactly what everyone is talking about.\n"
    description += f"Don't forget to Like & Subscribe for more daily {niche} updates!\n\n"
    description += " ".join([f"#{t}" for t in final_tags])
    
    title = f"🔴 {topic} | You Won't Believe This 🤯"
    
    return {
        "title": title,
        "description": description,
        "tags": final_tags
    }

if __name__ == "__main__":
    data = get_live_seo_data("Ronaldo sigma male", "football")
    print(data)
