"""Headless OAuth flow - generates auth URL and handles callback."""
import json
import os
import stat
import sys
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

TOKEN_DIR = Path.home() / ".gw-mcp"
TOKEN_FILE = TOKEN_DIR / "token.json"
CREDS_FILE = TOKEN_DIR / "credentials.json"

# Start with read-only for safety
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        global SCOPES
        SCOPES = [
            "https://mail.google.com/",
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/documents",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/presentations",
            "https://www.googleapis.com/auth/forms.body",
            "https://www.googleapis.com/auth/forms.responses.readonly",
            "https://www.googleapis.com/auth/tasks",
            "https://www.googleapis.com/auth/contacts",
        ]

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
    # Use run_local_server with open_browser=False so it prints the URL
    creds = flow.run_local_server(port=8086, open_browser=False)
    
    TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(TOKEN_DIR, stat.S_IRWXU)  # 0700
    TOKEN_FILE.write_text(creds.to_json())
    os.chmod(TOKEN_FILE, stat.S_IRUSR | stat.S_IWUSR)  # 0600
    print(f"\n✅ Token saved to {TOKEN_FILE}")

if __name__ == "__main__":
    main()
