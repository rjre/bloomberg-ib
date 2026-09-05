"""Read a Base/Enriched Feed or On Demand stream in real time.

Usage:
    python -m examples.example_read_stream

Set IB_CONNECT_STREAM_ID in your .env, or hardcode `stream_id` below.
"""
import logging
import time

from ib_connect import IBConnectClient
from ib_connect.config import load_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("example_read_stream")


def handle_event(event: dict) -> None:
    event_type = event.get("@type")
    if event_type == "CONTENT_EVENT":
        room = event.get("roomName", event.get("roomId"))
        for msg in event.get("messages", []):
            sender = msg.get("sender", {}).get("fullName", "unknown")
            log.info("[%s] %s: %s", room, sender, msg.get("message"))
        for enrichment in event.get("enrichments", []):
            log.info("  enrichment: %s", enrichment)
    elif event_type == "ADDITIONAL_ENRICHMENTS_EVENT":
        log.info(
            "additional enrichments for %s: %s",
            event.get("contentEventId"),
            event.get("enrichments"),
        )
    elif event_type in ("JOIN_ROOM_EVENT", "LEAVE_ROOM_EVENT", "CREATE_ROOM_EVENT", "DELETE_ROOM_EVENT"):
        log.info("room membership event: %s -> %s", event_type, event.get("users"))
    else:
        log.info("event: %s", event)


def run(stream_id: str) -> None:
    settings = load_settings()
    client = IBConnectClient(settings.client_id, settings.client_secret, settings.base_url)

    backfill_id = None
    while True:
        try:
            for event in client.read_stream(stream_id, backfill_id=backfill_id):
                handle_event(event)
                backfill_id = event.get("backfillId", backfill_id)
        except Exception:  # noqa: BLE001 - reconnect on any transport/API error
            log.exception("stream disconnected, reconnecting in 5s (backfillId=%s)", backfill_id)
            time.sleep(5)


if __name__ == "__main__":
    """
    Reading the streamed data from IB
    """
    stream_id = "<YOUR_STREAM_ID>"

    settings = load_settings()
    run(settings.stream_id or stream_id)
