from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os
import json

# Allow OAuth for HTTP (for local development)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid"
]

def get_flow():
    flow = Flow.from_client_secrets_file(
        "credentials.json",
        scopes=SCOPES,
        redirect_uri="http://localhost:8000/auth/callback"
    )
    return flow

def get_gmail_credentials():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file(
            "token.json",
            SCOPES
        )

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Failed to refresh Gmail credentials: {e}")
                # Delete invalid token file
                if os.path.exists("token.json"):
                    os.remove("token.json")
                return None

    return creds

def save_credentials(creds):
    with open("token.json", "w") as token:
        token.write(creds.to_json())
