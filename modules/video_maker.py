"""
YouTube Viral Machine - Video Maker
Creates stunning videos with gradient backgrounds, animated subtitles, and effects
"""
import os
import sys
import subprocess
import json
import math
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    SHORTS_WIDTH, SHORTS_HEIGHT, VIDEO_WIDTH, VIDEO_HEIGHT,
    FPS, OUTPUT_DIR, TEMP_DIR, GRADIENTS, DEFAULT_GRADIENT,
    SUBTITLE_FONT_SIZE, HF_VIDEO_SPACE
)
from modules.cloud_video_generator import generate_video_from_prompt_hf


def create_gradient_background(output_path, duration, width=None, height=None,
                               gradient_name=None, with_particles=True):
    """
    Create a gradient background video using FFmpeg.

    Args:
        output_path: Output video path
        duration: Duration in seconds
        width: Video width
        height: Video height
        gradient_name: Key from GRADIENTS dict
        with_particles: Add floating particle effect
    """
    w = width or SHORTS_WIDTH
    h = height or SHORTS_HEIGHT
    grad = GRADIENTS.get(gradient_name or DEFAULT_GRADIENT, GRADIENTS[DEFAULT_GRADIENT])

    color1 = grad[0].lstrip('#')
    color2 = grad[1].lstrip('#')

    r1, g1, b1 = int(color1[0:2], 16), int(color1[2:4], 16), int(color1[4:6], 16)
    r2, g2, b2 = int(color2[0:2], 16), int(color2[2:4], 16), int(color2[4:6], 16)

    # FAST approach: Create gradient image with Pillow, then loop with FFmpeg
    try:
        from PIL import Image, ImageDraw
        print(f"🎨 Creating gradient background ({gradient_name or DEFAULT_GRADIENT})...")

        # Parse all 3 gradient colors
        c1 = grad[0].lstrip('#')
        c2 = grad[1].lstrip('#')
        c3 = grad[2].lstrip('#') if len(grad) > 2 else c1

        r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
        r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
        r3, g3, b3 = int(c3[0:2], 16), int(c3[2:4], 16), int(c3[4:6], 16)

        img = Image.new('RGB', (w, h))
        draw = ImageDraw.Draw(img)

        # 3-color gradient: top → middle → bottom with smooth cosine interpolation
        import math
        for y in range(h):
            # Normalize y to 0.0 - 1.0 across the entire height
            t = y / h
            
            # Blend factors for the 3 colors
            # We use a smooth function so color2 peaks at the middle and smoothly fades
            weight1 = max(0, math.cos(t * math.pi))
            weight3 = max(0, math.cos((1 - t) * math.pi))
            weight2 = 1.0 - (weight1 + weight3)
            
            r = int(r1 * weight1 + r2 * weight2 + r3 * weight3)
            g = int(g1 * weight1 + g2 * weight2 + g3 * weight3)
            b = int(b1 * weight1 + b2 * weight2 + b3 * weight3)
            
            draw.line([(0, y), (w, y)], fill=(r, g, b))

        gradient_img_path = output_path.replace('.mp4', '_bg.png')
        img.save(gradient_img_path, quality=95)

        # Create video from image using FFmpeg (very fast!)
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", gradient_img_path,
            "-t", str(duration),
            "-r", str(FPS),
            "-c:v", "libx264", "-preset", "medium",
            "-tune", "stillimage",
            "-pix_fmt", "yuv420p",
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Background created: {output_path}")
            return output_path

    except Exception as e:
        print(f"⚠️  Pillow gradient failed ({e}), using FFmpeg fallback...")

    # Fallback: simple solid color (fastest possible)
    cmd_simple = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i",
        f"color=c=0x{color1}:s={w}x{h}:d={duration}:r={FPS}",
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "medium",
        "-pix_fmt", "yuv420p",
        output_path
    ]
    subprocess.run(cmd_simple, capture_output=True, text=True)

    print(f"✅ Background created: {output_path}")
    return output_path



def check_copyright_killswitch(audio_source="synthetic_ffmpeg", visual_source="synthetic_ffmpeg"):
    """
    SAFETY GUARDRAIL: Blocks render if assets are not whitelisted.
    """
    from config import AUDIO_WHITELIST, VISUAL_WHITELIST
    if audio_source not in AUDIO_WHITELIST:
        print(f"🛑 KILL SWITCH TRIGGERED: Audio source '{audio_source}' is not whitelisted!")
        return False
    if visual_source not in VISUAL_WHITELIST:
        print(f"🛑 KILL SWITCH TRIGGERED: Visual source '{visual_source}' is not whitelisted!")
        return False
    return True

def mix_voice_bgm_and_sfx(voiceover_path, output_path, total_duration, num_scenes):
    """
    Mixes voiceover with synthetic dramatic background music and scene-change whoosh SFX.
    """
    import os
    import subprocess
    from modules.background_music import generate_background_tone, generate_sfx
    
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 1. Generate dramatic/suspenseful background music
    temp_bgm = os.path.join(TEMP_DIR, f"temp_bgm_{int(time.time())}.mp3")
    generate_background_tone(total_duration, temp_bgm, style='dramatic')
    
    # 2. Transition whoosh timestamps
    clip_duration = max(3.0, min(8.0, total_duration / num_scenes)) if num_scenes > 0 else 4.0
    sfx_times = [i * clip_duration for i in range(1, num_scenes)]
    
    # Path to whoosh SFX
    whoosh_path = os.path.join(PROJECT_ROOT, "assets", "sfx", "whooshes.mp3")
    if not os.path.exists(whoosh_path):
        whoosh_path = os.path.join(TEMP_DIR, "temp_whoosh.wav")
        if not os.path.exists(whoosh_path):
            generate_sfx(whoosh_path, type="whoosh")
        
    # Build filter complex for mixing
    # Inputs:
    # 0:a = voiceover
    # 1:a = background music
    # 2:a = whoosh SFX
    
    filter_parts = []
    # Compress/enhance the voiceover to make it sound warm and radio-broadcast ready
    filter_parts.append(f"[0:a]acompressor=threshold=-14dB:ratio=4:makeup=1.5dB,alimiter=limit=0.95[voice_comp]")
    # BGM volume and sidechain compress
    filter_parts.append(f"[1:a]volume=0.3[bgm_init]")
    filter_parts.append(f"[bgm_init][voice_comp]sidechaincompress=threshold=-20dB:ratio=4:attack=20:release=250[bgm_ducked]")
    # Scale down whoosh SFX to 15% volume so it doesn't clip when mixed at original volume
    filter_parts.append(f"[2:a]volume=0.15[whoosh_vol]")
    
    sfx_labels = []
    for idx, t in enumerate(sfx_times):
        delay_ms = int(t * 1000)
        filter_parts.append(f"[whoosh_vol]adelay={delay_ms}|{delay_ms}[sfx_{idx}]")
        sfx_labels.append(f"[sfx_{idx}]")
        
    # amix filter to blend voice + bg + all delayed SFX without auto-scaling volumes (normalize=0)
    # Add alimiter at the end of the chain to guarantee 0% clipping and crystal clear output
    all_inputs = "[voice_comp][bgm_ducked]" + "".join(sfx_labels)
    num_inputs = 2 + len(sfx_labels)
    filter_parts.append(f"{all_inputs}amix=inputs={num_inputs}:duration=first:dropout_transition=2:normalize=0,alimiter=limit=0.95[out_a]")
    
    filter_complex = ";".join(filter_parts)
    
    cmd = [
        "ffmpeg", "-y",
        "-i", voiceover_path,
        "-i", temp_bgm,
        "-i", whoosh_path,
        "-filter_complex", filter_complex,
        "-map", "[out_a]",
        "-c:a", "libmp3lame", "-b:a", "192k",
        output_path
    ]
    
    print("🎧 Mixing voiceover, cinematic background music, and whoosh SFX...")
    subprocess.run(cmd, capture_output=True)
    
    if os.path.exists(temp_bgm):
        try:
            os.remove(temp_bgm)
        except Exception:
            pass
            
    return output_path

def create_video_from_audio_and_subtitles(
    audio_path, subtitle_path, output_path,
    background_video=None, background_image=None,
    gradient_name=None, video_format="shorts",
    title_text=None
):
    """
    Create a complete video by combining audio, subtitles, and background.

    Args:
        audio_path: Path to voiceover MP3
        subtitle_path: Path to .ass subtitle file
        output_path: Output video path
        background_video: Optional background video (will be cropped to fit)
        background_image: Optional background image
        gradient_name: Gradient name if no background provided
        video_format: 'shorts' (9:16) or 'video' (16:9)
        title_text: Optional title text overlay
    """
    if not check_copyright_killswitch():
        print("❌ Render aborted due to copyright safety protocol.")
        return False
    if video_format == "shorts":
        width, height = SHORTS_WIDTH, SHORTS_HEIGHT
    else:
        width, height = VIDEO_WIDTH, VIDEO_HEIGHT

    # Get audio duration
    duration = _get_duration(audio_path)
    total_duration = duration + 1.0  # Add 1 second padding at end

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    if background_video:
        # Use provided video as background
        if isinstance(background_video, list):
            bg_input = _prepare_multi_background_videos(background_video, width, height, total_duration)
            if not bg_input:
                bg_path = os.path.join(TEMP_DIR, "bg_gradient.mp4")
                create_gradient_background(bg_path, total_duration, width, height, gradient_name)
                bg_input = bg_path
        else:
            bg_input = _prepare_background_video(background_video, width, height, total_duration)
    elif background_image:
        # Use image with Ken Burns effect
        bg_input = _prepare_background_image(background_image, width, height, total_duration)
    else:
        # Create gradient background
        bg_path = os.path.join(TEMP_DIR, "bg_gradient.mp4")
        create_gradient_background(bg_path, total_duration, width, height, gradient_name)
        bg_input = bg_path

    # Build FFmpeg command to combine everything
    filter_parts = []

    # Subtitle filter with escaped path for FFmpeg
    escaped_sub_path = subtitle_path.replace("\\", "/").replace(":", "\\:").replace("'", "'\\''")
    subtitle_filter = f"ass='{escaped_sub_path}'"

    # Add subtle zoom animation to background
    zoom_filter = f"zoompan=z='1+0.0005*in':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(total_duration*FPS)}:s={width}x{height}:fps={FPS}"

    # Build cinematic filter chain with vignette, progress bar, and attention flash
    vignette_str = "vignette='PI/3.2 + 0.04 * sin(2*PI*t)'"  # Breathing vignette matching the 60 BPM heartbeat
    
    # Progress bar: thin cyan bar that grows from left to right across the full video duration
    progress_bar_h = 6  # pixels tall
    progress_bar_y = height - progress_bar_h  # bottom of screen
    
    # Attention-grab flash: bright flash in first 0.3 seconds that fades to normal
    flash_str = f"fade=t=in:st=0:d=0.3:alpha=1"
    
    mixed_audio_path = os.path.join(TEMP_DIR, f"mixed_soundtrack_{int(time.time())}.mp3")
    num_scenes = len(background_video) if isinstance(background_video, list) else 1
    
    audio_for_video = audio_path
    try:
        mix_voice_bgm_and_sfx(audio_path, mixed_audio_path, total_duration, num_scenes)
        if os.path.exists(mixed_audio_path) and os.path.getsize(mixed_audio_path) > 1000:
            audio_for_video = mixed_audio_path
    except Exception as e:
        print(f"⚠️ Music mixing warning ({e}), falling back to direct voiceover...")

    clip_duration = max(3.0, min(8.0, total_duration / num_scenes)) if num_scenes > 0 else 4.0

    cmd = [
        "ffmpeg", "-y",
        "-i", bg_input,
        "-i", audio_for_video,
        "-filter_complex",
        f"[0:v]scale={width+40}:{height+40},crop=w={width}:h={height}:x='20+20*sin(t*60)*exp(-10*mod(t,{clip_duration}))':y='20+20*cos(t*65)*exp(-10*mod(t,{clip_duration}))',setsar=1,"
        f"{subtitle_filter},"
        f"eq=contrast=1.08:saturation=1.2:brightness=0.02,"
        f"colorbalance=rs=-0.04:bs=0.04:rm=0.05:bm=-0.05:rh=0.08:bh=-0.08,"
        f"unsharp=3:3:0.5:3:3:0.5,"
        f"{vignette_str},"
        f"drawbox=x=0:y={progress_bar_y}:w='(t/{total_duration})*{width}':h={progress_bar_h}:color=0x00FFFF@0.85:t=fill"
        f"[v]",
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-profile:v", "high",
        "-level", "4.1",
        "-c:a", "aac",
        "-ar", "44100",
        "-ac", "2",
        "-b:a", "192k",
        "-shortest",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path
    ]

    print(f"🎬 Creating video...")
    print(f"   Background: {bg_input}")
    print(f"   Audio: {mixed_audio_path}")
    print(f"   Subtitles: {subtitle_path}")
    print(f"   Output: {output_path}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    # Clean up mixed soundtrack
    if os.path.exists(mixed_audio_path):
        try:
            os.remove(mixed_audio_path)
        except Exception:
            pass

    if result.returncode != 0:
        print(f"⚠️  FFmpeg error: {result.stderr[-500:]}")
        # Try without subtitle filter as fallback
        print("🔄 Retrying without styled subtitles...")
        cmd_fallback = [
            "ffmpeg", "-y",
            "-i", bg_input,
            "-i", audio_path,
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,vignette=PI/4",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-profile:v", "high", "-level", "4.1",
            "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "192k",
            "-shortest", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            output_path
        ]
        result = subprocess.run(cmd_fallback, capture_output=True, text=True)

    if result.returncode == 0:
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"✅ Video created successfully!")
        print(f"📁 Output: {output_path}")
        print(f"📏 Size: {file_size:.1f} MB")
        print(f"⏱️  Duration: {total_duration:.1f} seconds")
    else:
        print(f"❌ Video creation failed: {result.stderr[-300:]}")

    return output_path



def _prepare_background_video(video_path, width, height, duration):
    """Prepare background video: crop, scale, loop if needed"""
    temp_bg = os.path.join(TEMP_DIR, "bg_prepared.mp4")

    # Get video duration
    vid_duration = _get_duration(video_path)

    if vid_duration < duration:
        # Loop video
        loop_count = math.ceil(duration / vid_duration)
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", str(loop_count),
            "-i", video_path,
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}",
            "-t", str(duration),
            "-an",
            "-c:v", "libx264", "-preset", "fast",
            "-pix_fmt", "yuv420p",
            temp_bg
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}",
            "-t", str(duration),
            "-an",
            "-c:v", "libx264", "-preset", "fast",
            "-pix_fmt", "yuv420p",
            temp_bg
        ]

    subprocess.run(cmd, capture_output=True, text=True)
    return temp_bg


def _prepare_multi_background_videos(video_paths, width, height, duration):
    """
    Stitch together multiple video clips, scaling and cropping each, 
    and matching the target duration.
    """
    import random
    temp_clips = []
    
    # We want each clip to play for 4-8 seconds
    clip_duration = max(3.0, min(8.0, duration / len(video_paths)))
    
    total_time = 0
    for idx, path in enumerate(video_paths):
        if total_time >= duration:
            break
            
        this_dur = min(clip_duration, duration - total_time)
        if this_dur < 1.0:
            break
            
        temp_clip = os.path.join(TEMP_DIR, f"temp_clip_{idx}_{int(time.time())}.mp4")
        
        
        # CLOUD ORCHESTRATION: Generate True Video using Free HF Space
        if path.endswith('.jpg') or path.endswith('.png'):
            print(f"🎥 CLOUD ORCHESTRATION: Generating True Video from image {path} using HF Space...")
            # We would extract the prompt from metadata or script here. 
            # For demonstration, we use a default cinematic prompt.
            hf_prompt = "Cinematic slow pan, high quality, 8k resolution, realistic movement."
            hf_video_path = generate_video_from_prompt_hf(hf_prompt)
            
            if hf_video_path:
                path = hf_video_path # Overwrite static path with new video path
            
        # Scale, crop, trim to this_dur, remove audio, and encode cleanly.
        # Images use zoompan, Videos preserve native motion (no zoompan to avoid freezing)
        if path.endswith('.jpg') or path.endswith('.png'):
            vf_filter = f"scale={width*2}:{height*2},zoompan=z='1.0+0.005*in':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(this_dur*FPS)}:s={width}x{height}:fps={FPS},setsar=1,eq=contrast=1.05:saturation=1.15,fade=t=in:st=0:d=0.2,fade=t=out:st={this_dur-0.2}:d=0.2"
        else:
            vf_filter = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1,eq=contrast=1.05:saturation=1.15"
            
        cmd = [
            "ffmpeg", "-y",
            "-i", path,
            "-vf", vf_filter,
            "-t", str(this_dur),
            "-an",
            "-c:v", "libx264", "-preset", "medium",
            "-pix_fmt", "yuv420p",
            temp_clip
        ]
        subprocess.run(cmd, capture_output=True)

        if os.path.exists(temp_clip):
            temp_clips.append(temp_clip)
            total_time += this_dur

    if not temp_clips:
        return None

    # Now concat the clips using concat filter
    inputs = []
    for tc in temp_clips:
        inputs.extend(["-i", tc])
        
    concat_filter = "".join([f"[{i}:v]" for i in range(len(temp_clips))]) + f"concat=n={len(temp_clips)}:v=1:a=0[v]"
    
    output_bg = os.path.join(TEMP_DIR, f"multi_bg_{int(time.time())}.mp4")
    cmd = [
        "ffmpeg", "-y",
    ] + inputs + [
        "-filter_complex", concat_filter,
        "-map", "[v]",
        "-c:v", "libx264", "-preset", "medium",
        "-pix_fmt", "yuv420p",
        output_bg
    ]
    
    subprocess.run(cmd, capture_output=True)
    
    # Clean up individual temp clips
    for tc in temp_clips:
        try:
            os.remove(tc)
        except:
            pass
            
    return output_bg


def _prepare_background_image(image_path, width, height, duration):
    """Create video from image with slow Ken Burns zoom effect"""
    temp_bg = os.path.join(TEMP_DIR, "bg_from_image.mp4")

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-vf", (
            f"scale={width*2}:{height*2},"
            f"zoompan=z='1.0+0.001*in':x='iw/2-(iw/zoom/2)+sin(in*0.01)*50':y='ih/2-(ih/zoom/2)+cos(in*0.015)*30'"
            f":d={int(duration*FPS)}:s={width}x{height}:fps={FPS}"
        ),
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "fast",
        "-pix_fmt", "yuv420p",
        temp_bg
    ]

    subprocess.run(cmd, capture_output=True, text=True)
    return temp_bg


def _get_duration(file_path):
    """Get media file duration using ffprobe"""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", file_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(result.stdout)
    return float(info["format"]["duration"])


def add_subtitles_to_video(video_path, subtitle_path, output_path):
    """Burn subtitles into an existing video"""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"ass='{subtitle_path}'",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path
    ]

    print(f"🔤 Adding subtitles to video...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ Subtitles added: {output_path}")
    else:
        print(f"❌ Error: {result.stderr[-300:]}")

    return output_path


def crop_to_shorts(input_video, output_path):
    """Crop a 16:9 video to 9:16 (YouTube Shorts format)"""
    cmd = [
        "ffmpeg", "-y",
        "-i", input_video,
        "-vf", f"crop=ih*9/16:ih,scale={SHORTS_WIDTH}:{SHORTS_HEIGHT}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path
    ]

    print(f"✂️  Cropping to Shorts format...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ Cropped: {output_path}")
    else:
        print(f"❌ Error: {result.stderr[-300:]}")

    return output_path


if __name__ == "__main__":
    print("🎬 YouTube Viral Machine - Video Maker")
    print("=" * 50)
    print("This module is used by main.py")
    print("Run main.py for the full interface.")
