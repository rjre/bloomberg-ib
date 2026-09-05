# IB Connect — condensed reference

Notes distilled from Bloomberg's IB Connect developer docs (developer.bloomberg.com/pages/products/ib-connect)
and `openapi.json` in this folder. This is a summary for quick orientation while building against
this repo's client — always check the live Bloomberg docs / API reference for anything
load-bearing, since coverage and schemas evolve.

## What IB Connect is

IB Connect integrates Instant Bloomberg (IB), Bloomberg's real-time chat platform, with internal
systems over REST. A **stream** (set up by your firm's Bloomberg rep, requested by your Admin)
scopes which users/events/workflows a given integration sees.

## Products

- **Feeds** (`GET /ib/v1/streams/{stream_id}`) — long-lived streamed connection.
  - **Base**: raw chat content + metadata, delivered automatically as users chat.
  - **Enriched**: Base + NLP-derived structured data (`enrichments`): entities (`entity_org`,
    `entity_person`), asset-class objects (`fixed_income_cash`, `equity`, `fx`, `option`, `repo`,
    `mortgage`, `security_lending`, `credit_derivative`, `fixed_income_multi_leg`), and `intent`.
    Some enrichments arrive later via a follow-up `ADDITIONAL_ENRICHMENTS_EVENT` (within ~8s of
    the original `CONTENT_EVENT`).
  - **On Demand**: user right-clicks a chat post and manually sends it to a stream
    (`trigger: MANUAL_SEND_TO_INTERNAL`). Can include an edit/notes step
    (`requesterUpdate.message` / `.note`) before delivery. Enables use of the Idea Drawer as a
    response channel.
  - Feeds use **at-least-once delivery** — dedupe on `eventId`, not `backfillId`.
  - Optional **Room Membership Events** (`JOIN_ROOM_EVENT`, `LEAVE_ROOM_EVENT`,
    `CREATE_ROOM_EVENT`, `DELETE_ROOM_EVENT`) — opt in with `sendRoomMembershipEvents=true`.

- **Chat Initiation** (`POST /ib/v1/initiateChat`) — pre-populates a Blast Window for a specific
  user, who reviews and clicks Send. Max 50 recipients, 250 UTF-8 chars, sender must belong to the
  credentialed firm.

- **Idea Drawer** (`POST`/`PATCH` `/ib/v1/streams/{stream_id}`) — push suggestions
  (`IDEA` in response to a feed event via `eventCorrelationId`, or unsolicited `UIDEA`) into a
  user's Idea Drawer. Up to 3 suggestions per idea; suggestions can be `VIEW_ONLY` or shareable
  into the original room; `customActionButtons` trigger `CUSTOM_ACTION_FEEDBACK_EVENT` instead of
  edit/send. Retract with `RETRACT_SUGGESTION` + `suggestionId`. Feedback
  (`IdeaDrawerFeedbackEvent`: `SENT_SUGGESTION`/`EDITED_SUGGESTION`/`DELETED_SUGGESTION`) arrives on
  the stream if `sendIdeaDrawerFeedbackEvents=true`.

- **Chatbots** (`POST /ib/v1/chatbot`) — role accounts that look like normal IB users.
  - *Notification* (one-way): post only.
  - *Interactive* (two-way): subscribe to a stream to receive `@mention`s / replies, then post
    back via the same endpoint. Must be invited to a room by a member with Inviter permission
    (managed in console.bloomberg.com/ib or `{EC<GO>}`, under Products > IB Connect). A cross-firm
    bot auto-leaves a room once the last user from your firm leaves ("Abandon Ship").

## Content types (chatbots, Idea Drawer, Chat Initiation)

Plain text, links, `@mention`s (max 10/message), tables (header rows, col/row span, cell align,
bold/italic/underline/strikethrough), Market Commentary cards (title + image + rich-text body +
instrument metadata — needs firm enablement), and Order Update cards (needs firm enablement).
See `MessageElement` / `IdeaTextElement` / `IdeaStructuredElement` in `openapi.json` for the exact
shapes.

## Auth & connectivity

- HTTPS only, TLS 1.2+, IP allowlisting (Enterprise Console).
- Every request carries a JWT signed with your `clientId`/`clientSecret` (from
  console.bloomberg.com > Connectivity > Web API > Monitor and Manage). One token per request.
  `ib_connect/auth.py` implements claims `{iss, exp, nbf, iat, region, method, path, host, jti}`
  (`region` always `"default"`), HMAC-SHA256 signed with the hex-decoded `clientSecret`, transcribed
  directly from Bloomberg's own `jwt.md`/`common.py` in the IB Connect sample code downloads. See
  README.md "JWT claim shape" for the exact fields.
- Streams are long-lived HTTP connections with heartbeats; you own reconnect logic. Use
  `backfillId` (from the last event received) to resume after a disconnect of up to 5 minutes —
  older backfill IDs return HTTP 410, invalid ones HTTP 400.

## Endpoints implemented in `ib_connect/client.py`

| Method | Path | Purpose |
|---|---|---|
| GET | `/ib/v1/check` | health check |
| GET | `/ib/v1/streams` | list stream ids |
| GET | `/ib/v1/streams/{stream_id}` | subscribe (streamed) |
| POST | `/ib/v1/streams/{stream_id}` | post IDEA / UIDEA / RETRACT_SUGGESTION |
| PATCH | `/ib/v1/streams/{stream_id}` | patch a suggestion |
| POST | `/ib/v1/initiateChat` | Chat Initiation |
| POST | `/ib/v1/chatbot` | chatbot posts a message |
| GET | `/ib/v1/chatbot/{chatbot_id}/rooms` | rooms a chatbot belongs to |
| POST | `/ib/v1/files` | upload a file (e.g. Market Commentary title image) |

Full request/response schemas are in `openapi.json` (this is Bloomberg's published OpenAPI 3.0
spec for IB Connect — open it in any Swagger/Redoc viewer for a browsable reference).
