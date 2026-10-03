---
title: "Deliberate-break proofs: a guard that has only ever passed is not known to work"
type: "principle"
category: "philosophy"
---

A guard — a test, a lint, a CI check, a license gate, a compile-time assertion — that has only ever been observed **passing** is not known to work. It may be asserting nothing. Adopt the ritual: **break the thing it guards, confirm it goes red, revert.** Cheap, fast, and it has caught real non-guards repeatedly.

**Why:** independently converged on at least four times across unrelated domains — a cross-language stride-drift checker that fired on the TypeScript side but never the Rust side of the same bug; a close gate that reported `PASS` over a build failure because it grepped for a string a compile error never prints; `cargo-deny`'s `private.ignore = true` silently exempting an AGPL probe crate from license enforcement because it carried the workspace's usual `publish = false` convention; and an S3 Object Lock "GoBD-relevant Compliance-locked bucket" that was, operationally, an ordinary deletable bucket because enabling Object Lock is a capability switch, not a protection, until a retention rule is actually set (full details: `vault/technical/testing/Deliberate-Break Proofs Are the Only Evidence a Guard Works.md`, `vault/technical/rust/cargo-deny private.ignore Silently Exempts an AGPL Probe Crate.md`, `vault/technical/infra/storage/S3 Object Lock Enabled Without a Retention Rule Protects Nothing.md`). Each one produced exactly the reassuring output that was hoped for — a false pass in a security control is the worst possible shape for a check to fail in, because the natural reaction is to move on satisfied.

**How to apply:**
1. Break the guarded property in the smallest way that is genuinely wrong.
2. Run the guard. Confirm red, and read the failure message — a red for the wrong reason is its own trap.
3. Revert, and confirm green again (verify against real state, e.g. `git status`, not by assuming the revert worked).
4. Where the guard is permanent and important, write the deliberate break into the test suite as its own test, so the guard's guard is also automated.
5. Every `ignore`/`skip`/`private`/`exception` clause on a guard (a license-gate exemption, a test skip pattern, a lint suppression) is a hole in what the proof actually covers — construct the proof to fall outside all of them, not just the common case.

Complements `[[verify-before-claiming-done]]` — that rule is about not claiming a task is done without fresh evidence; this one is about not trusting a guard's silence as evidence in the first place, which is a distinct and easier trap to fall into since a passing guard doesn't even prompt the question. Relevant wherever a mechanical gate is the thing standing between a mistake and production — licence enforcement and retention/access guarantees are the two that cite this most directly.
