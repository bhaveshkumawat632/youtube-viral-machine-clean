import os
import subprocess

def generate_background_tone(duration, output_path, style='ambient'):
    """
    Generate a cinematic background audio tone using FFmpeg.
    Produces richer, layered sound compared to simple sine waves.
    """
    print(f"🎵 Generating background music ({style})...")
    
    import random
    rf = random.uniform(0.9, 1.1) # Randomize base pitch by +/- 10%
    
    if style == 'dramatic':
        # Deep cinematic drone: layered bass + sub-bass + slow LFO modulation + lub-dub heartbeat at 60 BPM
        expr = (
            f"aevalsrc="
            f"'0.15*sin(2*PI*t*{55 * rf})"      # Sub-bass (A1)
            f"+0.08*sin(2*PI*t*{82.5 * rf})"     # Low bass (E2)
            f"+0.03*sin(2*PI*t*{220 * rf})*sin(2*PI*t*{0.15 * rf})"  # Slow LFO shimmer
            f"+0.38*sin(2*PI*t*{50 * rf})*(exp(-38*mod(t,1.0)) + 0.22*exp(-38*mod(t-0.22,1.0)))"  # Double heartbeat (60 BPM)
            f"':d={duration},"
            f"lowpass=f={180 * rf},"              # Keep it deep and warm
            f"afade=t=in:d=2,"             # 2s fade in
            f"afade=t=out:st={max(0, duration-3)}:d=3,"  # 3s fade out
            f"aecho=0.8:0.7:40:0.3"        # Subtle reverb
        )
    elif style == 'suspense':
        # Rising tension: frequency sweep effect
        expr = (
            f"aevalsrc="
            f"'0.15*sin(2*PI*t*({40 * rf}+t*2))"  # Rising frequency sweep
            f"+0.10*sin(2*PI*t*{55 * rf})"         # Constant sub-bass anchor
            f"+0.06*sin(2*PI*t*{110 * rf})*sin(2*PI*t*{0.3 * rf})"  # Pulsing overtone
            f"':d={duration},"
            f"lowpass=f={250 * rf},"
            f"afade=t=in:d=1.5,"
            f"afade=t=out:st={max(0, duration-2)}:d=2,"
            f"aecho=0.8:0.6:50:0.25"
        )
    elif style == 'upbeat':
        # Warm, positive ambient with gentle chord
        expr = (
            f"aevalsrc="
            f"'0.10*sin(2*PI*t*{220 * rf})"       # A3
            f"+0.08*sin(2*PI*t*{277 * rf})"       # C#4
            f"+0.06*sin(2*PI*t*{330 * rf})"       # E4
            f"+0.04*sin(2*PI*t*{440 * rf})*sin(2*PI*t*{0.5 * rf})"  # Gentle A4 pulse
            f"':d={duration},"
            f"lowpass=f={500 * rf},"
            f"afade=t=in:d=2,"
            f"afade=t=out:st={max(0, duration-3)}:d=3,"
            f"aecho=0.8:0.5:60:0.2"
        )
    else:  # ambient (default)
        # Warm cinematic pad: rich layered low frequencies with gentle movement
        expr = (
            f"aevalsrc="
            f"'0.12*sin(2*PI*t*{65 * rf})"        # Low C2
            f"+0.10*sin(2*PI*t*{98 * rf})"        # G2 (fifth)
            f"+0.07*sin(2*PI*t*{130 * rf})"       # C3 (octave)
            f"+0.04*sin(2*PI*t*{196 * rf})*sin(2*PI*t*{0.2 * rf})"  # Gentle G3 pulse
            f"+0.03*sin(2*PI*t*{262 * rf})*sin(2*PI*t*{0.1 * rf})"  # Very soft C4 shimmer
            f"':d={duration},"
            f"lowpass=f={300 * rf},"              # Warm low-pass
            f"afade=t=in:d=2,"             # Smooth fade in
            f"afade=t=out:st={max(0, duration-3)}:d=3,"  # Smooth fade out
            f"aecho=0.8:0.6:50:0.25"       # Subtle reverb
        )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", expr,
        "-c:a", "libmp3lame", "-b:a", "128k",
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Fallback to simple tone if complex synthesis fails
        print(f"⚠️  Rich synthesis failed, using simple fallback...")
        simple_expr = f"aevalsrc=0.15*sin(2*PI*t*80)+0.10*sin(2*PI*t*120):d={duration}"
        cmd_fallback = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", simple_expr,
            "-c:a", "libmp3lame", "-b:a", "128k",
            output_path
        ]
        subprocess.run(cmd_fallback, capture_output=True)
    
    return output_path

def generate_sfx(output_path, type="whoosh"):
    """
    Generate synthetic sound effects using FFmpeg.
    """
    import os
    print(f"🪄 Generating SFX ({type})...")
    
    if type == "whoosh":
        # Sweeping noise to simulate a whoosh/transition sound
        expr = "anoisesrc=c=white:d=0.5,bandpass=f=2000:w=1000,tremolo=f=10:d=1,volume=1.5"
        cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", expr, "-c:a", "pcm_s16le", output_path]
    elif type == "pop":
        # Short pop/click for subtitles
        expr = "aevalsrc='sin(2000*t)*exp(-30*t)':d=0.1,volume=0.5"
        cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", expr, "-c:a", "aac", output_path]
    elif type == "impact":
        # Deep impact hit for dramatic moments
        expr = "aevalsrc='sin(60*t)*exp(-5*t)+0.5*sin(120*t)*exp(-8*t)':d=0.8,volume=2.0"
        cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", expr, "-c:a", "aac", output_path]
    else:
        # Default to whoosh for unknown types
        print(f"⚠️  Unknown SFX type '{type}', defaulting to whoosh")
        expr = "anoisesrc=c=white:d=0.5,bandpass=f=2000:w=1000,tremolo=f=10:d=1,volume=1.5"
        cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", expr, "-c:a", "aac", output_path]
        
    subprocess.run(cmd, capture_output=True)
    return output_path

def mix_audio(voiceover_path, music_path, output_path, music_volume=0.15):
    """
    Mix voiceover with background music using FFmpeg.
    """
    print(f"🎧 Mixing voiceover and background music...")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", voiceover_path,
        "-i", music_path,
        "-filter_complex", f"[1:a]volume={music_volume}[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[a]",
        "-map", "[a]",
        "-c:a", "libmp3lame", "-b:a", "192k",
        output_path
    ]
    
    subprocess.run(cmd, capture_output=True)
    return output_path
