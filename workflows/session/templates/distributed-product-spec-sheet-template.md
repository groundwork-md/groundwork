---
title: "Distributed product specification sheet — master template"
type: "reference"
category: "session"
---

Used by `workflows/session/start-new-project.md` step 1 for any new project classified as a
**distributed product** — software the *user* runs on their own machine or infrastructure (a CLI,
a library, a desktop app, an agent) rather than software *we* operate for them. Sibling to
`enterprise-spec-sheet-template.md`, which covers the hosted case. See that workflow's
classification step for which applies.

The gap this fills: the enterprise template's §3.1
(hosting infrastructure), §3.4 (RTO/RPO), §5.3 (message brokers), §6.1.1 (data residency in our data
centres), §6.3.1 (RBAC/MFA) and §7.4 (uptime SLAs) have nothing to say about software running on
someone else's laptop — and filling them with "out of scope" nine times produces a document that is
structurally perfect and content-free, the exact failure mode a placeholder check over the
spec exists to catch.

**Compliance is translated, not dropped** (an explicit decision). A distributed product
sits under the same legal and audit bounds as a hosted one; the obligations simply land in different
places. GDPR becomes *what leaves the user's machine* plus the hosted parts you do run (docs site,
download host, any telemetry sink). Publisher-disclosure obligations (an imprint, in some jurisdictions) attach to the public web presence, not the
binary. ISO 27001 / SOC 2 readiness becomes supply-chain integrity, release signing and a
vulnerability-disclosure path. §6 is therefore a full section here, not a reduced one.

**How to apply:** copy the template below verbatim into a new draft file (see
`start-new-project.md` step 1 for the exact filename/location), then iterate on it directly with
the maintainer — section by section, asking rather than assuming, until every section is either filled in
with real project-specific content or explicitly marked out of scope for this project (never left as
an empty placeholder or a silent omission). Section 4 duplicates per functional domain the project
actually has; every other section appears once.

**Diagrams: use your diagramming skill or tool, if you have one, wherever a section is naturally a
diagram, not prose.** Sections where a real diagram belongs:

| Section | Diagram type |
|---|---|
| §3.1 Execution Model & Process Topology | architecture or deployment diagram |
| §3.5 Local State & On-Disk Layout | ER/data model or tree diagram |
| §3.6 Failure Modes & Degradation | state machine or flowchart |
| §4.X.2 User Persona Maps & Interaction Journeys | user journey diagram |
| §4.X.4 State Machine Logic | state machine diagram |
| §4.X.5 Interface Surface | flowchart per command group; never a UI wireframe |
| §5.1 Interface Stability Contract | state machine (version lifecycle) |
| §5.3 Outbound Network Calls | data flow diagram — every egress point, or a stated "none" |
| §6.4.2 Release Integrity Chain | sequence diagram (source → build → sign → publish → verify) |
| §7.1 CI/CD Lifecycle | process or swimlane diagram |
| §7.2 Distribution Channels | deployment or dependency diagram |
| Appendix A | ER/data model diagram |

**Not a fit**: §4.X.5 for graphical apps — literal UI mockups belong in a design tool, not
a diagramming one. And per `standards/philosophy/design-aesthetic-clean-simple.md`, a diagram that
does not earn its place should be deleted rather than drawn.

---

```markdown
# DISTRIBUTED PRODUCT SPECIFICATION SHEET
**Document ID:** SPEC-[PROJECT_NAME]-2026-V1.0
**Confidentiality Level:** [Restricted / Internal / Public — a public-source project's spec is often itself public]
**Owner:** [Company Name] UG (haftungsbeschränkt)
**Product Class:** Distributed — executed by the user, not operated by us

---

## 1. DOCUMENT CONTROL & GOVERNANCE
*   **1.1 Change Log & Version History:** (Version, Date, Author, Approved By, Description of Changes).
*   **1.2 Document Sign-Off Matrix:** (Approval across Product Owner, Lead Architect, and — where the project ships publicly — whoever owns legal/licensing sign-off).
*   **1.3 Referenced & Applicable Documents:** (Internal standards, external regulatory standards, upstream project policies, dependency licences).
*   **1.4 Glossary of Terms & Acronyms:** (Domain terminology, technical acronyms, and any term the product's own interface uses in a non-obvious sense).

## 2. EXECUTIVE SUMMARY & BUSINESS CONTEXT
*   **2.1 Strategic Product Vision:** (What it is, who runs it, and why it exists as a distributed tool rather than a service).
*   **2.2 Business Model & Sustainability:** (Open-core, dual licence, paid support, sponsorship, or explicitly non-commercial. State it — "free and unfunded" is a real answer that sets maintenance expectations.)
*   **2.3 Stakeholder Analysis & RACI Matrix:** (Maintainers, external contributors, downstream users, packagers/distributors, and any integrator embedding the tool).
*   **2.4 Project Constraints & Dependencies:** (Deadlines, resource limits, upstream projects depended on, and parallel work this must align with).
*   **2.5 Adoption & Success Criteria:** (What "working" looks like — install success rate, issue volume, whether the project reaches self-hosting/self-development, etc.)

## 3. PRODUCT ARCHITECTURE & RUNTIME TOPOLOGY
*   **3.1 Execution Model & Process Topology:**
    *   3.1.1 Where it runs (interactive shell, CI runner, container, editor extension, background daemon) and the process lifetime of each.
    *   3.1.2 Privilege model (what it requires, what it must never require — filesystem scope, network, credentials).
    *   3.1.3 Concurrency model (sync, asyncio, threads, subprocess fan-out) and its consequences for the interface.
*   **3.2 Supported Platform & Toolchain Matrix:**
    *   3.2.1 Operating systems and CPU architectures, with tiers (fully supported / best-effort / unsupported).
    *   3.2.2 Runtime versions (language runtime minimum and maximum).
    *   3.2.3 **External tool minimum versions, with the specific feature each minimum is required for.** Every external binary the product shells out to gets a declared floor and a feature-detection or refusal strategy — an undeclared assumption about an external tool's version is a defect that only appears on someone else's machine.
    *   3.2.4 How the matrix is *tested*, not merely declared.
*   **3.3 Application Architecture Framework:**
    *   3.3.1 Architectural patterns (layering, ports/adapters, domain model, plugin boundaries).
    *   3.3.2 Single-engine rule: which behaviours must have exactly one implementation, and what enforces that.
*   **3.4 Technology Stack Whitelist:** (Permitted languages, runtimes, UI frameworks, and libraries — with the reason for each and the compiled-dependency policy, since a compiled dependency turns "pip install works" into "sometimes needs a toolchain").
*   **3.5 Local State & On-Disk Layout:**
    *   3.5.1 What the product writes, where (config, cache, data), and per-platform path conventions.
    *   3.5.2 File formats, their versioning, and whether they are human-readable and diffable.
    *   3.5.3 Ownership: the user's data stays the user's — readable and usable without this tool installed.
*   **3.6 Failure Modes & Graceful Degradation:**
    *   3.6.1 Offline behaviour (the tool must work with no network unless a feature inherently needs one).
    *   3.6.2 Missing optional dependencies — degrade with a named, actionable message rather than a traceback.
    *   3.6.3 Partial failure and recovery (interrupted writes, half-completed multi-step operations, resumability).
    *   3.6.4 Refusal as a first-class outcome: which conditions the product declines rather than guesses at, and how those refusals stay legible.

## 4. DOMAIN-DRIVEN FUNCTIONAL SPECIFICATIONS
*(Duplicate Chapter 4 for every core domain/sub-system the product actually has)*

*   **4.X DOMAIN NAME**
    *   **4.X.1 Functional Domain Overview:** (Context, purpose, and scope of this domain).
    *   **4.X.2 User Persona Maps & Interaction Journeys:** (Including the non-human personas — CI pipelines, agents, and integrating code, which have different needs from a person at a terminal).
    *   **4.X.3 Functional Requirement Matrix (FR):**

        | Req ID | Requirement Description | Priority (MoSCoW) | Acceptance Criteria |
        | :--- | :--- | :--- | :--- |
        | FR-DOM1-001 | The system must... | Must Have | Given/When/Then scenarios |
    *   **4.X.4 Complex Business Rules & State Machine Logic:** (Validation rules, state transition matrices, and which transitions are refused rather than merely discouraged).
    *   **4.X.5 Interface Surface Specification:** (Command/API surface for this domain: arguments, flags, output shapes, exit codes, and interactive vs non-interactive behaviour. For graphical products, screen structure and routing.)

## 5. INTERFACE CONTRACTS & INTEGRATION
*   **5.1 Public Interface Surface & Stability Contract:**
    *   5.1.1 What is public API (commands, flags, output formats, exit codes, file formats, plugin interfaces) and what is explicitly internal.
    *   5.1.2 Versioning scheme and what constitutes a breaking change *for each* of those surfaces.
    *   5.1.3 Deprecation policy: notice period, warning mechanism, and removal criteria.
*   **5.2 Automation & Non-Interactive Contract:**
    *   5.2.1 Every operation reachable without a prompt — no input may be obtainable *only* interactively.
    *   5.2.2 Machine-readable output for every command that reports anything, produced from the same values as the human rendering.
    *   5.2.3 Exit-code taxonomy, distinguishing success, a deliberate refusal, a user error, and an internal fault.
    *   5.2.4 Errors and refusals parseable as data, not merely legible as prose.
    *   5.2.5 Determinism: no interactive fallback, no TTY assumption, no unbounded wait when running unattended.
*   **5.3 Outbound Network Calls:**
    *   5.3.1 An exhaustive enumeration of every call the product makes, or an explicit "none". This is the section a privacy-conscious user reads first.
    *   5.3.2 Which are opt-in, which can be disabled, and how.
    *   5.3.3 Update checks and their privacy properties.
*   **5.4 Extension Points:** (Plugins, hooks, config files, environment variables — and the stability contract each carries).
*   **5.5 Third-Party Interoperability:** (External services or tools integrated with, and the degradation path when each is absent, unauthenticated or unreachable.)

## 6. COMPLIANCE, SECURITY & GOVERNANCE
*(Full section. A distributed product carries the same legal bounds as a hosted one — the obligations land in different places, they do not disappear.)*
*   **6.1 Data Privacy & GDPR:**
    *   6.1.1 **Data that leaves the user's machine** — enumerated, with lawful basis for each. The default position is none.
    *   6.1.2 Personal data the product handles *locally* (git identities, credentials, file contents) and why local processing does not make us a controller of it.
    *   6.1.3 Hosted components we *do* operate (documentation site, download host, package registry, telemetry sink, issue tracker) — data residency and lawful basis for each.
    *   6.1.4 Data subject rights for those hosted components (Art. 15 access, Art. 17 erasure) and the route to exercise them.
    *   6.1.5 Privacy by design in local state (what is written to disk, what is never written — credentials, tokens, content).
*   **6.2 Financial & Records Compliance (GoBD):** (Applicability check. Where the product touches records with retention obligations, the immutability and audit-trail design; where it does not, state that it was checked and ruled out.)
*   **6.3 Publication Obligations:** (Impressumspflicht §5 DDG and privacy policy for the project's public web presence — docs site, landing page, download page. Attaches to the website, not the binary, but it attaches.)
*   **6.4 Information Security Framework (ISO 27001 / SOC 2 Preparation):**
    *   6.4.1 **Supply-chain integrity:** dependency policy and licence allow-list, pinning strategy, SBOM generation, provenance attestation, and the review path for adding a dependency.
    *   6.4.2 **Release integrity:** artefact signing, checksum publication, reproducible builds where achievable, and the **trust model of the installation path** — an install one-liner that pipes to a shell is a real decision with a real threat model, and must be stated and justified rather than adopted by convention.
    *   6.4.3 Vulnerability disclosure: security contact, embargo policy, advisory publication, and patch-release commitments.
    *   6.4.4 Cryptographic standard matrix (TLS for every download and API call; signature algorithms for releases).
    *   6.4.5 **Least privilege on the user's machine:** what the product reads, writes and executes; what it will never do (arbitrary code from config, network egress by default, credential storage in plaintext).
    *   6.4.6 Handling of untrusted input — repository content, config files, and command output are all attacker-influenceable in the general case.
*   **6.5 Licensing & Intellectual Property:**
    *   6.5.1 Product licence, and the position on contributor agreements for external contributions (a CLA, a sign-off line, or none).
    *   6.5.2 Dependency licence compliance and the attribution/NOTICE obligations that follow.
    *   6.5.3 Trademark and naming position.
*   **6.6 EU AI Act Applicability:** (Applies where the product embeds, calls, or ships models. State the check and its outcome either way.)

## 7. RELEASE ENGINEERING, DISTRIBUTION & SUPPORT
*   **7.1 Automated CI/CD Lifecycle:** (Gates, static analysis, coverage thresholds, and **execution across the §3.2 platform matrix** — a matrix that is declared but only ever tested on the maintainer's machine is a documented assumption, not a supported platform.)
*   **7.2 Distribution Channels & Installation:**
    *   7.2.1 Channels (language package registry, OS package managers, container image, standalone binary, install script) and which is canonical.
    *   7.2.2 Installation path for each, including the runtime bootstrap problem where the product's language is not guaranteed present.
    *   7.2.3 Upgrade path, and how a user learns an upgrade exists.
    *   7.2.4 Uninstall path, and what it leaves behind.
*   **7.3 Versioning, Changelog & Compatibility:** (Scheme, release cadence, changelog discipline, and the forward/backward compatibility window for on-disk formats.)
*   **7.4 Observability of Software You Do Not Operate:**
    *   7.4.1 Diagnostics the user can produce and send (a `doctor`-style self-check, a redacted diagnostic bundle).
    *   7.4.2 Crash and error reporting stance — opt-in, opt-out, or absent, and what it would contain.
    *   7.4.3 Logging: destination, verbosity control, and the rule that secrets never reach a log.
*   **7.5 Support Boundaries & End-of-Life Policy:** (What is supported, by whom, on what timescale; which versions receive security fixes; how EOL is announced.)
*   **7.6 Community & Contribution Governance:** (Contribution process, issue triage, review requirements, code of conduct, maintainer succession, and — where an AI agent performs triage or review — an explicit `human_gates` boundary per `workflows/repo-workflow/templates/maintainer-policy-template.md`.)

## 8. MIGRATION, COMPATIBILITY & OUT OF SCOPE
*   **8.1 Data & Format Migration Strategy:** (How on-disk formats evolve, whether migrations are automatic or explicit, and whether an older version can still read newer data.)
*   **8.2 The User's Exit Path:** (Export, uninstall, and whether the data remains usable without the product. A distributed product's decommissioning plan is the user's, not ours — which makes format openness a compliance property, not just a nicety.)
*   **8.3 Definitive Out-of-Scope Registry:** (Explicit boundary setting, to defend against scope creep during development.)

---
## APPENDIX: TECHNICAL BLUEPRINTS
*   **Appendix A:** Conceptual Data Model & Entity-Relationship Diagrams (ERD).
*   **Appendix B:** Interface Contract Catalog (full command/API reference, exit codes, output schemas).
*   **Appendix C:** Regulatory Compliance Verification Checklist.
*   **Appendix D:** Supported Platform & Toolchain Matrix (the tested detail behind §3.2).
```
