import os
import subprocess
import json
import re
import sys

# Import CONFIG_OUTPUT_DIR from config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import OUTPUT_DIR as CONFIG_OUTPUT_DIR, BASE_DIR

def run_ffprobe(file_path):
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", file_path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {file_path}: {res.stderr}")
    return json.loads(res.stdout)

def analyze_audio(file_path):
    cmd = ["ffmpeg", "-i", file_path, "-af", "volumedetect,silencedetect=noise=-30dB:d=0.5", "-f", "null", "-"]
    res = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = res.stdout
    
    max_volume = None
    silence_starts = len(re.findall(r'silence_start', out))
    
    vol_match = re.search(r'max_volume: ([\-\.\d]+) dB', out)
    if vol_match:
        max_volume = float(vol_match.group(1))
        
    return {
        "max_volume": max_volume,
        "silence_periods": silence_starts,
        "clipping": max_volume is not None and max_volume >= 0.0,
        "passed": max_volume is not None and max_volume < 0.0 and silence_starts == 0
    }

def analyze_video(file_path):
    cmd = ["ffmpeg", "-i", file_path, "-vf", "freezedetect=n=0.003,blackdetect=d=0.1", "-f", "null", "-"]
    res = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = res.stdout
    
    freeze_starts = len(re.findall(r'lavfi\.freezedetect\.freeze_start', out))
    black_starts = len(re.findall(r'black_start', out))
    
    return {
        "frozen_frames": freeze_starts,
        "black_frames": black_starts,
        "passed": freeze_starts == 0 and black_starts == 0
    }

def find_candidate_videos():
    if len(sys.argv) > 1:
        candidates = []
        for arg in sys.argv[1:]:
            if os.path.exists(arg):
                candidates.append(os.path.abspath(arg))
        if candidates:
            return candidates

    candidates = []
    # 1. Look in the standard CONFIG_OUTPUT_DIR
    if os.path.exists(CONFIG_OUTPUT_DIR):
        for root, _, files in os.walk(CONFIG_OUTPUT_DIR):
            for file in files:
                if file.endswith(".mp4") and not file.startswith("temp"):
                    candidates.append(os.path.join(root, file))
                    
    # 2. Look in local output/vidrush
    vidrush_dir = os.path.join(BASE_DIR, "output", "vidrush")
    if os.path.exists(vidrush_dir):
        for root, _, files in os.walk(vidrush_dir):
            for file in files:
                if file.endswith(".mp4") and not file.startswith("temp"):
                    path = os.path.join(root, file)
                    if path not in candidates:
                        candidates.append(path)
                        
    # 3. Look in fallback Testing/output
    testing_out = os.path.join(BASE_DIR, "Testing", "output")
    if os.path.exists(testing_out):
        for root, _, files in os.walk(testing_out):
            for file in files:
                if file.endswith(".mp4") and not file.startswith("temp"):
                    path = os.path.join(root, file)
                    if path not in candidates:
                        candidates.append(path)
    return candidates

def calculate_scores(probe, audio, video):
    # Technical score
    tech_score = 100
    v_stream = None
    a_stream = None
    for s in probe.get("streams", []):
        if s["codec_type"] == "video":
            v_stream = s
        elif s["codec_type"] == "audio":
            a_stream = s
            
    if not v_stream:
        tech_score -= 50
    else:
        width = int(v_stream.get("width", 0))
        height = int(v_stream.get("height", 0))
        if not ((width == 1080 and height == 1920) or (width == 1920 and height == 1080)):
            tech_score -= 20
            
    if not a_stream:
        tech_score -= 30
        
    duration = float(probe.get("format", {}).get("duration", 0))
    if duration < 15 or duration > 180:
        tech_score -= 10
        
    # Video Quality score
    video_score = 100
    video_score -= min(40, video["frozen_frames"] * 10)
    video_score -= min(40, video["black_frames"] * 10)
    
    # Audio Quality score
    audio_score = 100
    if audio["clipping"]:
        audio_score -= 20
    audio_score -= min(40, audio["silence_periods"] * 10)
    
    # Overall Score
    overall_score = int((tech_score + video_score + audio_score) / 3)
    
    return {
        "technical": tech_score,
        "video": video_score,
        "audio": audio_score,
        "overall": overall_score
    }

def generate_report():
    print("Initiating Genuine Comprehensive Validation...")
    
    report = "# 📊 Comprehensive AI Video QA Validation Report\n\n"
    
    candidates = find_candidate_videos()
    if not candidates:
        report += "## 🎯 Executive Summary\n"
        report += "**Overall Score:** N/A (NO VIDEOS FOUND)\n"
        report += "**Recommendation:** Please run the video generator pipeline first.\n\n"
        report += "### Error: No video files (.mp4) found in output directories.\n"
    else:
        overall_scores_sum = 0
        file_reports = []
        
        for idx, path in enumerate(candidates):
            print(f"Analyzing candidate {idx+1}/{len(candidates)}: {path}")
            try:
                probe = run_ffprobe(path)
                audio = analyze_audio(path)
                video = analyze_video(path)
                
                scores = calculate_scores(probe, audio, video)
                overall_scores_sum += scores["overall"]
                
                v_stream = next((s for s in probe["streams"] if s["codec_type"] == "video"), None)
                width = v_stream["width"] if v_stream else 0
                height = v_stream["height"] if v_stream else 0
                fps = eval(v_stream["r_frame_rate"]) if v_stream else 0.0
                duration = float(probe["format"]["duration"])
                
                file_report = f"### Video File: `{os.path.basename(path)}`\n"
                file_report += f"**Path:** `{path}`\n\n"
                file_report += f"- **Overall Score:** {scores['overall']}/100\n"
                file_report += f"- **Video Quality Score:** {scores['video']}/100\n"
                file_report += f"- **Audio Quality Score:** {scores['audio']}/100\n"
                file_report += f"- **Technical Validation Score:** {scores['technical']}/100\n\n"
                
                file_report += "#### 1. Video Diagnostics\n"
                file_report += f"- Frozen frames detected: {video['frozen_frames']} ({'❌ FAILED' if video['frozen_frames'] > 0 else '✅ PASSED'})\n"
                file_report += f"- Black frames detected: {video['black_frames']} ({'❌ FAILED' if video['black_frames'] > 0 else '✅ PASSED'})\n\n"
                
                file_report += "#### 2. Audio Diagnostics\n"
                file_report += f"- Max volume: {audio['max_volume']} dB\n"
                file_report += f"- Audio clipping: {audio['clipping']} ({'❌ FAILED' if audio['clipping'] else '✅ PASSED'})\n"
                file_report += f"- Silence periods: {audio['silence_periods']} ({'❌ FAILED' if audio['silence_periods'] > 0 else '✅ PASSED'})\n\n"
                
                file_report += "#### 3. Technical Specs\n"
                file_report += f"- Resolution: {width}x{height}\n"
                file_report += f"- FPS: {fps:.2f}\n"
                file_report += f"- Duration: {duration:.2f} seconds\n\n"
                file_report += "---\n\n"
                file_reports.append(file_report)
            except Exception as e:
                file_reports.append(f"### Error analyzing `{path}`: {e}\n\n---\n\n")
                
        avg_score = int(overall_scores_sum / len(candidates)) if candidates else 0
        report += "## 🎯 Executive Summary\n"
        report += f"**Overall Score:** {avg_score}/100 ({'PASSED' if avg_score >= 80 else 'FAILED'})\n"
        report += f"**Recommendation:** {'Ready for Production.' if avg_score >= 80 else 'Remediation advised.'}\n\n"
        report += "".join(file_reports)
        
    report_path = os.path.join(CONFIG_OUTPUT_DIR, "comprehensive_qa_report.md")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"Validation complete! Report saved to {report_path}")

if __name__ == "__main__":
    generate_report()
