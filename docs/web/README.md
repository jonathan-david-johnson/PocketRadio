# PocketRadio Web

Browser companion to PocketRadio. Vite + React SPA, hosted on Vercel.
Backend: Supabase (RLS keyed by Pocket Casts `user_uuid`).

## Auth model

Single login = Pocket Casts account (no separate Supabase Auth signup). A
Supabase Edge Function validates the PC-issued token and maps it to
`user_uuid` for RLS, mirroring the iOS `ServerSettings.userId` /
`x-user-uuid` pattern.

## Repo

`pocket-radio-web/` — own git repo (`jonathan-david-johnson/pocket-radio-web`),
not yet scaffolded.

## Milestones

See `current_milestone.md` (symlink → `milestones/`). M1 is radio-only,
parity with console/menubar.
