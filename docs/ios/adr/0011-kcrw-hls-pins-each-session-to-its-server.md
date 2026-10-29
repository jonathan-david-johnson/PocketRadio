# 0011 — KCRW HLS pins each listening session to the server that owns it

**Status:** Accepted 2026-10-28 as the approach for the Debug experiment on `experiment/unified-skew`. The user selected it as the production path on 2026-10-29, conditional on the remaining route checks. Measured on the Mac and in a phone packet capture. Pinning passed phone runs on the speaker; Bluetooth, CarPlay and background playback are not yet tested.

**Decision:** For KCRW's HLS stream, the app fetches the master playlist itself and rewrites its variant URL to `http://<server>/…`, where `<server>` is the address that the listening session ID names. The variant playlist and every segment, whose URIs are relative, then go to the server that holds the session, whatever DNS returns. As a backstop, when the segment loader still stops, the app replaces the item, which starts a new session. The current code remains Debug-only. After Bluetooth, wired CarPlay, and locked/background checks pass, promote this pin-and-backstop path to Release; that requires a separate code change, manual validation, and approval to merge.

## What the server does

Measured on 2026-10-28 against `https://streams.kcrw.com/e24_aac/playlist.m3u8` from a Mac on two home networks, and in a capture of the phone's traffic over USB (`rvictl`).

| Question | Result |
|---|---|
| How is the stream served? | Every master playlist request starts a new listening session (the `Server` header says `Streaming Server 9.1.4`; ads come from AdsWizz). The variant URL carries the session in its query (`listeningSessionID`). Segment URIs are relative and carry no session. |
| How many servers are there? | Two. `streams.kcrw.com` resolves to `216.235.84.31` or `66.85.89.38`. Each address is always the same server (by its `Instance-id` header). The local resolver cached each answer for 30 s, and the answer changed between lookups: 12 changes in 15 minutes. The two servers serve the same audio, numbered 95 segments apart. |
| Which server holds a session? | The one that answered the master request. One `_`-separated field of the session ID is that server's `IP:port` in base64, with `!` for `=` (for example `MjE2LjIzNS44NC4zMTo4MA!` is `216.235.84.31:80`). It matched the answering server in every check. |
| What happens on the other server? | A segment request without the session gets an HTTP `404 Not Found` status code. Sent to each server by address: owner `200`, other `404`, over both HTTPS and plain HTTP. |
| Can a header or cookie choose the server? | No. `X-AIS-SessionID`, the `ListenerInfo` cookie (which arrives already expired) and `Instance-id` were all ignored. |
| Can the session in each segment URL fix it? | Not for AVPlayer. The other server then forwards the request, taking 7–11.5 s to the first byte, sometimes ending in `504 Gateway Timeout`. AVPlayer gives up on a segment after about one target duration (6 s). |
| Does HTTPS to the server's address work? | No. The certificate names `streams.kcrw.com`, not the address. Plain HTTP to the address works. |

## How it reaches the phone

- **AVPlayer reconnects.** In the capture, AVPlayer closed its own connections after 25–100 s and opened new ones. It also reconnected when the phone moved between Wi-Fi and cellular. A new connection made after DNS has changed reaches the other server.
- **The error follows at once.** Three times, AVPlayer logged `CoreMediaErrorDomain` `-12889` ("No response for media file in 6.013s") within 2 ms of closing a short connection to the other server. Each of those connections carried about 17–20 kB, consistent with an error response; the encryption hides the status.
- **Loading then stops.** In 7 of 10 earlier phone sessions the segment loader stopped with 113–119 s buffered. In four of them the buffer ran out about 2 minutes later. AVPlayer then waited 6–17 s and restarted 66–72 s back. Once, a Bluetooth session failed outright (`-12889` and teardown).
- **Other clients avoid it.** KCRW's iOS app plays one continuous connection at 192 kb/s, almost certainly the direct MP3 stream, not HLS. The web player uses HLS but fetches one segment at a time on the same connection. It played 9 minutes through 8 DNS changes with no failed request.

## Design choices

| Choice | Reason | Alternatives not selected |
|---|---|---|
| **Pin the variant to the owning server.** A resource loader serves only the master playlist under a custom scheme (`kcrwpin`), decodes the owner, and rewrites the variant on the master's own host to `http://<owner>/…`. If no owner decodes, the master passes through unchanged. Debug-only, KCRW HLS profile only. | On the Mac, AVPlayer forced to open a new connection for every request played 15 minutes through 12 DNS changes with no errors when pinned; unpinned, it logged 54 errors and ran dry within 5 minutes. The program-date clock and the saved skew (ADR 0010) are unchanged. | **A local proxy that prefetches and retries:** works, but it is far more code. **Serve segments from the resource loader:** AVPlayer passed one segment to the loader, then failed the item with `CoreMediaErrorDomain -12881`, whatever the content type. **The direct MP3 stream:** immune, but needs the media-time clock and a new calibration. |
| **Plain HTTP to the owner.** | HTTPS to an address fails the certificate check. The app already allows arbitrary loads (`NSAllowsArbitraryLoads`). | Pin the address under HTTPS: neither AVPlayer nor `URLSession` can pin an address while keeping the host name for the certificate. |
| **Keep the item replacement as a backstop.** While playing, if the end of the loaded range hasn't grown for 20 s, `DefaultPlayer` gives the same AVPlayer a fresh item (a new session), at most once per 60 s and three times per play. It re-applies the rate without seeking (ADR 0007). | On the phone before pinning, each replacement cost about 7 s of silence and about 7 s of content, with no replay. Without pinning, each new session lost its loader again within 40–90 s, so replacement alone is not a fix. All three numbers are hypotheses. | Reload through `PlaybackManager.play`: asynchronous activation and pause races. Wait for 20 s of `waiting`: the recovered stalls waited only 6 and 17 s, and the replay was already queued. |
| **Do not change the forward buffer.** | AVPlayer already buffers the whole window. | The 30 s suggested in [ADR 0007](0007-live-radio-resumes-after-a-stall-without-seeking.md) would hold less. |

## Consequences

- **The audio is unencrypted.** So is the session ID in the variant URL. Neither carries account data.
- **It depends on an undocumented format.** If KCRW changes the session ID, decoding fails and playback behaves as before pinning, with replacement as the backstop. If a server's address changes while a session is playing, that session's requests fail until the backstop replaces the item.
- **Each session has its own program-date phase.** Each session stamps its first segment with the time it opened. Eight sessions labeled the same segment with times spread over 5 s, so a saved skew carries up to about ±3 s between sessions (ADR 0010). A replacement can move the clock by that much.
- **A new session may start with an ad.** About 1 in 5–10 opened with an AdsWizz preroll of about 15 s, followed by `EXT-X-DISCONTINUITY`. Its effect on the clock was not measured.
- **The provider could fix it for everyone** by putting the session in segment URIs, or by forwarding within one target duration.

## Verification

| Behavior | Covered by |
|---|---|
| Server behavior, DNS rotation, session-to-server encoding, KCRW app and web player behavior | Mac probes and the phone capture on 2026-10-28, summarized above. The probe scripts and capture were temporary and are not in the repo. |
| Decoding the owner; rewriting the variant; leaving the master unchanged without an owner or on another host; the loader's lifetime | `KCRWSessionPinningTests` |
| The real loader with AVPlayer: pinned variant, program date present, buffer full, no errors over 2.5 minutes | Mac run of `KCRWSessionPinning.swift` on 2026-10-28 |
| Backstop watchdog, rate limit and recovery owner | `LiveLoaderWatchdogTests`, `KCRWReconnectBudgetTests`, `KCRWLoaderRecoveryTests` |
| Pinning on a real phone | About 21 minutes across three sessions on 2026-10-28 and 2026-10-29, on the speaker: Wi-Fi, cellular, a pause and resume, and a live Wi-Fi to cellular switch. No AVPlayer errors, stalls or replacements; the buffer stayed at 107–122 s. Bluetooth, CarPlay and background playback not yet run. |
