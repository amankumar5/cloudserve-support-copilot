import os
import sys

# Ensure parent path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.core.logging import logger

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def setup_google_oauth():
    print("=" * 60)
    print("Google Drive OAuth 2.0 Setup Utility")
    print("=" * 60)

    creds_path = settings.GOOGLE_CREDENTIALS_PATH
    token_path = settings.GOOGLE_TOKEN_PATH

    if not os.path.exists(creds_path):
        print(f"Error: Google OAuth credentials file not found at: {creds_path}")
        print("\nPlease follow these steps:")
        print("1. Go to Google Cloud Console (https://console.cloud.google.com/).")
        print("2. Enable the 'Google Drive API'.")
        print("3. Create an OAuth 2.0 Client ID (Desktop app or Web app).")
        print("4. Download the client secret JSON file and save it to 'data/credentials.json'.")
        print("5. Re-run this script to complete authorization.")
        return

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
        creds = flow.run_local_server(port=8080)

        os.makedirs(os.path.dirname(token_path), exist_ok=True)
        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())

        print(f"\nAuthorization successful! Token saved to: {token_path}")
    except Exception as e:
        logger.error(f"OAuth setup failed: {e}")
        print(f"\nFailed to complete OAuth authorization: {e}")


if __name__ == "__main__":
    setup_google_oauth()
