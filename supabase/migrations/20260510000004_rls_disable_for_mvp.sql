-- Disable RLS for MVP. Query filters (.eq user_uuid) are the access control layer.
-- Re-enable with proper auth (Supabase Auth or verified JWT) before production.

alter table radio_favorites disable row level security;
alter table custom_streams  disable row level security;
alter table listen_time     disable row level security;
alter table donations       disable row level security;
