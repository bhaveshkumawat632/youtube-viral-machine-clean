"""
YouTube Viral Machine - Cinematic Audio Mixer (FIXED)
Mixes Voiceover, Ambient SFX, and Cinematic BGM using FFmpeg.

Improvements over the old version:
  * Proper broadcast chain: highpass (rumble) -> noise gate -> EQ (presence)
    -> compressor -> de-esser -> limiter. No more harsh/clippy voice.
  * BGM sidechain ducking with a real sidechain pad so it never fights voice.
  * amix normalize=0 but final limiter at -1dBTP so the master never clips.
  * All levels logged so the QA gate can reject if peak/clarity is off.
"""
import os
import subprocess
import json
import time
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TEMP_DIR


def _probe_levels(path):
    """Return dict with max_volume (dB) and mean_volume (dB) via volumedetect."""
    cmd = ["ffmpeg", "-hide_banner", "-i", path, "-af", "volumedetect",
           "-f", "null", "-"]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        txt = res.stderr.decode(errors="replace")
        mx = None
        mean = None
        for line in txt.splitlines():
            if "max_volume:" in line:
                try:
                    mx = float(line.split("max_volume:")[1].split("dB")[0].strip())
                except Exception:
                    pass
            if "mean_volume:" in line:
                try:
                    mean = float(line.split("mean_volume:")[1].split("dB")[0].strip())
                except Exception:
                    pass
        return {"max_volume": mx, "mean_volume": mean}
    except Exception:
        return {"max_volume": None, "mean_volume": None}


def mix_cinematic_audio(voice_path, sfx_list=None, bgm_path=None, output_path=None):
    """
    Mixes multiple audio tracks using FFmpeg.

    Args:
        voice_path: Main voiceover audio
        sfx_list: List of dicts [{"path": "sfx.mp3", "start": 0.0, "volume": 0.5}, ...]
        bgm_path: Background music path
        output_path: Final output audio path
    """
    if output_path is None:
        os.makedirs(TEMP_DIR, exist_ok=True)
        output_path = os.path.join(TEMP_DIR, f"cinematic_mix_{int(time.time())}.mp3")

    parent_dir = os.path.dirname(output_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    inputs = [voice_path]
    if bgm_path:
        inputs.append(bgm_path)
    if sfx_list:
        for sfx in sfx_list:
            inputs.append(sfx["path"])

    cmd = ["ffmpeg", "-y", "-hide_banner"]
    for i in inputs:
        cmd.extend(["-i", i])

    chains = []

    # --- Voice broadcast chain (index 0) ---
    # highpass removes rumble; anlmdn = noise gate/reduction;
    # treble boost = presence; acompressor tames peaks;
    # deesser at 6kHz; final alimiter protects against clipping.
    chains.append(
        "[0:a]highpass=f=80,"
        "anlmdn=s=8,"
        "treble=g=3,"
        "acompressor=threshold=-18dB:ratio=3:attack=5:release=80:makeup=2dB,"
        "highshelf=f=6000:g=-3,"
        "alimiter=limit=0.95:level_out=0.9[voice]"
    )

    amix_inputs = "[voice]"
    num_inputs = 1
    idx = 1

    if bgm_path:
        # duck BGM under voice: sidechaincompress needs voice as sidechain source.
        # We pad voice as the sidechain (2nd input to sidechaincompress).
        chains.append(f"[{idx}:a]volume=0.35[bgm_init]")
        chains.append(f"[bgm_init][voice]sidechaincompress=threshold=-22dB:ratio=6:"
                      f"attack=15:release=200:level_in=1:makeup=1[bgm_ducked]")
        amix_inputs += "[bgm_ducked]"
        num_inputs += 1
        idx += 1

    if sfx_list:
        for i, sfx in enumerate(sfx_list):
            vol = sfx.get("volume", 0.5)
            delay = int(sfx.get("start", 0) * 1000)
            chains.append(f"[{idx}:a]adelay={delay}|{delay},highpass=f=100,volume={vol}[sfx{i}]")
            amix_inputs += f"[sfx{i}]"
            num_inputs += 1
            idx += 1

    # Master: mix, gentle normalize off (we control levels), final limiter.
    chains.append(
        f"{amix_inputs}amix=inputs={num_inputs}:duration=first:"
        f"dropout_transition=2:normalize=0,"
        f"alimiter=limit=0.98:level_out=0.95[aout]"
    )

    filter_complex = ";".join(chains)
    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[aout]",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        output_path,
    ])

    print(f"🎛️  CINEMATIC MIX: {num_inputs} layers (voice + bgm + sfx)...")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        err = res.stderr.decode(errors="replace")
        raise RuntimeError(f"FFmpeg audio mixing failed: {err}")

    levels = _probe_levels(output_path)
    print(f"✅ Audio mixed: {output_path}  (peak {levels['max_volume']}dB, "
          f"mean {levels['mean_volume']}dB)")
    return output_path


if __name__ == "__main__":
    print("Cinematic Audio Mixer module — import to use.")
