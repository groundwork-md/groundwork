---
title: "Prefer composable over bundled, especially for infrastructure"
type: "rule"
category: "philosophy"
---

When one tool bundles several roles (its own proxy, its own tunnel, its own control plane, its own database), that convenience is also the thing that will stop you fixing it. Prefer components with real seams — each independently inspectable, replaceable and debuggable — over a single tool that swallows four jobs.

**Why:** learned concretely, twice in two days. A self-hosted access gateway was adopted specifically *because* it bundled a reverse proxy, a WireGuard tunnel, identity-aware access control and a control plane into one product, explicitly instead of "a hand-rolled proxy plus mesh combo." That reasoning was sound on paper. Then its tunnel component turned out to have an unresolved upstream bug in TCP proxying, and the bundling turned a component failure into a total blocker:

- **No seam to replace the broken part.** The relay could not be swapped out without also removing the reverse proxy, the access control and the control plane.
- **Failure was hard to localise.** Routes lived in a service's own database rather than in files, so "is this configured correctly?" could not be answered by reading a diff.
- **Debugging fought the abstraction.** Diagnosis required reading the vendor's own source to learn that an entryPoint had to be named a particular way, and that a field the API happily returned was never actually read.

The replacement, a standalone reverse proxy and a standalone mesh coordinator as separate components, is more moving parts on paper, but every route is a file in git and any single piece can be swapped without touching the others.

**Confirmed independently the very next day, a different tool:** a self-hosted deployment/PaaS tool was adopted for its bundled control plane, internal reverse proxy and deploy orchestration, which were exactly the pitch. Its OIDC integration was made to genuinely work end to end after real debugging effort (two independent bugs, both root-caused and fixed). Then a separate, unrelated failure, its own built-in "localhost" deploy target reporting unreachable despite manual SSH/docker access working fine with the identical key, **could not be isolated**: the bundled control plane gave no seam to inspect *just* the deploy-target-reachability check in isolation from everything else the tool owns. Root cause was never found; the tool was abandoned in favor of another rather than continuing to debug a black box. Same shape as the first case: real, non-trivial integration work had already succeeded (OIDC login, in this case) before the bundled-vs-composable cost showed up somewhere else entirely.

**How to apply:**

- Weigh "fewer things to run" against "can I replace exactly one of these when it breaks." For infrastructure, the second usually matters more.
- Treat *configuration living inside a service's own database* as a real cost, not a neutral implementation detail. Version-controlled config makes misconfiguration visible in review, and makes a bad change revertible.
- A tool that is a thin orchestration layer over components you could otherwise run yourself is a far safer bundle than one that reimplements them.
- This is a **tension with, not a contradiction of**, `[[prefer-self-hosted-fewer-third-parties]]`: fewer third parties remains the goal, but not achieved by adopting one product that owns four roles. Fewer *vendors* is the aim; fewer *seams* is not.
- When a bundled tool does fail this way, `[[debugging-escalation-after-repeated-failures]]` applies — repeated fixes against the same symptom mean re-examining the choice, not attempting a fourth workaround. In the gateway case exactly three fixes went in before the tool itself was correctly identified as the problem; the deployment-tool case reached the same conclusion faster, stopping after the *unrelated* failure rather than continuing to patch around a bundled tool's own opacity, once the pattern was already recognized. Recognizing the pattern once made the second occurrence cheaper to call correctly — itself a case for writing this note down in the first place.
