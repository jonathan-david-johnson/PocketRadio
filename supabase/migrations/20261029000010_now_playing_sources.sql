begin;

alter table public.curated_stations
  add column metadata_source jsonb null
  check (metadata_source is null or jsonb_typeof(metadata_source) = 'object');

update public.curated_stations
  set metadata_source = '{"adapter":"kcrw","params":{}}'::jsonb
  where id = 'kcrw_eclectic_24';

update public.curated_stations
  set metadata_source = '{"adapter":"kexp","params":{}}'::jsonb
  where id = 'kexp';

create table public.station_metadata_sources (
  station_uuid uuid primary key,
  adapter text not null check (adapter ~ '^[a-z0-9_]{1,64}$'),
  params jsonb not null default '{}'::jsonb check (jsonb_typeof(params) = 'object'),
  enabled boolean not null default true,
  terms_reviewed_on date not null,
  notes text not null default '' check (length(notes) <= 2000)
);

alter table public.station_metadata_sources enable row level security;
revoke all on public.station_metadata_sources from public, anon, authenticated;
grant select on public.station_metadata_sources to anon, authenticated;
grant all on public.station_metadata_sources to service_role;
create policy "anyone can read metadata sources" on public.station_metadata_sources
  for select to anon, authenticated using (true);

commit;
