# Sign in to the web player by pairing with the phone

Status: accepted (2026-10-11). Supersedes the email/password login in the
original web M1 plan.

The web player signs in with Pocket Casts' device-code grant. It requests a
code (`POST device/authorize`), shows it as a QR code, and polls `user/token`
with grant type `urn:ietf:params:oauth:grant-type:device_code` until the user
approves the code in the PocketRadio iOS app. The fork already has the
approval screen (`DeviceApproveView`, reached through the `/pair` route).
Pairing works for any Pocket Casts account, including Sign in with Apple and
Google accounts. Apple and Google sign-in can't run on our origin, because
their identity tokens are issued only to Pocket Casts' own clients. The user's
password also never passes through our server.

## Considered Options

- **Pairing only (chosen).**
- **Email and password through our server**, as the menubar and Roku do.
  This works only for accounts that have a password, and it sends the
  password through our server.
- **Both.** This adds a second login path we don't need.

## Consequences

- Device-code authorization, polling and refresh use the `tv` scope, matching
  the fork's tvOS Pairing caller. The device authorization endpoint rejects the
  password-login `mobile` scope with either JSON or protobuf. M1 proved JSON
  code issuance, approval, session creation and the three read-only list calls
  on staging. The phone and the web must use the same Pocket Casts environment
  (`PC_API_ENVIRONMENT`): the fork's staging build approves against `.net`, and
  a web using `.com` makes the phone show "Your QR code expired" for any
  `invalid_grant`. See `archive/web-m1:docs/web/experiments/2026-10-12_live_pairing_setup.md`.
- The first sign-in, and each sign-in after the session expires, needs the
  phone. Sessions are rolling 90 days: each visit extends the expiry. The web
  player offers **Sign out** and **Sign out everywhere**; the latter ends every
  web session for the account.
- M1 confirmed that `device/authorize` and the device-code `user/token` grant
  accept JSON through our Worker, and that the fork approves a scanned code on
  the staging build. Not examined: camera routing and prefill of the `pktc://`
  scheme, and which app wins if the official Pocket Casts app is installed
  (Universal links on `pocketcasts.com` belong to Automattic's app). See the
  [communication doc](../architecture/communication.md).
- The Worker stores the Pocket Casts tokens server-side and issues the
  web session. The browser never holds a Pocket Casts token.
