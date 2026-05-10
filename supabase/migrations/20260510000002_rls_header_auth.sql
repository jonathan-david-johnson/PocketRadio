-- Update RLS policies to use x-user-uuid request header instead of current_setting GUC.
-- PostgREST 10+ exposes request headers as request.header.* GUC variables.
-- iOS client passes "x-user-uuid": ServerSettings.userId on every request.

drop policy "own rows only" on radio_favorites;
drop policy "own rows only" on custom_streams;
drop policy "own rows only" on listen_time;
drop policy "own rows only" on donations;

create policy "own rows only" on radio_favorites
  using (user_uuid = current_setting('request.header.x-user-uuid', true))
  with check (user_uuid = current_setting('request.header.x-user-uuid', true));

create policy "own rows only" on custom_streams
  using (user_uuid = current_setting('request.header.x-user-uuid', true))
  with check (user_uuid = current_setting('request.header.x-user-uuid', true));

create policy "own rows only" on listen_time
  using (user_uuid = current_setting('request.header.x-user-uuid', true))
  with check (user_uuid = current_setting('request.header.x-user-uuid', true));

create policy "own rows only" on donations
  using (user_uuid = current_setting('request.header.x-user-uuid', true))
  with check (user_uuid = current_setting('request.header.x-user-uuid', true));
