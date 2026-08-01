"""
Paisa Bhai bot - FAST local LLM chat (1-to-1, no middleman, no duplicate replies).
Uses a small/fast model so Telegram doesn't time out and re-send "thinking".
Duplicate-reply guard prevents the "soch raha hoon" glitch.
"""
import os
import sys
import json
import time
import asyncio
import subprocess
import urllib.request

try:
    from telegram import Update
    from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
except ImportError:
    print("python-telegram-bot not installed")
    raise SystemExit(1)

BASE = "/home/junglee01/youtube-viral-machine"
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
if not BOT_TOKEN:
    for line in open(os.path.join(BASE, ".botenv")):
        line = line.strip()
        if line.startswith("BOT_TOKEN="):
            BOT_TOKEN = line.split("=", 1)[1].strip().strip('"').strip("'")

# FAST model to avoid Telegram timeout/duplicate
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = os.environ.get("BOT_LLM", "qwen2.5:7b")

QUEUE = os.path.join(BASE, "bot_queue")
os.makedirs(QUEUE, exist_ok=True)
USER_ID = None
PROCESSED = set()  # dedupe message ids

SYSTEM = ("Tu 'Paisa Bhai' hai - ek Hindi/English (HINGLISH) assistant jo user ke YouTube "
          "(VidRush animated videos) aur money-maker blog ko manage karta hai. "
          "JARURI: Har jawab HINGLISH mein de (Hindi + English mix, jaise 'video banao', "
          "'site update karo'). KABHI pure English mat bol. Lambi story mat de, sirf 2-3 line. "
          "KABHI bhi fake date/number mat bol - agar status chahiye toh keh 'abhi check kar raha hoon' "
          "ya actual info de. User order de sakta hai (video banao, site update karo, status batao).")

# Fast local model to avoid Telegram timeout / duplicate "thinking"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = os.environ.get("BOT_LLM", "hermes-1.5b")

import re as _re

def _is_hinglish(text):
    # Devanagari present OR clearly Hinglish (has common Hindi words)
    if _re.search(r"[\u0900-\u097f]", text):
        return True
    hinglish_words = ["hai", "hain", "ka", "ke", "ki", "main", "tu", "tum", "bhai",
                      "video", "site", "kar", "karo", "banao", "status", "dekho",
                      "abhi", "pehle", "aur", "nahi", "theek", "ok", "haan"]
    low = text.lower()
    return any(w in low for w in hinglish_words)

def llm_chat(user_text):
    payload = {
        "model": MODEL,
        "prompt": f"{SYSTEM}\n\nUser: {user_text}\n\nPaisa Bhai:",
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": 80},
    }
    try:
        req = urllib.request.Request(OLLAMA_URL,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=60).read()
        reply = json.loads(resp.decode()).get("response", "").strip()
        # enforce Hinglish: if model drifted to pure English, prepend Hinglish framing
        if not _is_hinglish(reply):
            reply = "Bhai, " + reply
        return reply
    except Exception as e:
        return f"[LLM error: {str(e)[:60]}]"

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global USER_ID
    USER_ID = update.message.from_user.id
    await update.message.reply_text(
        "नमस्ते! Main Paisa Bhai hoon. Ab se direct jawab doonga (1-to-1). "
        "Order do - main samajhta hoon.\n\nTry: 'video banao', 'site update karo', 'status batao'")

async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global USER_ID
    USER_ID = update.message.from_user.id
    mid = update.message.message_id
    if mid in PROCESSED:
        return  # dedupe - no double "thinking"
    PROCESSED.add(mid)
    txt = update.message.text or ""
    await update.message.reply_text("💭 ...")
    reply = llm_chat(txt)
    # replace the "thinking" bubble by editing it
    try:
        await update.message.edit_text(reply[:4000])
    except Exception:
        for i in range(0, len(reply), 4000):
            await update.message.reply_text(reply[i:i+4000])

async def handle_voice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global USER_ID
    USER_ID = update.message.from_user.id
    mid = update.message.message_id
    if mid in PROCESSED:
        return
    PROCESSED.add(mid)
    try:
        vf = await update.message.voice.get_file()
        path = os.path.join(QUEUE, f"v_{mid}.ogg")
        await vf.download_to_drive(path)
        txt = ""
        try:
            r = subprocess.run([sys.executable, "-c",
                f"import whisper; m=whisper.load_model('tiny'); print(m.transcribe('{path}')['text'])"],
                capture_output=True, text=True, timeout=90)
            txt = r.stdout.strip()
        except Exception:
            txt = ""
        if not txt:
            await update.message.reply_text("🎤 Voice samjha nahi (STT off). Text likho.")
            return
        await update.message.reply_text("💭 ...")
        reply = llm_chat("🎤 VOICE: " + txt)
        try:
            await update.message.edit_text(reply[:4000])
        except Exception:
            await update.message.reply_text(reply[:4000])
    except Exception as e:
        await update.message.reply_text("Voice error: " + str(e)[:80])

def main():
    if not BOT_TOKEN:
        print("BOT_TOKEN missing"); raise SystemExit(1)
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("🤖 Paisa Bhai FAST bot starting (model:", MODEL, ")")
    app.run_polling(drop_pending_updates=True, allowed_updates=["message"])

if __name__ == "__main__":
    main()
