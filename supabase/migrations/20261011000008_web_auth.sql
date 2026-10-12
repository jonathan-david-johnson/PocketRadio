-- Web-only secret storage. See web ADR 0002 and ADR 0003.
-- Apply only with explicit approval. No header-trust policies belong here.
begin;

create table public.pc_tokens (
  user_uuid uuid primary key,
  email text not null check (length(email) between 3 and 320),
  access_token text not null check (length(access_token) between 1 and 8192),
  refresh_token text not null check (length(refresh_token) between 1 and 8192),
  expires_at timestamptz not null,
  grant_started_at timestamptz not null,
  revision bigint not null default 1,
  refresh_lease text,
  refresh_session_hash text,
  refresh_until timestamptz,
  refresh_after timestamptz
);
create table public.web_sessions (
  session_hash text primary key check (session_hash ~ '^[0-9a-f]{64}$'),
  user_uuid uuid not null references public.pc_tokens(user_uuid) on delete cascade,
  created_at timestamptz not null,
  expires_at timestamptz not null,
  next_probe_at timestamptz
);
create index web_sessions_user_idx on public.web_sessions(user_uuid);
create index web_sessions_expiry_idx on public.web_sessions(expires_at);
create table public.web_pairings (
  pairing_hash text primary key check (pairing_hash ~ '^[0-9a-f]{64}$'),
  browser_hash text not null check (browser_hash ~ '^[0-9a-f]{64}$'),
  origin text not null check (origin like 'https://%' and length(origin) <= 512),
  created_at timestamptz not null,
  expires_at timestamptz not null,
  status text not null check (status in ('authorizing', 'pending', 'consumed', 'expired', 'error')),
  device_code text,
  interval_seconds integer not null default 5 check (interval_seconds between 5 and 60),
  next_poll_at timestamptz,
  poll_count integer not null default 0,
  poll_lease text,
  lease_until timestamptz,
  minted_session_hash text,
  check (device_code is null or length(device_code) between 1 and 8192)
);
create index web_pairings_browser_idx on public.web_pairings(browser_hash, created_at);
create index web_pairings_created_idx on public.web_pairings(created_at);
create index web_pairings_expiry_idx on public.web_pairings(expires_at);

-- Persistent fence survives token/session deletion and future fresh grants.
create table public.web_account_revocations (
  user_uuid uuid primary key,
  revoked_at timestamptz not null
);
create table public.web_relays (
  relay_id text primary key check (relay_id ~ '^[A-Za-z0-9_-]{1,128}$'),
  user_uuid uuid not null,
  session_hash text not null check (session_hash ~ '^[0-9a-f]{64}$'),
  started_at timestamptz not null,
  expires_at timestamptz not null,
  active boolean not null default true,
  check (expires_at <= started_at + interval '66 minutes')
);
create index web_relays_user_idx on public.web_relays(user_uuid, started_at);
create index web_relays_expiry_idx on public.web_relays(expires_at);
alter table public.web_account_revocations enable row level security;
alter table public.web_relays enable row level security;
revoke all on public.web_account_revocations, public.web_relays from public, anon, authenticated;
grant all on public.web_account_revocations, public.web_relays to service_role;

alter table public.pc_tokens enable row level security;
alter table public.web_sessions enable row level security;
alter table public.web_pairings enable row level security;
revoke all on public.pc_tokens, public.web_sessions, public.web_pairings from public, anon, authenticated;
grant all on public.pc_tokens, public.web_sessions, public.web_pairings to service_role;

-- Invoker rights plus explicit service-role-only EXECUTE; no SECURITY DEFINER.
-- p_now comes only from the Worker clock; browser input never supplies it.
create function public.web_pair_reserve(p_pairing_hash text, p_browser_hash text, p_origin text, p_now timestamptz)
returns boolean language plpgsql set search_path = pg_catalog, public as $$
begin
  -- Bound code generation across isolates, including failed authorizations.
  perform pg_advisory_xact_lock(63171011001);
  if (select count(*) from public.web_pairings where created_at > p_now - interval '1 minute') >= 100
     or (select count(*) from public.web_pairings where browser_hash = p_browser_hash and created_at > p_now - interval '1 minute') >= 3 then
    return false;
  end if;
  -- Keep a minute of tombstones for rate gating, discard abandoned secret codes.
  delete from public.web_pairings where expires_at < p_now - interval '1 hour';
  update public.web_pairings set status = 'expired', device_code = null, poll_lease = null, lease_until = null
    where expires_at <= p_now and status in ('authorizing', 'pending');
  insert into public.web_pairings(pairing_hash, browser_hash, origin, created_at, expires_at, status)
    values (p_pairing_hash, p_browser_hash, p_origin, p_now, p_now + interval '15 minutes', 'authorizing');
  return true;
end $$;

create function public.web_pair_activate(p_pairing_hash text, p_browser_hash text, p_origin text, p_now timestamptz,
  p_device_code text, p_expires_in integer, p_interval integer)
returns boolean language plpgsql set search_path = pg_catalog, public as $$
begin
  if p_expires_in not between 1 and 900 or p_interval not between 5 and 60 then return false; end if;
  perform pg_advisory_xact_lock(hashtextextended('browser:' || p_browser_hash, 0));
  update public.web_pairings set status = 'pending', device_code = p_device_code,
    expires_at = least(expires_at, p_now + make_interval(secs => p_expires_in)), interval_seconds = p_interval,
    next_poll_at = p_now + make_interval(secs => p_interval)
    where pairing_hash = p_pairing_hash and browser_hash = p_browser_hash and origin = p_origin
      and status = 'authorizing' and expires_at > p_now;
  if not found then return false; end if;
  update public.web_pairings set status = 'error', device_code = null, poll_lease = null, lease_until = null
    where browser_hash = p_browser_hash and origin = p_origin and pairing_hash <> p_pairing_hash
      and status in ('authorizing', 'pending');
  return true;
end $$;

create function public.web_pair_cancel(p_pairing_hash text, p_browser_hash text, p_origin text)
returns boolean language plpgsql set search_path = pg_catalog, public as $$
declare r public.web_pairings%rowtype; u uuid;
begin
  select * into r from public.web_pairings where pairing_hash = p_pairing_hash
    and browser_hash = p_browser_hash and origin = p_origin for update;
  if not found then return false; end if;
  select user_uuid into u from public.web_sessions where session_hash = r.minted_session_hash;
  if u is not null then
    perform pg_advisory_xact_lock(hashtextextended('account:' || u::text, 0));
    delete from public.web_sessions where session_hash = r.minted_session_hash;
  end if;
  update public.web_pairings set status = 'error', device_code = null, poll_lease = null, lease_until = null
    where pairing_hash = p_pairing_hash;
  return true;
end $$;

create function public.web_pair_claim(p_pairing_hash text, p_browser_hash text, p_origin text, p_lease text, p_now timestamptz)
returns jsonb language plpgsql set search_path = pg_catalog, public as $$
declare r public.web_pairings%rowtype;
begin
  if p_lease !~ '^[0-9a-f]{64}$' then return jsonb_build_object('status', 'expired'); end if;
  select * into r from public.web_pairings where pairing_hash = p_pairing_hash and browser_hash = p_browser_hash
    and origin = p_origin for update;
  if not found or r.expires_at <= p_now or r.status <> 'pending' or r.poll_count >= 180 then
    if found and r.status in ('authorizing', 'pending') and (r.expires_at <= p_now or r.poll_count >= 180) then
      update public.web_pairings set status = 'expired', device_code = null, poll_lease = null, lease_until = null
        where pairing_hash = p_pairing_hash;
    end if;
    return jsonb_build_object('status', 'expired');
  end if;
  if r.next_poll_at > p_now or r.lease_until > p_now then
    return jsonb_build_object('status', 'pending', 'retry_in',
      greatest(1, ceil(extract(epoch from (greatest(r.next_poll_at, r.lease_until) - p_now)))::integer));
  end if;
  update public.web_pairings set poll_lease = p_lease, lease_until = p_now + interval '30 seconds',
    next_poll_at = p_now + make_interval(secs => r.interval_seconds), poll_count = poll_count + 1
    where pairing_hash = p_pairing_hash;
  return jsonb_build_object('status', 'poll', 'device_code', r.device_code, 'interval', r.interval_seconds);
end $$;

create function public.web_pair_finish(p_pairing_hash text, p_browser_hash text, p_origin text, p_lease text,
  p_now timestamptz, p_status text)
returns boolean language plpgsql set search_path = pg_catalog, public as $$
begin
  if p_status not in ('pending', 'slow_down', 'expired', 'error') then return false; end if;
  update public.web_pairings set
    status = case when p_status in ('pending', 'slow_down') then 'pending' else p_status end,
    device_code = case when p_status in ('pending', 'slow_down') then device_code else null end,
    interval_seconds = case when p_status = 'slow_down' then least(60, interval_seconds + 5) else interval_seconds end,
    next_poll_at = p_now + make_interval(secs => case when p_status = 'slow_down' then least(60, interval_seconds + 5) else interval_seconds end),
    poll_lease = null, lease_until = null
    where pairing_hash = p_pairing_hash and browser_hash = p_browser_hash and origin = p_origin
      and status = 'pending' and poll_lease = p_lease and lease_until > p_now and expires_at > p_now;
  return found;
end $$;

create function public.web_pair_consume(p_pairing_hash text, p_browser_hash text, p_origin text, p_lease text,
  p_now timestamptz, p_session_hash text, p_user_uuid uuid, p_email text, p_access_token text,
  p_refresh_token text, p_expires_in integer)
returns boolean language plpgsql set search_path = pg_catalog, public as $$
declare r public.web_pairings%rowtype;
begin
  if p_expires_in not between 1 and 31536000 then return false; end if;
  select * into r from public.web_pairings where pairing_hash = p_pairing_hash and browser_hash = p_browser_hash
    and origin = p_origin and status = 'pending' and poll_lease = p_lease
    and lease_until > p_now and expires_at > p_now for update;
  if not found then return false; end if;
  perform pg_advisory_xact_lock(hashtextextended('account:' || p_user_uuid::text, 0));
  -- Same lock as revocation: either consume wins and is deleted, or its
  -- start time is fenced even if approval completes after a new fresh grant.
  if exists (select 1 from public.web_account_revocations
    where user_uuid = p_user_uuid and revoked_at >= r.created_at) then return false; end if;
  -- Older pairing completions cannot overwrite a newer grant or its refresh.
  insert into public.pc_tokens(user_uuid, email, access_token, refresh_token, expires_at, grant_started_at)
    values (p_user_uuid, p_email, p_access_token, p_refresh_token, p_now + make_interval(secs => p_expires_in), r.created_at)
    on conflict (user_uuid) do update set email = excluded.email, access_token = excluded.access_token,
      refresh_token = excluded.refresh_token, expires_at = excluded.expires_at,
      grant_started_at = excluded.grant_started_at, revision = pc_tokens.revision + 1,
      refresh_lease = null, refresh_session_hash = null, refresh_until = null, refresh_after = null
      where pc_tokens.grant_started_at <= excluded.grant_started_at;
  insert into public.web_sessions(session_hash, user_uuid, created_at, expires_at)
    values (p_session_hash, p_user_uuid, p_now, p_now + interval '90 days');
  update public.web_pairings set status = 'consumed', minted_session_hash = p_session_hash,
    device_code = null, poll_lease = null, lease_until = null
    where pairing_hash = p_pairing_hash;
  return true;
end $$;

create function public.web_session_roll(p_session_hash text, p_now timestamptz)
returns jsonb language plpgsql set search_path = pg_catalog, public as $$
declare u uuid;
begin
  update public.web_sessions set expires_at = greatest(expires_at, p_now + interval '90 days')
    where session_hash = p_session_hash and expires_at > p_now returning user_uuid into u;
  if not found then return null; end if;
  return jsonb_build_object('user_uuid', u);
end $$;

create function public.web_session_email(p_session_hash text, p_now timestamptz)
returns text language sql stable set search_path = pg_catalog, public as $$
  select t.email from public.web_sessions s join public.pc_tokens t using (user_uuid)
    where s.session_hash = p_session_hash and s.expires_at > p_now;
$$;
create function public.web_session_signout(p_session_hash text)
returns boolean language plpgsql set search_path = pg_catalog, public as $$
declare u uuid;
begin
  select user_uuid into u from public.web_sessions where session_hash = p_session_hash;
  if not found then return false; end if;
  perform pg_advisory_xact_lock(hashtextextended('account:' || u::text, 0));
  delete from public.web_sessions where session_hash = p_session_hash;
  return found;
end $$;
create function public.web_session_signout_everywhere(p_session_hash text, p_now timestamptz)
returns boolean language plpgsql set search_path = pg_catalog, public as $$
declare u uuid;
begin
  select user_uuid into u from public.web_sessions where session_hash = p_session_hash and expires_at > p_now;
  if not found then return false; end if;
  perform pg_advisory_xact_lock(hashtextextended('account:' || u::text, 0));
  -- Recheck after lock acquisition; a concurrent sign-out cannot reuse identity.
  if not exists (select 1 from public.web_sessions where session_hash = p_session_hash and user_uuid = u and expires_at > p_now) then
    return false;
  end if;
  insert into public.web_account_revocations(user_uuid, revoked_at) values (u, p_now)
    on conflict (user_uuid) do update set revoked_at = greatest(web_account_revocations.revoked_at, excluded.revoked_at);
  delete from public.pc_tokens where user_uuid = u; -- Cascades all web sessions.
  return found;
end $$;
create function public.web_probe_claim(p_session_hash text, p_now timestamptz)
returns boolean language plpgsql set search_path = pg_catalog, public as $$
begin
  update public.web_sessions set next_probe_at = p_now + interval '30 seconds'
    where session_hash = p_session_hash and expires_at > p_now and (next_probe_at is null or next_probe_at <= p_now);
  return found;
end $$;

create function public.web_token_claim(p_session_hash text, p_lease text, p_now timestamptz)
returns jsonb language plpgsql set search_path = pg_catalog, public as $$
declare u uuid; r public.pc_tokens%rowtype;
begin
  if p_lease !~ '^[0-9a-f]{64}$' then return null; end if;
  select user_uuid into u from public.web_sessions where session_hash = p_session_hash and expires_at > p_now;
  if not found then return null; end if;
  perform pg_advisory_xact_lock(hashtextextended('account:' || u::text, 0));
  if not exists (select 1 from public.web_sessions where session_hash = p_session_hash and expires_at > p_now) then return null; end if;
  select * into r from public.pc_tokens where user_uuid = u for update;
  if not found then return null; end if;
  if r.expires_at > p_now + interval '30 seconds' then
    return jsonb_build_object('status', 'ready', 'access_token', r.access_token);
  end if;
  if r.refresh_until > p_now or r.refresh_after > p_now then return jsonb_build_object('status', 'busy'); end if;
  update public.pc_tokens set refresh_lease = p_lease, refresh_session_hash = p_session_hash,
    refresh_until = p_now + interval '30 seconds' where user_uuid = u;
  return jsonb_build_object('status', 'refresh', 'user_uuid', u, 'refresh_token', r.refresh_token);
end $$;
create function public.web_token_finish(p_session_hash text, p_lease text, p_now timestamptz, p_user_uuid uuid,
  p_email text, p_access_token text, p_refresh_token text, p_expires_in integer)
returns boolean language plpgsql set search_path = pg_catalog, public as $$
begin
  if p_expires_in not between 1 and 31536000 then return false; end if;
  perform pg_advisory_xact_lock(hashtextextended('account:' || p_user_uuid::text, 0));
  -- Store the valid rotation for surviving B, even if claiming A signed out.
  -- The caller must separately recheck A before using credentials.
  if not exists (select 1 from public.web_sessions where user_uuid = p_user_uuid and expires_at > p_now) then
    return false;
  end if;
  update public.pc_tokens set email = p_email, access_token = p_access_token, refresh_token = p_refresh_token,
    expires_at = p_now + make_interval(secs => p_expires_in), revision = revision + 1,
    refresh_lease = null, refresh_session_hash = null, refresh_until = null, refresh_after = null
    where user_uuid = p_user_uuid and refresh_lease = p_lease and refresh_session_hash = p_session_hash
      and refresh_until > p_now and not exists (select 1 from public.web_account_revocations r
        where r.user_uuid = p_user_uuid and r.revoked_at >= pc_tokens.grant_started_at);
  return found;
end $$;
create function public.web_token_release(p_session_hash text, p_lease text, p_now timestamptz)
returns boolean language plpgsql set search_path = pg_catalog, public as $$
begin
  -- The claimant may have signed out while upstream was failing. Release by
  -- the stored CAS binding, not a surviving session or merely its account.
  update public.pc_tokens set refresh_lease = null, refresh_session_hash = null,
    refresh_until = null, refresh_after = p_now + interval '30 seconds'
    where refresh_lease = p_lease and refresh_session_hash = p_session_hash;
  return found;
end $$;

-- Pairing row -> sorted account locks is the common consume/cancel ordering.
-- A delayed approval response can set a cookie, but cannot revive the row it names.
create function public.web_signout(p_session_hash text, p_pairing_hash text, p_browser_hash text,
  p_origin text, p_now timestamptz, p_everywhere boolean)
returns boolean language plpgsql set search_path = pg_catalog, public as $$
declare r public.web_pairings%rowtype; u uuid;
begin
  select * into r from public.web_pairings where pairing_hash = p_pairing_hash
    and browser_hash = p_browser_hash and origin = p_origin for update;
  for u in select distinct user_uuid from public.web_sessions
    where session_hash in (p_session_hash, r.minted_session_hash) order by user_uuid loop
    perform pg_advisory_xact_lock(hashtextextended('account:' || u::text, 0));
  end loop;
  if p_everywhere then
    perform public.web_session_signout_everywhere(p_session_hash, p_now);
    perform public.web_session_signout_everywhere(r.minted_session_hash, p_now);
  else
    delete from public.web_sessions where session_hash in (p_session_hash, r.minted_session_hash);
  end if;
  update public.web_pairings set status = 'error', device_code = null, poll_lease = null, lease_until = null
    where pairing_hash = r.pairing_hash;
  return true;
end $$;

-- Relay heartbeats are checks, NOT visits: no expiry or cookie roll.
create function public.web_session_check(p_session_hash text, p_now timestamptz)
returns boolean language sql stable set search_path = pg_catalog, public as $$
  select exists (select 1 from public.web_sessions
    where session_hash = p_session_hash and expires_at > p_now);
$$;

-- Per-account persistent admission: 5 starts in the trailing minute, 2 live
-- leases, max 65 minutes playback + 1 minute initialization. Released rows
-- remain for rate gating. Cleanup bounds retained rows to <=7 per account.
create function public.web_relay_admit(p_session_hash text, p_relay_id text, p_now timestamptz)
returns boolean language plpgsql set search_path = pg_catalog, public as $$
declare u uuid;
begin
  if p_relay_id is null or p_relay_id !~ '^[A-Za-z0-9_-]{1,128}$' then return false; end if;
  -- Serialize global stale cleanup before account locks; avoid cleanup cycles
  -- between admissions in different accounts.
  perform pg_advisory_xact_lock(63171011002);
  delete from public.web_relays r where r.started_at <= p_now - interval '1 minute'
    and (not r.active or r.expires_at <= p_now or not exists (select 1 from public.web_sessions s
      where s.session_hash = r.session_hash and s.expires_at > p_now));
  select user_uuid into u from public.web_sessions where session_hash = p_session_hash and expires_at > p_now;
  if not found then return false; end if;
  perform pg_advisory_xact_lock(hashtextextended('account:' || u::text, 0));
  if not public.web_session_check(p_session_hash, p_now) then return false; end if;
  if exists (select 1 from public.web_relays where relay_id = p_relay_id)
    or (select count(*) from public.web_relays where user_uuid = u
      and started_at > p_now - interval '1 minute') >= 5
    or (select count(*) from public.web_relays r where r.user_uuid = u and r.active and r.expires_at > p_now
      and exists (select 1 from public.web_sessions s where s.session_hash = r.session_hash and s.expires_at > p_now)) >= 2 then
    return false;
  end if;
  insert into public.web_relays(relay_id, user_uuid, session_hash, started_at, expires_at)
    values (p_relay_id, u, p_session_hash, p_now, p_now + interval '66 minutes');
  return true;
end $$;
create function public.web_relay_release(p_session_hash text, p_relay_id text)
returns boolean language plpgsql set search_path = pg_catalog, public as $$
begin
  update public.web_relays set active = false where relay_id = p_relay_id and session_hash = p_session_hash;
  return found;
end $$;

-- Revoke PostgreSQL's default PUBLIC EXECUTE for every new RPC by exact signature.
revoke all on function public.web_signout(text,text,text,text,timestamptz,boolean),
  public.web_session_check(text,timestamptz), public.web_relay_admit(text,text,timestamptz), public.web_relay_release(text,text),
  public.web_pair_reserve(text,text,text,timestamptz),
  public.web_pair_activate(text,text,text,timestamptz,text,integer,integer),
  public.web_pair_cancel(text,text,text), public.web_pair_claim(text,text,text,text,timestamptz),
  public.web_pair_finish(text,text,text,text,timestamptz,text),
  public.web_pair_consume(text,text,text,text,timestamptz,text,uuid,text,text,text,integer),
  public.web_session_roll(text,timestamptz), public.web_session_email(text,timestamptz),
  public.web_session_signout(text), public.web_session_signout_everywhere(text,timestamptz),
  public.web_probe_claim(text,timestamptz), public.web_token_claim(text,text,timestamptz),
  public.web_token_finish(text,text,timestamptz,uuid,text,text,text,integer), public.web_token_release(text,text,timestamptz)
  from public, anon, authenticated;
grant execute on function public.web_signout(text,text,text,text,timestamptz,boolean),
  public.web_session_check(text,timestamptz), public.web_relay_admit(text,text,timestamptz), public.web_relay_release(text,text),
  public.web_pair_reserve(text,text,text,timestamptz),
  public.web_pair_activate(text,text,text,timestamptz,text,integer,integer),
  public.web_pair_cancel(text,text,text), public.web_pair_claim(text,text,text,text,timestamptz),
  public.web_pair_finish(text,text,text,text,timestamptz,text),
  public.web_pair_consume(text,text,text,text,timestamptz,text,uuid,text,text,text,integer),
  public.web_session_roll(text,timestamptz), public.web_session_email(text,timestamptz),
  public.web_session_signout(text), public.web_session_signout_everywhere(text,timestamptz),
  public.web_probe_claim(text,timestamptz), public.web_token_claim(text,text,timestamptz),
  public.web_token_finish(text,text,timestamptz,uuid,text,text,text,integer), public.web_token_release(text,text,timestamptz)
  to service_role;

commit;
