"""
Hermes-side relay listener: watches bot_queue/incoming.txt.
When a new user command appears, Hermes (this script is a placeholder; the
actual agent reads incoming.txt and writes outgoing.txt) acts and writes the
reply to bot_queue/outgoing.txt so bot_relay.py sends it to Telegram.

This file is the contract: 
  incoming.txt  = "UID|text" lines (appended by bot_relay.py)
  outgoing.txt  = Hermes writes final reply here (bot_relay.py sends + clears)
"""
import os, time

BASE = "/home/junglee01/youtube-viral-machine"
QUEUE = os.path.join(BASE, "bot_queue")
INCOMING = os.path.join(QUEUE, "incoming.txt")
OUTGOING = os.path.join(QUEUE, "outgoing.txt")

print("Hermes relay listener contract:")
print(" - bot_relay.py appends user msgs to", INCOMING)
print(" - Hermes reads them, acts, writes reply to", OUTGOING)
print(" - bot_relay.py sends + clears", OUTGOING)
