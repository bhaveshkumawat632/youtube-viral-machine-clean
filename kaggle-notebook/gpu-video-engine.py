#!/usr/bin/env python3
"""
🚀 YouTube Viral Machine — Kaggle P100 GPU Video Engine
Generates proper animated video clips using LTX Video AI model.
Exposes Gradio API for remote pipeline connection.
"""

import sys
# Force stdout and stderr to be unbuffered
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(line_buffering=True)

# ============================================================
# STEP 1: Install Dependencies
# ============================================================
import subprocess

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", package])

print("📦 Installing dependencies...")
install("diffusers")
install("transformers")
install("accelerate")
install("gradio")
install("safetensors")
install("sentencepiece")
install("protobuf")
print("✅ All dependencies installed!")

# ============================================================
# STEP 2: GPU Check
# ============================================================
import torch
import gc

print("\n🔍 Checking GPU...")
if torch.cuda.is_available():
    gpu_name = torch.cuda.get_device_name(0)
    gpu_mem = torch.cuda.get_device_properties(0).total_mem / (1024**3)
    print(f"✅ GPU Found: {gpu_name} ({gpu_mem:.1f} GB VRAM)")
else:
    print("❌ No GPU! Enable in Settings → Accelerator → GPU P100")
    raise RuntimeError("GPU Required!")

# ============================================================
# STEP 3: Load LTX Video Model
# ============================================================
print("\n📦 Loading LTX Video Model (2-3 min first time)...")

from diffusers import LTXPipeline
from diffusers.utils import export_to_video
import tempfile
import os

pipe = LTXPipeline.from_pretrained(
    "Lightricks/LTX-Video",
    torch_dtype=torch.float16,
    variant="fp16"
)
pipe.to("cuda")
pipe.enable_model_cpu_offload()

print("✅ LTX Video Model loaded on GPU!")

# ============================================================
# STEP 4: Video Generation Function
# ============================================================
def generate_video(prompt, num_frames=49, num_inference_steps=25):
    """Generate animated video from text prompt."""
    print(f"\n🎬 Generating: '{prompt[:80]}...'")
    
    enhanced = f"{prompt}, cinematic lighting, hyperrealistic, 4k, smooth motion"
    negative = "worst quality, blurry, jittery, distorted, text, watermark, static"
    
    try:
        frames = pipe(
            prompt=enhanced,
            negative_prompt=negative,
            num_frames=int(num_frames),
            width=512,
            height=768,
            num_inference_steps=int(num_inference_steps),
            guidance_scale=7.5,
        ).frames[0]
        
        out_path = os.path.join(tempfile.gettempdir(), "generated_video.mp4")
        export_to_video(frames, out_path, fps=24)
        
        size_kb = os.path.getsize(out_path) / 1024
        print(f"✅ Done! Size: {size_kb:.0f} KB")
        
        torch.cuda.empty_cache()
        gc.collect()
        
        return out_path
    except Exception as e:
        print(f"❌ Error: {e}")
        torch.cuda.empty_cache()
        gc.collect()
        return None

# ============================================================
# STEP 5: Launch Gradio API (Public URL)
# ============================================================
import gradio as gr

print("\n🌐 Starting Gradio API Server...")
print("=" * 50)
print("⏳ Wait for the public URL to appear below...")
print("=" * 50)

demo = gr.Interface(
    fn=generate_video,
    inputs=[
        gr.Textbox(label="Scene Prompt"),
        gr.Slider(16, 81, value=49, step=1, label="Frames"),
        gr.Slider(10, 50, value=25, step=1, label="Steps"),
    ],
    outputs=gr.Video(label="Generated Video"),
    title="🎬 YouTube Viral Machine — GPU Video Engine",
)

_, _, share_url = demo.launch(share=True, debug=False)
print(f"📡 Generated share URL: {share_url}")

# Send the share URL back to the local backend server via Cloudflare tunnel
import urllib.request
import json
try:
    print("📡 Reporting share URL to host...")
    url = "https://areas-tracy-signatures-grants.trycloudflare.com/api/set-gradio-url"
    req = urllib.request.Request(
        url,
        data=json.dumps({"gradio_url": share_url}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        print(f"✅ Host response: {response.read().decode()}")
except Exception as e:
    print(f"❌ Failed to report share URL: {e}")
