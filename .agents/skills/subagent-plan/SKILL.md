---
name: subagent-plan
description: Create model subagent plans when the user asks for a subagent plan, delegation plan, or multi-model implementation workflow. Applies to OpenAI and Anthropic models only, not open-weight models or other publishers.
---

# Subagent plan

## Rate snapshot

**Last updated: 2026-10-04 (UTC).** These are selected public rates, not a complete model catalog or a guarantee of account access. Check freshness before using them.

### API rates — USD per 1 million tokens

Standard-speed text rates from [OpenAI API pricing](https://developers.openai.com/api/docs/pricing) and [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing). OpenAI rows use short-context rates; Anthropic rows use default global routing.

| Publisher | Model ID | Uncached input | Cached input/read | Cache write | Output |
|---|---|---:|---:|---:|---:|
| OpenAI | `gpt-6-astra` | $10.00 | $1.00 | $12.50 | $50.00 |
| OpenAI | `gpt-6.1-sol` | $2.00 | $0.10 | $2.50 | $10.00 |
| OpenAI | `gpt-6-luna` | $0.10 | $0.01 | $0.125 | $0.50 |
| Anthropic | `claude-fable-5-1` | $10.00 | $0.25 | $12.50 / $20.00 | $50.00 |
| Anthropic | `claude-opus-5-5` | $4.00 | $0.20 | $5.00 / $8.00 | $20.00 |
| Anthropic | `claude-sonnet-5-5` | $2.00 | $0.20 | $2.50 / $4.00 | $10.00 |
| Anthropic | `claude-haiku-4-5` | $1.00 | $0.10 | $1.25 / $2.00 | $5.00 |

Anthropic cache-write cells show **5-minute / 1-hour** prices. The Haiku ID is an alias; its current dated API ID is `claude-haiku-4-5-20251001`. Confirm IDs and access against the [Anthropic model overview](https://platform.claude.com/docs/en/about-claude/models/overview) and the local model registry.

OpenAI's listed flagship API models charge 2x input/cache rates and 1.5x output rates for requests over 272,000 input tokens, applied to the full request; see the [Sol 6.1 model specification](https://developers.openai.com/api/docs/models/gpt-6.1-sol). Anthropic 4.6 and later models include long context at standard token rates. Speed modes, regional routing, tools, and account agreements can change costs. Do not apply this table to an unlisted model or billing mode.

### OpenAI subscription credits — credits per 1 million tokens

Standard-speed rates from [OpenAI Codex/ChatGPT Work pricing](https://developers.openai.com/codex/pricing/). These apply to eligible credit billing, including purchased credits; they are **not API dollars or a conversion formula for included subscription allowance**.

| Model ID | Uncached input | Cached input | Output |
|---|---:|---:|---:|
| `gpt-6-astra` | 250 | 25 | 1,250 |
| `gpt-6.1-sol` | 50 | 2.5 | 250 |
| `gpt-6-sol` | 50 | 5 | 250 |
| `gpt-6-luna` | 2.5 | 0.25 | 12.5 |
| `gpt-5.6-terra` | 50 | 5 | 300 |
| `gpt-5.6-luna` | 5 | 0.5 | 30 |

Codex credit billing has no separate cache-write charge. Credit rates alone do not determine included subscription consumption. Model, context, reasoning, tools, caching, and speed affect usage. For example, Terra is not cheaper than Sol 6.1 at these rates; Luna is. Never infer a fixed quota multiplier from the price ratio.

Anthropic API prices are separate from Pro/Max subscription limits. Claude and Claude Code share included usage; API-credit use is separately billed. This snapshot does not establish a public per-token conversion for included Anthropic subscription allowance. See [Claude Code with Pro/Max](https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan). Label subscription-quota savings as unknown rather than substituting API dollar estimates.

## Start here — scope and freshness gate

0. **Check teh applicability of tihs process**: User should be specifying a specific plan with multiple steps. If there are no substeps or if there is uncertainty propmt the user until you get clarity on what the ask is.
1. **Confirm applicability.** Identify the active model's publisher, exact model ID, configured provider ID, authentication route, and billing mode from session metadata or non-secret configuration. Do not read or print credentials. This skill applies only to OpenAI or Anthropic models. For open-weight models or other publishers, state that this policy does not apply and use the user's existing planning workflow; do not impose these rates or model-routing rules. If the publisher or billing mode is unclear, ask before making cost claims or selecting delegates.
2. **Get today's date.** Use the runtime date in UTC, not a remembered date from conversation history. Read `Last updated` above. The snapshot is stale when today is later than the update date plus **one calendar month**, clamping the day to the destination month's last day. An age of exactly one month is still fresh. A missing, invalid, or future update date also requires verification.
3. **Stop if stale or unverified.** Before proposing a plan, selecting models, launching agents, or editing the snapshot, ask: "The rate snapshot was last updated on <date> and is more than one month old [or cannot be verified]. Would you like me to refresh the OpenAI and Anthropic rates before planning, explicitly use this snapshot as stale, or stop?" Wait for the user's answer. Do not treat silence or declining an update as permission to continue with stale prices.
4. **Handle the answer.** If the user approves an update, fetch current official sources for both publishers, verify model IDs, units, caching, context tiers, and subscription distinctions, then update the tables, source links, and date. Advance the global date only after verifying the whole snapshot; otherwise retain the old date and disclose which rates remain unverified. If source access fails, pause and offer retry, explicitly using stale data, or stopping. If the user explicitly accepts stale data, label the plan and every cost estimate with the snapshot date and stale status. If they choose to stop, stop.
5. **Continue only after the gate passes.** Use the current or explicitly accepted snapshot to prepare the plan below. Report snapshot changes and follow repository rules for commits; do not automatically commit, push, or start implementation merely because this skill was invoked.


## Model Determination ##
- The goal is to choose the most appropriate model for each substep where appropriate means it's a model capabible of accomplishing the task with high accuracy and confidence BUT not one that wastes tokens. When in doubt choose a more capibile model.

## Keep delegates within the active provider

- For an OpenAI model, choose only OpenAI models. For an Anthropic model, choose only Anthropic models. This includes implementation, discovery, tests, review, and escalation.
- Verify proposed models are actually available through the active provider. Use exact provider/model identifiers in the plan; a public model listing or local registry entry alone does not prove account access.
- Inspect existing agent definitions before reuse. Do not launch a role agent that has a different provider/model configured. If the delegation tool cannot pin the intended provider/model, disclose the limitation and ask how to proceed; do not silently fall back.


## Completion check

Before returning the plan, verify that the freshness gate passed, every delegate stays within the active publisher/provider/authentication route, every slice has a token budget and stopping condition, all costs have explicit units and assumptions, and implementation remains behind the project's approval gate. This skill provides planning instructions; it does not itself enforce token limits or configure subagent models.
