---
title: "Don't fight native agent tooling — build with files, folders and grep"
type: "rule"
category: "philosophy"
---

An agent already has excellent tools for one specific shape of problem: **finding things in a
filesystem.** `ls`, `grep`, `find`, reading a path. They are fast, they need no setup, they work in
every session, and they never fall out of sync with the thing they describe, because they read it
directly.

Anything built to replace them starts behind and stays behind. A custom index has to be maintained.
A database has to be queried through a layer that must be loaded first. A bespoke format has to be
parsed. Each is a new thing that can be stale, and staleness in a lookup layer is worse than absence,
because the wrong answer is indistinguishable from the right one.

**So structure information the way the filesystem already works, and let the native tools do the
work.** Directories carry hierarchy. Filenames carry identity. Frontmatter carries attributes.
Markdown carries content. `grep` is the query engine.

**Why:** every durable thing here is built this way and it keeps paying off. Groundwork is folders
of markdown with YAML frontmatter, so "is there a standard about X" is one `grep`. A tracker that
keeps its issues as plain files on a branch is the same idea: a clone carries the tracker with it and `git log` is the audit
trail. The chunked spec format is directories of small files. None of these needed a tool to be
readable, and all of them survive the tool being unavailable.

The same reasoning arrived independently in `RinDig/icm-architect`, which states it as *numbered
folders carry sequencing, hierarchy carries context scoping, plain markdown files carry state* —
see the research on folder structure as an agent-readable map.

**How to apply:**

1. **Reach for a directory before a registry.** If the answer is "which things of kind X exist", the
   answer should be `ls`.
2. **Make filenames answer questions.** A descriptive filename is a free index entry that cannot go
   stale. `Postgres Init Scripts Never Rerun Against a Live Data Dir.md` needs no summary.
3. **Put attributes in frontmatter**, so a filter is a `grep` rather than a parse.
4. **When an index is genuinely needed, generate it** from the files themselves and gate it on a
   staleness check — never hand-maintain it. See your layer's `standards/tech/` on generated directory maps.
5. **Prefer one fact per file.** Files are the unit an agent loads, so a file holding two facts
   forces loading both.
6. **Do not invent a query language.** If the lookup is hard enough to need one, the layout is wrong.

**Where this does not apply:** genuinely relational questions across large data — "every item
blocked by something in this milestone, ordered by rank" — are what a real index is for. Build one
then, derive it from the files, and keep the files authoritative so it can be dropped and rebuilt.
That is the *files are truth, the index is a derived cache* rule.
