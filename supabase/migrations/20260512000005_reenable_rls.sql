-- Re-enable RLS for all tables after security advisory.
-- Uses PostgREST request.headers JSON parsing (same approach as migration 003).
-- iOS client injects "x-user-uuid" header on every request via RadioSupabase.client().

-- Re-enable RLS
alter table radio_favorites enable row level security;
alter table custom_streams  enable row level security;
alter table listen_time     enable row level security;
alter table donations       enable row level security;

-- Drop any lingering policies to start clean
drop policy if exists "own rows only" on radio_favorites;
drop policy if exists "own rows only" on custom_streams;
drop policy if exists "own rows only" on listen_time;
drop policy if exists "own rows only" on donations;

-- Create policies using request.headers JSON to extract x-user-uuid
-- PostgREST 10+ stores all request headers in request.headers as JSON
-- iOS client sets header: SupabaseClientOptions.Global(headers: ["x-user-uuid": userId])

create policy "own rows only" on radio_favorites
  using (user_uuid = (current_setting('request.headers', true)::json->>'x-user-uuid'))
  with check (user_uuid = (current_setting('request.headers', true)::json->>'x-user-uuid'));

create policy "own rows only" on custom_streams
  using (user_uuid = (current_setting('request.headers', true)::json->>'x-user-uuid'))
  with check (user_uuid = (current_setting('request.headers', true)::json->>'x-user-uuid'));

create policy "own rows only" on listen_time
  using (user_uuid = (current_setting('request.headers', true)::json->>'x-user-uuid'))
  with check (user_uuid = (current_setting('request.headers', true)::json->>'x-user-uuid'));

create policy "own rows only" on donations
  using (user_uuid = (current_setting('request.headers', true)::json->>'x-user-uuid'))
  with check (user_uuid = (current_setting('request.headers', true)::json->>'x-user-uuid'));