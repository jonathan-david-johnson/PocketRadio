-- Fix RLS: migration 002 used hyphens in the GUC name.
-- PostgREST stores request.headers as a JSON object with lowercase keys.
-- Parse the JSON directly instead of relying on request.header.* naming.

drop policy "own rows only" on radio_favorites;
drop policy "own rows only" on custom_streams;
drop policy "own rows only" on listen_time;
drop policy "own rows only" on donations;

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
