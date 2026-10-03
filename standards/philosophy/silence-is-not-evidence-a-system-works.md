---
title: "A running system's silence is not evidence it works"
type: "rule"
category: "philosophy"
---

An error-free log is not a working system. A service that starts cleanly, stays up, and prints nothing alarming may be doing nothing at all. Before believing a component works, check its **effect** — bytes actually delivered, a connection actually established, state actually changed — not the absence of complaints.

**Why:** three unrelated failures in a single deployment session each failed **completely silently**:

- A tunnel relay in a bundled access-gateway product accepted TCP connections and forwarded zero bytes. The reverse proxy in front of it was listening, so `nc -zv` reported the port open and healthy. Nothing logged an error on either side: the relay had loaded zero proxy mappings and said so nowhere.
- A container could not reach a Tailscale mesh IP, because Tailscale does not forward traffic originating from Docker bridge subnets. `nc` succeeded from the *host* and timed out from *inside the container*, with no error on either side until a long connect timeout — which reads like a firewall problem and isn't.
- Komodo Core accepted an agent's websocket and immediately dropped it, because it did not know that agent's public key. Neither side logged anything; the only visible symptom was TCP state cycling `ESTAB → FIN-WAIT-1` on a repeating retry.

In all three, "no errors in the log" was actively misleading. Each was diagnosed by inspecting TCP state (`ss -tn`) or by making a real request and checking the *result* — never by reading logs.

**How to apply:**

1. Pick the check that observes the system's **effect**, not its health: real bytes received by a listener, a row actually written, an audit event actually recorded — not "the container is up" or "the status is green."
2. For anything network-shaped, `nc -zv` proves only that *something* accepted a connection. Send real data and confirm it arrives.
3. Test from where the traffic actually originates. A host and a container on that host are different network positions and routinely give different answers.
4. Prefer a check that reports **how** something connected over one that reports only **whether** — a path descriptor (direct vs. relayed) catches degradation that a success/fail check cannot — a mesh VPN can appear to peer directly through conntrack alone, then silently fall back to a relay.
5. When the symptom is "it connects and then doesn't work," look at connection *state over time* rather than a single sample.

Complements `[[deliberate-break-proofs]]`, which is the same trap one layer up: that note is about a **guard** whose silence is mistaken for evidence; this one is about a **running system** whose silence is mistaken for function. Both come down to a green signal that was never actually asserting anything, and both are worse than a loud failure because the natural reaction is to move on satisfied.

Part of a recurring family of "the control appears enabled but protects nothing" findings — object-lock enabled without a retention rule protects nothing, and a dependency-audit ignore list can silently exempt the very crate it was meant to catch. See also `[[verify-before-claiming-done]]` for the claim-side discipline.
