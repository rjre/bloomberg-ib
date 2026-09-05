"""JWT authentication for Bloomberg IB Connect.

This implementation is transcribed directly from Bloomberg's own official
`common.py` / `jwt.md`, shipped inside the IB Connect sample code downloads
(Feeds, Chatbot, and Chat Initiation packages - the JWT logic is byte-identical
across all three) at:
https://developer.bloomberg.com/pages/products/terminal_connect/downloads
(requires a Bloomberg-authenticated account; downloaded and verified 2026-09-05).

Confirmed claim set (from `jwt.md` and `common.py`):
  - iss:    your clientId
  - exp:    now + 300 seconds
  - nbf:    now - 60 seconds
  - iat:    now - 60 seconds
            (nbf/iat are backdated 60s in Bloomberg's own code "in case our
            clock is not well synchronized" - jwt.md's own validation rule
            listing a stricter exp-nbf<=30s window is stale/inconsistent with
            this; the actual shipped code uses the wider window above, so
            that's what's implemented here)
  - region: the literal string "default" - "default" is documented as the
            only allowed value, always sent, not configurable
  - method: the HTTP method of THIS specific request ("GET", "POST", ...)
  - path:   the URL path only - no scheme, no host, no query string
  - host:   the full base URL INCLUDING scheme (e.g. "https://api.bloomberg.com"),
            not just the hostname - this is exactly the `endpoint` constant in
            Bloomberg's common.py, passed through unchanged
  - jti:    a fresh UUID per request (the sample calls this "jti", not
            "request_id")
  - Signing: HMAC-SHA256, key = clientSecret hex-decoded to raw bytes
             (`binascii.unhexlify` in the original)
  - Transport: appended to the URL as a `jwt=` query parameter
  - One token per request - mint fresh, never reuse.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

import jwt as pyjwt

REGION = "default"  # "default" is the only allowed value per Bloomberg's jwt.md


@dataclass
class JWTAuth:
    client_id: str
    client_secret: str  # hex-encoded, as downloaded from console.bloomberg.com

    def _signing_key(self) -> bytes:
        try:
            return bytes.fromhex(self.client_secret)
        except ValueError as exc:
            raise ValueError(
                "IB_CONNECT_CLIENT_SECRET does not look like a hex string. "
                "Bloomberg signs with the secret hex-decoded to raw bytes - "
                "double check the value from your console.bloomberg.com "
                "credential file."
            ) from exc

    def build_claims(self, method: str, path: str, host: str) -> dict:
        now = int(time.time())
        return {
            "iss": self.client_id,
            "exp": now + 300,
            "nbf": now - 60,
            "iat": now - 60,
            "region": REGION,
            "method": method,
            "path": path,
            "host": host,
            "jti": str(uuid.uuid4()),
        }

    def token(self, method: str, path: str, host: str) -> str:
        """Mint a fresh, single-use JWT bound to this exact request.

        Call this once per outgoing request - never cache/reuse a token.
        `host` must be the full base URL including scheme (e.g.
        "https://api.bloomberg.com"), matching Bloomberg's own sample code.
        """
        return pyjwt.encode(
            self.build_claims(method, path, host),
            self._signing_key(),
            algorithm="HS256",
        )
