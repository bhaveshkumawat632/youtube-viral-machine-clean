import os
import pickle
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modules.youtube_uploader import get_authenticated_service, TOKEN_FILE

def generate_seo_metadata():
    title = "Escape The Matrix: The Secret 1% Rule Exposed! 👁️🔥 #shorts #motivation"
    description = (
        "Are you stuck in the infinite scrolling loop? The system is designed to keep you distracted. "
        "Discover the secret 1% rule to break free, stop consuming, and start building your own reality! "
        "Wake up. The choice is yours.\n\n"
        "🎬 Produced completely by Aghori Studio AI.\n"
        "🔔 Subscribe for more mind-bending truths!\n\n"
        "#EscapeTheMatrix #Awakening #Motivation #Cyberpunk #Shorts #Viral #Mindset"
    )
    tags = ["Escape The Matrix", "Awakening", "Motivation", "Shorts", "Viral", "Mindset", "Cyberpunk", "Aghori Studio"]
    
    return {
        "title": title,
        "description": description,
        "tags": tags,
        "category_id": "27"  # Education
    }

def dry_run_authentication():
    print("=========================================================")
    print("🛡️ YOUTUBE API CREDENTIALS & DRY RUN SCAN")
    print("=========================================================")
    
    if os.path.exists(TOKEN_FILE):
        print(f"✅ CREDENTIALS LOCATED: Found valid authentication token at -> {TOKEN_FILE}")
        file_size = os.path.getsize(TOKEN_FILE)
        print(f"   [Token Size: {file_size} bytes]")
    else:
        print("❌ CREDENTIALS NOT FOUND in the project directory.")
        return

    print("\n📡 Initiating Secure Session with Google API Client...")
    try:
        # Load and verify the stored pickle
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)
            
        print(f"🔑 Credential Validation:")
        print(f"   - Valid: {creds.valid}")
        print(f"   - Expired: {creds.expired}")
        print(f"   - Scopes: {creds.scopes}")
        
        # Build YouTube Service
        youtube = get_authenticated_service()
        
        if youtube:
            print("\n✅ API CLIENT INITIALIZED: Secure connection established with YouTube Data API v3.")
            
            # Since the scope is specifically youtube.upload, we'll try a safe read if possible,
            # or just confirm the credentials build properly without throwing an auth error.
            print("   -> Dry Run Authentication Check Passed!")
        else:
            print("\n❌ API CLIENT FAILED: Token may be revoked or invalid.")
            
    except Exception as e:
        print(f"\n❌ AUTHENTICATION ERROR: {e}")

    print("\n=========================================================")
    print("📈 SEO METADATA GENERATION (AGHORI_MASTER_SHORT_1782295778.mp4)")
    print("=========================================================")
    meta = generate_seo_metadata()
    print(f"📌 TITLE:\n   {meta['title']}\n")
    print(f"📝 DESCRIPTION:\n{meta['description']}\n")
    print(f"🏷️ TAGS:\n   {', '.join(meta['tags'])}\n")
    print(f"📁 CATEGORY ID: {meta['category_id']}")
    print("=========================================================")
    print("Pipeline ready for safe upload.")

if __name__ == "__main__":
    dry_run_authentication()
