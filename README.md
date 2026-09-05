# bloomberg-ib

A Python client + runnable examples for Bloomberg's **IB Connect** API (integrates Instant
Bloomberg — Bloomberg's real-time chat platform — with internal systems via REST).

Generated from Bloomberg's IB Connect developer docs and OpenAPI spec
([docs/REFERENCE.md](docs/REFERENCE.md), [docs/openapi.json](docs/openapi.json)).

## Setup

1. **Get credentials.** Go to [console.bloomberg.com](https://console.bloomberg.com) →
   Connectivity → Web API → Monitor and Manage → Create New Application. Download the credential
   file (`clientId`, `clientSecret`, `expiration`).
2. **Allowlist your IP(s)** in the Enterprise Console, IP Allowlist tab.
3. **Ask your Bloomberg rep for a stream** if you don't already have one (required for Feeds,
   On Demand, Idea Drawer, and interactive Chatbots).
4. **Install dependencies** (Python 3.8+):

   ```bash
   pip install -r requirements.txt
   ```

5. **Configure credentials**: copy `.env.example` to `.env` and fill it in. `.env` is gitignored —
   never commit real credentials.

   ```bash
   cp .env.example .env
   ```

## Project layout

```
ib_connect/          importable client library
  auth.py            JWT minting (clientId/clientSecret -> short-lived token per request)
  client.py          IBConnectClient - wraps every endpoint in docs/openapi.json
  config.py          loads IB_CONNECT_* env vars

examples/            runnable scripts mirroring the Quick Start guide
  example_read_stream.py       consume a Base/Enriched/On Demand feed
  example_chat_initiation.py   send a Chat Initiation (Blast Window) message
  example_chatbot.py           post as a chatbot: text, links, mentions, tables, ...
  chatbot_testing.py           two-way chatbot: listen for @mentions, auto-reply

docs/
  REFERENCE.md       condensed product/API notes
  openapi.json        Bloomberg's published OpenAPI 3.0 spec for IB Connect
```

## Running an example

```bash
python -m examples.example_read_stream
python -m examples.example_chat_initiation
python -m examples.example_chatbot
python -m examples.chatbot_testing
```

`example_read_stream.py` and `chatbot_testing.py` use `IB_CONNECT_STREAM_ID` from `.env`.
`chatbot_testing.py` also needs `IB_CONNECT_CHATBOT_UUID`.

## Using the client directly

```python
from ib_connect import IBConnectClient

client = IBConnectClient(client_id="...", client_secret="...")

client.health_check()
client.list_streams()

for event in client.read_stream("<stream_id>"):
    ...  # CONTENT_EVENT, ADDITIONAL_ENRICHMENTS_EVENT, JOIN_ROOM_EVENT, ...
```

## JWT claim shape

IB Connect requires a JWT signed with your `clientId`/`clientSecret` on every request, one token
per request. Bloomberg's own sample repo for this (`jwt.md` / `authentication_service_mode.md`)
sits behind a console.bloomberg.com / blpprofessional.com login this project couldn't reach, so
`ib_connect/auth.py` was cross-checked instead against two independent public sources describing
the same underlying "Bloomberg Web API" JWT scheme (IB Connect shares its credential flow and
"Web API Connectivity policy" doc with Bloomberg's other Web API products):

- [SAP Cloud Integration's Bloomberg JWT auth blog](https://blogs.sap.com/2022/07/28/sap-cloud-integration-bloomberg-api-integration-using-jwt-oauth-authentication./) —
  working Groovy reference implementation, plus real "invalid path parameter" errors from
  production traffic against this API family.
- Bloomberg's own `beap_lib.beap_auth` Python package (`Credentials`, `BEAPAdapter`), as consumed
  by the open-source [QF-Lib project](https://qf-lib.readthedocs.io/en/v2.2/_modules/qf_lib/data_providers/bloomberg_beap_hapi/bloomberg_beap_hapi_data_provider.html)
  against the same `https://api.bloomberg.com` host.

Confirmed and implemented: claim set `{iat, exp, nbf, iss, method, path, host, request_id}`, where
`method`/`path`/`host` describe the exact request the token is for (a mismatch is rejected as
"invalid path parameter"), `host` excludes the scheme, `path` excludes host/query string, tokens
are short-lived (30s) and single-use, and signing is HMAC-SHA256 with the `clientSecret`
**hex-decoded to raw bytes** (not the hex string itself). `IBConnectClient` mints a fresh token
bound to each request automatically — you don't need to touch this.

**Still unconfirmed for IB Connect specifically:** the `region` claim. It's part of the shared
scheme per the sources above, but nothing reachable states what value (or whether one at all) IB
Connect expects, since its docs only ever show a single `api.bloomberg.com` host. Left optional —
set `IB_CONNECT_REGION` only if your Bloomberg representative confirms it's required.

Sanity-check all of this with a real `client.health_check()` call before relying on it.

## Security

- `.env`, `*.credentials.json`, and `credentials.json` are gitignored. Never commit real
  `clientId`/`clientSecret` values.
- Credentials expire on the date in the downloaded credential file — rotate before then.
