#!/usr/bin/env python3
"""Exchange the OAuth code (from gen_oauth_url.py) and save token.pickle."""
import sys, os, pickle
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT = os.path.join(BASE_DIR, "client_secrets.json")
TOKEN = os.path.join(BASE_DIR, "token.pickle")

if len(sys.argv) < 2:
    print("Usage: python3 complete_oauth.py <AUTH_CODE>")
    raise SystemExit(1)

code = sys.argv[1].strip()
flow = InstalledAppFlow.from_client_secrets_file(CLIENT, SCOPES)
flow.fetch_token(code=code)
creds = flow.credentials
with open(TOKEN, "wb") as f:
    pickle.dump(creds, f)
print(f"✅ token.pickle saved. The non-stop engine will now auto-upload.")
