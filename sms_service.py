import os

from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN"),
)


def _send_sms(body):
    sender = os.getenv("TWILIO_SMS_FROM", "").strip()
    recipient = os.getenv("TWILIO_SMS_TO", "").strip()
    if not sender or not recipient:
        return {
            "success": False,
            "error": "Set TWILIO_SMS_FROM to an SMS-capable Twilio number and TWILIO_SMS_TO to the destination number.",
        }
    if sender.startswith("whatsapp:") or recipient.startswith("whatsapp:"):
        return {"success": False, "error": "SMS numbers must not use the whatsapp: prefix."}

    try:
        result = client.messages.create(from_=sender, to=recipient, body=body)
        print("SMS SID:", result.sid)
        print("SMS status:", result.status)
        return {"success": True, "sid": result.sid, "status": result.status}
    except Exception as e:
        print(f"SMS sending failed: {e}")
        return {"success": False, "error": str(e)}


def send_sms_message(company, date, time, role=None):
    if role:
        body = f"Interview alert: {role} interview at {company} on {date} at {time}."
    else:
        body = f"Interview alert: interview at {company} on {date} at {time}."
    return _send_sms(body)


def send_sms_simple_message(message):
    return _send_sms(message)
