"""Loads IB Connect credentials/config from environment variables.

Copy .env.example to .env and fill in real values, or export the
IB_CONNECT_* variables another way. Never commit real credentials.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


@dataclass
class Settings:
    client_id: str
    client_secret: str
    base_url: str
    stream_id: Optional[str] = None
    chatbot_uuid: Optional[int] = None
    region: Optional[str] = None


def load_settings() -> Settings:
    client_id = os.environ.get("IB_CONNECT_CLIENT_ID")
    client_secret = os.environ.get("IB_CONNECT_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError(
            "IB_CONNECT_CLIENT_ID / IB_CONNECT_CLIENT_SECRET are not set. "
            "Copy .env.example to .env and fill in credentials downloaded from "
            "console.bloomberg.com (Connectivity > Web API > Monitor and Manage)."
        )
    chatbot_uuid = os.environ.get("IB_CONNECT_CHATBOT_UUID")
    return Settings(
        client_id=client_id,
        client_secret=client_secret,
        base_url=os.environ.get("IB_CONNECT_BASE_URL", "https://api.bloomberg.com"),
        stream_id=os.environ.get("IB_CONNECT_STREAM_ID"),
        chatbot_uuid=int(chatbot_uuid) if chatbot_uuid else None,
        # Unconfirmed for IB Connect - see ib_connect/auth.py. Only set
        # IB_CONNECT_REGION if your Bloomberg representative tells you to.
        region=os.environ.get("IB_CONNECT_REGION"),
    )
