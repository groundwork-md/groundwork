---
title: "Templates and standards stay generic; real specifics are asked for at runtime"
type: "principle"
category: "philosophy"
---

Nothing in `standards/` or `workflows/` — templates, defaults, boilerplate — ever carries real entity-specific or personal-specific values. They use generic placeholders (`{{company_name}}`, `{{address}}`, etc.), filled in per use case, not baked in as a default.

**Why:** there isn't one canonical real entity to default to — projects may be issued under different companies over time, and a template that hardcodes one specific entity's details silently becomes wrong (or leaks that entity's real data into an unrelated context) the moment it's reused for another.

**How to apply:** when a task actually needs real specifics (drafting a real legal document, filling in a real business address), ask for them at that point rather than assuming a default or reaching for whatever real value happens to be sitting in context. If a real value is worth keeping for reuse, it belongs in `vault/companies/<entity>/` or `vault/personal/`, tagged `sensitivity: "real-identity"` — never in a template or standard.

See [[no-real-pii-in-examples]] for the closely related rule about mockup/example content specifically.
