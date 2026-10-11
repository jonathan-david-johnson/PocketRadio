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

- The first sign-in, and each sign-in after the session expires, needs the
  phone. Sessions are rolling 90 days: each visit extends the expiry. The web
  player offers **Sign out** and **Sign out everywhere**; the latter ends every
  web session for the account.
- Before building on pairing, a spike must confirm that:
  - the fork completes approval from a QR code. Universal links on
    `pocketcasts.com` belong to Automattic's app, so the QR code likely needs
    the fork's `pktc://` scheme. The official app, if installed, may claim
    that scheme too.
  - `device/authorize` and the device-code `user/token` grant accept JSON
    through our Worker. iOS sends protobuf.
- The Worker stores the Pocket Casts tokens server-side and issues the
  web session. The browser never holds a Pocket Casts token.
