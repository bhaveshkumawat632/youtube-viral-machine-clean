#!/bin/bash

# Configuration
SESSION_NAME="youtube_bot_2026"
BOT_SCRIPT="/home/junglee01/youtube-viral-machine/master_auto_bot.py"
WAIT_TIME=86400 # 24 hours in seconds (86400)

echo "Checking if bot is already running..."
tmux has-session -t $SESSION_NAME 2>/dev/null

if [ $? != 0 ]; then
    echo "Starting ZERO TOUCH YouTube Bot in background (Tmux)..."
    
    # Create the session
    tmux new-session -d -s $SESSION_NAME -n "BotRunner"
    
    # Send the infinite loop command
    # This loop will run the python script, then sleep for 24 hours, then run it again forever.
    tmux send-keys -t $SESSION_NAME "while true; do" C-m
    tmux send-keys -t $SESSION_NAME "    clear" C-m
    tmux send-keys -t $SESSION_NAME "    echo '====================================='" C-m
    tmux send-keys -t $SESSION_NAME "    echo '🚀 STARTING DAILY YOUTUBE BOT CYCLE'" C-m
    tmux send-keys -t $SESSION_NAME "    echo '====================================='" C-m
    tmux send-keys -t $SESSION_NAME "    source /home/junglee01/youtube-viral-machine/venv/bin/activate 2>/dev/null || echo 'No venv found, using system python'" C-m
    tmux send-keys -t $SESSION_NAME "    python3 $BOT_SCRIPT" C-m
    tmux send-keys -t $SESSION_NAME "    echo '✅ Cycle finished. Sleeping for 24 hours...'" C-m
    tmux send-keys -t $SESSION_NAME "    sleep $WAIT_TIME" C-m
    tmux send-keys -t $SESSION_NAME "done" C-m
    
    echo "================================================="
    echo "🎉 SUCCESS: YouTube Bot is now running 24/7!"
    echo "================================================="
    echo "To view the live bot logs, run:"
    echo "  tmux attach -t $SESSION_NAME"
    echo "To detach again, press Ctrl+b then d."
else
    echo "Bot is already running! Attach using: tmux attach -t $SESSION_NAME"
fi
