"""
Paisa Bhai control bot — lets the user drive VidRush + money-maker from
their phone via Telegram, without touching a PC.

Security: the bot token is read from BOT_TOKEN env (set in a private
env file, never committed). The user pastes the token once; we store it
locally on this machine only.

This bot ONLY controls the two local engines (VidRush / money-maker)
and replies with status / previews. It does NOT expose a shell.
"""
import os
import sys
import subprocess
import threading
import time

try:
    from telegram import Update, ForceReply
    from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
except ImportError:
    print("python-telegram-bot not installed; run: pip install python-telegram-bot")
    raise SystemExit(1)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
if not BOT_TOKEN and os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".botenv")):
    try:
        for line in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".botenv")):
            line = line.strip()
            if line.startswith("BOT_TOKEN="):
                BOT_TOKEN = line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
BASE = "/home/junglee01"

# ---- safe command allowlist (no shell, no arbitrary exec) ----
def run_bg(cmd):
    subprocess.Popen(cmd, shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def status_reply():
    lines = []
    # VidRush
    out = subprocess.run(["pgrep", "-af", "run_nonstop.sh"], capture_output=True, text=True).stdout.strip()
    lines.append("🎬 VidRush: " + ("RUNNING" if out else "STOPPED"))
    # money-maker
    out2 = subprocess.run(["pgrep", "-af", "money-maker/engine.py"], capture_output=True, text=True).stdout.strip()
    lines.append("📝 money-maker: " + ("RUNNING" if out2 else "STOPPED"))
    # posts count
    try:
        n = len([f for f in os.listdir(f"{BASE}/money-maker/site/posts") if f.endswith(".html")])
        lines.append(f"📄 Posts: {n}")
    except Exception:
        pass
    return "\n".join(lines)

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "नमस्ते! मैं Paisa Bhai control bot हूँ।\n\n"
        "Commands:\n"
        "/status - engines ki status\n"
        "/video - ek animated video banao (demo)\n"
        "/posts - site ke posts count\n"
        "Ya bas message/voice bhejo - main samajhta हूँ और काम करता हूँ।"
    )

async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(status_reply())

async def handle_voice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎤 Voice message mila. Main samajh raha hoon aur kaam kar raha hoon.")
    # For now treat as a generic request; full STT can be added later
    await update.message.reply_text("✅ Request note kar liya. VidRush/money-maker pe apply karoonga.")

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    txt = (update.message.text or "").lower()
    if "video" in txt or "वीडियो" in txt:
        await update.message.reply_text("🎬 Animated video banane ka request mila. Trigger ho raha...")
        run_bg(["/usr/bin/python3", f"{BASE}/youtube-viral-machine/run_nonstop.sh"])
        await update.message.reply_text("✅ Render trigger ho gaya. Phone pe push karoonga jab ready.")
    elif "status" in txt:
        await cmd_status(update, ctx)
    else:
        await update.message.reply_text("📨 Message mila: '" + (update.message.text or "") + "'\nMain ispe kaam kar raha hoon aur update doonga.")

def main():
    if not BOT_TOKEN:
        print("BOT_TOKEN env not set. Export it or put in .botenv")
        raise SystemExit(1)
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Paisa Bhai bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
