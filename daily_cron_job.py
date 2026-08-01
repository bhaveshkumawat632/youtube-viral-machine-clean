import os
import sys
import time

sys.path.insert(0, '/home/junglee01/youtube-viral-machine')
from modules.trend_scraper import fetch_trending_topics
from generate_masterpiece import download_high_energy_clip, create_2026_masterpiece
from modules.quality_review import run_quality_review
from modules.upload_manager import upload_to_youtube, track_daily_metrics

def execute_daily_plan(niche="football"):
    print("\n" + "🔥"*25)
    print("📅 DAILY AUTOMATION PIPELINE INITIATED")
    print("🔥"*25)
    
    # 1. Research & Content Plan
    topic = fetch_trending_topics(niche)
    
    # 2. Download raw content based on trend
    raw_video = download_high_energy_clip(query=topic)
    
    # 3. Create fresh video
    print("\n🎬 [CONTENT CREATION] Injecting fresh script and rendering visuals...")
    final_video = create_2026_masterpiece(raw_video)
    
    # 4. Verify Quality and Copyright
    passed = run_quality_review(final_video)
    
    # 5. Upload & Optimize
    if passed:
        video_url = upload_to_youtube(final_video, niche=niche, title_hint=topic)
        track_daily_metrics(video_url)
        print("\n🏆 [SUCCESS] Daily workflow completed successfully.")
    else:
        print("\n🛑 [HALTED] Video failed quality review. Skipping upload. Alert sent to admin.")

if __name__ == "__main__":
    target_niche = sys.argv[1] if len(sys.argv) > 1 else "football"
    execute_daily_plan(target_niche)
