// pc-relay — JSON<->protobuf relay for the Pocket Casts API.
//
// Why this exists: Roku's roUrlTransfer truncates binary POST responses at the
// first NUL byte (proven in docs/roku/spikes.md, Spike 1), and Roku has no
// AsyncPostToFile. So the Roku channel speaks JSON to this relay; the relay
// speaks protobuf to api.pocketcasts.com. Stateless: the channel holds the
// auth token and passes it per call; the relay stores nothing.
//
// Access control: shared secret in the `x-relay-secret` header, checked against
// the RELAY_SECRET function env var. Deployed with verify_jwt = false.

import {
  concat,
  decode,
  Fields,
  getRepeatedBytes,
  getString,
  getVarint,
  getBytes,
  int32Value,
  lenDelimField,
  stringField,
  unwrapInt,
  varintField,
} from "./protobuf.ts";

const API_BASE = "https://api.pocketcasts.com";
const UA = "PocketRadio/1.0";

function octetHeaders(token?: string): HeadersInit {
  const h: Record<string, string> = {
    "Content-Type": "application/octet-stream",
    "Accept": "application/octet-stream",
    "User-Agent": UA,
  };
  if (token) h["Authorization"] = `Bearer ${token}`;
  return h;
}

async function pcPost(path: string, body: Uint8Array, token?: string): Promise<Uint8Array> {
  const resp = await fetch(API_BASE + path, {
    method: "POST",
    headers: octetHeaders(token),
    body,
  });
  if (resp.status === 401 || resp.status === 403) {
    throw new RelayError(resp.status, "unauthorized");
  }
  if (!resp.ok) {
    throw new RelayError(502, `pocketcasts ${path} -> ${resp.status}`);
  }
  return new Uint8Array(await resp.arrayBuffer());
}

class RelayError extends Error {
  constructor(public status: number, msg: string) {
    super(msg);
  }
}

// BrightScript ParseJSON rejects \uXXXX escape sequences — both surrogate pairs
// (non-BMP chars) and control characters (U+0000-U+001F) that JSON.stringify emits.
// Strip both from string values before serializing.
function brsClean(v: unknown): unknown {
  if (typeof v === "string") {
    return v
      .replace(/[\uD800-\uDFFF]/g, "")   // surrogate pairs (emoji, etc)
      .replace(/[\x00-\x1F\x7F]/g, "");  // control chars
  }
  if (Array.isArray(v)) return v.map(brsClean);
  if (v !== null && typeof v === "object") {
    return Object.fromEntries(
      Object.entries(v as Record<string, unknown>).map(([k, val]) => [k, brsClean(val)]),
    );
  }
  return v;
}

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(brsClean(data)), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

// ---- handlers --------------------------------------------------------------

// POST /user/login — no auth. {email,password} -> {token,userId,email}
async function login(p: any) {
  const body = concat(
    stringField(1, p.email),
    stringField(2, p.password),
    stringField(3, "mobile"),
  );
  const resp = decode(await pcPost("/user/login", body));
  return json({
    token: getString(resp, 1),
    userId: getString(resp, 2),
    email: getString(resp, 3),
  });
}

// Fetch the user's podcast subscriptions as a uuid -> title map.
// up_next/sync only returns the podcast UUID per episode, not its name.
async function fetchPodcastTitles(token: string): Promise<Map<string, string>> {
  const body = concat(stringField(1, "2"), stringField(2, "mobile"));
  const resp = decode(await pcPost("/user/podcast/list", body, token));
  const map = new Map<string, string>();
  for (const b of getRepeatedBytes(resp, 1)) {
    const e = decode(b);
    const uuid = getString(e, 1) ?? "";
    if (uuid) map.set(uuid, getString(e, 4) ?? "");
  }
  return map;
}

// Fetch authoritative playback positions for a set of podcasts, keyed by episode uuid.
// /user/podcast/episodes returns bare varints (f3 playedUpTo, f6 duration).
async function fetchPlaybackData(
  token: string,
  podcastUuids: string[],
): Promise<Map<string, { playedUpTo: number; duration: number }>> {
  const map = new Map<string, { playedUpTo: number; duration: number }>();
  const lists = await Promise.all(
    podcastUuids.map(async (pu) => {
      const body = concat(
        stringField(1, "2"),
        stringField(2, "mobile"),
        stringField(3, pu),
      );
      return decode(await pcPost("/user/podcast/episodes", body, token));
    }),
  );
  for (const resp of lists) {
    for (const b of getRepeatedBytes(resp, 1)) {
      const e = decode(b);
      const uuid = getString(e, 1) ?? "";
      if (!uuid) continue;
      map.set(uuid, {
        playedUpTo: getVarint(e, 3) ?? 0,
        duration: getVarint(e, 6) ?? 0,
      });
    }
  }
  return map;
}

// POST /up_next/sync (read) — Bearer. {deviceId} -> {episodes:[...]}
async function upNext(p: any) {
  const body = concat(
    varintField(1, Date.now()),
    stringField(2, "2"),
    stringField(6, p.deviceId),
  );
  // Fetch the queue and the podcast-name map in parallel; both need the token.
  const [rawSync, titles] = await Promise.all([
    pcPost("/up_next/sync", body, p.token),
    fetchPodcastTitles(p.token),
  ]);
  const resp = decode(rawSync);

  // f4 = repeated EpisodeResponse, f5 = repeated EpisodeSyncResponse
  const episodes = getRepeatedBytes(resp, 4).map((b) => {
    const e = decode(b);
    const published = getBytes(e, 5); // Timestamp{ f1 = seconds }
    const podcast = getString(e, 3) ?? "";
    return {
      title: getString(e, 1) ?? "",
      url: getString(e, 2) ?? "",
      podcast,
      podcastName: titles.get(podcast) ?? "",
      uuid: getString(e, 4) ?? "",
      published: published ? unwrapInt(published) ?? 0 : 0,
      playedUpTo: 0,
      duration: 0,
    };
  });

  const syncByUuid = new Map<string, { playedUpTo: number; duration: number }>();
  for (const b of getRepeatedBytes(resp, 5)) {
    const s = decode(b);
    const uuid = getString(s, 1);
    if (!uuid) continue;
    syncByUuid.set(uuid, {
      playedUpTo: unwrapInt(getBytes(s, 6)) ?? 0, // f6 = Int32Value
      duration: unwrapInt(getBytes(s, 7)) ?? 0, // f7 = Int32Value
    });
  }
  for (const ep of episodes) {
    const s = syncByUuid.get(ep.uuid);
    if (s) {
      ep.playedUpTo = s.playedUpTo;
      ep.duration = s.duration;
    }
  }

  // up_next/sync f5 doesn't reliably carry the latest resume position, so overlay
  // authoritative playedUpTo/duration from /user/podcast/episodes (one call per
  // distinct podcast, in parallel). Without this, episodes restart from 0 on reload.
  const podcastUuids = [...new Set(episodes.map((e) => e.podcast).filter(Boolean))];
  if (podcastUuids.length) {
    const playback = await fetchPlaybackData(p.token, podcastUuids);
    for (const ep of episodes) {
      const pb = playback.get(ep.uuid);
      if (pb) {
        if (pb.playedUpTo > 0) ep.playedUpTo = pb.playedUpTo;
        if (pb.duration > 0) ep.duration = pb.duration;
      }
    }
  }

  // First f4 entry = top of queue / currently playing.
  return json({ episodes });
}

// POST /user/podcast/episodes — Bearer. {podcastUuid} -> [{uuid,playedUpTo,duration}]
// NOTE: here playedUpTo/duration are BARE varints (f3/f6), not Int32Value.
async function podcastEpisodes(p: any) {
  const body = concat(
    stringField(1, "2"),
    stringField(2, "mobile"),
    stringField(3, p.podcastUuid),
  );
  const resp = decode(await pcPost("/user/podcast/episodes", body, p.token));
  const items = getRepeatedBytes(resp, 1).map((b) => {
    const e = decode(b);
    return {
      uuid: getString(e, 1) ?? "",
      playedUpTo: getVarint(e, 3) ?? 0,
      duration: getVarint(e, 6) ?? 0,
    };
  });
  return json({ episodes: items });
}

// POST /sync/update_episode — Bearer. Save playback position/status.
async function updateEpisode(p: any) {
  const body = concat(
    stringField(1, p.uuid),
    stringField(2, p.podcast),
    int32Value(3, p.position | 0), // Int32Value{ f1 = seconds }
    varintField(4, p.status | 0), // 1 notPlayed / 2 inProgress / 3 completed
    varintField(5, p.duration | 0),
  );
  await pcPost("/sync/update_episode", body, p.token);
  return json({ ok: true });
}

// POST /up_next/sync (change) — Bearer. action: "playNow" | "remove".
async function upNextChange(p: any) {
  const actionCode = p.change === "playNow" ? 1 : 4; // 1 playNow, 4 remove
  const change = concat(
    stringField(1, p.uuid),
    varintField(2, actionCode),
    varintField(3, Date.now()),
    stringField(4, p.title ?? ""),
    stringField(5, p.url ?? ""),
    stringField(6, p.podcast ?? ""),
  );
  const changes = lenDelimField(2, change); // Api_UpNextChanges{ f2 = Change }
  const body = concat(
    varintField(1, Date.now()),
    stringField(2, "2"),
    lenDelimField(4, changes),
    stringField(6, p.deviceId),
  );
  await pcPost("/up_next/sync", body, p.token);
  return json({ ok: true });
}

// POST /user/named_settings/update — Bearer, effectively read-only.
// Send only f2; nothing is written. -> {skipForward,skipBack}
async function namedSettings(p: any) {
  const body = stringField(2, "PocketRadio");
  const resp = decode(await pcPost("/user/named_settings/update", body, p.token));
  // f5 skipForward, f6 skipBack; each Api_Int32Setting{ f1 = Int32Value{ f1=int } }
  const unwrapSetting = (fn: number): number | undefined => {
    const settingBytes = getBytes(resp, fn);
    if (!settingBytes) return undefined;
    const inner = getBytes(decode(settingBytes), 1); // -> Int32Value
    return unwrapInt(inner);
  };
  return json({
    skipForward: unwrapSetting(5) ?? 45,
    skipBack: unwrapSetting(6) ?? 10,
  });
}

// POST /user/podcast/list — Bearer. -> [{uuid,title}]
async function podcastList(p: any) {
  const titles = await fetchPodcastTitles(p.token);
  const podcasts = [...titles].map(([uuid, title]) => ({ uuid, title }));
  return json({ podcasts });
}

const HANDLERS: Record<string, (p: any) => Promise<Response>> = {
  login,
  upNext,
  podcastEpisodes,
  updateEpisode,
  upNextChange,
  namedSettings,
  podcastList,
};

Deno.serve(async (req) => {
  if (req.method !== "POST") return json({ error: "POST only" }, 405);

  const secret = Deno.env.get("RELAY_SECRET");
  if (!secret) return json({ error: "relay misconfigured (no RELAY_SECRET)" }, 500);
  if (req.headers.get("x-relay-secret") !== secret) {
    return json({ error: "forbidden" }, 403);
  }

  let payload: any;
  try {
    payload = await req.json();
  } catch {
    return json({ error: "bad json" }, 400);
  }

  const handler = HANDLERS[payload?.action];
  if (!handler) return json({ error: `unknown action: ${payload?.action}` }, 400);

  // login needs no token; everything else does.
  if (payload.action !== "login" && !payload.token) {
    return json({ error: "missing token" }, 400);
  }

  try {
    return await handler(payload);
  } catch (e) {
    if (e instanceof RelayError) return json({ error: e.message }, e.status);
    return json({ error: String(e) }, 500);
  }
});
