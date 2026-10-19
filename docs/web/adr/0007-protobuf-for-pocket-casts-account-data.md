# Protobuf for Pocket Casts account data

Status: accepted (2026-10-18), by the user at the M1 gate.

## Decision

The web player's Pages Functions speak **protobuf** (`application/octet-stream`)
to the Pocket Casts server for account data: subscriptions, playlists, a
podcast's episodes, Up Next, episode position and played state, and named
settings. This is the wire format the iOS app and the menubar app use, so it is
the contract those clients already depend on.

The browser is unaffected. It talks only to our Functions, which return plain
JSON to it.

The device-authorization and token calls (`device/authorize`, `user/token`) keep
their current JSON form. They are proven live in staging and are not account
data.

## Why

M1 observed the server answering JSON on three list endpoints (HTTP 200, a JSON
object). That is tolerated behavior the native clients never use, with no
confirmed field names, and unknown support on the write endpoints
(`up_next/sync`, `sync/update_episode`). Protobuf is the same format the native
clients rely on for every one of these endpoints, so it is the more stable
choice and covers writes without a second format. Evidence:
[E3 record](experiments/2026-10-18_api_formats_and_station_terms.md).

## Consequences

- The Functions need a protobuf codec for the messages M2–M7 use. The choice
  between hand-written encode/decode (as in the menubar's `APIService.swift`)
  and a generated TypeScript library is made in M2; no `.proto` file is in this
  repo, only iOS's generated `api.pb.swift`. Field numbers and names come from
  that file.
- Keep all Pocket Casts protobuf code behind one Function module so the rest of
  the app sees plain typed objects.
- Treat every field as optional: protobuf omits defaults, and wrapper types
  (`BoolValue`, `Int32Value`) can be absent.
- Protobuf from the web has **not** been run against the live server. The first
  M2 use is the playlist list. Verify it with a read-only call before building on
  it, and record the result.
- The M1 JSON probe stays as historical evidence. It is not the production
  client.
- The sync write endpoints stay un-called until the user approves a test.

## Considered options

- **JSON only:** simplest and already observed on reads, but unofficial for these
  endpoints and unknown for writes.
- **Mixed (JSON reads, protobuf writes):** two code paths for little gain once a
  codec exists.
- **Protobuf (chosen):** matches the native clients and the menubar spec, at the
  cost of a codec and harder inspection.
