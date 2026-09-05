"""Thin client for the Bloomberg IB Connect REST API.

Endpoints implemented here mirror docs/openapi.json (Bloomberg's published
IB Connect API reference):

  GET   /ib/v1/check                       - health check
  GET   /ib/v1/documentation.json          - the API's own live OpenAPI schema
  GET   /ib/v1/streams                      - list stream ids available to your firm
  GET   /ib/v1/streams/{stream_id}          - subscribe to a stream (long-lived, streamed)
  POST  /ib/v1/streams/{stream_id}          - post a suggestion (IDEA / UIDEA / RETRACT_SUGGESTION)
  PATCH /ib/v1/streams/{stream_id}          - patch a previously posted suggestion
  POST  /ib/v1/initiateChat                 - Chat Initiation (Blast Window)
  POST  /ib/v1/chatbot                      - chatbot posts a message to a room
  GET   /ib/v1/chatbot/{chatbot_id}/rooms   - rooms a chatbot is a member of
  POST  /ib/v1/files                        - upload a file (returns a file id)

Every request's JWT is bound to that request's exact method/path/host (see
ib_connect/auth.py) - the token is minted fresh, right before the call, and
is not reused.
"""
from __future__ import annotations

import json
from typing import Any, Iterator, Optional

import requests

from .auth import JWTAuth

DEFAULT_BASE_URL = "https://api.bloomberg.com"


class IBConnectError(Exception):
    def __init__(self, status_code: int, body: Any):
        super().__init__(f"IB Connect API error {status_code}: {body}")
        self.status_code = status_code
        self.body = body


class IBConnectClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str = DEFAULT_BASE_URL,
        session: Optional[requests.Session] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.auth = JWTAuth(client_id, client_secret)
        self.session = session or requests.Session()

    # -- internal helpers -------------------------------------------------

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _auth_params(self, method: str, path: str, extra: Optional[dict] = None) -> dict:
        # `host` claim is the full base URL including scheme, matching
        # Bloomberg's own sample code (see ib_connect/auth.py).
        params = {"jwt": self.auth.token(method, path, self.base_url)}
        if extra:
            params.update({k: v for k, v in extra.items() if v is not None})
        return params

    @staticmethod
    def _raise_for_status(resp: requests.Response) -> None:
        if not resp.ok:
            try:
                body = resp.json()
            except ValueError:
                body = resp.text
            raise IBConnectError(resp.status_code, body)

    # -- health / streams metadata -----------------------------------------

    def health_check(self) -> dict:
        path = "/ib/v1/check"
        resp = self.session.get(self._url(path), params=self._auth_params("GET", path))
        self._raise_for_status(resp)
        return resp.json() if resp.content else {}

    def get_documentation(self) -> dict:
        """The API serves its own OpenAPI schema at this path (per Bloomberg's
        own `example_documentation.py` sample) - a live alternative/cross-check
        to docs/openapi.json."""
        path = "/ib/v1/documentation.json"
        resp = self.session.get(self._url(path), params=self._auth_params("GET", path))
        self._raise_for_status(resp)
        return resp.json()

    def list_streams(self) -> dict:
        path = "/ib/v1/streams"
        resp = self.session.get(self._url(path), params=self._auth_params("GET", path))
        self._raise_for_status(resp)
        return resp.json()

    # -- streaming ----------------------------------------------------------

    def read_stream(
        self,
        stream_id: str,
        send_content_events: bool = True,
        send_idea_drawer_feedback_events: bool = False,
        send_room_membership_events: bool = False,
        backfill_id: Optional[str] = None,
        chunk_timeout: Optional[float] = None,
    ) -> Iterator[dict]:
        """Open the long-lived stream connection and yield decoded JSON events.

        This is a generator: iterate it to consume events as they arrive.
        Each `dict` is one JSON envelope (CONTENT_EVENT, ADDITIONAL_ENRICHMENTS_EVENT,
        JOIN_ROOM_EVENT, etc). Track the `backfillId` field on each event so a
        reconnect after a drop can resume with `backfill_id=...` (see
        docs/REFERENCE.md, Backfill and Replay).
        """
        path = f"/ib/v1/streams/{stream_id}"
        params = self._auth_params(
            "GET",
            path,
            {
                "sendContentEvents": send_content_events,
                "sendIdeaDrawerFeedbackEvents": send_idea_drawer_feedback_events,
                "sendRoomMembershipEvents": send_room_membership_events,
                "backfillId": backfill_id,
            },
        )
        with self.session.get(
            self._url(path),
            params=params,
            stream=True,
            timeout=chunk_timeout,
        ) as resp:
            self._raise_for_status(resp)
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue  # blank lines / heartbeats keep the connection alive
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue

    def post_suggestion(self, stream_id: str, payload: dict) -> dict:
        """Post an IDEA / UIDEA / RETRACT_SUGGESTION to a stream (Idea Drawer)."""
        path = f"/ib/v1/streams/{stream_id}"
        resp = self.session.post(
            self._url(path),
            params=self._auth_params("POST", path),
            json=payload,
        )
        self._raise_for_status(resp)
        return resp.json() if resp.content else {}

    def patch_suggestion(self, stream_id: str, payload: dict) -> dict:
        path = f"/ib/v1/streams/{stream_id}"
        resp = self.session.patch(
            self._url(path),
            params=self._auth_params("PATCH", path),
            json=payload,
        )
        self._raise_for_status(resp)
        return resp.json() if resp.content else {}

    # -- chat initiation ------------------------------------------------------

    def initiate_chat(self, payload: dict) -> dict:
        path = "/ib/v1/initiateChat"
        resp = self.session.post(
            self._url(path),
            params=self._auth_params("POST", path),
            json=payload,
        )
        self._raise_for_status(resp)
        return resp.json() if resp.content else {}

    # -- chatbots -------------------------------------------------------------

    def post_chatbot_message(self, payload: dict) -> dict:
        path = "/ib/v1/chatbot"
        resp = self.session.post(
            self._url(path),
            params=self._auth_params("POST", path),
            json=payload,
        )
        self._raise_for_status(resp)
        return resp.json() if resp.content else {}

    def get_chatbot_rooms(self, chatbot_id: int) -> dict:
        path = f"/ib/v1/chatbot/{chatbot_id}/rooms"
        resp = self.session.get(self._url(path), params=self._auth_params("GET", path))
        self._raise_for_status(resp)
        return resp.json()

    # -- file uploads (used for Market Commentary title images, attachments) --

    def upload_file(self, file_path: str, mime_type: Optional[str] = None) -> dict:
        path = "/ib/v1/files"
        with open(file_path, "rb") as fh:
            files = {"file": (file_path, fh, mime_type)} if mime_type else {"file": fh}
            resp = self.session.post(
                self._url(path),
                params=self._auth_params("POST", path),
                files=files,
            )
        self._raise_for_status(resp)
        return resp.json()
