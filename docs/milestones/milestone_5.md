# M5: Listen Time + Usage Screen

**Status**: NOT STARTED

## Goal

Usage & Donations screen shows accurate listen time and supports donation self-reporting.

## Done when

- Listen time accumulates while streaming
- Usage & Donations screen shows per-station hours + estimated cost
- Inline donation amount saves to Supabase
- Support ratio displays

## What to build

- `ListenTimeTracker.swift` — accumulates seconds, syncs to Supabase in 60s increments, flushes on app background
- `UsageDonationsViewController` — per-station listen time, cost estimate, donation field, donate button
- Donation input → writes to Supabase `donations` table

## Notes

- See `docs/designs/usage.md` for layout and cost formula (`seconds / 3600 * $0.005`)
- Check `docs/todo.md` open question: does PC already track podcast listen time? Read PC source before building.
- Support ratio = `total_donated / total_estimated_cost` for radio only
