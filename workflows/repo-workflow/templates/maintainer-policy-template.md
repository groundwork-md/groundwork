---
title: "AI-assisted-maintenance policy template"
type: "reference"
category: "repo-workflow"
---

A machine-readable statement of what an AI agent may and may not do when it triages issues and pull requests on a repo. The part that matters is the list of **decisions reserved for humans**: an explicit, checkable list of calls the agent never makes alone. Its `merge` block is the same rule as `[[subagent-merge-authority-must-be-explicit]]`, written as data a script can check instead of a sentence in an instruction file. The file format below is this project's own design; adapt the keys to whatever tooling reads it.

**How to apply:** use it only on a repo where an agent genuinely does triage or review work; on any other repo it is process with nothing to enforce it. Fill in `checks.commands` with the project's real checks. Keep `reserved_for_humans` close to as written, since it is the load-bearing part, and add to it rather than removing from it.

---

```json
{
  "version": 1,
  "repo": "<owner>/<name>",
  "integration_branch": "<branch>",

  "merge": {
    "method": "merge-commit",
    "authorised_by": "a named human, per pull request, in writing",
    "preconditions": [
      "branch is current with the integration branch",
      "no merge conflicts",
      "every review thread resolved",
      "no outstanding change request",
      "all checks green on the exact head commit being merged"
    ]
  },

  "checks": {
    "commands": [
      "<placeholder: one real test, lint or build command per required check>"
    ],
    "ci_jobs_required": []
  },

  "triage": {
    "read_whole_thread_before_acting": true,
    "look_for_competing_pull_requests": true,
    "reproduce_on_current_integration_branch": true,
    "check_history_for_why_it_is_the_way_it_is": true,
    "pull_requests_opened_by_agent_per_run": 1
  },

  "pull_requests": {
    "handle_version_bumps_one_at_a_time": true,
    "inspect_workflows_from_first_time_forks_before_running": true,
    "ask_to_split_large_or_mixed_changes": true,
    "wait_for_post_merge_jobs_before_the_next_merge": true
  },

  "reserved_for_humans": [
    "what the project prioritises next",
    "accepting a large or mixed-scope change",
    "approving CI workflows from a first-time contributor",
    "closing an issue whose resolution is ambiguous",
    "anything touching a security disclosure",
    "authorising a merge"
  ]
}
```
