---
title: "Every automated run has a measured budget: time, bytes written and disk growth, multiplied by its parallelism"
type: "rule"
category: "philosophy"
---

**Why:** one project hit the same two failures again and again within three days (2026-11-03 to 2026-11-06), and each patch held for a day.
- **Disk:** a build machine's WSL disk file filled its whole drive three times. Every agent died, and WSL stopped. The fixes were cache caps (`bound-regenerable-output`), a launch guard and a worktree prune. Each fix bounded what was *kept*. None bounded what each run *writes*.
- **Time:** a branch check ran about 4,500 tests in 15 to 25 minutes. Two issues made it "fast" (shared fixtures, a build cache, a fast/full split, symbol-aware selection, parallel workers). A census then showed what one check still did:
  - It ran **96 full builds**, about half its time.
  - The selection still reached a median 60 of 83 build-test modules per branch.
  - The work hadn't shrunk. It had only been spread over workers.

Both failures have one root: **nobody measured what one run costs, so nothing kept it small, and parallel agents multiplied it.** Five agents each running a check with 96 builds of a 128 MB image write hundreds of GB per hour. A VM disk file grows with every new block written. It doesn't shrink when files are deleted inside the guest (WSL 2.7 disables sparse VHDs as unsafe). So the guest's free space says nothing about the host. On 2026-11-06 a launch guard was relaxed mid-session to count the guest's slack, and the drive filled two hours later.

The same cost is billable minutes and storage on any CI, so this is not a local-machine problem.

## The rule

1. **Measure the run before optimising it.** Every check, build or test pipeline reports, per run:
   - the wall time;
   - the work count (builds, downloads, containers);
   - the bytes written, and the cache growth.

   The report comes from the tooling itself, not from a one-off investigation. An unmeasured run has no budget, and an unbudgeted run grows.
2. **Set a budget for each run kind, and enforce it in the tool.**
   - **The branch gate is small:** minutes, and at most one expensive build. Full verification runs **once per integration**, on the main branch or a batch of merges, not once per branch (`separate-verification-from-deployment`).
   - Going over budget fails loudly in the tool's own output, the way a size cap evicts (`bound-regenerable-output`). A reviewer's memory doesn't count.
3. **Multiply by parallelism before you launch.** Run cost × parallel runs × runs per hour is the real load. Check it against the host's real capacity before raising parallelism.
4. **Guards measure the real resource, on the outermost layer.**
   - Disk: the host drive's free space, not the guest's, a container's or a VM's.
   - Time: the wall clock of the gate as people wait for it, not the CPU time.
   - A guard counts only what is physically free.
5. **A guard is not relaxed during a session.** If a safety guard blocks work, the work waits, or the owner decides. Changing what a guard counts or its threshold is a decision for the owner, recorded with its reason, never an agent's workaround.
6. **The second recurrence stops patching.** When the same resource failure comes back after a fix, the next step is this rule's measurement, not another cap (`debugging-escalation-after-repeated-failures`).

## How to apply

- **New pipeline:** write its run report (time, work count, bytes) in the same change as the pipeline, with a budget per run kind.
- **Existing slow or heavy pipeline:** take a census first (what runs, how often, what it writes). Then cut the repeated work: build once and share it, and run the full suite once per integration. Never add workers before the census.
- **Before parallel agents or CI fan-out:** cost × parallelism against the host's free resources. The launch guard checks the outermost layer.
- **VM, WSL, Docker Desktop and CI runner disks:** treat them as growing only. Compaction is a deliberate maintenance step with the guest stopped, scheduled, not an emergency fix. Keep heavy scratch writes (temporary build trees) in a bounded RAM disk or a fixed-size scratch volume, not in the growing disk.
