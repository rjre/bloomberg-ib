"""JWT authentication for Bloomberg Web APIs (IB Connect and related products).

IB Connect's own Quick Start guide is thin on claim-level detail ("The JWT
must be signed using your clientId and clientSecret... one token per
request"), and Bloomberg's official sample code for this is gated behind a
console.bloomberg.com / blpprofessional.com login this project has no access
to. What's implemented below was cross-checked against independent, publicly
reachable sources describing the same underlying "Bloomberg Web API" JWT
scheme that IB Connect explicitly shares (its docs point at the very same
console.bloomberg.com credential flow and the same "Web API Connectivity
policy" document used by Bloomberg's other Web API products, e.g. Data
License / BEAP HAPI, which also runs on `https://api.bloomberg.com`):

  - SAP Cloud Integration's public blog on Bloomberg JWT auth, with a working
    Groovy reference implementation and real "invalid path parameter" errors
    from production traffic against this same API family:
    https://blogs.sap.com/2022/07/28/sap-cloud-integration-bloomberg-api-integration-using-jwt-oauth-authentication./
  - Bloomberg's own `beap_lib.beap_auth` Python package (`Credentials`,
    `BEAPAdapter`), as consumed by the open-source QF-Lib project against
    `https://api.bloomberg.com`:
    https://qf-lib.readthedocs.io/en/v2.2/_modules/qf_lib/data_providers/bloomberg_beap_hapi/bloomberg_beap_hapi_data_provider.html

Confirmed (consistent across both sources above):
  - Claim set: iat, exp, nbf, iss, method, path, host, request_id.
  - `iss` is your clientId.
  - `method` is the HTTP method of THIS specific request ("GET", "POST", ...).
  - `path` is the URL path only - no scheme, no host, no query string.
    Bloomberg rejects a token whose `path` doesn't exactly match the request
    ("This JWT has invalid path parameter").
  - `host` is the hostname only, no scheme (e.g. "api.bloomberg.com", not
    "https://api.bloomberg.com" - a documented, real-world fix for the same
    error above).
  - `request_id` is a fresh UUID per request.
  - Tokens are short-lived and single-use (Bloomberg's own Groovy sample uses
    a 30 second expiry) - mint one per request, never reuse.
  - Signing: HMAC-SHA256, where the key is your clientSecret **hex-decoded to
    raw bytes**, not the hex string itself.

Still NOT verified specifically for IB Connect (flagged, not guessed):
  - The `region` claim. It's part of the shared Bloomberg Web API JWT scheme
    per the sources above, but nothing we could reach states what value (or
    whether one at all) IB Connect expects - its docs only ever show a single
    `api.bloomberg.com` host with no region parameter. Left optional here:
    pass `region=` if your Bloomberg representative confirms IB Connect
    requires one; omitted from the token entirely by default.

Before relying on this in production, sanity check it with a real
`IBConnectClient.health_check()` call and adjust if Bloomberg's response
says otherwise.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Optional

import jwt as pyjwt


@dataclass
class JWTAuth:
    client_id: str
    client_secret: str  # hex-encoded, as downloaded from console.bloomberg.com
    ttl_seconds: int = 30
    region: Optional[str] = None

    def _signing_key(self) -> bytes:
        try:
            return bytes.fromhex(self.client_secret)
        except ValueError as exc:
            raise ValueError(
                "IB_CONNECT_CLIENT_SECRET does not look like a hex string. "
                "Bloomberg's Web API JWT scheme signs with the secret "
                "hex-decoded to raw bytes - double check the value from your "
                "console.bloomberg.com credential file."
            ) from exc

    def build_claims(self, method: str, path: str, host: str) -> dict:
        now = int(time.time())
        claims = {
            "iat": now,
            "nbf": now,
            "exp": now + self.ttl_seconds,
            "iss": self.client_id,
            "method": method.upper(),
            "path": path,
            "host": host,
            "request_id": str(uuid.uuid4()),
        }
        if self.region:
            claims["region"] = self.region
        return claims

    def token(self, method: str, path: str, host: str) -> str:
        """Mint a fresh, single-use JWT bound to this exact request.

        Call this once per outgoing request - never cache/reuse a token.
        """
        return pyjwt.encode(
            self.build_claims(method, path, host),
            self._signing_key(),
            algorithm="HS256",
        )
