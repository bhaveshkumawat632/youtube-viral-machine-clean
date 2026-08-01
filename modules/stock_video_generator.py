import os
import time
import requests

def get_pexels_video(query, output_path):
    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        raise ValueError("PEXELS_API_KEY environment variable is missing. Cannot fetch stock footage.")

    url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&per_page=1"
    headers = {"Authorization": api_key}
    
    print(f"🔍 Searching Pexels for: '{query}'")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise RuntimeError(f"Pexels API Error: {response.status_code} - {response.text}")
        
    data = response.json()
    if not data.get("videos"):
        raise RuntimeError(f"No Pexels videos found for query: '{query}'")
        
    video_files = data["videos"][0]["video_files"]
    
    # Sort by height to get HD (preferably 1920 height)
    best_file = None
    for file in sorted(video_files, key=lambda x: x.get('height', 0), reverse=True):
        if file['link'].endswith('.mp4'):
            best_file = file['link']
            break
            
    if not best_file:
        best_file = video_files[0]['link']
        
    print(f"⬇️ Downloading Pexels video from: {best_file}")
    vid_response = requests.get(best_file, stream=True)
    with open(output_path, "wb") as f:
        for chunk in vid_response.iter_content(chunk_size=8192):
            f.write(chunk)
            
    return output_path
