---
title: "A subagent never has implicit merge authority"
type: "principle"
category: "philosophy"
---

When dispatching a subagent to do real code work, don't tell it to "auto-merge on CI-green" without separately checking whether review-before-merge applies to that work. It does, by default, for anything a subagent produces.

**Why:** your own standing authorization to merge things yourself mid-session (explicit or clearly-implied by an ongoing conversation) does not automatically transfer to a subagent just because it's doing similar-shaped work — a subagent's prompt is the *only* context it has. If the prompt says "merge it," it will, without knowing whether a review policy is actually still in force for that specific delegation.

**Rule:** default every subagent prompt with a PR/merge step to "open the PR and stop — leave it for review," unless you've explicitly granted merge authority *in this specific delegation, for this specific piece of work*. Never infer merge authority for a subagent from your own merging behavior earlier in the same session.
