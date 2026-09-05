"""JWT authentication for IB Connect.

IB Connect requires a JSON Web Token (JWT), signed with your `clientId` /
`clientSecret` pair, on every request ("one token per request" per the
Quick Start guide). Credentials are obtained from
https://console.bloomberg.com (Connectivity > Web API > Monitor and Manage
> Create New Application) and look like:

    {
      "clientId": "...",
      "clientSecret": "...",
      "expiration": "YYYY-MM-DD HH:MM:SS+TZ"
    }

NOTE: Bloomberg's own sample repo ships a `jwt.md` / `authentication_service_mode.md`
that spells out the exact required claim set for this token. Those files were
not included in the documentation bundle this project was generated from, so
the claims below (`iss`/`sub` = clientId, short `exp`, standard `iat`/`nbf`/`jti`)
are a best-effort default based on the "signed with clientId/clientSecret,
one token per request" description in the Quick Start guide. Verify this
against Bloomberg's sample code / representative before relying on it, and
adjust `JWTAuth.build_claims` if the required claim names differ.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

import jwt as pyjwt


@dataclass
class JWTAuth:
    client_id: str
    client_secret: str
    ttl_seconds: int = 60

    def build_claims(self) -> dict:
        now = int(time.time())
        return {
            "iss": self.client_id,
            "sub": self.client_id,
            "iat": now,
            "nbf": now,
            "exp": now + self.ttl_seconds,
            "jti": str(uuid.uuid4()),
        }

    def token(self) -> str:
        """Mint a fresh, short-lived JWT. Call this once per request."""
        return pyjwt.encode(
            self.build_claims(),
            self.client_secret,
            algorithm="HS256",
        )
