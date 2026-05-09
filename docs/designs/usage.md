# Usage & Donations Screen

## Location
Settings → Usage & Donations

## Tone
Guilt-free / celebratory. No push notifications or interruptions. User visits on their own terms.

## Layout

```
Usage & Donations
─────────────────────────────────
RADIO STATIONS

  KCRW                    [logo]
  40h 12m listened
  Est. cost to station: $0.20
  [I donated $___] [Support KCRW ↗]

  WNYC                    [logo]
  12h 5m listened
  Est. cost to station: $0.06
  [I donated $___] [Support WNYC ↗]

─────────────────────────────────
PODCASTS

  Fresh Air               [logo]
  22h listened

  99% Invisible           [logo]
  8h listened

─────────────────────────────────
TOTAL
  Radio: 52h 17m  |  Podcasts: 30h
  Est. total cost: $0.26
  Total donated: $25.00
  Your support ratio: 96x 🎉
```

## Rules

- **Radio stations**: show listen-time, estimated cost, editable donation field, donate URL
- **Podcasts**: show listen-time only — no cost estimate (no per-listener streaming cost)
- **Cost estimate**: `seconds_listened / 3600 * $0.005` per station (constant configurable in code)
- **Donation field**: inline editable dollar amount, persisted to Supabase `donations` table
- **Support button**: opens station `donate_url` in system browser
- **Support ratio**: `total_donated / total_estimated_cost`, shown with celebratory emoji
- Ratio only calculated and shown for radio (where cost is defined)
- Sort: radio and podcast sections each sorted by listen-time descending

## Data Sources

| Field | Source |
|-------|--------|
| Listen-time (radio) | `listen_time` table in Supabase, keyed by `user_uuid + station_id` |
| Listen-time (podcasts) | PC existing playback history |
| Donations | `donations` table in Supabase |
| Station logo | radio-browser.info `favicon` field / podcast artwork |
| Donate URL | `curated_stations.json` `donate_url` field |

## MVP Scope

- No push nudges — passive screen only
- No payment processing — honor system
- No historical breakdown — lifetime totals only
