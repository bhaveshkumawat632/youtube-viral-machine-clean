#!/usr/bin/env python3
"""
One-time YouTube OAuth URL generator for the VidRush engine.
Prints the consent URL. The user opens it, logs into the target
Google/YouTube account, copies the auth code, then runs:

    python3 complete_oauth.py <CODE>

That saves token.pickle and the non-stop engine auto-publishes forever.
"""
import os, pickle
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT = os.path.join(BASE_DIR, "client_secrets.json")
TOKEN = os.path.join(BASE_DIR, "token.pickle")

if os.path.exists(TOKEN):
    print("✅ token.pickle already exists — uploads are live. Nothing to do.")
    raise SystemExit(0)

flow = InstalledAppFlow.from_client_secrets_file(CLIENT, SCOPES)
auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
print("\n" + "="*70)
print("YOUTUBE UPLOAD AUTH REQUIRED (one-time)")
print("="*70)
print("1) Open this URL in ANY browser:")
print()
print(auth_url)
print()
print("2) Log into the YouTube channel you want to publish to.")
print("3) Copy the 'code' Google shows you.")
print("4) Run:  python3 complete_oauth.py <PASTE_CODE_HERE>")
print("="*70 + "\n")
