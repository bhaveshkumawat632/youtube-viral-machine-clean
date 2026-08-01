import os
from datetime import datetime, timedelta
import re

LOG_FILE = "daily_log.txt"
SUMMARY_FILE = "WEEKLY_SUMMARY.txt"

def run_weekly_audit():
    if not os.path.exists(LOG_FILE):
        return

    with open(LOG_FILE, "r") as f:
        content = f.read()

    # We will simply parse the blocks
    blocks = content.split("--------------------------------------------------")
    
    total_videos = 0
    total_uploaded = 0
    total_failed = 0
    total_fallback_ratio = 0.0
    valid_blocks = 0
    alerts_triggered = 0
    
    # Calculate cutoff for last 7 days
    cutoff_date = datetime.now() - timedelta(days=7)
    
    for block in blocks:
        if not block.strip(): continue
        
        # Extract date from block header e.g. [2026-06-28 01:20:25]
        date_match = re.search(r'\[(.*?)\]', block)
        if date_match:
            try:
                date_obj = datetime.strptime(date_match.group(1), "%Y-%m-%d %H:%M:%S")
                if date_obj < cutoff_date:
                    continue # Older than 7 days
            except:
                pass
                
        valid_blocks += 1
        total_videos += 1
        
        if "ATTENTION NEEDED" in block:
            alerts_triggered += 1
            
        if "Upload Status: Success" in block:
            total_uploaded += 1
        elif "Upload Status: Failed" in block or "QA Gate: FAIL" in block:
            total_failed += 1
            
        # Extract fallback ratio e.g. (Ratio: 0.0%)
        ratio_match = re.search(r'\(Ratio:\s*([\d\.]+)%\)', block)
        if ratio_match:
            total_fallback_ratio += float(ratio_match.group(1))

    if valid_blocks == 0:
        summary = f"=== WEEKLY PIPELINE AUDIT ({datetime.now().strftime('%Y-%m-%d')}) ===\n"
        summary += "Videos Processed: 0\n"
        summary += "Status: INACTIVE (No logs in the last 7 days)\n"
        summary += "="*50 + "\n"
        with open(SUMMARY_FILE, "w") as f:
            f.write(summary)
        return
        
    avg_fallback = total_fallback_ratio / valid_blocks
    
    summary = f"=== WEEKLY PIPELINE AUDIT ({datetime.now().strftime('%Y-%m-%d')}) ===\n"
    summary += f"Videos Processed: {total_videos}\n"
    summary += f"Videos Uploaded: {total_uploaded}\n"
    summary += f"Videos Failed/Skipped: {total_failed}\n"
    summary += f"Average Synthetic Fallback Ratio: {avg_fallback:.1f}%\n"
    summary += f"Alerts Triggered: {alerts_triggered}\n"
    summary += "Status: " + ("HEALTHY" if alerts_triggered == 0 and avg_fallback < 15.0 else "REVIEW REQUIRED") + "\n"
    summary += "="*50 + "\n"
    
    with open(SUMMARY_FILE, "w") as f:
        f.write(summary)
        
if __name__ == "__main__":
    run_weekly_audit()
