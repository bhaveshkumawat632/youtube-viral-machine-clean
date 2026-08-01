import os
import requests
import random
import time

def search_and_download_pexels_videos(search_terms, output_dir, pexels_api_key=None, video_format="shorts", target_duration=30):
    """
    Search Pexels for videos matching search terms, download them, and return a list of local file paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    downloaded_files = []
    
    if not pexels_api_key:
        print("⚠️ No Pexels API key provided. Visual generation will fall back to gradients/local assets.")
        return downloaded_files

    headers = {
        "Authorization": pexels_api_key
    }
    
    orientation = "portrait" if video_format == "shorts" else "landscape"
    
    # We want to fill target_duration. Each clip can be 5-10 seconds.
    # We loop through search terms and download one video for each until we have enough.
    clips_needed = max(3, int(target_duration / 6))
    
    # Deduplicate search terms
    unique_terms = []
    for term in search_terms:
        term = term.strip().lower()
        if term and term not in unique_terms:
            unique_terms.append(term)
            
    if not unique_terms:
        unique_terms = ["cinematic", "nature", "abstract"]
        
    print(f"🔍 Searching Pexels for terms: {unique_terms} (format: {video_format})")
    
    term_idx = 0
    downloaded_duration = 0
    
    while downloaded_duration < target_duration and len(downloaded_files) < clips_needed:
        # Get next term (loop around if needed)
        term = unique_terms[term_idx % len(unique_terms)]
        term_idx += 1
        
        # Pexels Video Search API
        url = f"https://api.pexels.com/videos/search?query={requests.utils.quote(term)}&per_page=5&orientation={orientation}"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                videos = data.get("videos", [])
                if not videos:
                    print(f"   ℹ️ No videos found on Pexels for '{term}'")
                    continue
                
                # Pick a random video from the top results to avoid repetition
                video = random.choice(videos[:3])
                
                # Find a suitable video file link
                video_files = video.get("video_files", [])
                # Prefer hd/sd links
                video_url = None
                
                # Sort video files by resolution to find the best match
                # For Shorts, we prefer smaller files that are portrait
                for vf in sorted(video_files, key=lambda x: x.get("width", 0)):
                    link = vf.get("link")
                    if link and ".mp4" in link:
                        video_url = link
                        break
                
                if video_url:
                    filename = f"pexels_{int(time.time())}_{random.randint(1000, 9999)}.mp4"
                    filepath = os.path.join(output_dir, filename)
                    
                    print(f"   📥 Downloading clip for '{term}': {video_url[:60]}...")
                    vid_resp = requests.get(video_url, stream=True, timeout=15)
                    if vid_resp.status_code == 200:
                        with open(filepath, 'wb') as f:
                            for chunk in vid_resp.iter_content(chunk_size=1024*1024):
                                if chunk:
                                    f.write(chunk)
                        
                        downloaded_files.append(filepath)
                        # Assume average of 8 seconds per clip if duration is not in API response
                        dur = video.get("duration", 8)
                        downloaded_duration += dur
                        print(f"   ✅ Saved clip to {filepath} ({dur}s)")
                    else:
                        print(f"   ❌ Failed to download video from {video_url}")
                else:
                    print(f"   ❌ No mp4 file found for video {video.get('id')}")
            else:
                print(f"   ❌ Pexels API returned status code {response.status_code} for '{term}'")
        except Exception as e:
            print(f"   ❌ Error searching Pexels for '{term}': {e}")
            
        # Add a tiny delay to be polite to the API
        time.sleep(0.5)
        
    return downloaded_files
