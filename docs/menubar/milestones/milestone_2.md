# M2: Pocket Casts Authentication

**Status**: COMPLETED — 2026-05-21

## Goal

User logs in with Pocket Casts email/password. Bearer token persists in macOS Keychain across app launches.

## Done when

- First launch: popover shows email + password fields and a "Log In" button
- Entering valid Pocket Casts credentials → POST to `api.pocketcasts.com/user/login` → Bearer token stored in Keychain
- Login success: popover switches to player view (M1 content)
- Quit and relaunch: token found in Keychain → player view shown immediately, no login form
- "Log Out" button in player view clears Keychain and returns to login form
- Invalid credentials show an error message

## Architecture

```
POST https://api.pocketcasts.com/user/login
Content-Type: application/octet-stream

Body: protobuf Api_UserLoginRequest {
  email: string (field 1)
  password: string (field 2)
  scope: "mobile" (field 3)
}

Response: protobuf Api_UserLoginResponse {
  token: string (field 1)
  uuid: string (field 2)
  email: string (field 3)
}
```

Token stored via `SecItemAdd`/`SecItemCopyMatching` in macOS Keychain.
Token sent in future API calls as `Authorization: Bearer {token}` header.

## Files

### NEW
- `Services/PocketCastsAPI.swift` — Manual protobuf encode/decode for login + logout
- `Services/KeychainManager.swift` — Keychain read/write/delete for Bearer token + userId
- `View Models/AuthViewModel.swift` — @Published auth state (loggedIn, email, errorMessage), login/logout actions

### EDIT
- `ContentView.swift` — Toggle between LoginView and PlayerView based on auth state
- `PocketRadioApp.swift` — Check Keychain on launch

## Manual smoke

1. Build and run
2. Popover shows login form
3. Enter valid Pocket Casts credentials → tap Log In
4. Popover switches to player view
5. Quit app, relaunch → player view shown immediately (no login)
6. Tap Log Out → returns to login form
7. Enter invalid credentials → error message shown

## Note

macOS will show a Keychain authorization dialog on first token access after fresh build. Click "Always Allow" to grant permanent access.
