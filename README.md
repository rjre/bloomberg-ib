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

## Known gap: JWT claim shape

IB Connect requires a JWT signed with your `clientId`/`clientSecret` on every request. Bloomberg's
own sample repo documents the exact required claims in `jwt.md` / `authentication_service_mode.md`,
which weren't part of the docs this project was generated from. `ib_connect/auth.py` implements a
reasonable default (`iss`/`sub` = clientId, short-lived `exp`, HS256) — verify it against
Bloomberg's sample code or your Bloomberg representative before relying on it, and adjust
`JWTAuth.build_claims()` if the real claim set differs.

## Security

- `.env`, `*.credentials.json`, and `credentials.json` are gitignored. Never commit real
  `clientId`/`clientSecret` values.
- Credentials expire on the date in the downloaded credential file — rotate before then.
