-- Per-station lyric sync offset (seconds). Positive/negative correction the
-- user dials in via the +/- controls so synced lyrics line up with the audio
-- (stations differ: KCRW ~ -42s HLS buffer, KEXP ~ +1s).
-- user_uuid = ServerSettings.userId from Pocket Casts iOS (x-user-uuid header).

create table lyric_offsets (
  user_uuid       text        not null,
  station_id      text        not null,
  offset_seconds  integer     not null default 0,
  updated_at      timestamptz not null default now(),
  primary key (user_uuid, station_id)
);

create index on lyric_offsets (user_uuid);

alter table lyric_offsets enable row level security;

-- Same header-based policy as the other tables (migration 005).
create policy "own rows only" on lyric_offsets
  using (user_uuid = (current_setting('request.headers', true)::json->>'x-user-uuid'))
  with check (user_uuid = (current_setting('request.headers', true)::json->>'x-user-uuid'));
