#!/usr/bin/env bash
# VidRush NON-STOP engine — runs the full pipeline forever (upload ENABLED).
# FREE_ONLY=1 -> skips paid video engines, uses free HF/Pollinations path.
# Survives session close (nohup). Restart-safe: kills any previous instance.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
export PATH="$HOME/.local/bin:$PATH"
export YVM_FREE_ONLY=1
export PYTHONUNBUFFERED=1
export VIDRUSH_ANIMATED=1

PIDFILE="$DIR/.nonstop.pid"
LOG="$DIR/nonstop.log"

# --- restart-safety: don't spawn duplicates ---
if [ -f "$PIDFILE" ]; then
  OLD=$(cat "$PIDFILE" 2>/dev/null)
  if [ -n "${OLD:-}" ] && kill -0 "$OLD" 2>/dev/null; then
    echo "[nonstop] already running as PID $OLD — exiting." | tee -a "$LOG"
    exit 0
  fi
fi
echo $$ > "$PIDFILE"

echo "[nonstop] ===== ENGINE START $(date) =====" | tee -a "$LOG"
RUN=0
while true; do
  RUN=$((RUN+1))
  echo "" | tee -a "$LOG"
  echo "[nonstop] --- RUN #$RUN @ $(date) ---" | tee -a "$LOG"
  # Full pipeline WITH upload (no --no-upload). Failsafe: any crash -> loop continues.
  /usr/bin/python3 vidrush_pipeline.py >> "$LOG" 2>&1
  CODE=$?
  echo "[nonstop] run #$RUN exited code=$CODE @ $(date)" | tee -a "$LOG"
  # Backoff so we don't hammer on repeated failures
  if [ "$CODE" -ne 0 ]; then
    echo "[nonstop] failure backoff 60s..." | tee -a "$LOG"
    sleep 60
  else
    echo "[nonstop] success backoff 30s..." | tee -a "$LOG"
    sleep 30
  fi
done
