# Token cached in a 0600 config-dir file, not the OS keychain

The Pocket Casts token and user UUID are cached in
`~/.config/pocket-radio/state.json` (mode 0600); account credentials live in
`~/.config/pocket-radio/config.toml` (mode 0600). We do **not** use the macOS
Keychain.

## Why

Mini mode (`pocket-radio kcrw`) must start playing instantly with no interactive
prompt, which requires a token cached where a non-interactive process can read it
without an access dialog. The macOS Keychain can prompt on read and is mac-only,
which breaks both the fast-start requirement and Linux portability. A 0600 file
in the XDG config dir is the same trust model the menubar already accepts (it
ships hardcoded test credentials), and keeps the app cross-platform and testable.

## Consequences

- The account password may be stored in plaintext on disk at mode 0600. This is a
  deliberate, documented trade-off; users who prefer not to store a password can
  omit it and accept an interactive login prompt the first time (and on token
  expiry).
- On a `401`, the engine transparently re-logs-in from `config.toml` creds if
  present, else prompts once and re-caches the token.
- `state.json` also holds `device_id` and the favorites display order (the
  menubar keeps these in `UserDefaults`).
