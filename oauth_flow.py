"""
OAuth flow that starts the local server, prints the auth URL, and waits for callback.
Run with -u flag for unbuffered output.
"""
import sys
import json
import os
import stat
import threading
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

TOKEN_DIR = Path.home() / ".gw-mcp"
TOKEN_FILE = TOKEN_DIR / "token.json"
CREDS_FILE = TOKEN_DIR / "credentials.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]

def main():
    flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
    
    print("Starting OAuth flow on port 8086...", flush=True)
    creds = flow.run_local_server(port=8086, open_browser=False, timeout_seconds=120)
    
    TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(TOKEN_DIR, stat.S_IRWXU)  # 0700
    TOKEN_FILE.write_text(creds.to_json())
    os.chmod(TOKEN_FILE, stat.S_IRUSR | stat.S_IWUSR)  # 0600
    print(f"TOKEN_SAVED:{TOKEN_FILE}", flush=True)

if __name__ == "__main__":
    main()
