# Web M1 platform constraints — E2/E5 discovery

**Status: source discovery complete; E2 camera behavior and E5 relay permission remain unresolved.** The fork contains the proposed Pairing route. Cloudflare supports a cross-isolate title channel through a Durable Object, but Pages must bind an object deployed by a separate Worker. Neither runtime capability nor general content-hosting language establishes permission for continuous third-party audio relaying.

Access date for every public source below: **2026-10-11 UTC**. Scope: read-only inspection plus this report; no deployment, phone/app launch, audio connection, credentials, migration application, or ADR changes.

## E2: what the iOS source establishes

Inspected the existing `pocket-radio-ios/` working tree after its instructions and active milestone. Its HEAD was `62ee754dc`; `podcasts/podcasts-Info.plist` already had a local modification. These are working-tree findings, not verification of an installed binary.

| Finding | Source under `pocket-radio-ios/` |
| --- | --- |
| The app declares `pktc` in `CFBundleURLTypes` → `CFBundleURLSchemes`. | `podcasts/podcasts-Info.plist:943–955` |
| Incoming `pktc` URLs pass to `JLRoutes.routeURL(url)`. Cold and warm scene URL deliveries reach that handler. | `podcasts/AppDelegate+UrlHandling.swift:19–24,62–64`; `podcasts/SceneDelegate.swift:25–30,45–50` |
| Startup calls `setupRoutes()`, which calls `setupTVPairingRoutes()`. That registers the exact `/pair` route and reads the query parameter `user_code`. | `podcasts/AppDelegate.swift:82`; `podcasts/AppDelegate+UrlHandling.swift:456,525–534` |
| Navigation passes the code to `showApproveDevice(code:)`, which presents `DeviceApproveView`. Its initializer puts the supplied code in SwiftUI state, or uses an empty string. | `podcasts/Main/NavigationManager.swift:263–267`; `podcasts/Main/MainTabBarController.swift:945–949`; `podcasts/DeviceApprove/DeviceApproveView.swift:90–93` |
| Approval requires a signed-in account; otherwise the action opens account onboarding. The signed-in action calls `AuthenticationHelper.deviceApprove(userCode:…, approve: true)`. Manual code entry exists; the field truncates changes beyond six characters and submission checks trimmed length ≥6. | `podcasts/DeviceApprove/DeviceApproveView.swift:21–60,200–221` |
| A delivered universal-link activity with `/pair` or `/pair/…` is rewritten to a `pktc` URL with its query preserved. The entitlement template lists `applinks:pocketcasts.com` and related domains. | `podcasts/AppDelegate+SiriShortcuts.swift:22–54`; `podcasts/podcasts.prototype.entitlements:7–22` |

**Proposed payload:** `pktc://pair?user_code=<percent-encoded approval code>`. This matches the source's scheme, route and query key. It must contain only the user-facing approval code, never a device grant secret, access token, or identity assertion.

**Not established:** Camera recognition of this custom scheme; successful JLRoutes normalization and prefill in the installed build; cold/warm presentation timing; which app wins if Automattic also registers `pktc`; actual approval success; or universal-link association for the fork's signed bundle. The entitlement declaration is not proof of Apple's domain association. No live association file or official-app binary was inspected. Test the actual `verification_uri_complete` response separately; its value was not observed here. A code-only fallback is a proposal requiring the parent/user's decision, not an ADR change.

## E5: current official terms

The legacy [Service-Specific Terms URL](https://www.cloudflare.com/service-specific-terms/) now redirects to the [terms overview](https://www.cloudflare.com/service-specific-terms-overview/). The relevant split pages both display **“Last updated: September 28, 2026.”** Do not substitute an old general “non-HTML” clause for these current service-specific provisions.

### Restriction: ordinary CDN audio delivery

[Application Services terms](https://www.cloudflare.com/service-specific-terms-application-services/), **Content Delivery Network (Free, Pro, or Business)**:

> Unless you are an Enterprise customer, Cloudflare offers specific Paid Services (e.g., the Developer Platform, Images, and Stream) that you must use in order to serve video and other large files via the CDN.

> Cloudflare reserves the right to disable or limit your access to or use of the CDN, or to limit your End Users’ access to certain of your resources through the CDN, if you use or are suspected of using the CDN without such Paid Services to serve video or a disproportionate percentage of pictures, audio files, or other large files.

This explicitly creates audio-delivery risk for ordinary CDN use. It names the Developer Platform among the Paid Services, but does not expressly classify an uncached Pages Function's continuous audio response or authorize it on Workers Free. Paying for a CDN Pro/Business plan is not itself the stated exception. Disabling cache is prudent architecture, not a legal exemption established by this clause.

### Permission, with limits: Developer Platform content hosting

[Developer Platform terms](https://www.cloudflare.com/service-specific-terms-developer-platform/), **Cloudflare Developer Platform**, explicitly includes Workers, Pages and Durable Objects:

> Unlike most Cloudflare products, the Developer Platform can be used to host content.

This permits content hosting in general. It does **not** expressly permit continuous audio proxying, third-party station redistribution, or any specified bandwidth volume.

The same section states:

> Cloudflare may temporarily limit your storage and/or the number of requests you can make or receive using the Developer Platform if processing such requests would put an undue burden on the Cloudflare network, adversely impact the Service, or otherwise threaten the integrity of Cloudflare’s networks.

It also requires use:

> in accordance with all associated developer documentation and any applicable third-party terms.

### Independent restriction: rights to the audio

The [Self-Serve Subscription Agreement](https://www.cloudflare.com/terms/) displays **“Last Updated September 12, 2025.”** Its Customer Content provision says:

> By transmitting Customer Content to or through the Services, you represent and warrant that Customer Content does not infringe, violate, or misappropriate any third-party right, including any copyright, trademark, patent, trade secret, moral right, privacy right, right of publicity, or any other intellectual property or proprietary right.

Section **2.7 Acceptable Use** prohibits transmitting audio/content that infringes intellectual property or is otherwise unlawful. A publicly reachable station URL does not establish redistribution rights. The [master-agreement index](https://www.cloudflare.com/legal/terms/) says exact terms depend on subscription type and subscribed services; no account-specific agreement was accessed.

**E5 conclusion:** general hosting permission, explicit CDN/rights restrictions, and silence on this precise continuous relay. Do not mark E5 “audio relaying permitted.” Ask Cloudflare for written clarification covering authenticated, non-cached, long-lived third-party radio audio through Pages Functions/Workers, both HTTP and HTTPS upstreams, the expected traffic, and Free versus Workers Paid. Workers Paid is the more defensible candidate, not a verified permission. Restricting the relay to HTTP reduces volume but does not remove the same terms/rights question.

## Runtime limits relevant to E4 deployment

Official sources: [Workers limits](https://developers.cloudflare.com/workers/platform/limits/) (updated 2026-10-08), [Pages Functions pricing](https://developers.cloudflare.com/pages/functions/pricing/) (2026-09-08), and [Pages limits](https://developers.cloudflare.com/pages/platform/limits/) (2026-09-05). Pages Functions use Workers quotas and the Standard usage model; static Pages asset limits are not streaming-response limits.

| Constraint | Verified documentation |
| --- | --- |
| Ordinary HTTP Worker CPU | Free: **10 ms per request**. Paid: **30 seconds default**, configurable up to **300,000 ms / 5 minutes**. Network waiting does not count; JS metadata parsing/copying does. A long response does not grant a fresh CPU budget per audio chunk. |
| Wall time | “There is no hard limit on duration for HTTP-triggered Workers.” Applies while the client remains connected, including response streaming. `waitUntil()` supplies only up to **30 seconds** after completion/disconnect, not an hour-long background relay. |
| Interruptions | Runtime updates give in-flight requests a **30-second grace period**, then terminate them. Unlimited configured duration is not uninterrupted-playback assurance. |
| Memory/body | **128 MB per isolate**, potentially shared by concurrent invocations. No enforced response-body size limit. Stream with bounded buffers; do not materialize the audio. |
| Quotas | Free: **100,000 requests/day**, shared with Pages Functions. Paid: no daily request cap, but billing applies. Subrequests: Free **50/invocation**; Paid **10,000 default**, configurable up to **10 million**. Redirect hops count. |
| Connections | Current docs specify **six simultaneous outgoing connections waiting for response headers**; they stop counting when headers arrive. Outbound WebSockets also count. Service-bound Workers share the top-level connection limit. |
| Pages static assets | **25 MiB per asset**, unrelated to a streamed Function response. |

Paid CPU configurability above is documented for Workers. The reviewed Pages configuration reference does not establish an equivalent `limits.cpu_ms` setting for Pages; verify the deployed Pages limit rather than assuming every Worker config key is accepted there.

[Durable Object limits](https://developers.cloudflare.com/durable-objects/platform/limits/) (2026-06-01) and [pricing](https://developers.cloudflare.com/durable-objects/platform/pricing/) (2026-09-30): Free can create/access **SQLite-backed** objects; new objects should use that backend. Legacy key-value-backed namespaces are restricted. Free DO quotas include **100,000 requests/day** and **13,000 GB-s/day**; exceeding a free allowance causes errors. Active/non-hibernatable duration is metered at the allocated 128 MB, even when waiting for I/O. An audio/SSE owner is not a free, hibernated connection.

**DO CPU ambiguity:** the DO limits table/default/reset text says **30 seconds**, increasable to five minutes, while the same page also says Workers per-plan limits apply. Do not promise 30 seconds of DO CPU on Free from this inconsistent wording; obtain clarification or deployed evidence. This does not change the Pages Free 10 ms outer-request limit.

The [DO lifecycle page](https://developers.cloudflare.com/durable-objects/concepts/durable-object-lifecycle/) (2026-09-30) says each pending operation prevents eviction until completion or **15 minutes from its start**, whichever comes first; later operations can extend residence. The limits page separately says DO HTTP/RPC wall time is unlimited while the caller remains connected. The operation window is not a documented universal 15-minute HTTP cutoff, but one pending fetch is not proof of hour-long object residency. Shutdown/runtime updates can interrupt in-flight work. Validate the actual stream/subscriber lifecycle over 60+ minutes; plan to restart with a new generation rather than silently reuse stale titles.

## Deployment-supported same-upstream title channels

The [Workers execution model](https://developers.cloudflare.com/workers/reference/how-workers-works/) states:

> Because there is no guarantee that any two user requests will be routed to the same or a different instance of your Worker, Cloudflare recommends you do not use or mutate global state.

A module-level title map shared by `/api/relay/:stationId` and `/api/relay-events/…` is therefore not a deployable rendezvous, even if local tests pass. A Service binding alone does not fix this.

**Supported primitive:** [Pages bindings](https://developers.cloudflare.com/pages/functions/bindings/) (2026-06-25):

> You must create a Durable Object Worker and bind it to your Pages project using the Cloudflare dashboard or your Pages project's Wrangler configuration file. You cannot create and deploy a Durable Object within a Pages project.

The [Pages configuration reference](https://developers.cloudflare.com/pages/functions/wrangler-configuration/) also requires **`script_name`** on Pages DO bindings. Configure the namespace/class/binding for both production and preview. Local validation requires the DO Worker and Pages dev servers, not only the page server.

Two proposed designs preserve the same upstream connection:

1. **Recommended: one DO owns each listener's relay generation.** Pages authenticates both audio and SSE requests, resolves an opaque session-bound relay handle to the same object, and forwards both through the namespace binding. The DO opens exactly one station connection, strips ICY bytes for audio and sends titles parsed from those bytes to its SSE subscriber. [DO instance-state documentation](https://developers.cloudflare.com/durable-objects/reference/in-memory-state/) guarantees requests to one object reach its one active instance; use instance state, not module globals. Restart/eviction needs explicit generation invalidation and cleanup.
2. **Pages owns audio; DO owns title rendezvous.** The parser on the audio request publishes only its own observed titles, tagged with listener handle, generation and sequence, to the DO; the authenticated SSE request subscribes to that same object. This also preserves provenance but adds publication calls, subrequest budgeting, ordering/replay and disconnect coordination. Do not open a second station connection for metadata. Avoid per-chunk publication; bound work and prove hour-long subrequest usage.

An equivalent deployment path is a **Pages Service binding → separate relay Worker → DO**. [Pages Service binding documentation](https://developers.cloudflare.com/pages/functions/bindings/#service-bindings) and [Worker HTTP binding documentation](https://developers.cloudflare.com/workers/runtime-apis/bindings/service-bindings/http/) support request forwarding; [Streams documentation](https://developers.cloudflare.com/workers/runtime-apis/streams/) supports returning streamed response bodies. The Worker still needs an explicit rendezvous such as its DO; its own globals cannot join separate audio/SSE requests. Browser routes can remain on the Pages origin. No second public browser origin is required.

**Layout consequence:** the accepted `functions/api/` layout can remain the authenticated front door, but either DO design requires an **additional Worker deployment**, class migration/configuration and Pages binding. Pages alone cannot deploy the DO. Parent must assign ownership for that wiring; this discovery slice cannot create it. Moving the entire site to Workers Static Assets would change the accepted hosting arrangement and is not authorized here. These are documented primitives and proposals, not a deployed SSE proof.

## Blockers and next checks

- **Permission gate — parent/user:** obtain Cloudflare clarification and establish station redistribution rights. If unresolved or refused, do not launch the all-station relay. Candidate fallbacks: direct HTTPS playback without relay-derived ICY titles; a rights-cleared relay on hosting that explicitly allows it; or HTTP-only relaying after separate permission. Each changes scope and requires a decision.
- **Deployment gate — parent:** approve/assign the extra DO Worker, SQLite class migration and production/preview bindings. Deployment remains unauthorized in this slice. Confirm CPU limits/DO Free ambiguity and bound cost before choosing a plan.
- **E2 — user:** scan the candidate QR with fork alone and with Automattic installed; check cold/warm launch, exact prefill and successful approval. Separately try the actual verification URI and manual entry. Record failures rather than inferring OS behavior from source.
- **E4 — parent/user after permission and deployment:** verify same listener/generation through distinct Pages requests, absence of a second upstream fetch, SSE reconnect/replay and stop cleanup. Then measure 60+ minutes for HTTP and HTTPS upstreams, CPU, DO duration, interruptions and audible continuity. Buffer delay still separates receipt time from audible playback.

## Verification boundary

Only this report was written. Required instructions and ADRs 0002–0004 were read; focused iOS routing/view/plist/entitlement sources and current official public documents were inspected. Context7 retrieved current Workers and Pages binding documentation, cross-checked against direct official fetches. One guessed Pages Functions limits URL returned 404; the official Pages index identified the correct platform limits/pricing pages.

**Red/green and tests:** not applicable to this read-only discovery slice; no implementation changed and no behavior test was run. None of E2/E4/E5's live or human pass criteria is claimed passed. No identity/proxy implementation was audited by this report.

Effective route: **`openai-codex/gpt-6.1-sol`**; environment matched and `pi auth check --provider openai-codex --json --no-refresh` reported ready/OAuth. No credential files were inspected. Budget: 300k input / 10k output planning allowance; exact harness usage and subscription consumption were unavailable, so no measured usage or cost is claimed.
