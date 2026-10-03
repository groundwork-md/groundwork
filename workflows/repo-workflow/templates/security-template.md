---
title: "SECURITY.md template"
type: "reference"
category: "repo-workflow"
---

A starting point for a project's vulnerability-disclosure policy. It covers who gets fixes, how to report privately, what a reporter can expect, and what counts as acceptable testing.

**How to apply:** copy the block below into `SECURITY.md`, fill in the project name and the real reporting route, and delete the alternative that does not apply. The route depends on the host: a host with built-in private vulnerability reporting can use that; a project without it needs a monitored security contact address, which belongs to whoever operates the project and is never invented here.

---

```markdown
# Security policy

## Which versions get fixes

<Only the latest commit on the default branch is fixed.>
<Or: the latest minor release of each major version listed in the table below is fixed.>

## How to report a vulnerability

Report it privately, using one of these routes:

- <the host's private vulnerability reporting feature, with its link>
- <or: an email to the project's security contact, <security contact>>

Please do not describe a suspected vulnerability in a public issue, pull request, discussion or
social-media post until a fix is available and a disclosure date has been agreed.

A report is easiest to act on when it says:

- which file, script, endpoint or workflow is affected;
- what an attacker could do with it and who would be harmed;
- the steps to reproduce it, or a minimal proof of concept;
- any preconditions the attack needs;
- a fix or mitigation, if you have one in mind.

Please leave secrets, credentials and other people's personal data out of the report.

## What happens next

We aim to acknowledge a report within <number> working days, confirm whether it is a
vulnerability, work out its scope, prepare a fix and agree a disclosure date with you. Reporters
are credited in the release notes unless they prefer not to be.

## Testing in good faith

Research that stays within the following limits will not be treated as hostile: use only
accounts and data you own, do not read, change or delete anyone else's data, and do not degrade
the service for other users. If a test could affect other people or systems, stop and send a
private report first.
```
