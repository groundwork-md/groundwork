# Security policy

## Which versions get fixes

There are no releases yet. Only the latest commit on the default branch is fixed.

## What counts as a vulnerability

The content here is markdown, so the realistic risks are in the mechanism and in what a note can
leak:

- `bin/gwk.py`, `bin/commit-msg` and the recipes in `groundwork.just`: for example a way to make them run
  a command, write a file outside the directories they are meant to touch, or follow a symlink
  somewhere unexpected (`just link` writes into `~/.claude/`).
- A secret, credential, personal data or private identifier that has been committed to this
  repository.
- Guidance in a note that would lead a reader or an agent to do something unsafe (for example, to
  put a secret on a command line).

## How to report a vulnerability

Report it privately through GitHub's private vulnerability reporting:

**https://github.com/groundwork-md/groundwork/security/advisories/new**

(or the "Report a vulnerability" button on the repository's Security tab).

Please do not describe a suspected vulnerability in a public issue, pull request, discussion or
social-media post until a fix is available and a disclosure date has been agreed.

A report is easiest to act on when it says:

- which file, script or recipe is affected;
- what an attacker could do with it and who would be harmed;
- the steps to reproduce it, or a minimal proof of concept;
- any preconditions the attack needs;
- a fix or mitigation, if you have one in mind.

Please leave secrets, credentials and other people's personal data out of the report.

## What happens next

groundwork is maintained in spare time, so there is no fixed response time. We read every report,
acknowledge it as soon as we can, confirm whether it is a vulnerability, work out its scope, prepare
a fix and agree a disclosure date with you. Reporters are
credited in the fix unless they prefer not to be.

## Testing in good faith

Research that stays within the following limits will not be treated as hostile: use only systems,
accounts and data you own, do not read, change or delete anyone else's data, and do not degrade a
service for other people. If a test could affect other people or systems, stop and send a private
report first.
