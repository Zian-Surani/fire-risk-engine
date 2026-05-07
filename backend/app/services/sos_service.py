import os
import logging
import asyncio
from pathlib import Path
from twilio.rest import Client
from typing import Dict, Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Read directly from the .env file on disk — completely immune to whatever
# stale values a long-running process may have inherited in os.environ.
# ---------------------------------------------------------------------------
def _read_env_file() -> Dict[str, str]:
    """Parse backend/.env directly. Returns a {key: value} dict."""
    candidates = [
        Path(__file__).resolve().parents[2] / ".env",   # app/services/ → backend/.env
        Path(__file__).resolve().parents[3] / "backend" / ".env",
    ]
    for target in candidates:
        if target.exists():
            result: Dict[str, str] = {}
            for raw in target.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                result[k.strip()] = v.strip()
            logger.debug("[SOS] Loaded credentials from %s", target)
            return result
    logger.warning("[SOS] .env not found — falling back to os.environ")
    return {}


class SosService:
    def __init__(self):
        self.account_sid: str | None = None
        self.auth_token: str | None = None
        self.from_number: str | None = None
        self.destination_number: str | None = None
        self.client: Client | None = None
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """
        Always re-reads credentials from the .env FILE on disk — not os.environ.
        This prevents stale process-environment values from overriding .env.
        """
        # Read fresh from disk every time (fast — tiny file)
        env = _read_env_file()

        # Fall back to os.environ for any key missing from the file
        def _get(key: str) -> str:
            return env.get(key, os.getenv(key, "")).strip()

        sid   = _get("TWILIO_ACCOUNT_SID")
        token = _get("TWILIO_AUTH_TOKEN")
        frm   = _get("TWILIO_FROM_NUMBER")
        dest  = _get("DESTINATION_PHONE_NUMBER")

        # Skip re-init only when client is healthy AND creds haven't changed
        if (
            self._initialized
            and self.client is not None
            and sid == self.account_sid
            and token == self.auth_token
        ):
            return

        self.account_sid       = sid   or None
        self.auth_token        = token or None
        self.from_number       = frm   or None
        self.destination_number = dest  or None

        logger.info(
            "[SOS] Credentials loaded — SID: %s | FROM: %s | TO: %s",
            f"{sid[:8]}..." if sid else "MISSING",
            frm  or "MISSING",
            dest or "MISSING",   # <-- this must now always print +917043733724
        )

        if self.account_sid and self.auth_token:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("[SOS] Twilio client initialized OK.")
            except Exception as e:
                self.client = None
                logger.error("[SOS] Twilio Client() failed: %s", e)
        else:
            self.client = None
            logger.warning("[SOS] Missing TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN.")

        self._initialized = True

    # ------------------------------------------------------------------
    # Synchronous Twilio call — runs in a thread via asyncio.to_thread()
    # ------------------------------------------------------------------
    def _send_sms_sync(self, user_id: str) -> Dict[str, Any]:
        logger.info(
            "[SOS] Sending SMS — from=%s  to=%s  user=%s",
            self.from_number, self.destination_number, user_id
        )
        message_body = (
            f"FIRE.OS EMERGENCY ALERT\n\n"
            f"SOS triggered by: {user_id}\n"
            "Status: CRITICAL — Immediate response requested."
        )
        message = self.client.messages.create(  # type: ignore[union-attr]
            body=message_body,
            from_=self.from_number,
            to=self.destination_number,
        )
        logger.info(
            "[SOS] SMS delivered — SID: %s  status: %s  to: %s",
            message.sid, message.status, self.destination_number
        )
        return {
            "success": True,
            "message_sid": message.sid,
            "recipient": self.destination_number,
        }

    # ------------------------------------------------------------------
    # Public async entry-point used by the FastAPI route
    # ------------------------------------------------------------------
    async def send_emergency_alert(self, user_id: str = "Admin") -> Dict[str, Any]:
        logger.info("[SOS] send_emergency_alert — user=%s", user_id)
        self._ensure_initialized()

        if not self.client:
            msg = "Twilio not configured. Verify TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN in .env."
            logger.error("[SOS] Aborted — %s", msg)
            return {"success": False, "error": msg}

        if not self.from_number or not self.destination_number:
            msg = (
                f"Phone numbers incomplete — "
                f"FROM={self.from_number!r}  TO={self.destination_number!r}. "
                "Check TWILIO_FROM_NUMBER / DESTINATION_PHONE_NUMBER in .env."
            )
            logger.error("[SOS] Aborted — %s", msg)
            return {"success": False, "error": msg}

        try:
            # Non-blocking: run synchronous Twilio HTTP in a thread
            return await asyncio.to_thread(self._send_sms_sync, user_id)
        except Exception as e:
            logger.exception("[SOS] Unexpected error: %s", e)
            return {"success": False, "error": str(e)}


# Singleton used by FastAPI routes
sos_service = SosService()
