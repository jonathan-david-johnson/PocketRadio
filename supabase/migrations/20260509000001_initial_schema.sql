-- VibeStreams initial schema
-- user_uuid = ServerSettings.userId from Pocket Casts iOS

create table radio_favorites (
  user_uuid   text        not null,
  station_id  text        not null,
  added_at    timestamptz not null default now(),
  primary key (user_uuid, station_id)
);

create table custom_streams (
  id          uuid        primary key default gen_random_uuid(),
  user_uuid   text        not null,
  name        text        not null,
  url         text        not null,
  donate_url  text,
  added_at    timestamptz not null default now()
);

create table listen_time (
  user_uuid   text        not null,
  station_id  text        not null,
  date        date        not null default current_date,
  seconds     integer     not null default 0,
  primary key (user_uuid, station_id, date)
);

create table donations (
  id          uuid        primary key default gen_random_uuid(),
  user_uuid   text        not null,
  station_id  text        not null,
  amount_cents integer    not null,
  donated_at  timestamptz not null default now()
);

-- indexes for common queries
create index on radio_favorites (user_uuid);
create index on custom_streams  (user_uuid);
create index on listen_time     (user_uuid);
create index on donations       (user_uuid);

-- Row Level Security: users can only touch their own rows
alter table radio_favorites enable row level security;
alter table custom_streams  enable row level security;
alter table listen_time     enable row level security;
alter table donations       enable row level security;

create policy "own rows only" on radio_favorites
  using (user_uuid = current_setting('app.user_uuid', true));

create policy "own rows only" on custom_streams
  using (user_uuid = current_setting('app.user_uuid', true));

create policy "own rows only" on listen_time
  using (user_uuid = current_setting('app.user_uuid', true));

create policy "own rows only" on donations
  using (user_uuid = current_setting('app.user_uuid', true));
