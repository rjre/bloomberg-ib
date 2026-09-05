"""Post messages to an IB chat room as a registered chatbot.

Demonstrates plain text, links, @mentions, a table, market commentary,
and an order update, per docs/REFERENCE.md (Chatbots) and
docs/openapi.json (ChatbotPostRequest / MessageElement).

Usage:
    python -m examples.example_chatbot
"""
import logging

from ib_connect import IBConnectClient
from ib_connect.config import load_settings

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("example_chatbot")

CHATBOT_UUID = 12345678  # Fake chatbot UUID, must be replaced with UUID of your chatbot
AT_MENTION_UUID = 11098254  # Working sample UUID, replace with UUID of user you want to @mention
ROOM_ID = "<room_id>"  # Ctrl + Shift + R on an IB room to see its ID. ex: "PCHAT-0x100000234567"


def post(client: IBConnectClient, chat_message: dict) -> None:
    payload = {
        "chatbotId": {"uuid": CHATBOT_UUID},
        "recipient": {"roomId": ROOM_ID},
        "chatMessage": [chat_message],
    }
    result = client.post_chatbot_message(payload)
    log.info("posted: %s", result)


def plain_text_message() -> dict:
    return {"text": "Hello from the IB Connect chatbot"}


def link_and_mention_message() -> dict:
    return {
        "messageElements": [
            {"contentType": "TEXT", "text": "Latest research is here: "},
            {"contentType": "LINK", "href": "https://oursite.org/", "title": "oursite"},
            {"contentType": "TEXT", "text": " "},
            {"contentType": "MENTION", "user": {"uuid": AT_MENTION_UUID}},
        ]
    }


def table_message() -> dict:
    return {
        "messageElements": [
            {
                "contentType": "TABLE",
                "rows": [
                    {
                        "isHeaderRow": True,
                        "cells": [
                            {"cell": [{"text": "Security"}]},
                            {"cell": [{"text": "Side"}]},
                            {"cell": [{"text": "Size"}]},
                        ],
                    },
                    {
                        "cells": [
                            {"cell": [{"text": "IBM 7 10/30/2045"}]},
                            {"cell": [{"text": "SELL"}]},
                            {"cell": [{"text": "5,000,000", "style": {"decorations": ["Bold"]}}]},
                        ]
                    },
                ],
            }
        ]
    }


def market_commentary_message() -> dict:
    """(Experimental, requires firm-specific enablement.)"""
    return {
        "messageElements": [
            {
                "contentType": "MARKET COMMENTARY",
                "title": "Out of the Box - Looking Out and Lookout",
                "body": {
                    "blocks": [
                        {
                            "type": "Paragraph",
                            "tokens": [
                                {"type": "Text", "text": "Jeff Bezos is having a tremendous year!"}
                            ],
                        }
                    ]
                },
            }
        ]
    }


def order_update_message() -> dict:
    """(Experimental, requires firm-specific enablement.)"""
    return {
        "messageElements": [
            {
                "contentType": "ORDER UPDATE",
                "body": {
                    "side": "SELL",
                    "size": 5000000,
                    "instrument": {"security_description": "IBM 7 10/30/2045"},
                    "orderType": "MKT",
                    "orderStatus": "FILLED",
                },
            }
        ]
    }


if __name__ == "__main__":
    settings = load_settings()
    client = IBConnectClient(settings.client_id, settings.client_secret, settings.base_url)

    post(client, plain_text_message())
    post(client, link_and_mention_message())
    post(client, table_message())
    # Market Commentary and Order Update require firm-specific enablement;
    # remove/comment these out if your firm hasn't had them turned on.
    # post(client, market_commentary_message())
    # post(client, order_update_message())
