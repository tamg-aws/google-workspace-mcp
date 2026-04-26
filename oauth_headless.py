"""Headless OAuth flow - generates auth URL and handles callback.

Token and credentials live under TOKEN_DIR. Override with the GW_MCP_TOKEN_DIR
env var to onboard multiple accounts side by side (one dir per account).

Default scopes are read-only. Pass --full or set GW_MCP_SCOPES=full for
read/write access. Start read-only; upgrade only when a workflow requires it.
"""
import json
import os
import stat
import sys
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

TOKEN_DIR = Path(os.environ.get("GW_MCP_TOKEN_DIR") or (Path.home() / ".gw-mcp"))
TOKEN_FILE = TOKEN_DIR / "token.json"
CREDS_FILE = TOKEN_DIR / "credentials.json"

# Least-privilege default: Gmail read-only. See auth.py for rationale.
READONLY_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
]

FULL_SCOPES = [
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


def _resolve_scopes(argv: list[str]) -> list[str]:
    if "--full" in argv[1:]:
        return FULL_SCOPES
    if (os.environ.get("GW_MCP_SCOPES") or "").strip().lower() == "full":
        return FULL_SCOPES
    return READONLY_SCOPES


def _ensure_credentials_file() -> None:
    """Materialize credentials.json from env vars if it isn't already on disk."""
    if CREDS_FILE.exists():
        return
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
    if not client_id or not client_secret:
        sys.exit(
            f"error: {CREDS_FILE} not found and "
            "GOOGLE_OAUTH_CLIENT_ID / GOOGLE_OAUTH_CLIENT_SECRET not set"
        )
    TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(TOKEN_DIR, stat.S_IRWXU)  # 0700
    payload = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [
                "urn:ietf:wg:oauth:2.0:oob",
                "http://localhost",
            ],
        }
    }
    CREDS_FILE.write_text(json.dumps(payload))
    os.chmod(CREDS_FILE, stat.S_IRUSR | stat.S_IWUSR)  # 0600


def main() -> None:
    scopes = _resolve_scopes(sys.argv)
    _ensure_credentials_file()

    print(f"token dir: {TOKEN_DIR}")
    print(f"scopes   : {'full' if scopes is FULL_SCOPES else 'readonly'} ({len(scopes)} entries)")

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), scopes)
    creds = flow.run_local_server(port=8086, open_browser=False)

    TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(TOKEN_DIR, stat.S_IRWXU)  # 0700
    TOKEN_FILE.write_text(creds.to_json())
    os.chmod(TOKEN_FILE, stat.S_IRUSR | stat.S_IWUSR)  # 0600
    print(f"\n✅ Token saved to {TOKEN_FILE}")


if __name__ == "__main__":
    main()
