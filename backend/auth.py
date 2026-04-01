"""
BuyBy Trading System — Multi-user Kite Auth Manager
Manages multiple KiteConnect sessions keyed by UUID session IDs.
"""

import uuid
from datetime import datetime, timezone

from kiteconnect import KiteConnect


class AuthManager:
    """Manages multiple concurrent Kite authentication sessions."""

    def __init__(self):
        self.sessions: dict[str, dict] = {}

    def get_kite(self, api_key: str, api_secret: str) -> KiteConnect:
        """Create a new KiteConnect instance for given credentials."""
        return KiteConnect(api_key=api_key)

    def create_session(self, api_key: str, api_secret: str) -> tuple[str, str]:
        """
        Create a new auth session.
        Returns (session_id, login_url).
        """
        session_id = str(uuid.uuid4())
        kite = self.get_kite(api_key, api_secret)
        login_url = kite.login_url()

        self.sessions[session_id] = {
            "api_key": api_key,
            "api_secret": api_secret,
            "access_token": None,
            "kite": kite,
            "created_at": datetime.now(timezone.utc),
        }

        return session_id, login_url

    def complete_login(self, session_id: str, request_token: str) -> str:
        """
        Complete Kite login with the request_token from callback.
        Returns the access_token.
        """
        sess = self.sessions.get(session_id)
        if not sess:
            raise ValueError(f"Session {session_id} not found")

        kite: KiteConnect = sess["kite"]
        data = kite.generate_session(request_token, api_secret=sess["api_secret"])
        access_token = data["access_token"]

        kite.set_access_token(access_token)
        sess["access_token"] = access_token

        return access_token

    def get_session(self, session_id: str) -> dict | None:
        """Return session dict or None if not found."""
        return self.sessions.get(session_id)

    def create_dev_session(self) -> str:
        """Create a dev session without Kite OAuth — for dashboard preview."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "api_key": "dev",
            "api_secret": "dev",
            "access_token": "dev_token",
            "kite": None,
            "user_name": "Dev Trader",
            "created_at": datetime.now(timezone.utc),
        }
        return session_id

    def remove_session(self, session_id: str) -> None:
        """Remove a session and clean up."""
        self.sessions.pop(session_id, None)
