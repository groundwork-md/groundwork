---
title: "Enterprise software specification sheet — master template"
type: "reference"
category: "session"
---

Used by `workflows/session/start-new-project.md` step 1 for any new project classified as a **real
product/venture** (not internal tooling — see that workflow's own classification step). Drafted
2026-08-28 as the standing structure for the collaborative whitepaper/spec-sheet iteration
that now precedes repo bootstrap for anything at that weight.

**How to apply:** copy the template below verbatim into a new draft file (see
`start-new-project.md` step 1 for the exact filename/location), then iterate on it directly with
the maintainer — section by section, asking rather than assuming, until every section is either filled in
with real project-specific content or explicitly marked out of scope for this project (never left
as an empty placeholder or a silent omission). Section 4 duplicates per functional domain the
project actually has; every other section appears once. Nothing gets treated as "good enough to
start coding" while a section still reads like the template's own generic prompt text.

**Diagrams: use your diagramming skill or tool, if you have one, wherever a section is naturally a
diagram, not prose.** Which one is the default belongs to your own layer. Sections where
a real diagram belongs instead of (or alongside) written text, with the fitting diagram type:

| Section | Diagram type |
|---|---|
| §3.1.2 Containerization Blueprint | deployment diagram |
| §3.1.3 Network Topology | architecture diagram (or IT current-state, if extending an existing system) |
| §3.2.1 Architectural Patterns | architecture / high-level diagram |
| §3.3 Data Layer & Storage Architecture | database schema diagram |
| §3.4.3 Failover & HA Orchestration | state machine or flowchart |
| §4.X.2 User Persona Maps & Interaction Journeys | user journey diagram |
| §4.X.4 State Machine Logic | state machine diagram |
| §5.1–5.3 API / Integration / Event-Driven Architecture | sequence diagram (per key flow) or data flow diagram |
| §6.3.1 IAM / RBAC / ABAC | DP security matrix |
| §7.1 CI/CD Lifecycle | process or swimlane diagram |
| §7.2 Deployment Strategy (Blue-Green/Canary) | deployment diagram |
| Appendix A: Conceptual Data Model / ERD | ER/data model diagram (already named in the template itself) |
| Appendix B: API Interface Contract Catalog | sequence diagram per cataloged flow, alongside the actual contract |

**Not a fit**: §4.X.5 UI/UX Wireframes — diagramming tools cover architecture, data and flow diagrams, not
literal UI mockups or wireframes; that section stays prose or uses an actual design tool. Don't force a
diagram into a section that doesn't need one — a table or three sentences that says everything a
diagram would is still the right call there; the point is matching the tool to what the section
actually needs; per `standards/philosophy/design-aesthetic-clean-simple.md`'s own "the highest-quality
move is usually deletion": a diagram that doesn't earn its
place is clutter, not documentation.

**Deliberate choice, not an oversight**: compliance/infrastructure sections (§3.1, §6) restate the
actual content for *this* project rather than just pointing at groundwork's standing defaults
(your layer's `standards/legal/` regulatory baseline, its `standards/tech/` hosting default,
etc.), an explicit decision, so each spec sheet stands alone (handoff to an external auditor,
investor, or compliance officer without groundwork access). The real cost of that choice: this
creates two copies of the same underlying fact (groundwork's standing default, and this project's
own restated version of it) that can drift apart the way a platform-architecture standard
and seven other files did after a deployment-tool switch (`workflows/groundwork/self-review.md`
found and fixed that drift). Mitigation: `workflows/groundwork/self-review.md`'s own
periodic pass should include checking active spec sheets against current standing defaults, same as
any other file that cites one.

---

```markdown
# ENTERPRISE SOFTWARE SPECIFICATION SHEET (MASTER TEMPLATE)
**Document ID:** SPEC-[PROJECT_NAME]-2026-V1.0
**Confidentiality Level:** Restricted / Internal
**Owner:** [Company Name] UG (haftungsbeschränkt)

---

## 1. DOCUMENT CONTROL & GOVERNANCE
*   **1.1 Change Log & Version History:** (Strict table detailing Version, Date, Author, Approved By, and Description of Changes).
*   **1.2 Document Sign-Off Matrix:** (Formal approval matrix for Executive Sponsors, Product Owners, Lead Architects, and Compliance Officers).
*   **1.3 Referenced & Applicable Documents:** (Links to internal corporate policies, external regulatory standards, and vendor agreements).
*   **1.4 Glossary of Terms & Acronyms:** (Exhaustive definitions of domain-specific terminology, technical acronyms, and business rules).

## 2. EXECUTIVE SUMMARY & BUSINESS CONTEXT
*   **2.1 Strategic Project Vision:** (High-level positioning within the corporate digital transformation roadmap).
*   **2.2 Business Case & ROI Matrix:** (Financial justification, tangible/intangible benefits, and cost-saving projections).
*   **2.3 Stakeholder Analysis & RACI Matrix:** (Responsible, Accountable, Consulted, Informed matrix across all business units and external partners).
*   **2.4 Project Constraints & Dependencies:** (Hard organizational deadlines, budget ceilings, resource limitations, and parallel project alignments).

## 3. CORE ARCHITECTURE & SYSTEM TOPOLOGY
*   **3.1 Target Infrastructure & Hosting Model (Your Hosting Provider's Environment):**
    *   3.1.1 Physical Infrastructure Spec (Dedicated Server setups, CPU/RAM allocations, bare-metal vs. virtualization layers).
    *   3.1.2 Cloud-Agnostic Containerization Blueprint (Docker, k3s, or localized Kubernetes definitions).
    *   3.1.3 Network Topology (Virtual Private Networks (VPNs), firewalls, subnets, DMZ configurations, and private IP addressing spaces).
*   **3.2 Application Architecture Framework:**
    *   3.2.1 Architectural Patterns (Microservices, Event-Driven, Clean Architecture, Domain-Driven Design).
    *   3.2.2 Technology Stack Whitelist (Permitted programming languages, runtimes, UI frameworks, and middleware components).
*   **3.3 Data Layer & Storage Architecture:**
    *   3.3.1 Relational & Non-Relational Database Layouts.
    *   3.3.2 Caching & In-Memory Data Grids (Redis, Memcached setups).
    *   3.3.3 Object Storage Configuration (For unstructured files, assets, and document storage).
*   **3.4 Business Continuity & Disaster Recovery (BCP/DR):**
    *   3.4.1 Recovery Objectives (Highly specific RTO and RPO metrics per sub-system/service tier).
    *   3.4.2 Cross-Region / Off-Site Backup Strategy (3-2-1 backup execution using your hosting provider's FTP/SFTP secure storage nodes with AES-256 server-side encryption).
    *   3.4.3 Failover & High-Availability (HA) Orchestration.

## 4. DOMAIN-DRIVEN FUNCTIONAL SPECIFICATIONS
*(Note: To scale to 100+ pages, duplicate Chapter 4 for every core domain/sub-system of your software)*

*   **4.X DOMAIN NAME (e.g., Domain 01: Core Billing Engine / Domain 02: User Identity)**
    *   **4.X.1 Functional Domain Overview:** (Context, purpose, and business scope of this specific domain).
    *   **4.X.2 User Persona Maps & Interaction Journeys:** (Detailed pathways for different user tiers).
    *   **4.X.3 Functional Requirement Matrix (Functional Requirements - FR):**

        | Req ID | Requirement Description | Priority (MoSCoW) | Acceptance Criteria |
        | :--- | :--- | :--- | :--- |
        | FR-DOM1-001 | The system must... | Must Have | Given/When/Then scenarios |
        | FR-DOM1-002 | The system must... | Should Have | Given/When/Then scenarios |
    *   **4.X.4 Complex Business Rules & State Machine Logic:** (Validation algorithms, mathematical formulas, and strict state transition matrices).
    *   **4.X.5 UI/UX Wireframes & Component Specifications:** (Structural description of frontend elements, input validations, and screen routing).

## 5. ENTERPRISE INTEGRATION ARCHITECTURE (API & EAI)
*   **5.1 Inbound API Specifications:** (RESTful, gRPC, or GraphQL design guidelines, payload formats, and strict rate-limiting policies).
*   **5.2 Outbound & Third-Party API Integrations:** (Specifications for connecting to external payment gateways, CRM systems, email relays, and analytics engines).
*   **5.3 Event-Driven Integration & Message Queues:** (Asynchronous communication layers using message brokers like RabbitMQ or Kafka within your hosting environment).
*   **5.4 Data Batch Processing & ETL Pipelines:** (Schematics for large-scale nightly or scheduled data migrations, validation hooks, and error-handling routines).

## 6. ENTERPRISE COMPLIANCE, SECURITY & GOVERNANCE
*   **6.1 Data Privacy & GDPR Compliance:**
    *   6.1.1 Data Residency Boundaries (Guaranteed physical storage within the data-centre jurisdiction your provider contractually commits to).
    *   6.1.2 Privacy by Design Mechanisms (Pseudonymization, automated anonymization engines, strict data lifecycle management).
    *   6.1.3 Data Subject Rights Enforcement (Automated workflows for Art. 15 Right to Access and Art. 17 Right to Erasure).
*   **6.2 Financial & Tax Auditing Compliance (GoBD):**
    *   6.2.1 Immutability Design (Technical layout preventing retrospective modification of transaction ledgers and financial logs).
    *   6.2.2 Audit Trail Architecture (Comprehensive logging of data states, user associations, and temporal metadata with a mandatory 10-year preservation rule).
*   **6.3 Information Security Framework (ISO 27001 / SOC 2 Preparation):**
    *   6.3.1 Identity & Access Management (IAM) (Role-Based Access Control (RBAC), Attribute-Based Access Control (ABAC), and Multi-Factor Authentication (MFA) mandates).
    *   6.3.2 Infrastructure Hardening Guidelines (SSH key constraints, disabled password logins, automated vulnerability patching routines).
    *   6.3.3 Enterprise Security Logging (Centralized, tamper-resistant system log collection with a 90-day hot retention window).
    *   6.3.4 Cryptographic Standard Matrix (Encryption algorithms enforced for Data-at-Rest (AES-256) and Data-in-Transit (TLS 1.3)).

## 7. SYSTEM OBSERVABILITY, OPERATIONS & DEVOPS
*   **7.1 Automated CI/CD Lifecycle:** (Pipeline requirements, automated static application security testing (SAST), and mandatory test coverage thresholds).
*   **7.2 Deployment Strategy:** (Blue-Green or Canary deployment mechanics to achieve zero-downtime rollouts).
*   **7.3 Monitoring, Telemetry & Alerting:** (Infrastructure metrics, application tracing, error-budget tracking, and PagerDuty/Slack routing rules).
*   **7.4 Operational Service Level Agreements (SLAs):** (Explicit platform uptime guarantees, incident response tiers (L1/L2/L3), and resolution targets).

## 8. MIGRATION, DECOMMISSIONING & OUT OF SCOPE
*   **8.1 Legacy Data Migration Strategy:** (Mapping, extraction, validation, and loading processes for pre-existing records).
*   **8.2 System Decommissioning Plan:** (Procedures for retiring legacy systems or elements safely without data loss).
*   **8.3 Definitive Out-of-Scope Registry:** (Explicit boundary setting to defend the project against scope creep during development phases).

---
## APPENDIX: TECHNICAL BLUEPRINTS
*   **Appendix A:** Conceptual Data Model & Entity-Relationship Diagrams (ERD).
*   **Appendix B:** System Interface Contract Catalog (OpenAPI Specs / Proto Files).
*   **Appendix C:** Regulatory Compliance Verification Checklist.
```
