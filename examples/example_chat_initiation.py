"""Send a Chat Initiation request (opens a Blast Window for the sender to review/send).

Usage:
    python -m examples.example_chat_initiation
"""
import logging

from ib_connect import IBConnectClient
from ib_connect.config import load_settings

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("example_chat_initiation")


def make_payload() -> dict:
    payload = {
        "sender": {"uuid": 3344334},
        "recipients": [
            {"uuid": 9008001},
            {"roomId": "PCHAT-0x0x0000001234567"},
            {"uuid": 776543},
        ],
        "chatMessage": {"text": "Hello World"},
    }
    return payload


if __name__ == "__main__":
    settings = load_settings()
    client = IBConnectClient(settings.client_id, settings.client_secret, settings.base_url)
    result = client.initiate_chat(make_payload())
    log.info("initiateChat response: %s", result)
