"""
Twilio SMS debug script -- FIRE Risk Intelligence Platform
Reads credentials from backend/.env and sends a test SMS.
"""

import os, sys, time
from dotenv import load_dotenv
from pathlib import Path

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding="utf-8")

# Load backend .env (works from any cwd)
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN")
FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")
TO_NUMBER   = os.getenv("DESTINATION_PHONE_NUMBER")

print("=" * 52)
print("  TWILIO SMS DEBUG -- FIRE Platform")
print("=" * 52)
print(f"SID   : {'[OK] ' + ACCOUNT_SID[:8] + '...' if ACCOUNT_SID else '[MISSING]'}")
print(f"TOKEN : {'[OK] ' + AUTH_TOKEN[:6] + '...'  if AUTH_TOKEN  else '[MISSING]'}")
print(f"FROM  : {FROM_NUMBER or '[MISSING]'}")
print(f"TO    : {TO_NUMBER   or '[MISSING]'}")
print("-" * 52)

if not all([ACCOUNT_SID, AUTH_TOKEN, FROM_NUMBER, TO_NUMBER]):
    print("[ERROR] One or more required env vars are missing. Aborting.")
    sys.exit(1)

try:
    from twilio.rest import Client
except ImportError:
    print("[ERROR] twilio package not installed. Run:  pip install twilio")
    sys.exit(1)

client = Client(ACCOUNT_SID, AUTH_TOKEN)

try:
    print("Sending test SMS ...")
    message = client.messages.create(
        body="FIRE Platform -- Twilio debug test. System operational.",
        from_=FROM_NUMBER,
        to=TO_NUMBER,
    )
    print(f"[OK] Message SID    : {message.sid}")
    print(f"     Initial status : {message.status}")
    print(f"     Date sent      : {message.date_sent}")
    print(f"     Price          : {message.price} {message.price_unit}")

    print("\nWaiting 6s for delivery confirmation ...")
    time.sleep(6)

    msg = client.messages(message.sid).fetch()
    print(f"\n[FINAL] Status      : {msg.status}")
    if msg.error_code:
        print(f"[ERROR] Code        : {msg.error_code}")
        print(f"        Message     : {msg.error_message}")
    else:
        print("[OK] No errors -- SMS delivered successfully!")

except Exception as e:
    print(f"\n[TWILIO ERROR] {e}")

print("=" * 52)
