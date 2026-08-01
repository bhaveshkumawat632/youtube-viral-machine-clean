# TEST_INFRA.md — E2E Test Methodology & Architecture

## 1. Overview
This document maps out the end-to-end (E2E) testing infrastructure for the YouTube Viral Machine upgrade. It details the testing methodology, feature inventory, 4-tier test case design, and local mocking strategy to ensure high-fidelity video generation and copyright compliance in a network-isolated environment.

---

## 2. Feature Inventory
The automated verification suite covers four main features:
1. **Subtitles & Transcription** (`subtitle_generator.py`)
   - ASS subtitle formatting & style templates
   - Karaoke-style word-by-word highlighting (pop-in animations)
   - Font settings, line grouping, and SRT conversion
   - Dynamic transcription fallback / even word distribution
2. **Audio Layering & Mixing** (`audio_mixer.py`)
   - Layering multiple audio tracks (Voiceover, BGM, SFX)
   - Ducking logic (FFmpeg volume and sidechaincompress filter building)
   - Volume adjustment and clipping control
3. **Visual Sourcing & Fallback Ladder** (`vidrush_pipeline.py`)
   - Priority 1: Private Colab GPU / HuggingFace Spaces (LTX + CogVideoX)
   - Priority 2: FAL.AI API (Kling/Veo/Wan)
   - Priority 3: Stock Video APIs (Pexels / Coverr)
   - Priority 4: Local Video Loops (gameplay, viral backgrounds)
   - Priority 5: Synthetic Gradient / Solid Color blocks
4. **QA Gate & Verification Suite** (`comprehensive_qa_validator.py` / `vidrush_pipeline.py`)
   - Duration validation (25–180 seconds, or 5-second test renders)
   - Codec checks (H.264 video, AAC audio, MP4 container format)
   - Layout checks (1080x1920 vertical portrait orientation)
   - Subtitle vertical safe-zone checks (avoiding top 12% and bottom 15%)
   - Business rules: fallback visuals ratio <=30%, license logging, alerts, upload dry-run safety

---

## 3. 4-Tier Test Case Design
To guarantee reliability and prevent regressions, the tests are organized into four distinct tiers:

### Tier 1: Feature Coverage (Happy-Path)
*Goal: Verify correct functionality under normal, expected conditions. At least 5 test cases per feature.*
- **Subtitles**: Hex color parsing, seconds-to-ASS timestamp conversion, line-grouping logic, SRT file output structure, and ASS file header layout.
- **Audio mixing**: Single VO track mixing, BGM integration with volume reduction, SFX integration with delays, multi-track layering, and output path creation.
- **Visual Sourcing**: HF space predict parsing, FAL.AI video URL parsing, Pexels video search API response processing, Coverr HTML link extraction, and local loop file selection.
- **QA Gate**: Manifest file presence check, correct format/layout verification, license logging confirmation, alert file generation, and dry-run upload safety bypass.

### Tier 2: Boundary & Corner Cases
*Goal: Verify error handling and robustness under extreme or unexpected inputs. At least 5 test cases per feature.*
- **Subtitles**: Empty script text, missing audio path, extreme timestamps, invalid hex colors, and extremely long single-word inputs.
- **Audio mixing**: Missing input audio files, negative SFX start times, zero/extreme volume values, empty SFX lists, and non-existent output directories.
- **Visual Sourcing**: Missing API keys (Pexels/FAL), 404 response on spaces, empty stock query results, missing/corrupted local loops, and fallback cascade execution.
- **QA Gate**: Out-of-bounds video duration, corrupted manifest JSON, 100% fallback video usage, unsafe stock source detection, and missing upload credentials.

### Tier 3: Cross-Feature Combinations
*Goal: Verify pairwise interactions and integration between features.*
- **Voice + Subtitles**: Syncing Whisper word timestamps with TTS audio length.
- **Audio Mixing + Video Rendering**: Combining mixed audio with video tracks under precise duration alignment.
- **AI Failure -> Stock Fallback**: Simulating cloud generation failure to confirm stock video sourcing takes over.
- **Stock Failure -> Local Loop Fallback**: Simulating both cloud and stock failures to confirm local loop video cutting is triggered.
- **Full Pipeline (Dry Run)**: Integrating all steps (script, audio, visuals, captions, QA) into a complete mock video compilation.

### Tier 4: Real-world Application Scenarios (E2E Render)
*Goal: Execute actual renders and assert concrete technical compliance using ffprobe.*
- **Render E2E Video**: Compile a short 5-second video.
- **Container check**: Assert container format is `mp4`.
- **Video Codec check**: Assert video codec is `h264`.
- **Audio Codec check**: Assert audio codec is `aac`.
- **Portrait Layout check**: Assert resolution is `1080x1920`.
- **Subtitle Safe-zone check**: Assert subtitle drawtext/ASS parameters avoid player overlay safe-zones (top 12% and bottom 15%).

---

## 4. Coverage Thresholds
- **Unit Logic (Tier 1 & 2)**: 100% code coverage.
- **Integration Logic (Tier 3)**: >90% code coverage.
- **E2E Render (Tier 4)**: Assert 100% correctness of metadata on generated MP4 artifacts.

---

## 5. Mocking Strategy
To enable fast, offline, and deterministic test runs in CODE_ONLY network mode:
- **`gradio_client.Client`**: Mocked to intercept calls to HF Spaces or Colab, returning mock paths to pre-generated valid 250KB MP4 files.
- **`fal_client`**: Mocked by patching `sys.modules` to return a mock subscriber that outputs mock URLs.
- **`requests.get` / `urllib.request.urlopen`**: Mocked to intercept Pexels and Coverr HTTP API requests, returning mock JSON and mock HTML responses.
- **`subprocess.run` (wget/curl)**: Mocked to intercept command-line downloads, automatically writing valid mock video files (>250KB) and image files (>1KB) to the requested output paths.
