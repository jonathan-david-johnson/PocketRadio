-- Synced tab bar layout (M12.3). One row per signed-in user: the ordered list
-- of tabs they've configured, so a layout change on one device shows up on
-- the next launch of another.
-- user_uuid = ServerSettings.userId from Pocket Casts iOS (x-user-uuid header).
-- slots is an ordered JSON array of TabDestination id strings, e.g.
-- ["podcasts","streams","playlist:<uuid>"] — not a serialized TabLayout.
-- Conflict resolution is last-write-wins on updated_at; no merge.

create table nav_layout (
  user_uuid   text        primary key,
  slots       jsonb       not null default '[]'::jsonb,
  updated_at  timestamptz not null default now()
);

alter table nav_layout enable row level security;

create policy "own rows only" on nav_layout
  using (user_uuid = (current_setting('request.headers', true)::json->>'x-user-uuid'))
  with check (user_uuid = (current_setting('request.headers', true)::json->>'x-user-uuid'));
