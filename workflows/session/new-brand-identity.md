---
title: "New brand identity: positioning, visual system, motion and copy, decided from options before any asset is built"
type: "rule"
category: "session"
---

The design-and-copy part of `start-new-project.md` §1, for any project with a public face: a
website, a product people see, a social presence. It replaces that file's one-line "design
direction" and "copy / positioning" bullets with a real process. It can also run on its own, for a
rebrand of something that already exists. Like §1, it ends with every decision made and recorded;
building the brand assets is the repo backlog that follows, never part of the deciding.

First run: 2026-10, a company rebrand plus a new website, about 30 decisions in one long session.
Everything below the "How to run it" rules was learned there, mostly from rounds that were
rejected.

## How to run it

- **Options, never a single answer.** Every creative decision gets a board with several real
  options (usually 4–10), built from whatever prior art exists, with a recommendation marked. The
  person decides; nothing is assumed or defaulted silently, even where a standing default exists.
  Prior art is a base for new ideas, not a choice to re-run.
- **Show, don't describe.** Boards are rendered pages (an artifact, or HTML), not text lists.
  Check every board visually before showing it: render it headless and look at the result. For
  animation, freeze frames at chosen times (`document.getAnimations().forEach(a => { a.pause();
  a.currentTime = t })`, then screenshot); virtual-time screenshots are unreliable.
- **Two rejections mean the principle is missing, not the execution.** When a round is rejected
  twice, stop producing variants and state the principle the options should satisfy, then get it
  agreed. On the first run the mascot failed three rounds (a pixel creature, a vector cartoon, a
  creature drawn on top of logo shapes) until the principle was named: *the silhouette alone must
  say what it is and that it's cute; draw nothing on top of a shape.* The next round was accepted.
- **Never switch the medium or style the person asked for.** If they ask for "blocky", a polished
  vector version is a rejection, however good it is.
- **Every claim must be true.** Check copy against the market research: "prices agencies can't
  match" was dropped because the price sat at the market median. Sales copy sells the benefit;
  a line that explains a limitation reads as an excuse.
- **Record as you go,** in the project's decision table (below), each decision with its choice
  and a note on why and what was rejected. A decision made in conversation and not written down
  did not happen.
- **Reopening is explicit.** When a later topic surfaces a missing decision (on the first run,
  motion surfaced after step 1 was closed), reopen the step in the record, decide it, and close it
  again.

## Where things live

**Paths are layer-relative.** Every `standards/…` and `vault/…` path in this workflow names a
path inside one groundwork layer, not under `~/.claude/groundwork/` itself, and a standard such as the
naming theme or the regulatory baseline usually lives in an upper layer, not in this one. Resolve a
note by name in `~/.claude/groundwork/INDEX.md` (each line names its layer; the layer handles are
`~/.claude/groundwork/<NN-layer>/`) or with `rg --files $(cat ~/.claude/groundwork/ROOTS) | rg <name>`. When
a note exists in several layers, read every copy; the higher-ranked layer is the more specific.
The project's own notes (decision table, copy, prototypes, market research) go in the layer that
owns the project: a company's project in the company layer.


- **Decision table:** `vault/projects/<slug>/README.md` (for a venture-weight project, the spec's
  design and copy sections reference it). Columns: `#`, decision, choice, note.
- **Copy:** `vault/projects/<slug>/copy/<page>.md`, every language side by side.
- **Prototype sources:** `vault/projects/<slug>/prototypes/`: the generator scripts and board HTML
  behind every accepted decision. Published boards and scratch directories are not durable; copy
  the sources in before the repo backlog points at them.
- **Anything private stays in the vault.** Finances, salaries, tax, internal constraints and
  vendor contract gaps are decision inputs, never content for a public brand or website repo.

## 1. Ground

- Collect the prior art: old logos, prototypes, earlier ADRs, live sites. Note what each one
  chose and why, and what failed in practice.
- Fix the hard constraints: which domains are owned (check before naming a domain anywhere),
  hosting, languages, tracking stance, legal entity, what is public and what is private.
- Decide the repos and licences: typically a public brand repo (tokens, masters, guidelines) and a
  consuming site. **Split the licence:** code (tokens, build scripts) under the layer's default
  code licence; logos, wordmark, mascot and other brand assets all rights reserved.

## 2. Positioning and offer

Settle this **before** site structure and copy. On the first run the page-structure question
could not be answered until customers, offer and pricing existed.

- **Customers and lanes:** who actually buys, in which segments, and through which channel. The
  channel shapes the customer.
- **Offer and pricing:** service lines, fixed or "from" prices, care/retainer terms, hourly rate.
  Do real market research and write the findings to `vault/markets/` so it never happens twice.
  Where income matters, build a financial model (revenue, tax, costs, buffer, recurring-revenue
  milestones) and keep it in the vault.
- **Terms the copy will promise:** ownership of work, cancellation, absence and availability,
  response times (promise none you can't keep), and anything about AI or data handling, checked
  against the tools' actual contracts.
- **Voice:** person (I or we), formality per language, rules (concrete over abstract, no
  unbackable claims, no invented numbers).
- **Headline, eyebrow, subline:** 4+ directions per lane, then one chosen per language.

## 3. Visual system

One board per decision, in this order; each step uses the earlier choices.

1. **Palette.** Several palettes as complete mini-pages. For the chosen one, compute contrast for
   every text/background pair and record which colours are fill-only (a saturated accent often
   fails as text on the light ground). Note what the dark theme needs (usually its own muted
   grey).
2. **Logo.** Many marks in the chosen palette, then refinements of the shortlisted few (mark-only,
   variations, grids). Decide colour use: one colour per use is the robust default. Run a
   trademark self-search on the chosen mark and record the result and the filing plan.
3. **Typography.** Only fonts with clean commercial terms: check the licence file itself (e.g.
   SIL OFL 1.1 **without** a Reserved Font Name, verified in the font's source repo), since an RFN
   or a custom licence restricts subsetting and logo use. Check the glyphs every language needs.
   Two or more rounds of display + text + mono pairings set in real copy.
4. **Mascot or character (optional).** Shapes first, colour later. Apply the silhouette principle
   from the start. Then the colour versions per background (aim for as few as possible: a version
   that works everywhere except the accent colour, plus one for the accent), then every pose,
   animated, mapped to UI states: idle, loading, success, not found, error, crash, empty. Remove
   anything that undercuts the state (a dead mascot needs no water line).
5. **Motion.** Principles in a sentence each, then tokens: durations in milliseconds **and** frames
   at 24/30/60 fps (video tools think in frames), named easing curves, transitions (a wipe in the
   brand's shape), text animation, how the mascot and logo enter. Cover UI and video (16:9 and
   9:16 from one timeline) in the same system. A **logo sting**: around ten ideas, then one or a
   hybrid, then its variant on every background, including the accent colour. Then a **colour rule
   for the whole brand**: on the accent background, which colour takes the accent role. Reduced
   motion always shows a still key frame.

## 4. Copy

- Write every page in full, in every language, from the decisions above: no lorem ipsum, no
  placeholders. SEO title and description per page.
- Microcopy for every state the mascot covers (404, error, crash, sent, empty, loading), short and
  kind, never joking about a real problem.
- Legal-language traps per jurisdiction: in German, "barrierearm" or "auf Barrierefreiheit
  ausgelegt", never "barrierefrei gebaut", which reads as a conformance promise.
- An optional **vocabulary theme** tied to the brand (on the first run: words that read as both
  tech and water, for a fish mascot): sparing, at most one per section, only where the plain
  meaning is already right, with an explicit use list and an avoid list (idioms that mean
  struggling, anything in error states).

## 5. Record and hand off

- Close the decision table: every row has a choice and a note. Link every board. Copy the
  prototype sources into the vault.
- Then `start-new-project.md` §2 and §3 as usual. The brand repo's backlog typically runs:
  licence split and conventions → design tokens in the W3C DTCG format → a token build (e.g.
  Style Dictionary) with committed outputs and a freshness check → an automated contrast check over
  declared role pairs in both themes → logo masters (wordmark converted to outlines) → favicon set
  → sting exports → mascot masters and animations → guidelines → a release the site pins. The site
  vendors a pinned brand release; it never reads the brand repo's working tree.
- Every backlog item carries the decided values (hex codes, timings, prices, copy file and section),
  never "see the board".
