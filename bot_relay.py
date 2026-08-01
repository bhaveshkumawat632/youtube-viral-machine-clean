"""
Telegram bot RELAY: user msg -> bot_queue/incoming.txt
Polls bot_queue/outgoing.txt -> sends to user.
THIS is controlled by Hermes (the agent reads incoming.txt, acts, writes outgoing.txt).
No local LLM auto-reply.
"""
import os, sys, time, asyncio, json, urllib.request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BASE = "/home/junglee01/youtube-viral-machine"
BOT_TOKEN = ""
NV_KEY = ""
for line in open(os.path.join(BASE, ".botenv")):
    line = line.strip()
    if line.startswith("BOT_TOKEN="):
        BOT_TOKEN = line.split("=", 1)[1].strip()
try:
    NV_KEY = open(os.path.expanduser("~/.config/nvidia/nvapi.key")).read().strip()
except Exception:
    NV_KEY = ""

NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_MODEL = "nvidia/llama-3.1-nemotron-nano-8b-v1"

SYSTEM = ("Tu 'Paisa Bhai' assistant hai (Hinglish bol). User tere YouTube (VidRush animated Hindi videos) "
          "aur money-maker blog ko manage karta hai. Commands samajh: 'video banao' = render new video, "
          "'status batao' = project status, 'site update' = rebuild blog. Hinglish me short jawab de.")

def nvidia_reply(user_text):
    if not NV_KEY:
        return "NVIDIA key missing"
    payload = {"model": NVIDIA_MODEL, "max_tokens": 200, "stream": False,
               "temperature": 0.6, "messages": [
                   {"role": "system", "content": SYSTEM},
                   {"role": "user", "content": user_text}]}
    req = urllib.request.Request(NVIDIA_URL, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {NV_KEY}", "Content-Type": "application/json",
                 "accept": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=60).read()
        return json.loads(r.decode())["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[NVIDIA err: {str(e)[:80]}]"

QUEUE = os.path.join(BASE, "bot_queue")
os.makedirs(QUEUE, exist_ok=True)
INCOMING = os.path.join(QUEUE, "incoming.txt")
OUTGOING = os.path.join(QUEUE, "outgoing.txt")
USER_FILE = os.path.join(QUEUE, "user_id.txt")
PROCESSED = set()

def write_incoming(uid, text):
    with open(INCOMING, "a", encoding="utf-8") as f:
        f.write(f"{uid}|{text}\n")

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    open(USER_FILE, "w").write(str(uid))
    await update.message.reply_text("Connected. Paisa Bhai active (NVIDIA Nemotron). Command do.")

async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    mid = update.message.message_id
    if mid in PROCESSED:
        return
    PROCESSED.add(mid)
    txt = update.message.text or ""
    open(USER_FILE, "w").write(str(uid))
    write_incoming(uid, txt)
    # NVIDIA smart reply (Hinglish)
    reply = nvidia_reply(txt)
    try:
        await update.message.reply_text(reply[:4000])
    except Exception as e:
        await update.message.reply_text(f"err {e}")

async def handle_voice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    open(USER_FILE, "w").write(str(uid))
    write_incoming(uid, "[VOICE]")
    await update.message.reply_text("Voice aaya, likh kar bhejo (NVIDIA text-only abhi).")

def poll_outgoing(app):
    """thread: watch outgoing.txt, send to user (Hermes manual override)."""
    last = 0
    while True:
        try:
            if os.path.exists(OUTGOING):
                size = os.path.getsize(OUTGOING)
                if size > last:
                    with open(OUTGOING, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                    if content:
                        uid = open(USER_FILE).read().strip() if os.path.exists(USER_FILE) else None
                        if uid:
                            try:
                                app.bot.send_message(chat_id=int(uid), text=content[:4000])
                            except Exception as e:
                                print("send err", e)
                        open(OUTGOING, "w").close()
                        last = 0
                    else:
                        last = size
        except Exception:
            pass
        time.sleep(2)

def main():
    if not BOT_TOKEN:
        print("BOT_TOKEN missing"); raise SystemExit(1)
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    import threading
    t = threading.Thread(target=poll_outgoing, args=(app,), daemon=True)
    t.start()
    print("🤖 Relay bot (NVIDIA Nemotron) starting")
    app.run_polling(drop_pending_updates=True, allowed_updates=["message"])

if __name__ == "__main__":
    main()
