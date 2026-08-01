import os
import urllib.parse
import requests
import time
import random

# Monkey-patch DNS resolution for image.pollinations.ai due to local network DNS issues
try:
    import urllib3.util.connection as connection
    orig_create_connection = connection.create_connection
    def patched_create_connection(address, *args, **kwargs):
        host, port = address
        if host == "image.pollinations.ai":
            # Cloudflare IPs for image.pollinations.ai resolved via public Google DNS API
            host = random.choice(["172.67.173.121", "104.21.30.173"])
        return orig_create_connection((host, port), *args, **kwargs)
    connection.create_connection = patched_create_connection
except Exception as e:
    print(f"⚠️ Failed to apply DNS patch: {e}")

def get_pollinations_image(prompt, output_path):
    print(f"🎨 Generating Image via Pollinations AI for: '{prompt}'")
    encoded_prompt = urllib.parse.quote(prompt)
    
    # We use random seeds to load-balance across backend GPUs
    seed = random.randint(1, 999999)
    
    # We omit custom width/height to bypass custom resizing queues on Pollinations servers.
    # FFmpeg will handle the scaling to vertical HD anyway!
    endpoints = [
        f"https://image.pollinations.ai/prompt/{encoded_prompt}?nologo=true&seed={seed}&private=true",
        f"https://image.pollinations.ai/prompt/{encoded_prompt}?nologo=true&seed={seed}"
    ]

    max_retries = 1
    for attempt in range(max_retries):
        for url in endpoints:
            try:
                print(f"   Trying endpoint: {url[:60]}... (Attempt {attempt+1}/{max_retries})")
                # Increased timeout to 40 seconds to give the server ample time to respond
                response = requests.get(url, stream=True, timeout=40)
                content_type = response.headers.get("content-type", "")
                if response.status_code == 200 and "image" in content_type:
                    with open(output_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"✅ Image downloaded successfully to: {output_path}")
                    return output_path
                else:
                    print(f"   ⚠️ Endpoint returned status {response.status_code} or invalid content-type '{content_type}'")
            except Exception as e:
                print(f"   ⚠️ Endpoint failed: {e}")
        
        print("⏳ All endpoints failed or overloaded. Waiting 4 seconds before retry...")
        time.sleep(4)
        
    raise RuntimeError(f"Failed to generate image via Pollinations AI after {max_retries} attempts.")
