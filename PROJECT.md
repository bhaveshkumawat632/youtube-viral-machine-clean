# Project: YouTube Viral Machine Upgrade

## Architecture
- Codebase executes CLI-driven automation pipelines to ingest scripts, generate voiceovers, dynamic subtitles, mix BGM/SFX, and compile video clips (AI-generated, stock, local loops) into high-retention vertical Shorts.
- All pipeline integrations must support the dual-track testing mechanism.

## Code Layout
- `main.py` / `vidrush_pipeline.py`: Main entry points for production.
- `config.py`: Central configuration and constants.
- `modules/subtitle_generator.py`: Transcribes audio, builds ASS subtitles with style templates.
- `modules/audio_mixer.py`: Combines voiceover, BGM, and SFX with proper levels.
- `modules/video_maker.py`: Final rendering of video and audio tracks via FFmpeg.
- `modules/cloud_video_generator.py`: Direct interface to AI video models.
- `modules/stock_video_generator.py`: Sourcing stock visual clips from APIs.
- `tests/`: Automated E2E verification test suite (R4).

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 0 | E2E Testing Suite | Create E2E test infra and Tiers 1-4 tests (Dual Track) | None | PLANNED |
| 1 | Dynamic Subtitles | Karaoke highlights, ASS burning, emojis mapping, jitter-free animation | None | PLANNED |
| 2 | Sound Design | Dynamic ducking (sidechaincompress), broadcast voiceover filter | None | PLANNED |
| 3 | Fail-safe Visuals | 4-tier fallback: AI -> Stock -> Local -> Gradient | None | PLANNED |
| 4 | Final E2E Pass | Ensure all E2E tests pass (Tier 1-4) | M0, M1, M2, M3 | PLANNED |
| 5 | Adversarial Hardening | Generate Tier 5 tests, whitebox analysis, fix coverage gaps | M4 | COMPLETED |

## Interface Contracts
### `modules/subtitle_generator.py`
- `generate_subtitle_file(audio_path, output_path, ...)` / `generate_ass_subtitles(...)` -> outputs standard `.ass` subtitle file path.
- Must support word-by-word timestamps, dynamic styling, and keyword-to-emoji mapping.

### `modules/audio_mixer.py`
- `mix_audio(voiceover_path, bgm_path, sfx_list, output_path, ...)` -> outputs mixed `.wav` / `.mp3` audio.
- Must execute dynamic BGM ducking using FFmpeg `sidechaincompress` when voice is active.

### `modules/cloud_video_generator.py`
- `generate_video_from_prompt_hf(prompt, output_path)` -> outputs generated/fetched visual scene path.
- Must catch all runtime and endpoint errors and transparently delegate to stock or local fallbacks.
