# Supabase Client Setup

## SDK

Add via SPM: `https://github.com/supabase/supabase-swift` (package: `Supabase`, target: `Supabase`)

## Initialization

File: `podcasts/Radio/SupabaseClient.swift`

```swift
import Supabase

enum RadioSupabase {
    static let client: SupabaseClient = {
        let url = URL(string: Bundle.main.infoDictionary?["SUPABASE_URL"] as? String ?? "")!
        let key = Bundle.main.infoDictionary?["SUPABASE_ANON_KEY"] as? String ?? ""
        return SupabaseClient(supabaseURL: url, supabaseKey: key)
    }()
}
```

## Environment config

`Info.plist` (not committed) entries, populated via Xcode Build Settings → User-Defined:

```
SUPABASE_URL  = $(SUPABASE_URL)
SUPABASE_ANON_KEY = $(SUPABASE_ANON_KEY)
```

Local dev values in `.env.local` (gitignored):
```
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_ANON_KEY=<local anon key from supabase start output>
```

Prod values in Xcode scheme environment variables or CI secrets.

## user_uuid injection

Supabase RLS uses `current_setting('app.user_uuid', true)`. Set per-request via PostgREST header:

```swift
extension RadioSupabase {
    /// Returns a query builder with user_uuid injected for RLS.
    static func authedTable(_ table: String) throws -> PostgrestQueryBuilder {
        guard let userId = ServerSettings.userId else {
            throw RadioError.notLoggedIn
        }
        return client
            .from(table)
            .select()  // overridden by caller
            // PostgREST reads this header and sets app.user_uuid for the request
            // Supabase Swift SDK: pass custom headers via .headers()
    }
}
```

Actually, inject user_uuid by setting a custom header on each request:

```swift
// Each manager method does:
let userId = try requireUserId()
let response = try await RadioSupabase.client
    .from("radio_favorites")
    .select()
    .eq("user_uuid", value: userId)   // also filter by user in query
    .execute()
```

Both the query filter AND the RLS policy protect rows. Belt-and-suspenders.

## Error type

```swift
enum RadioError: Error {
    case notLoggedIn
    case networkError(Error)
    case notFound
}
```

## Local dev setup

```bash
supabase start
# outputs: API URL, anon key — paste into .env.local
```

Schema already migrated (`supabase/migrations/20260509000001_initial_schema.sql`).
Push schema changes: `supabase db push` (requires `supabase link` first).
