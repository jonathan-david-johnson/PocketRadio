# The web player is our own app, not a fork or an extension

Status: accepted (2026-10-11)

PocketRadio's web player is a standalone app in `pocket-radio-web/`. It calls
the Pocket Casts API directly and ports its logic from the open-source iOS fork
and the menubar app. iOS and Android fork Automattic's open-source apps, but
Pocket Casts' web player is proprietary: Automattic publishes only the iOS and
Android source (MPL-2.0). We chose a standalone app because configurable
navigation is a core feature, and we can only build it reliably in an app whose
navigation we control.

## Considered Options

- **Standalone app (chosen).** We own the navigation, Streams, lyrics, and
  installability. The cost is rebuilding every Pocket Casts screen the web
  player offers.
- **Browser extension on `pocketcasts.com`.** This keeps all of Pocket Casts'
  screens and sign-in, and avoids CORS because requests come from Pocket
  Casts' own origin. We rejected it because it modifies a proprietary page
  that breaks when Pocket Casts deploys. Making that page follow the synced
  tab layout would mean rewriting its sidebar from outside. An extension can't
  be installed as a web app, and Safari requires shipping it inside a macOS
  app.
- **Copying Pocket Casts' shipped web code.** It is proprietary, so this is
  not allowed.

## Consequences

- Each Pocket Casts screen on the web is a port, so web scope is chosen screen
  by screen rather than inherited.
- Pocket Casts' API allows only its own origin through CORS, so every Pocket
  Casts call goes through our server code (see ADR 0002).
