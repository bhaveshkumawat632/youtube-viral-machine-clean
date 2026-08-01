# VidRush Finish Runbook

## How to Run

### Full Pipeline (render + upload)
```bash
cd /home/junglee01/youtube-viral-machine-clean
source .venv/bin/activate
python3 vidrush_pipeline.py
```

### Render Only (skip YouTube upload)
```bash
python3 vidrush_pipeline.py --no-upload
```
Output lands in `output/vidrush/` with QA gating, thumbnail, and daily log update.

### Interactive Menu
```bash
python3 main.py
```
Choose script-to-video, auto-clipper, subtitles, voiceover, batch generate, or SEO generator.

### Non-Stop / Cron
```bash
# Infinite loop: run pipeline, backoff, repeat
bash run_nonstop.sh

# Daily cron (also runs weekly_audit.py on Sundays)
bash cron_runner.sh
```

## Required Environment Variables

Create `.env` from `.env.example`:

| Variable | Purpose | Fallback behavior |
|---|---|---|
| `OPENROUTER_API_KEY` | Script generation + SEO metadata via Llama 70B | Uses built-in static script + template SEO |
| `REPLICATE_API_TOKEN` | AI thumbnail via FLUX (black-forest-labs/flux-schnell) | FFmpeg gradient fallback thumbnail |
| `PEXELS_API_KEY` | Stock video sourcing (Tier 2) | Skips to local loops / synthetic gradient (Tier 3/4) |
| `PRIVATE_API_URL` | Optional private Hugging Face/Gradio AI video space | Falls through to Tier 3/4 |
| `API_SECRET_KEY` | Defined in template; not currently used in pipeline | — |

Load with `python-dotenv` (already in `requirements.txt`).

## Upload Credentials

YouTube upload requires:
- `client_secrets.json` — Google Cloud OAuth client (downloaded from Google Cloud Console)
- `token.pickle` — cached auth token (created automatically on first auth)

On headless servers, run:
```bash
python3 complete_oauth.py
```
to generate `token.pickle` via console flow.

## Output & Logs

| Path | Content |
|---|---|
| `output/vidrush/` | Rendered videos, audio, thumbnails |
| `output/vidrush/failed/` | QA-failed or upload-failed videos |
| `daily_log.txt` | Append-only run log with QA and upload status |
| `ALERT.txt` | Urgent alerts when QA or upload fails |
| `assets/manifest.json` | Asset license/source tracking for QA |

## Troubleshooting

### QA Gate Failed
Check `daily_log.txt` for the exact reason. Common causes:
- **Fallback ratio > 30%**: Too many synthetic visuals. Ensure network/API keys are set so Tier 1/2 assets load.
- **Duration out of bounds**: Video must be 25–180s.
- **Missing manifest**: Re-run pipeline; it should regenerate `assets/manifest.json`.

### Upload Failed
- Verify `client_secrets.json` exists in project root.
- Re-auth: delete `token.pickle` and rerun to refresh OAuth.
- Check YouTube Data API quota in Google Cloud Console.
- If headless, use `complete_oauth.py` for console-based auth.

### Missing or Broken Assets
- Verify fonts exist at `assets/fonts/Montserrat-ExtraBold.ttf` (or edit `config.py` to point to an installed font).
- Ensure FFmpeg is installed: `ffmpeg -version`.
- Ensure required Python deps: `pip install -r requirements.txt`.

### Pipeline Hangs / Slow
- Edge-TTS requires internet. Without it, audio generation fails silently or hangs.
- Replicate/OpenRouter calls have 60–120s timeouts. A slow network will extend pipeline time.
- If running nonstop, check `nonstop.log` for backoff behavior after failures.

### No Audio / Black Screen
- Check `daily_log.txt` for FFmpeg subprocess errors.
- Run with `PYTHONUNBUFFERED=1` to see live subprocess output.
