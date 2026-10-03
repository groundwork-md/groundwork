---
title: "Start-new-project: resolve every open decision, scope everything, then write code"
type: "rule"
category: "session"
---

Applies identically regardless of project shape — a single repo, a monorepo, or a project spanning several separate repos. Nothing in this process branches on that; whichever shape it turns out to be, every repo the project needs still gets the local-first bootstrap (`workflows/repo-workflow/bootstrap.md`), and the decision-resolution and scoping steps below happen once at the project level before any of them.

**The point of this workflow: nothing about the idea is still open by the time the first issue gets claimed.** Scoping isn't "figure it out as we build" — every real decision gets made up front and baked into the milestone and issue backlog, so implementation is just execution against an already-settled plan.

**Paths are layer-relative.** Every `standards/…`, `vault/…` and `workflows/…` path in this
workflow names a path inside one groundwork layer, not under `~/.claude/groundwork/` itself. Most of the
standards it points at (naming theme, domain availability, licence, regulatory baseline, hosting)
live in an upper layer, not in this one. Resolve a note by name in `~/.claude/groundwork/INDEX.md` (each
line names its layer; the layer handles are `~/.claude/groundwork/<NN-layer>/`) or with
`rg --files $(cat ~/.claude/groundwork/ROOTS) | rg <name>`. When a note exists in several layers, read
every copy; the higher-ranked layer is the more specific. The project's own notes (spec, decision
list, whitepaper draft) go in the layer that owns the project: a company's project in the company
layer.

## 1. Classify project weight, then resolve every open decision

**First, classify the project** — this decides which version of step 1 applies, and the classification itself is a real decision to make explicitly with the maintainer, not inferred silently.

Two independent questions, in this order. **Does it have external users or real-world stakes?** If no, it is internal tooling. If yes, then: **who operates it — us, or the user?**

| Classification | Test | Step 1 route |
|---|---|---|
| **Hosted product/venture** | Real users, and **we run it** on our infrastructure | §1a, `enterprise-spec-sheet-template.md` |
| **Distributed product** | Real users, and **they run it** on their own machine or infrastructure — a CLI, library, desktop app or agent | §1a, `distributed-product-spec-sheet-template.md` |
| **Internal tooling** | No external users, no business model | §1b lightweight decision list |

The hosted/distributed split exists because the enterprise template is built around infrastructure the project's operator runs — hosting, network topology, RTO/RPO, message brokers, RBAC/MFA, uptime SLAs — none of which has anything to say about software running on someone else's laptop. Filling nine sections with "out of scope" produces a document that is structurally perfect and content-free, which is the failure mode a placeholder check over the spec exists to catch.

**A distributed product is not a lighter compliance obligation** (an explicit decision). It sits under the same legal and audit bounds; the obligations land in different places. GDPR becomes *what leaves the user's machine* plus the hosted parts we do run — docs site, download host, any telemetry sink. Impressumspflicht attaches to the public web presence rather than the binary. ISO 27001 / SOC 2 readiness becomes supply-chain integrity, release signing, and a vulnerability-disclosure path. §6 is a full section in both templates, never a reduced one.

Reclassification is legitimate and should be explicit: a project scoped as internal tooling and later rebuilt as a distributed product changes the licence decision, the naming rules and the spec route all at once.

### 1a. Real product/venture: the spec-sheet process

Applies to **both** product classifications above; only the template differs — `enterprise-spec-sheet-template.md` for hosted, `distributed-product-spec-sheet-template.md` for distributed. Everything else in this section is identical for the two.

Decided 2026-08-28 (the maintainer's own template, adapted into `workflows/session/templates/enterprise-spec-sheet-template.md`): before any repo exists, draft a full specification sheet collaboratively — **iterate section by section with the maintainer, over and over, until every section is filled with real project-specific content or explicitly marked out of scope, never left reading like the template's own generic prompt text.** This is where the decisions the lightweight list below would otherwise cover (name, license, regulatory scope, business model, tech stack, design, copy) actually get made — the spec sheet's sections are a superset of that list, not a separate parallel process. **If the project has a public face, its design and copy sections are decided through `new-brand-identity.md` (`/new-brand-identity`)**, which the spec then references.

- **Template**: whichever the classification selected. Copy it verbatim; do not merge sections from the other one, and do not prune sections up front — a section is removed only by being explicitly marked out of scope *with its reason*, which is the record of the decision having been made at all.
- **Format: the chunked spec format**, `workflows/session/templates/spec-format/`. Not a single
  file. A single file failed concretely: one spec reached 2,001 lines and 175 functional
  requirements, and still shipped a product that could not reassign a work item, because all eight of
  its sections described **the system** and none described **people**. Length was not the problem.
  The format supplies what was missing:
  - **`01-actors.md`** — every role and what it may do. That spec had no equivalent; writing one
    took under an hour and produced six findings immediately.
  - **A dimensions block per domain** — actors, over time, multiplicity, unwanted, and *not-you*.
    The last two are the ones never invented unprompted. *Over time* and *Not-you* cannot be
    answered honestly without noticing that work changes hands.
  - **Diagrams before prose**, using your diagramming skill or tool if you have one. A diagram is a forcing function: an
    ER diagram cannot be drawn without committing to cardinality, a swimlane without naming who
    acts. **A swimlane with exactly one lane is a finding, not a diagram.**
  - **EARS requirement syntax** — *When* / *While* / *If-then* / *Where* — so each requirement maps
    to a test directly, and unwanted behaviour is a first-class category rather than something
    remembered.
  - **~300 lines per file, stable IDs, issues citing the IDs they implement.** A spec nobody can
    load alongside the work stops governing it.

  The two older single-file templates remain for reference; new projects use the chunked format.
- **Draft location**: `vault/projects/<project-slug>/spec.md` — `vault/projects/` already exists as a designed-but-until-now-empty home for exactly this, and `vault/` README already anticipates a `repo` frontmatter field for notes under it. Copy the template from `workflows/session/templates/enterprise-spec-sheet-template.md` verbatim as the starting point; frontmatter `type: "spec"`, `repo: "<project-slug>"`.
- **Compliance/infra sections (§3.1, §6) restate the actual content per project**, not just a pointer to the regulatory-baseline and hosting notes in `standards/legal/` and `standards/tech/` — an explicit call, so the document stands alone for an external reader (auditor, investor, compliance officer) without groundwork access. Real cost, accepted deliberately: two copies of the same underlying fact that can drift apart, the same way a platform-architecture standard and seven other files drifted after a deployment-tool switch (`workflows/groundwork/self-review.md`). Mitigation: a self-review pass should check active spec sheets under `vault/projects/` against current standing defaults, same as any other file that cites one.
- **The spec is the internal drafting record and stays in groundwork**, at `vault/projects/<project-slug>/spec.md`, permanently. What reaches the repo depends on whether that repo is private or public:
  - **Private repo** — copy, do not move, the finished spec into it (e.g. `docs/SPEC.md`). Same audience, no filtering needed.
  - **Public repo** — the repo gets a **whitepaper derived from the spec, never the spec itself**. A spec sheet written properly is candid about the predecessor's failures, cites internal paths and sibling repositories by name, and records commercial optionality. Every one of those is correct in the drafting record and wrong in a public repo. The whitepaper is its own document with its own audience: why the problem is worth solving, the model and its guarantees, the architecture at the depth an evaluator or contributor needs, and what the product deliberately will not do. It carries no requirement matrices and no internal references.

    The whitepaper is drafted in `vault/projects/<project-slug>/` only because the repo does not exist yet, and is **moved** there at bootstrap, not copied — groundwork keeps no copy of it. It is a public product artifact with one home, which removes the possibility of drift rather than managing it.

  In every case groundwork's copy of the **spec** stays permanently as the drafting record, even if the repo's own document later evolves independently (the repo owns ongoing changes to its own spec; groundwork keeps the as-drafted snapshot, same durable-record reasoning as `workflows/session/retire-project.md`'s own concern about not losing information when a project's working state goes away).
- Only once the spec sheet is genuinely complete does step 2 (repo bootstrap) start — implementation still doesn't begin until step 3 (full backlog) either way.

**Distributed products carry three decisions the hosted route does not**, and none of them should be deferred past the spec: the **supported platform and toolchain matrix** (§3.2 — every external binary gets a declared version floor and a feature-detection strategy, because an undeclared assumption about an external tool's version is a defect that only ever appears on someone else's machine); the **installation trust model** (§6.4.2 — a `curl | sh` one-liner is a real threat-model decision, not a convention to adopt silently); and the **non-interactive contract** (§5.2 — every operation reachable without a prompt, since agents and CI are first-class users of a distributed tool rather than an afterthought).

**Never symlink a document from groundwork into a repo.** Git stores a symlink *as a symlink* (mode `120000`, target path as content), so committing one into a public repo gives every person who clones it a dangling link and publishes the maintainer's local filesystem layout. A gitignored symlink avoids that but is a live footgun — one `git add -f`, one link-following tool, one archive command, and either the path or the internal document ships. It also breaks on Windows, which needs Developer Mode to create symlinks at all.

**To see the internal spec while working in the repo, use a multi-root editor workspace** (a `.code-workspace` file, or the JetBrains equivalent) listing groundwork and the project repo as sibling roots. Both trees are visible, the spec is editable in place, and **nothing at all is added to the repo** — no file, no symlink, no gitignore entry, nothing that can leak. Works identically on every platform.

### 1b. Internal tooling: the lightweight decision list

Work through each of these with the maintainer directly — nothing here gets assumed or defaulted silently, even where a standing default exists, since the default might not fit this specific idea:

- **Name.** Generate candidates per your layer's naming theme (`standards/marketing/`), verify all six TLDs correctly per its domain-availability rule (`standards/tech/`) before treating any candidate as viable.
- **License.** Resolve it from your layer's `standards/legal/` default-licence note, if it has one. Distinct from that layer's dependency-licence policy, which governs what dependencies a project may consume, not what license the project itself ships under. Still confirm per project rather than rubber-stamping — a project not meant to be open-source-facing at all legitimately deviates (a source-available licence, closed source), but the layer's default is the starting point, not a from-scratch decision each time. Internal-only tooling commonly deviates to no-license/private.
- **Regulatory scope.** Check your layer's regulatory baseline (`standards/legal/`) against this specific project — data protection, accounting and tax rules, publisher disclosure, AI-specific regulation and any sector regulation (financial, health, children) that your jurisdiction defines. Record which regimes actually apply and which were checked-and-ruled-out, not silently skipped.
- **Business model / monetization.** `standards/business-model/` exists but is currently empty — there's no standing default to fall back on. Resolve pricing/licensing-model/monetization shape per project (commonly N/A for internal tooling).
- **Tech stack.** Start from `standards/tech/` defaults (a language toolchain, a hosting provider, etc.) where they actually apply, but the stack as a whole — languages, frameworks, hosting, major dependencies — is a real per-project decision, not a rubber stamp. Record real choices as ADRs once decided.
- **Design direction, copy and positioning.** For a project with a public face, run `new-brand-identity.md` (`/new-brand-identity`): positioning and offer, then palette, logo, type, an optional mascot and motion, then the full copy, each decided from rendered options and recorded. `standards/philosophy/design-aesthetic-clean-simple.md` is the baseline taste and your layer's `standards/marketing/` the baseline stance for copy; neither is inherited wholesale (commonly N/A for internal tooling).

## 2. Repo bootstrap

For each repo the project turns out to need: the local-first bootstrap per `workflows/repo-workflow/bootstrap.md` — no remote unless a specific one is genuinely justified later, `production` and `development` branches, and the tracker set up through its adapter (`workflows/repo-workflow/adapters/github-issues.md`). A monorepo is one bootstrap; a multi-repo project is the same bootstrap repeated once per repo, sharing the decisions already resolved in step 1. For a venture-weight project, this is also the point where the finished spec sheet gets copied into the new repo per step 1a above.

## 3. Scope everything before any code

Full milestone and issue backlog, filed through the tracker adapter (`/new-issue` for each issue; the field rules are in `workflows/repo-workflow/issue-lifecycle.md`) — not a partial plan filled in as work proceeds. Every issue already carries its resolved decisions from step 1 (the chosen stack, the chosen name, the chosen license, real copy where the ticket touches user-facing text) — never a placeholder/TBD waiting on a decision that should've been made in step 1.

M0 is Foundation, per the naming convention in `workflows/repo-workflow/milestones.md` — but **not** "CI/CD is always its first issue": there is no standing CI/CD requirement. M0's actual first issues are whatever the project genuinely needs first (license file, scaffold, licensing/naming already resolved so they just need recording) — set up CI/CD only if and when a real need for it shows up.

## 4. Only then: implementation

Claim the first issue per `workflows/repo-workflow/issue-lifecycle.md`. If implementation surfaces a decision that step 1 missed, stop and resolve it properly (the same as any mid-work discovery there) rather than deciding it inline and moving on — the whole point of front-loading decisions is that implementation shouldn't be where they get made.
