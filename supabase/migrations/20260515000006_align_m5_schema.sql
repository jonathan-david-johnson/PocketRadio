-- Migration 006: Align listen_time and donations schemas with iOS M5 code
--
-- The initial schema (migration 001) created these tables with daily granularity
-- and per-donation rows. The iOS M5 code expects cumulative totals per station:
--
--   listen_time:  PK (user_uuid, station_id), seconds as double precision
--   donations:    PK (user_uuid, station_id), amount_dollars as double precision
--
-- This migration safely transforms existing data via create-new / migrate / drop-old.

-- ============================================================
-- Step 1: Create new tables with the M5 schema
-- ============================================================

CREATE TABLE IF NOT EXISTS public.listen_time_new (
    user_uuid   TEXT NOT NULL,
    station_id  TEXT NOT NULL,
    seconds     DOUBLE PRECISION NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT NOW(),

    PRIMARY KEY (user_uuid, station_id)
);

CREATE TABLE IF NOT EXISTS public.donations_new (
    user_uuid       TEXT NOT NULL,
    station_id      TEXT NOT NULL,
    amount_dollars  DOUBLE PRECISION NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    PRIMARY KEY (user_uuid, station_id)
);


-- ============================================================
-- Step 2: Migrate data from old tables
-- ============================================================

-- listen_time: sum seconds across all dates per (user_uuid, station_id)
INSERT INTO public.listen_time_new (user_uuid, station_id, seconds, created_at)
SELECT
    user_uuid,
    station_id,
    SUM(seconds)::DOUBLE PRECISION,
    NOW()
FROM public.listen_time
GROUP BY user_uuid, station_id
ON CONFLICT (user_uuid, station_id) DO UPDATE SET
    seconds = public.listen_time_new.seconds + EXCLUDED.seconds;

-- donations: sum amount_cents per (user_uuid, station_id), convert to dollars
INSERT INTO public.donations_new (user_uuid, station_id, amount_dollars, created_at, updated_at)
SELECT
    user_uuid,
    station_id,
    SUM(amount_cents) / 100.0,
    MIN(donated_at),
    MAX(donated_at)
FROM public.donations
GROUP BY user_uuid, station_id
ON CONFLICT (user_uuid, station_id) DO UPDATE SET
    amount_dollars = public.donations_new.amount_dollars + EXCLUDED.amount_dollars,
    updated_at = GREATEST(public.donations_new.updated_at, EXCLUDED.updated_at);


-- ============================================================
-- Step 3: Drop old tables (cascade removes dependent indexes / policies)
-- ============================================================

DROP TABLE public.listen_time CASCADE;
DROP TABLE public.donations CASCADE;


-- ============================================================
-- Step 4: Rename new tables to final names
-- ============================================================

ALTER TABLE public.listen_time_new RENAME TO listen_time;
ALTER TABLE public.donations_new RENAME TO donations;


-- ============================================================
-- Step 5: Recreate indexes for common query patterns
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_listen_time_user_uuid   ON public.listen_time (user_uuid);
CREATE INDEX IF NOT EXISTS idx_listen_time_station_id  ON public.listen_time (station_id);
CREATE INDEX IF NOT EXISTS idx_donations_user_uuid     ON public.donations   (user_uuid);
CREATE INDEX IF NOT EXISTS idx_donations_station_id    ON public.donations   (station_id);


-- ============================================================
-- Step 6: Re-enable RLS and recreate policies (same pattern as migration 005)
-- ============================================================

ALTER TABLE public.listen_time ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.donations   ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "own rows only" ON public.listen_time;
DROP POLICY IF EXISTS "own rows only" ON public.donations;

CREATE POLICY "own rows only" ON public.listen_time
  USING (user_uuid = (current_setting('request.headers', true)::json->>'x-user-uuid'))
  WITH CHECK (user_uuid = (current_setting('request.headers', true)::json->>'x-user-uuid'));

CREATE POLICY "own rows only" ON public.donations
  USING (user_uuid = (current_setting('request.headers', true)::json->>'x-user-uuid'))
  WITH CHECK (user_uuid = (current_setting('request.headers', true)::json->>'x-user-uuid'));
