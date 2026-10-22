-- The curated radio stations every surface offers, moved out of the iOS bundle
-- (pocket-radio-ios/podcasts/Radio/curated_stations.json) so that the web
-- player can read the same list. The rows are public and the same for every
-- user: the anon and authenticated roles may read them but never write.
-- The web player reads them through its Worker, only for a signed-in session.
-- Apply only with explicit approval.
begin;

create table public.curated_stations (
  id                  text    primary key check (id ~ '^[a-z0-9_]{1,64}$'),
  -- Display order, as in the iOS file.
  position            integer not null unique,
  name                text    not null check (length(name) between 1 and 200),
  description         text    not null check (length(description) <= 500),
  -- An iOS asset catalog name, not a URL.
  logo_asset          text    not null check (length(logo_asset) between 1 and 200),
  tracklist_url       text    check (tracklist_url like 'https://%'),
  -- radio-browser station UUIDs for the station's streams.
  radio_browser_uuids uuid[]  not null check (cardinality(radio_browser_uuids) >= 1),
  default_seed_uuid   uuid    not null,
  seed_as_favorite    boolean not null,
  constraint default_seed_is_a_stream check (default_seed_uuid = any (radio_browser_uuids))
);

alter table public.curated_stations enable row level security;
revoke all on public.curated_stations from public, anon, authenticated;
grant select on public.curated_stations to anon, authenticated;
grant all on public.curated_stations to service_role;
create policy "anyone can read" on public.curated_stations
  for select to anon, authenticated using (true);

insert into public.curated_stations
  (id, position, name, description, logo_asset, tracklist_url, radio_browser_uuids, default_seed_uuid, seed_as_favorite)
values
  ('kcrw_eclectic_24', 1, 'KCRW Eclectic 24', 'Eclectic music from KCRW', 'kcrw_logo',
   'https://tracklist-api.kcrw.com/Music/all/1?page_size=10',
   array['18e31f25-53c8-4213-a1ec-dccc0443a788', '25ff2df8-f8ea-4af8-b283-48ba3bdcaf69', '6238f5e8-a9ee-4c88-9713-2d1ab4112ac9']::uuid[],
   '6238f5e8-a9ee-4c88-9713-2d1ab4112ac9', true),
  ('kexp', 2, 'KEXP', 'Where the music matters', 'kexp_logo',
   'https://api.kexp.org/v2/plays/?limit=10',
   array['445cbb3a-1c4e-49aa-a268-f5b6acfa8f2e', '399ca326-0f67-4015-a51b-d7ba2bd4ebbe', 'a509502d-1ba7-4d51-9791-0be5a7d5ec34']::uuid[],
   '445cbb3a-1c4e-49aa-a268-f5b6acfa8f2e', true),
  ('npr_hourly', 3, 'NPR Hourly Newscast', 'Live news updates every hour', 'npr_logo',
   null,
   array['a5314180-7573-4b46-aafc-51ed2d5b9e71']::uuid[],
   'a5314180-7573-4b46-aafc-51ed2d5b9e71', true);

commit;
