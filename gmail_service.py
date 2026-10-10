import base64
from googleapiclient.discovery import build
from auth import get_gmail_credentials

def get_gmail_service():
    creds = get_gmail_credentials()
    if not creds or not creds.valid:
        raise PermissionError("Gmail is not authenticated. Use the Authenticate Gmail button first.")
    service = build('gmail', 'v1', credentials=creds)
    return service

def get_new_emails(limit=5):
    try:
        print(f"Fetching up to {limit} emails from Gmail...")
        service = get_gmail_service()
        results = service.users().messages().list(
            userId="me",
            maxResults=limit
        ).execute()

        messages = results.get("messages", [])
        print(f"Found {len(messages)} Gmail messages")
        emails = []

        for message in messages:
            print(f"Processing Gmail message ID: {message['id']}")
            msg = service.users().messages().get(
                userId="me",
                id=message["id"],
                format="full"
            ).execute()

            headers = msg["payload"].get("headers", [])
            subject = ""
            sender = ""
            date = ""

            for header in headers:
                if header["name"].lower() == "subject":
                    subject = header["value"]
                if header["name"].lower() == "from":
                    sender = header["value"]
                if header["name"].lower() == "date":
                    date = header["value"]

            body = extract_body(msg["payload"])

            emails.append({
                "id": message["id"],
                "sender": sender,
                "subject": subject,
                "body": body,
                "date": date
            })
            print(f"Processed email from {sender}")

        print(f"Retrieved {len(emails)} Gmail messages")
        return emails
    except Exception as e:
        print(f"Gmail email fetch failed: {e}")
        raise

def extract_body(payload):
    body = ""

    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                data = part["body"].get("data")
                if data:
                    body += base64.urlsafe_b64decode(
                        data
                    ).decode(
                        "utf-8",
                        errors="ignore"
                    )
    else:
        data = payload["body"].get("data")
        if data:
            body = base64.urlsafe_b64decode(
                data
            ).decode(
                "utf-8",
                errors="ignore"
            )

    return body
