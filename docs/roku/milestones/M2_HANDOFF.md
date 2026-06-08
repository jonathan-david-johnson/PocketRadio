# M2 Handoff — in progress, 2 bugs open (2026-05-31)

Resume doc for M2 (login + persistence via relay). M1 done + committed. M2 code written but **uncommitted** and **two bugs open**.

## State

- **Committed/pushed:** through M1 (audio) + milestone rewrite. Relay (`pc-relay`) live + proven.
- **Uncommitted working tree** (`pocket-radio-roku`): M2 implementation —
  - `source/registry.brs` — `AuthRead/AuthWrite/AuthClear` over `roRegistrySection("auth")`. (Has a debug `print` in `AuthRead`.)
  - `components/MainScene.brs` — rewritten: boot→`AuthRead`→`showMain` or two-step `KeyboardDialog` login → relay `login` → `AuthWrite` → `showMain`. `*`=logout, OK=play/pause KCRW (M1 audio carried forward).
  - `components/MainScene.xml` — title "M2"; now includes `registry.brs` + `secrets.brs` scripts.
- Currently sideloaded on device = this M2 build.

## What works
- Relay `login` from device → 200, token decoded. Audio still plays on main screen. Build clean (no BrightScript errors).

## 🐞 Bug 1 — persistence not sticking
Relaunch does NOT auto-login: telnet shows `login resp status=200` again instead of an "auto-login as …" path. So `AuthRead` returns invalid on relaunch → token never read back.
- **Leading hypothesis:** `roRegistrySection` writes are buffered until `Flush()`. If `data.userId` or `data.email` is `invalid`/non-string, `sec.Write(...)` errors mid-`AuthWrite` → `Flush()` never runs → token lost. Relay JSON keys are `token`,`userId`,`email` (camel `userId`) — verify `ParseJSON` gives non-invalid strings for all three before `Write`.
- Just-added debug: `AuthRead` prints `exists(token)=`. Next: add prints in `AuthWrite` (values/lengths) to confirm what's written + that `Flush` is reached.

## 🐞 Bug 2 — `*` opens OS options screen, doesn't log out
Pressing `*` shows the Roku options overlay rather than running `logout()`.
- `onKeyEvent` maps `key="options"` → `logout()` and returns true, but only when `m.mode="main"`. Either the key name isn't `"options"` at press time, or `m.mode<>"main"`, so `onKeyEvent` returns false and the OS handles `*`.
- **Possible coupling with Bug-flow:** if `KeyboardDialog.buttonSelected` fires spuriously (index 0) on attach, the prefilled login dialogs auto-advance — which would (a) make login "complete" with no user input and (b) make `logout()`→`promptEmail()` instantly re-login, looking like "didn't log out". **Confirm whether `buttonSelected` observer fires without a real press.** If so, guard it (ignore until a real press, or re-check `m.dlg` identity).

## Note: ECP keypress is BLOCKED on this device
`curl …:8060/keypress/<Key>` does NOT reach the channel (device "Control by mobile apps → Network access" is restrictive). **Key input must be tested on the physical remote.** `launch/dev` + telnet capture (port 8085) still work. So login-flow/`*` testing requires the user at the remote.

## Repro / test loop
```bash
cd pocket-radio-roku
ROKU_PASS=jdjroku make install          # sideload
# capture telnet while relaunching:
python3 -c '...socket read 8085 for ~10s...'  &   # (pattern used all session)
curl -s -d "" http://10.99.99.50:8060/launch/dev
# then drive login / press * on the PHYSICAL remote; read /tmp/roku_log.txt
```
Telnet filter: `grep -E "MainScene|registry|ERROR|BRIGHTSCRIPT"`.

## Next steps
1. Add `AuthWrite` debug prints; relaunch; confirm whether `Flush` runs + values valid. Fix the write (coerce to strings / guard invalids). Verify auto-login prints "auto-login as …" on relaunch.
2. Diagnose `KeyboardDialog.buttonSelected` spurious-fire; if real, guard. Re-test that login needs actual presses.
3. Fix `*` logout (confirm key name `"options"`; ensure `m.mode="main"`). Verify `*` → audio stop + AuthClear + email prompt; and that it does NOT auto-relogin.
4. Strip all debug prints. Build clean.
5. Commit (`pocket-radio-roku`) + mark M2 done in `milestone_2.md`, advance `current_milestone` → M3. Push.

## Key facts
- Relay URL + secret + test creds: gitignored `pocket-radio-roku/SECRETS.local.md` + `source/secrets.brs` (`RelayUrl()/RelaySecret()/TestEmail()/TestPassword()`).
- `source/secrets.brs` is required to run (zipped by `make build`, never committed). Components needing it must `<script uri="pkg:/source/secrets.brs">`.
- Gotchas: `source/` globals not in component scope (include via `<script>`); don't re-run one Task node from its own observer (fresh Task per call).
- Device `10.99.99.50`, dev pass in SECRETS.local.md (`jdjroku`).
