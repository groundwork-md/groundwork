---
title: "Prefer self-hosted / built-in solutions over external vendors"
type: "default"
category: "philosophy"
---

Strongly prefer self-hosted / built-in solutions over external vendors and BaaS platforms, and minimize the number of third parties in general. When proposing a dependency, distinguish a *library* (acceptable — code you control, runs in your own process) from an external *service* (avoid unless justified — a vendor you depend on operationally and whose data-handling you don't control).

**Why:** control over data (data stays in owner-controlled, self-hostable infra — also helps with GDPR: erasure, export, consent, retention are all easier to actually guarantee when the data never leaves infra you control), fewer external moving parts, and — for anything meant to be reusable by others — staying vendor-neutral for whoever else uses it.

**How to apply:** default to self-hosted/library options. When an external service genuinely seems needed, surface it explicitly and offer a self-hosted alternative rather than reaching for the vendor by default. GDPR-consciousness is a recurring concern worth factoring in whenever touching user data, regardless of which specific project.
