"""
Google OAuth2 authentication and service builder.
Handles OAuth flow, token storage, token refresh, and building Google API service objects.
"""

import json
import os
import stat
import time
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError, TransportError
from googleapiclient.discovery import build

# Where tokens get stored
TOKEN_DIR = Path.home() / ".gw-mcp"
TOKEN_FILE = TOKEN_DIR / "token.json"
CREDS_FILE = TOKEN_DIR / "credentials.json"

# Scopes — read from the existing token file if available, otherwise use defaults.
# This avoids scope mismatch errors when refreshing tokens that were issued with
# narrower scopes (e.g. readonly) than the full set below.
_FULL_SCOPES = [
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
    "https://www.googleapis.com/auth/meetings.space.created",
    "https://www.googleapis.com/auth/meetings.space.readonly",
]

def _get_scopes() -> list[str]:
    """Read scopes from existing token, or fall back to full scopes for new auth."""
    if TOKEN_FILE.exists():
        try:
            token_data = json.loads(TOKEN_FILE.read_text())
            saved_scopes = token_data.get("scopes", [])
            if saved_scopes:
                return saved_scopes
        except (json.JSONDecodeError, KeyError):
            pass
    return _FULL_SCOPES

SCOPES = _get_scopes()

# Service cache so we don't rebuild on every call
_service_cache: dict = {}


def _get_credentials() -> Credentials:
    """Get valid OAuth2 credentials, refreshing or re-authenticating as needed."""
    creds = None

    # Try loading existing token
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # If no valid creds, do the OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError as e:
                # Token revoked or invalid — delete and raise clear error
                if TOKEN_FILE.exists():
                    TOKEN_FILE.unlink()
                _service_cache.clear()
                raise RuntimeError(
                    f"Google OAuth token revoked or invalid. "
                    f"Re-run oauth_headless.py to re-authenticate. Error: {e}"
                ) from e
            except TransportError as e:
                # Network error — retry once with backoff
                time.sleep(2)
                try:
                    creds.refresh(Request())
                except Exception as retry_err:
                    raise RuntimeError(
                        f"Failed to refresh Google OAuth token after retry. "
                        f"Check network. Error: {retry_err}"
                    ) from retry_err
        else:
            # Build credentials.json from env vars if it doesn't exist
            if not CREDS_FILE.exists():
                client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
                client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
                if not client_id or not client_secret:
                    raise RuntimeError(
                        "No credentials found. Either place credentials.json in ~/.gw-mcp/ "
                        "or set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET env vars."
                    )
                TOKEN_DIR.mkdir(parents=True, exist_ok=True)
                os.chmod(TOKEN_DIR, stat.S_IRWXU)  # 0700
                creds_data = {
                    "installed": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
                    }
                }
                CREDS_FILE.write_text(json.dumps(creds_data))
                os.chmod(CREDS_FILE, stat.S_IRUSR | stat.S_IWUSR)  # 0600

            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        # Save token for next time
        TOKEN_DIR.mkdir(parents=True, exist_ok=True)
        os.chmod(TOKEN_DIR, stat.S_IRWXU)  # 0700
        TOKEN_FILE.write_text(creds.to_json())
        os.chmod(TOKEN_FILE, stat.S_IRUSR | stat.S_IWUSR)  # 0600

    return creds


def get_service(service_name: str, version: str):
    """Build and cache a Google API service object."""
    cache_key = f"{service_name}:{version}"
    if cache_key not in _service_cache:
        creds = _get_credentials()
        _service_cache[cache_key] = build(service_name, version, credentials=creds)
    return _service_cache[cache_key]


def clear_cache():
    """Clear the service cache (useful after re-auth)."""
    _service_cache.clear()
