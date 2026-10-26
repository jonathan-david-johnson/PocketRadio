# Deploying the web player

How the web player is hosted and how the private staging site was set up. The
hosting decision is
[ADR 0002](../adr/0002-cloudflare-hosts-web-player-supabase-is-database.md).

## What exists

| Piece | State |
|---|---|
| Cloudflare Pages project `pocket-radio-web-m1-staging` | Direct upload, production branch `main`, behind Cloudflare Access |
| Supabase project `pocket-radio-web-m1-staging` | Separate Free database (`us-east-1`, `nano`). Only web migration `20261011000008` applied |
| Access | Two self-hosted applications, each with one Allow policy for the owner's email: the main host and the preview wildcard (`*.pocket-radio-web-m1-staging.pages.dev`). No Everyone or Bypass rule |
| Pages secrets (production environment only) | `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `PC_API_ENVIRONMENT=staging`, `SHARED_SUPABASE_URL`, `SHARED_SUPABASE_ANON_KEY` |

Since 2026-10-22 the staging site reads shared tables (`nav_layout`, which the
phone writes, and `curated_stations`) from the main PocketRadio database. The
`SHARED_SUPABASE_URL` and `SHARED_SUPABASE_ANON_KEY` Pages secrets point at it;
the `curated_stations` migration is applied there. Sessions and tokens stay in
the staging database, and the main database's service-role key is never given
to the site. The Layout is keyed by user UUID. The web takes it from the Pocket Casts token.
The phone writes under the `ServerSettings.userId` it cached at sign-in.
Matching servers is necessary but not sufficient: the phone must be a build on
the same server as `PC_API_ENVIRONMENT` (`StagingDebug`, `.net`) and its cached
id must equal the account's UUID. If the Sidebar ignores phone reorders, compare
the first 8 characters of the web session's UUID (staging `web_sessions`) with
the phone's writer in `nav_layout`. On 2026-10-23 they differed because the
phone's cached id was stale; signing out and back in on the phone fixed it.
Production has no deployment yet.

## Rules learned the hard way

- **Name the project.** `make deploy` requires `PAGES_PROJECT`; never deploy to
  the root configuration's default `pocket-radio-web` target.
- **Read what Wrangler says it uploads.** `wrangler pages deploy` uploads
  `./functions` from the working directory. A "placeholder" deploy run from the
  app folder uploaded the real server code. Deploy placeholders from an empty
  directory.
- **An empty Pages project returns Cloudflare error 522 behind Access.** A
  one-line placeholder deployment fixes it.
- **Protect both hosts.** Cloudflare's "Restrict previews" toggle protects
  preview URLs only. Create two Access applications in Zero Trust: the main
  `pages.dev` host and its wildcard. Confirm unauthenticated requests get a 302
  to the Access login before uploading the app.
- **Zero Trust onboarding asks for a payment method even on the Free plan.**
  Cloudflare says Free isn't charged. Stop if a paid plan is required.
- **Wrangler's OAuth login has no Access scopes.** Access applications were
  created with a scoped user API token (Access Apps and Policies Edit, Pages
  Edit, one account, IP-restricted). Wrangler then needs
  `CLOUDFLARE_ACCOUNT_ID` set. Keep the token in the ignored
  `.wrangler/cf-token` and delete it when the work is done.
- **Commit before you deploy.** The first upload shipped 28 uncommitted files,
  so the deployment couldn't be reproduced from git.
- **Staging and production token stores aren't namespaced.** Use a separate
  database for each, and don't point a production deployment at the staging
  store.

## Resuming

1. Check the Pages project has the three secrets, `PC_API_ENVIRONMENT=staging` and the two `SHARED_SUPABASE_*` secrets.
2. `make test typecheck build`, then check no secret appears in `dist/`.
3. `PAGES_PROJECT=pocket-radio-web-m1-staging make deploy`, after reading the
   file list Wrangler prints.
4. Sign in through Access, Pair from the phone, and check the page.

Nothing here has been checked against Linux, production `.com`, or Workers
paid-plan limits.
