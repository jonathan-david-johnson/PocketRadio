# PocketRadio Web

Browser companion to PocketRadio. Vite + React SPA, hosted on Vercel.
Backend: Supabase (RLS keyed by Pocket Casts `user_uuid`).

## Auth model

Single login = Pocket Casts account (no separate Supabase Auth signup). A
Supabase Edge Function validates the PC-issued token and maps it to
`user_uuid`, then is the **sole setter** of the `x-user-uuid` header on
Supabase calls.

Unlike iOS — which sets `x-user-uuid` client-side and gets away with it
because the anon key is buried in a binary — the browser exposes the anon
key and can forge any header. So web **never** talks to `user_uuid`-scoped
tables directly: all such access is proxied through the Edge Function. The
existing header-based RLS is not auth on its own; the proxy is what makes it
safe. See `milestones/milestone_1.md` § Security model.

## Repo

`pocket-radio-web/` — own git repo (`jonathan-david-johnson/pocket-radio-web`),
not yet scaffolded.

## Milestones

See `current_milestone.md` (symlink → `milestones/`). M1 is radio-only,
parity with console/menubar.
