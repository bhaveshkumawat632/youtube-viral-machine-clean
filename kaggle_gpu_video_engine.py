# ============================================================
# 🚀 KAGGLE GPU VIDEO GENERATOR — Copy-Paste into Kaggle Notebook
# ============================================================
# INSTRUCTIONS:
# 1. Go to kaggle.com → New Notebook
# 2. Turn ON GPU: Settings → Accelerator → GPU P100
# 3. Paste this ENTIRE code into a single cell
# 4. Click "Run All"
# 5. Copy the Gradio URL that appears (ends with .gradio.live)
# 6. Paste that URL into: youtube-viral-machine/config.py → PRIVATE_API_URL
# ============================================================

# Step 1: Install dependencies
# NOTE: In Kaggle/Jupyter, use: !pip install -q torch torchvision diffusers transformers accelerate gradio safetensors sentencepiece protobuf
# For local use, install via requirements.txt or pip manually.
try:
    import torch  # noqa: F401
    import gradio  # noqa: F401
except ImportError:
    raise RuntimeError("kaggle_gpu_video_engine.py requires torch and gradio. Install via pip first.")

import torch
import gradio as gr
import tempfile
import os
import gc

print("🔍 Checking GPU...")
if torch.cuda.is_available():
    gpu_name = torch.cuda.get_device_name(0)
    gpu_mem = torch.cuda.get_device_properties(0).total_mem / (1024**3)
    print(f"✅ GPU Found: {gpu_name} ({gpu_mem:.1f} GB VRAM)")
else:
    print("❌ No GPU detected! Enable GPU in Settings → Accelerator → GPU P100")
    raise RuntimeError("GPU Required!")

# Step 2: Load LTX Video Model (Lightweight, fits in 16GB VRAM)
print("\n📦 Loading LTX Video Model... (this takes 2-3 minutes first time)")

from diffusers import LTXPipeline
from diffusers.utils import export_to_video

pipe = LTXPipeline.from_pretrained(
    "Lightricks/LTX-Video",
    torch_dtype=torch.float16,
    variant="fp16"
)
pipe.to("cuda")
pipe.enable_model_cpu_offload()  # Save VRAM by offloading when not needed

print("✅ Model loaded successfully!")

# Step 3: Video Generation Function
def generate_video(prompt, num_frames=49, num_inference_steps=30):
    """Generate a video from text prompt."""
    print(f"\n🎬 Generating video for prompt: '{prompt[:80]}...'")
    
    # Enhance prompt for better quality
    enhanced_prompt = f"{prompt}, cinematic lighting, hyperrealistic, 4k quality, smooth motion, professional cinematography"
    negative_prompt = "worst quality, blurry, jittery, distorted, text, watermark, static, low quality"
    
    try:
        # Generate video frames
        video_frames = pipe(
            prompt=enhanced_prompt,
            negative_prompt=negative_prompt,
            num_frames=num_frames,
            width=512,
            height=768,  # Vertical (9:16 ratio for Shorts)
            num_inference_steps=num_inference_steps,
            guidance_scale=7.5,
        ).frames[0]
        
        # Save to temp file
        output_path = os.path.join(tempfile.gettempdir(), "generated_video.mp4")
        export_to_video(video_frames, output_path, fps=24)
        
        file_size = os.path.getsize(output_path) / 1024
        print(f"✅ Video generated! Size: {file_size:.0f} KB")
        
        # Clean up GPU memory
        torch.cuda.empty_cache()
        gc.collect()
        
        return output_path
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        torch.cuda.empty_cache()
        gc.collect()
        return None

# Step 4: Launch Gradio API Server
print("\n🌐 Starting Gradio API Server...")

demo = gr.Interface(
    fn=generate_video,
    inputs=[
        gr.Textbox(label="Prompt", placeholder="Describe the video scene..."),
        gr.Slider(minimum=16, maximum=81, value=49, step=1, label="Number of Frames"),
        gr.Slider(minimum=10, maximum=50, value=25, step=1, label="Inference Steps"),
    ],
    outputs=gr.Video(label="Generated Video"),
    title="🎬 YouTube Viral Machine — Kaggle GPU Video Engine",
    description="Paste your scene prompt and generate animated video clips!",
)

# share=True creates a public URL that our pipeline can connect to
demo.launch(share=True, debug=True)
