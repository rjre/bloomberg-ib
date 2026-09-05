"""Interactive (two-way) chatbot: subscribe to a stream, listen for @mentions,
and reply automatically.

Usage:
    python -m examples.chatbot_testing
"""
import logging
import time

from ib_connect import IBConnectClient
from ib_connect.config import load_settings

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("chatbot_testing")


def mentions_chatbot(event: dict, chatbot_uuid: int) -> bool:
    for msg in event.get("messages", []):
        for element in msg.get("messageElements", []) or []:
            if element.get("contentType") == "MENTION":
                if element.get("user", {}).get("uuid") == chatbot_uuid:
                    return True
    return False


def build_reply(room_id: str, chatbot_uuid: int, reply_to_id: str) -> dict:
    return {
        "chatbotId": {"uuid": chatbot_uuid},
        "recipient": {"roomId": room_id},
        "chatMessage": [
            {
                "messageElements": [
                    {"contentType": "TEXT", "text": "You mentioned me! How can I help?"}
                ],
                "replyToId": reply_to_id,
            }
        ],
    }


def run(client: IBConnectClient, stream_id: str, chatbot_uuid: int) -> None:
    backfill_id = None
    while True:
        try:
            for event in client.read_stream(stream_id, backfill_id=backfill_id):
                backfill_id = event.get("backfillId", backfill_id)
                if event.get("@type") != "CONTENT_EVENT":
                    continue
                if not mentions_chatbot(event, chatbot_uuid):
                    continue
                room_id = event.get("roomId")
                for msg in event.get("messages", []):
                    reply = build_reply(room_id, chatbot_uuid, msg.get("ibPostId"))
                    result = client.post_chatbot_message(reply)
                    log.info("replied in %s: %s", room_id, result)
        except Exception:  # noqa: BLE001 - reconnect on any transport/API error
            log.exception("stream disconnected, reconnecting in 5s (backfillId=%s)", backfill_id)
            time.sleep(5)


if __name__ == "__main__":
    settings = load_settings()
    if not settings.stream_id or not settings.chatbot_uuid:
        raise SystemExit(
            "Set IB_CONNECT_STREAM_ID and IB_CONNECT_CHATBOT_UUID in your .env before running this."
        )
    client = IBConnectClient(
        settings.client_id, settings.client_secret, settings.base_url, region=settings.region
    )
    run(client, settings.stream_id, settings.chatbot_uuid)
