"""Interactive (two-way) chatbot: subscribe to a stream, detect when the bot
is @mentioned, and reply automatically.

Mention detection here mirrors Bloomberg's own `chatbot_testing.py` sample
(downloaded from the IB Connect Chatbot sample code package): an incoming
CONTENT_EVENT is treated as a mention of the bot when its `enrichments`
array contains an `entity_person` enrichment whose `instrument.uuid` matches
the chatbot's UUID *and* the bot's UUID appears in the event's
`participants` list. This requires an Enriched (not Base) feed stream - a
`MENTION` message element (used when *composing* a message) is not what
shows up on the receiving end.

Usage:
    python -m examples.chatbot_testing
"""
import logging
import time

from ib_connect import IBConnectClient
from ib_connect.config import load_settings

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("chatbot_testing")


def is_bot_mentioned(event: dict, chatbot_uuid: int) -> bool:
    is_mentioned = False
    for enrichment in event.get("enrichments", []) or []:
        if enrichment.get("@type") == "entity_person":
            if enrichment.get("instrument", {}).get("uuid") == chatbot_uuid:
                is_mentioned = True
                break
    if not is_mentioned:
        return False

    return any(
        participant.get("uuid") == chatbot_uuid
        for participant in event.get("participants", [])
    )


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
                if not is_bot_mentioned(event, chatbot_uuid):
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
    client = IBConnectClient(settings.client_id, settings.client_secret, settings.base_url)
    run(client, settings.stream_id, settings.chatbot_uuid)
