# PocketRadio Web

The browser surface of PocketRadio: our own web player for the Pocket Casts
account and radio domain shared with iOS, menubar, console, and Roku. Navigation
terms follow the iOS tab bar glossary in `docs/ios/architecture/configurable-tab-bar.md`.

## Language

**Web player**:
PocketRadio's standalone browser app in `pocket-radio-web/`. It is not Pocket
Casts' proprietary web player, nor a wrapper around it.
_Avoid_: "web app" alone (ambiguous with Pocket Casts' web player), "PWA" as a name.

**Destination**:
A place the user can navigate to that can root a tab: Podcasts, Playlists,
Discover, Streams, Profile, Up Next, or a single playlist. The same set as on iOS.
_Avoid_: "tab" alone, "screen", "page".

**Manual playlist**:
A Pocket Casts playlist whose episodes the user picked by hand. Pocket Casts'
server returns its episodes directly.
_Avoid_: "static playlist", "list".

**Smart playlist**:
A Pocket Casts playlist defined by rules (podcasts, played state, release window,
and so on) whose episodes the client must work out. Pocket Casts' server returns
only the rules.
_Avoid_: "filter" (the legacy iOS name, still used in code as `EpisodeFilter`),
"auto playlist".

**Smart playlist placeholder**:
What the Web player shows for a Smart playlist until Smart playlist evaluation
ships: the name, a summary of the rules, and a pointer to the iPhone. The
tab stays in the Layout.

**Layout**:
The user's ordered list of Destinations, synced across devices. One Layout per
Pocket Casts account.
_Avoid_: "tab config", "nav settings".

**Stream relay**:
Our server-side pass-through that every radio station plays through on the Web
player. It forwards the audio and reports the track titles embedded in it.
_Avoid_: "proxy" alone (the API proxy is a different thing), "pc-relay" (the
existing Roku Edge Function).

**Track**:
A song playing on a radio station, identified by artist and title. Lyrics belong
to a Track.
_Avoid_: "episode" (podcasts only), "song" in code.

**Lyric offset**:
A per-station number of seconds that shifts lyric lines to match the audio. The
Web player keeps its own Lyric offsets, separate from the ones iOS and the
menubar share.
_Avoid_: "delay", "sync offset".

**Curated station**:
One of the hand-picked stations every PocketRadio surface offers, defined once in
Supabase. Distinct from a station the user found through Browse.
_Avoid_: "default station", "built-in station".

**Pairing**:
Signing the Web player in to a Pocket Casts account by approving a one-time code
in the PocketRadio iOS app. The only way to sign in to the Web player.
_Avoid_: "login" (implies a password), "device auth", "QR login".

**Sidebar**:
The Web player's navigation on a wide window: every Destination in one list,
split by the Bar line.
_Avoid_: "nav", "menu", "tab bar" (the narrow-window form).

**Bar line**:
The divider in the Sidebar at the point where the iPhone's tab bar ends and its
More tab begins. Destinations above it are on the phone's bar.
_Avoid_: "More row" (that is the iOS settings row), "separator".

**Streams**:
The radio destination, with Favorites and Browse (station search).
_Avoid_: "Radio", "Stations" as the destination name.
