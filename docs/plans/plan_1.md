# PocketRadio — App Plan

## Context

A free, open-source internet radio player focused on NPR/public radio stations (KCRW, WNYC, etc.) with a curated station list and the ability to add custom stream URLs. The app includes a "Support [Station]" donation link for each station. The author wants the project to be forkable and community-maintainable after they move on, but wants the donation mechanism preserved in any fork.

---

## License

**Recommendation: AGPL v3**

- Strongest copyleft: any derivative, including network-deployed forks, must release source under the same license.
- Copyright notice preservation is legally tested (Jacobsen v. Katzer, 2008): removing a URL from a copyright notice = copyright infringement.
- **Enforcement strategy**: embed each station's donation URL inside the app's copyright notice and inside the station data JSON. Stripping the copyright notice = infringement. The JSON is data (not just a UI button), making it harder to argue the donation link is merely cosmetic.
- Add a plain-English `NOTICE` file stating: *"Any distributed fork of this software must preserve, in a clearly visible location within the user interface, working links to the public radio stations' donation pages as distributed in `stations.json`. Removal of these links constitutes a violation of this license."*
- Accept that community norms do the heavy lifting for forks that comply in spirit but not letter.

What NOT to do: don't write a fully custom license — it tanks adoption and is unenforceable in ways a standard license isn't.

---

## Tech Stack

| Layer | Choice | Reason |
|-------|--------|--------|
| Framework | **Expo SDK 52+ (managed workflow)** | Minimizes native boilerplate; EAS Build handles signing |
| Language | TypeScript | Standard |
| Audio | **react-native-track-player v4** | Industry standard; Apache 2.0; background service, lock screen controls, notification controls, CarPlay/Android Auto |
| Widgets | **expo-widgets** | Zero native setup for iOS WidgetKit + Android; since you're Expo-managed this is the right fit; you can drop into native Swift/Kotlin for customization since you're comfortable there |
| Widget ↔ App data | App Groups (iOS UserDefaults) + SharedPreferences (Android) | Standard shared storage for widget refresh |
| Local storage | **MMKV** (via `react-native-mmkv`) | Fast; works in Expo via config plugin |
| Navigation | **Expo Router** | File-based, integrates cleanly with Expo |
| State | **Redux Toolkit** | User-familiar; RTK Query handles async cleanly |
---

## Architecture

```
┌─────────────────────────────────────────┐
│  Expo App (React Native)                │
│  ┌──────────┐  ┌──────────┐  ┌───────┐ │
│  │ Station  │  │  Player  │  │ Add   │ │
│  │ List     │  │  Screen  │  │Stream │ │
│  └──────────┘  └──────────┘  └───────┘ │
└────────────────────┬────────────────────┘
                     │
        ┌────────────┴─────────────┐
        ▼                          ▼
┌───────────────┐       ┌──────────────────┐
│ RNTP v4       │       │ Shared Storage   │
│ Background    │──────▶│ (playback state, │
│ Audio Service │       │  current station)│
└───────────────┘       └────────┬─────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
          ┌─────────────────┐     ┌──────────────────┐
          │ iOS Widget      │     │ Android Widget   │
          │ (WidgetKit/     │     │ (AppWidget via   │
          │  SwiftUI via    │     │  expo-widgets /  │
          │  expo-widgets)  │     │  Kotlin native)  │
          └─────────────────┘     └──────────────────┘
```

The widget shows: station logo, station name, play/pause button. Tapping opens the app.

---

## Data Model

### `stations.json` (bundled, read-only curated list)
```json
{
  "stations": [
    {
      "id": "kcrw",
      "name": "KCRW",
      "streamUrl": "https://...",
      "donateUrl": "https://www.kcrw.com/support",
      "logoUrl": "...",
      "description": "Music and NPR news from Santa Monica"
    }
  ]
}
```

### User-added streams (MMKV)
Same shape as above, `id` is a UUID, no `donateUrl` required (optional).

---

## Screens

1. **Station List** — curated stations + user-added streams. Each card has a "Support" button linking to `donateUrl`.
2. **Mini Player** — persistent bottom bar (always visible when a station is loaded). Play/pause, station name.
3. **Now Playing** — full screen player, station info, donate link prominent.
4. **Add Stream** — simple form: name + stream URL (validates the URL is a playable audio stream before saving).

No user accounts, no backend, no analytics.

---

## Key Implementation Notes

- **react-native-track-player background service**: configured via `PlaybackService.ts` registered at app root. Handles remote-play, remote-pause, remote-stop events (lock screen / notification).
- **Widget data sync**: after any playback state change, write `{ stationName, stationId, isPlaying, logoUrl }` to App Groups shared UserDefaults (iOS) and SharedPreferences (Android). expo-widgets reads this to update widget timeline.
- **Stream validation** on Add Stream: attempt a HEAD request to the URL; if `Content-Type` is `audio/*` or `application/ogg`, accept it.
- **Donate links**: rendered as `Linking.openURL()` calls — they open in the system browser, not an in-app webview, so the station gets the full referral.

---

## Critical Files (to create)

```
app/
  _layout.tsx          # Root layout, registers RNTP PlaybackService
  index.tsx            # Station list screen
  now-playing.tsx      # Full player screen
  add-stream.tsx       # Custom stream form
src/
  services/
    PlaybackService.ts # RNTP background handler
    player.ts          # RNTP setup, queue management
  store/
    playerStore.ts     # Zustand: current station, playback state
    streamStore.ts     # Zustand: user-added custom streams (persisted MMKV)
  data/
    stations.json      # Curated NPR station list with donate URLs
  widgets/
    PlayerWidget.tsx   # expo-widgets widget definition
    widgetSync.ts      # Writes shared storage after state changes
assets/
  logos/               # Station logos
LICENSE                # AGPL v3 full text
NOTICE                 # Plain-English donation preservation statement
```

---

## Verification

1. **Audio playback**: tap a station → audio starts, lock screen shows controls, app can be backgrounded and audio continues.
2. **Widget**: add widget to home screen → shows current station + play/pause; toggling in widget changes playback in app.
3. **Custom stream**: paste a valid MP3/HLS stream URL → appears in list → plays.
4. **Donate link**: tap "Support KCRW" → opens `kcrw.com/support` in Safari/Chrome.
5. **License check**: run `npx license-checker` → confirm no dependencies with licenses incompatible with AGPL v3.
