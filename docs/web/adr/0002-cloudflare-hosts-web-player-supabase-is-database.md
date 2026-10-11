# Host the web player on Cloudflare, with Supabase as its database

Status: accepted (2026-10-11). Supersedes the Vercel hosting and Edge Function
proxy in the original web M1 plan.

Cloudflare Pages serves the web player. Cloudflare Workers, on the same origin,
run all of its server code: Pairing and sessions, Pocket Casts API calls, reads
and writes of user rows, and the stream relay. For the web player, Supabase is
only the database. Roku's `pc-relay` Edge Function is unaffected.

Supabase can't host the page itself. Edge Functions rewrite `text/html` to
`text/plain` unless the project pays for a custom domain, and Supabase says
website hosting is not a goal. Serving the page and the API from one origin
keeps the httpOnly session cookie first-party, which Safari requires. Workers
beat Vercel and Supabase functions because HTTP-triggered Workers have no
wall-clock limit while the client stays connected. That lets a Worker relay a
continuous radio stream. Once the relay is on Workers, putting the rest of the
server code there too leaves one runtime and one secret store, removes a
network hop, and needs no cookie forwarding.

## Considered Options

- **Cloudflare for page and all server code; Supabase as database (chosen).**
- **Cloudflare for page and relay; Supabase Edge Functions for the API behind
  an `/api/*` proxy.** Follows the `pc-relay` precedent, but splits server code
  across two runtimes and adds a hop to every request.
- **Vercel with an `/api/*` rewrite.** Its function duration limits rule out the
  stream relay.
- **Supabase with a paid custom domain.** Extra cost, against the vendor's
  stated intent, and Edge Function wall-clock limits still rule out the relay.

## Consequences

- For shared user tables (`radio_favorites`, `nav_layout`, web Lyric offsets),
  Workers call Supabase with the anon key and set `x-user-uuid` from the
  session. Existing RLS applies unchanged. The browser never sees the key or
  the user's id.
- Web-only secret tables (Pocket Casts tokens, sessions) get **no** anon-key
  policy. Header-trust RLS can't protect them, because the anon key ships in
  the iOS binary and anyone holding it can forge `x-user-uuid`. Workers reach
  these tables with the service-role key, stored as a Cloudflare secret.
- Before relying on the relay, verify Workers CPU limits (piping should use
  almost no CPU) and Cloudflare's terms for proxying audio.
- A custom domain is optional. The `*.pages.dev` address works until one is
  chosen.
