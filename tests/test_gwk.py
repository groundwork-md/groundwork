"""Tests for the mechanism in `bin/gwk.py` and the `bin/commit-msg` hook. Stdlib only.

Run with `just gwk-test`. Every test that touches the filesystem works in a temporary directory with
its own HOME, so a run never reads or writes the real `~/.claude`.
"""

import os
import subprocess
import sys
import tempfile
import tomllib
import unittest
import unittest.mock

BIN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bin")
GWK = os.path.join(BIN, "gwk.py")
HOOK = os.path.join(BIN, "commit-msg")
sys.path.insert(0, BIN)

import gwk  # noqa: E402


def run(args, *, layer=None, home=None, env=None, cwd=None):
    """Run `gwk.py` as a subprocess, the way the recipes do, returning the CompletedProcess."""
    full = dict(os.environ)
    full.pop("GWK_LAYER", None)
    full.pop("GWK_COMMIT_REFERENCE", None)
    if layer:
        full["GWK_LAYER"] = layer
    if home:
        full["HOME"] = home
    full.update(env or {})
    return subprocess.run([sys.executable, GWK, *args], capture_output=True, text=True,
                          env=full, cwd=cwd)


class CommitSubject(unittest.TestCase):
    def test_issue_mode_accepts_a_referenced_subject(self):
        self.assertIsNone(gwk.check_commit_subject("feat(links): add a broken-link check (#42)", "issue"))

    def test_issue_mode_accepts_merge_and_release_types_and_breaking_marker(self):
        for subject in ("merge(recipes): branch recipes into development (#7)",
                        "release(app): 1.0.0 (#9)",
                        "feat(api)!: drop the v1 routes (#12)"):
            self.assertIsNone(gwk.check_commit_subject(subject, "issue"), subject)

    def test_issue_mode_requires_the_reference(self):
        problem = gwk.check_commit_subject("feat(links): add a broken-link check", "issue")
        self.assertIn("issue reference is required", problem)

    def test_issue_mode_rejects_a_reference_that_is_not_hash_number(self):
        for subject in ("fix(x): thing (JG-43)", "fix(x): thing (#)", "fix(x): thing #42",
                        "fix(x): (#42)"):
            self.assertIsNotNone(gwk.check_commit_subject(subject, "issue"), subject)

    def test_scope_is_required_in_both_modes(self):
        for mode in ("issue", "none"):
            problem = gwk.check_commit_subject("feat: add thing (#1)", mode)
            self.assertIn("scope is required", problem)

    def test_unknown_type_shape_is_rejected_in_both_modes(self):
        for mode in ("issue", "none"):
            self.assertIsNotNone(gwk.check_commit_subject("Update stuff", mode))
            self.assertIsNotNone(gwk.check_commit_subject("Feat(x): Capitalised type", mode))

    def test_none_mode_needs_no_reference_but_accepts_one(self):
        self.assertIsNone(gwk.check_commit_subject("docs(workflows): reword a rule", "none"))
        self.assertIsNone(gwk.check_commit_subject("docs(workflows): reword a rule (#3)", "none"))

    def test_empty_subject_is_rejected(self):
        self.assertEqual(gwk.check_commit_subject("   ", "none"), "empty subject")

    def test_every_documented_type_is_accepted_in_both_modes(self):
        documented = ("feat fix docs style refactor perf test build ci chore revert merge release"
                      .split())
        self.assertEqual(list(gwk.COMMIT_TYPES), documented)
        for type_ in documented:
            self.assertIsNone(gwk.check_commit_subject(f"{type_}(x): do a thing (#1)", "issue"), type_)
            self.assertIsNone(gwk.check_commit_subject(f"{type_}(x): do a thing", "none"), type_)

    def test_a_type_outside_the_list_is_rejected_by_name_in_both_modes(self):
        for subject in ("wip(x): do a thing (#1)", "update(x): do a thing (#1)",
                        "Feat(x): do a thing (#1)", "features(x): do a thing (#1)"):
            for mode in ("issue", "none"):
                problem = gwk.check_commit_subject(subject, mode)
                self.assertIsNotNone(problem, subject)
                self.assertIn("unknown type", problem, subject)
                self.assertIn("feat fix docs", problem, subject)

    def test_an_unknown_type_is_reported_before_the_missing_scope(self):
        self.assertIn("unknown type 'wip'", gwk.check_commit_subject("wip: do a thing", "none"))

    def test_a_type_that_is_only_a_prefix_of_a_valid_one_is_rejected(self):
        for subject in ("featx(x): a thing", "fixup(x): a thing", "tests(x): a thing"):
            self.assertIn("unknown type", gwk.check_commit_subject(subject, "none"), subject)


class CommitReferenceConfig(unittest.TestCase):
    def test_environment_overrides_the_layer_file(self):
        old = os.environ.get("GWK_COMMIT_REFERENCE")
        try:
            os.environ["GWK_COMMIT_REFERENCE"] = "none"
            self.assertEqual(gwk.commit_reference(), "none")
            os.environ["GWK_COMMIT_REFERENCE"] = "issue"
            self.assertEqual(gwk.commit_reference(), "issue")
            os.environ["GWK_COMMIT_REFERENCE"] = "tickets"
            with self.assertRaises(SystemExit):
                gwk.commit_reference()
        finally:
            if old is None:
                os.environ.pop("GWK_COMMIT_REFERENCE", None)
            else:
                os.environ["GWK_COMMIT_REFERENCE"] = old

    def test_default_is_issue_when_nothing_is_configured(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "groundwork-layer.toml"), "w") as f:
                f.write('schema = 1\nname = "x"\n')
            done = run(["check-subject", "fix(x): no reference"], layer=tmp)
        self.assertEqual(done.returncode, 1)
        self.assertIn("issue reference is required", done.stderr)

    def test_layer_file_value_is_honoured(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "groundwork-layer.toml"), "w") as f:
                f.write('schema = 1\nname = "x"\ncommit_reference = "none"\n')
            done = run(["check-subject", "fix(x): no reference"], layer=tmp)
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_a_typo_in_the_layer_file_fails_instead_of_disabling_the_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "groundwork-layer.toml"), "w") as f:
                f.write('schema = 1\nname = "x"\ncommit_reference = "nonee"\n')
            done = run(["check-subject", "fix(x): no reference"], layer=tmp)
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("commit_reference must be one of", done.stderr)


class CommitMessage(unittest.TestCase):
    """`just commit` builds its message here, so the reference helper is tested without git."""

    def build(self, message, branch, reference):
        with unittest.mock.patch.dict(os.environ, {"GWK_COMMIT_REFERENCE": reference}):
            return gwk.build_commit_message("feat", "links", message, branch)

    def test_issue_mode_takes_the_reference_from_the_branch_number(self):
        self.assertEqual(self.build("add a check", "feature/42-link-checker", "issue"),
                         "feat(links): add a check (#42)")

    def test_an_explicit_reference_is_kept_and_wins_over_the_branch(self):
        self.assertEqual(self.build("add a check (#7)", "feature/42-link-checker", "issue"),
                         "feat(links): add a check (#7)")

    def test_a_branch_without_a_number_adds_nothing(self):
        for branch in ("main", "development", "feature/link-checker", None):
            self.assertEqual(self.build("add a check", branch, "issue"), "feat(links): add a check")

    def test_none_mode_never_adds_a_reference(self):
        self.assertEqual(self.build("add a check", "feature/42-link-checker", "none"),
                         "feat(links): add a check")

    def test_only_the_first_line_is_the_subject(self):
        self.assertEqual(self.build("add a check\n\nwhy it matters", "bugfix/9-x", "issue"),
                         "feat(links): add a check (#9)\n\nwhy it matters")

    def test_a_rejected_message_stops_before_anything_is_committed(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "groundwork-layer.toml"), "w") as f:
                f.write('schema = 1\nname = "x"\ncommit_reference = "issue"\n')
            subprocess.run(["git", "init", "-q", "-b", "main", tmp], check=True)
            bad = run(["commit-message", "feat", "links", "add a check"], layer=tmp)
            subprocess.run(["git", "-C", tmp, "checkout", "-q", "-b", "feature/5-x"], check=True)
            good = run(["commit-message", "feat", "links", "add a check"], layer=tmp)
        self.assertEqual(bad.returncode, 1)
        self.assertIn("issue reference is required", bad.stderr)
        self.assertEqual(bad.stdout, "")
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertEqual(good.stdout, "feat(links): add a check (#5)")

    def test_a_scope_that_is_not_valid_is_rejected(self):
        done = run(["commit-message", "feat", "Bad Scope", "add a check"], env={"GWK_COMMIT_REFERENCE": "none"})
        self.assertEqual(done.returncode, 1)


class Hook(unittest.TestCase):
    def hook(self, subject, **env):
        with tempfile.TemporaryDirectory() as tmp:
            msg = os.path.join(tmp, "MSG")
            with open(msg, "w") as f:
                f.write(subject + "\n\nbody\n")
            full = dict(os.environ, **env)
            full.pop("GWK_LAYER", None)
            return subprocess.run([sys.executable, HOOK, msg], capture_output=True, text=True,
                                  env=full, cwd=tmp)

    def test_accepts_the_issue_form(self):
        done = self.hook("feat(links): add a check (#42)", GWK_COMMIT_REFERENCE="issue")
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_rejects_a_missing_reference_and_says_how_to_fix_it(self):
        done = self.hook("feat(links): add a check", GWK_COMMIT_REFERENCE="issue")
        self.assertEqual(done.returncode, 1)
        self.assertIn("(#N)", done.stderr)

    def test_none_mode_accepts_a_plain_subject(self):
        done = self.hook("feat(links): add a check", GWK_COMMIT_REFERENCE="none")
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_rejects_a_scope_less_subject(self):
        done = self.hook("feat: add a check (#42)", GWK_COMMIT_REFERENCE="issue")
        self.assertEqual(done.returncode, 1)
        self.assertIn("scope is required", done.stderr)

    def test_rejects_an_unknown_type_and_lists_the_valid_ones(self):
        for mode in ("issue", "none"):
            done = self.hook("wip(links): add a check (#42)", GWK_COMMIT_REFERENCE=mode)
            self.assertEqual(done.returncode, 1, mode)
            self.assertIn("unknown type 'wip'", done.stderr)
            self.assertIn("refactor perf test build ci chore revert merge release", done.stderr)

    def test_accepts_every_documented_type(self):
        for type_ in gwk.COMMIT_TYPES:
            done = self.hook(f"{type_}(links): add a check", GWK_COMMIT_REFERENCE="none")
            self.assertEqual(done.returncode, 0, f"{type_}: {done.stderr}")

    def test_comment_lines_pass_through(self):
        self.assertEqual(self.hook("# Please enter the commit message").returncode, 0)


class CheckLog(unittest.TestCase):
    def repo(self, tmp):
        subprocess.run(["git", "init", "-q", "-b", "main", tmp], check=True)
        with open(os.path.join(tmp, "groundwork-layer.toml"), "w") as f:
            f.write('schema = 1\nname = "x"\ncommit_reference = "none"\n')

    def test_a_repo_with_no_commits_is_not_a_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.repo(tmp)
            done = run(["check-log"], layer=tmp)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("no commits yet", done.stdout)
        self.assertNotIn("Traceback", done.stderr)

    def test_a_directory_that_is_not_a_repo_is_a_clear_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "groundwork-layer.toml"), "w") as f:
                f.write('schema = 1\nname = "x"\n')
            done = run(["check-log"], layer=tmp)
        self.assertEqual(done.returncode, 1)
        self.assertIn("not a git repository", done.stdout)
        self.assertNotIn("Traceback", done.stderr)

    def test_counts_conforming_violating_and_grandfathered_commits(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.repo(tmp)
            ident = ["-c", "user.name=t", "-c", "user.email=t@example.invalid"]
            shas = []
            for subject in ("feat(x): fine", "bad subject", "also bad"):
                subprocess.run(["git", "-C", tmp, *ident, "commit", "-q", "--allow-empty", "-m", subject],
                               check=True)
                shas.append(subprocess.run(["git", "-C", tmp, "rev-parse", "HEAD"],
                                           capture_output=True, text=True).stdout.strip())
            done = run(["check-log"], layer=tmp)
            self.assertEqual(done.returncode, 1)
            self.assertIn("conforming:    1", done.stdout)
            self.assertIn("violations:    2", done.stdout)

            os.makedirs(os.path.join(tmp, ".groundwork"))
            with open(os.path.join(tmp, ".groundwork", "commit-baseline.txt"), "w") as f:
                f.write(f"{shas[1]} predates the rule\n{shas[2]} predates the rule\n")
            done = run(["check-log"], layer=tmp)
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("grandfathered: 2", done.stdout)


class Imports(unittest.TestCase):
    def layer(self, tmp, name, imports):
        os.makedirs(os.path.join(tmp, "claude", "commands"))
        os.makedirs(os.path.join(tmp, "workflows"))
        with open(os.path.join(tmp, "groundwork-layer.toml"), "w") as f:
            f.write(f'schema = 1\nname = "{name}"\nnote_dirs = ["workflows"]\n')
        with open(os.path.join(tmp, "workflows", "w.md"), "w") as f:
            f.write("x\n")
        with open(os.path.join(tmp, "claude", "commands", "c.md"), "w") as f:
            f.write("\n".join(imports) + "\n")

    def test_a_handle_import_resolves_against_the_stack_without_an_assembled_home(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as home:
            self.layer(tmp, "base", ["@~/.claude/groundwork/00-base/workflows/w.md"])
            done = run(["imports"], layer=tmp, home=home)
        self.assertEqual(done.returncode, 0, done.stdout)

    def test_a_missing_file_behind_a_valid_handle_fails(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as home:
            self.layer(tmp, "base", ["@~/.claude/groundwork/00-base/workflows/gone.md"])
            done = run(["imports"], layer=tmp, home=home)
        self.assertEqual(done.returncode, 1)
        self.assertIn("resolves to nothing", done.stdout)

    def test_a_base_layer_with_the_wrong_name_gets_an_explanation(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as home:
            self.layer(tmp, "mine", ["@~/.claude/groundwork/00-base/workflows/w.md"])
            done = run(["imports"], layer=tmp, home=home)
        self.assertEqual(done.returncode, 1)
        self.assertIn('name = "base", rank = 0', done.stdout)

    def test_a_hardcoded_home_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as home:
            self.layer(tmp, "base", ["@/Users/someone/notes/w.md"])
            done = run(["imports"], layer=tmp, home=home)
        self.assertEqual(done.returncode, 1)
        self.assertIn("hardcodes a home directory", done.stdout)


class NewLayer(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = os.path.join(self.tmp.name, "home")
        os.makedirs(self.home)
        self.layer = os.path.join(self.tmp.name, "my-layer")

    def tearDown(self):
        self.tmp.cleanup()

    def gwk(self, *args, layer=None):
        return run(list(args), layer=layer or self.layer, home=self.home)

    def test_creates_a_layer_that_passes_every_check_and_links(self):
        made = run(["new-layer", self.layer], home=self.home)
        self.assertEqual(made.returncode, 0, made.stdout + made.stderr)
        for args in (["map"], ["map", "--check"], ["frontmatter"], ["links"], ["paths"],
                     ["imports"], ["entry"], ["direction"], ["check-log"], ["link"], ["symlinks"]):
            done = self.gwk(*args)
            self.assertEqual(done.returncode, 0, f"{args}: {done.stdout}{done.stderr}")
        handles = sorted(os.listdir(os.path.join(self.home, ".claude", "groundwork")))
        self.assertEqual(handles, ["00-base", "10-my-layer", "INDEX.md", "ROOTS"])

    def test_writes_the_identity_files_only_when_both_halves_are_given(self):
        made = run(["new-layer", self.layer, "--author-name", "Alice Example",
                    "--author-email", "alice@example.invalid"], home=self.home)
        self.assertEqual(made.returncode, 0, made.stdout + made.stderr)
        with open(os.path.join(self.layer, ".groundwork", "author-name")) as f:
            self.assertEqual(f.read(), "Alice Example\n")
        with open(os.path.join(self.layer, ".groundwork", "author-email")) as f:
            self.assertEqual(f.read(), "alice@example.invalid\n")
        ignored = subprocess.run(["git", "-C", self.layer, "check-ignore", ".groundwork/author-email"],
                                 capture_output=True, text=True)
        self.assertEqual(ignored.returncode, 0, "the identity files must be git-ignored")

    def test_identity_comes_from_the_environment_too_and_is_absent_otherwise(self):
        made = run(["new-layer", self.layer], home=self.home,
                   env={"GWK_AUTHOR_NAME": "Alice Example", "GWK_AUTHOR_EMAIL": "alice@example.invalid"})
        self.assertEqual(made.returncode, 0, made.stdout + made.stderr)
        self.assertTrue(os.path.isfile(os.path.join(self.layer, ".groundwork", "author-name")))
        other = os.path.join(self.tmp.name, "other")
        made = run(["new-layer", other], home=self.home)
        self.assertEqual(made.returncode, 0, made.stdout + made.stderr)
        self.assertFalse(os.path.exists(os.path.join(other, ".groundwork", "author-name")))
        self.assertIn("GWK_AUTHOR_NAME", made.stdout)

    def test_half_an_identity_is_refused_before_anything_is_written(self):
        done = run(["new-layer", self.layer, "--author-name", "Alice Example"], home=self.home)
        self.assertEqual(done.returncode, 1)
        self.assertFalse(os.path.exists(self.layer))

    def test_refuses_a_non_empty_target_and_the_base_name(self):
        os.makedirs(self.layer)
        with open(os.path.join(self.layer, "keep.txt"), "w") as f:
            f.write("mine\n")
        self.assertEqual(run(["new-layer", self.layer], home=self.home).returncode, 1)
        other = os.path.join(self.tmp.name, "other")
        done = run(["new-layer", other, "--name", "base"], home=self.home)
        self.assertEqual(done.returncode, 1)
        self.assertFalse(os.path.exists(other))

    def test_refuses_a_target_inside_the_base_clone(self):
        done = run(["new-layer", os.path.join(os.path.dirname(BIN), "nested-layer")], home=self.home)
        self.assertEqual(done.returncode, 1)
        self.assertFalse(os.path.exists(os.path.join(os.path.dirname(BIN), "nested-layer")))

    def test_rejects_an_invalid_layer_name(self):
        done = run(["new-layer", self.layer, "--name", "Not Valid"], home=self.home)
        self.assertEqual(done.returncode, 1)

    def test_link_on_a_stack_without_the_base_handle_fails_with_a_reason(self):
        self.assertEqual(run(["new-layer", self.layer], home=self.home).returncode, 0)
        manifest = os.path.join(self.layer, "groundwork.toml")
        with open(manifest) as f:
            text = f.read()
        with open(manifest, "w") as f:
            f.write(text.replace('name = "base"', 'name = "foundation"'))
        done = self.gwk("link")
        self.assertEqual(done.returncode, 1)
        self.assertIn("00-base", done.stdout)

    def test_link_in_the_base_itself_says_how_to_create_a_top_layer(self):
        done = run(["link"], layer=os.path.dirname(BIN), home=self.home)
        self.assertEqual(done.returncode, 1)
        self.assertIn("just new-layer", done.stdout)
        self.assertFalse(os.path.exists(os.path.join(self.home, ".claude", "groundwork", "00-base")))


class MapDeclaredDirectory(unittest.TestCase):
    def test_a_declared_but_missing_directory_is_a_clear_failure_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "groundwork-layer.toml"), "w") as f:
                f.write('schema = 1\nname = "x"\nnote_dirs = ["notes"]\n'
                        '[map.notes]\nheading = "Notes"\npurpose = "p"\n')
            done = run(["map"], layer=tmp)
        self.assertEqual(done.returncode, 1)
        self.assertIn("directory does not exist", done.stdout)
        self.assertNotIn("Traceback", done.stderr)


# ----------------------------------------------------------------------- migrate-from-heimathafen

GIT_IDENT = ["-c", "user.name=t", "-c", "user.email=t@example.invalid"]


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=True).stdout


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def read_file(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def snapshot(root):
    """Every path under `root` (skipping .git) with its content or symlink target."""
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for name in dirnames + filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            if os.path.islink(full):
                out[rel] = ("link", os.readlink(full))
            elif os.path.isfile(full):
                with open(full, "rb") as f:
                    out[rel] = ("file", f.read())
            else:
                out[rel] = ("dir", None)
    return out


LEGACY_PREAMBLE = (
    "<!-- GENERATED by `hafen map` from each note's frontmatter — never hand-edit.\n"
    "     `hafen doctor` fails when this file no longer matches the tree.\n"
    "     To change an entry, change that note's `title:`. To add one, add the note. -->")

LEGACY_LAYER_TOML = """# What this layer is, for the shared mechanism in `bin/hh.py`.
schema = 1
name = "mine"
note_dirs = ["standards"]
entry_file = "claude/CLAUDE.md"
entry_max_words = 400
assembled = true

# the standards directory
[map.standards]
heading = "Standards"
purpose = "What to reach for."
"""


def make_old_base(tmp, name="old-base"):
    """A stand-in for the old base: a layer that ships hafen.just and bin/hh.py."""
    base = os.path.join(tmp, name)
    write(os.path.join(base, "hafen-layer.toml"), 'schema = 1\nname = "base"\nassembled = false\n')
    write(os.path.join(base, "hafen.just"), "# old recipes\n")
    write(os.path.join(base, "bin", "hh.py"), "# old script\n")
    return base


def make_legacy_layer(tmp, old_base, name="layer"):
    """A committed, clean layer written the way the old mechanism wrote them."""
    root = os.path.join(tmp, name)
    write(os.path.join(root, "hafen-layer.toml"), LEGACY_LAYER_TOML)
    write(os.path.join(root, "hafen.toml"),
          'schema = 1\n[[layer]]\nname = "base"\npath = ".hafen/base"\nrank = 0\n'
          '[[layer]]\nname = "mine"\npath = "."\nrank = 10\n')
    write(os.path.join(root, "justfile"), "import? '.hafen/base/hafen.just'\n")
    write(os.path.join(root, ".hafen", "commit-baseline.txt"), "# none\n")
    write(os.path.join(root, ".hafen", "link-baseline.txt"), "# none\n")
    os.symlink(os.path.relpath(old_base, os.path.join(root, ".hafen")),
               os.path.join(root, ".hafen", "base"))
    write(os.path.join(root, "claude", "CLAUDE.md"),
          "# CLAUDE.md: mine\n\n@~/.claude/hafen/00-base/claude/CLAUDE.md\n\n"
          "Run `just hh-test` with HH_AUTHOR_NAME set; the stack is `hafen.toml`.\n")
    write(os.path.join(root, "standards", "README.md"),
          '---\ntitle: "Standards"\ntype: "index"\ncategory: "standards"\n---\n\nSee `~/.claude/hafen/ROOTS`.\n')
    write(os.path.join(root, "standards", "MAP.md"),
          '---\ntitle: "Map — standards"\ntype: "index"\ncategory: "map"\n---\n\n'
          + LEGACY_PREAMBLE + "\n\n# Standards\n\nWhat to reach for.\n\n1 notes. Paths are relative to `standards/`.\n\n"
          "## standards/\n\n- [Standards](README.md)\n")
    with open(os.path.join(root, "image.bin"), "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n\x00\x00hafen.just\x00")
    subprocess.run(["git", "init", "-q", "-b", "main", root], check=True)
    git(root, "add", "-A")
    git(root, *GIT_IDENT, "commit", "-q", "-m", "chore(layer): start")
    return root


class MigrateFromHeimathafen(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_base = make_old_base(self.tmp.name)
        self.layer = make_legacy_layer(self.tmp.name, self.old_base)
        self.home = os.path.join(self.tmp.name, "home")
        os.makedirs(self.home)

    def tearDown(self):
        self.tmp.cleanup()

    def migrate(self, *args, layer=None):
        return run(["migrate-from-heimathafen", layer or self.layer, *args], home=self.home)

    def test_a_dry_run_writes_nothing_and_lists_every_change_with_counts(self):
        before = snapshot(self.layer)
        done = self.migrate("--dry-run")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual(snapshot(self.layer), before)
        out = done.stdout
        for line in ("would rename   hafen-layer.toml -> groundwork-layer.toml",
                     "would rename   hafen.toml -> groundwork.toml",
                     "would rename   .hafen/ -> .groundwork/",
                     "would symlink  .groundwork/base:",
                     "would rewrite  claude/CLAUDE.md  [assembly-path x1, env-var x1, stack-file x1, test-recipe x1]",
                     "would rewrite  standards/MAP.md  [map-preamble x1]",
                     "renames:            3  (2 file(s), 1 directory)",
                     "base symlink:       1 repointed",
                     "config-key:       1 file(s), 1 replacement(s)",
                     "not text, skipped:  1"):
            self.assertIn(line, out)
        self.assertEqual(git(self.layer, "status", "--porcelain"), "")

    def test_applying_renames_rewrites_and_leaves_history_and_the_index_alone(self):
        head = git(self.layer, "rev-parse", "HEAD")
        count = git(self.layer, "rev-list", "--count", "HEAD")
        done = self.migrate()
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        for old in ("hafen-layer.toml", "hafen.toml", ".hafen"):
            self.assertFalse(os.path.lexists(os.path.join(self.layer, old)), old)
        for new in ("groundwork-layer.toml", "groundwork.toml", ".groundwork/commit-baseline.txt"):
            self.assertTrue(os.path.lexists(os.path.join(self.layer, new)), new)
        self.assertEqual(read_file(os.path.join(self.layer, "justfile")),
                         "import? '.groundwork/base/groundwork.just'\n")
        self.assertIn('path = ".groundwork/base"', read_file(os.path.join(self.layer, "groundwork.toml")))
        entry = read_file(os.path.join(self.layer, "claude", "CLAUDE.md"))
        self.assertIn("@~/.claude/groundwork/00-base/claude/CLAUDE.md", entry)
        self.assertIn("`just gwk-test` with GWK_AUTHOR_NAME set; the stack is `groundwork.toml`", entry)
        self.assertEqual(git(self.layer, "rev-parse", "HEAD"), head)
        self.assertEqual(git(self.layer, "rev-list", "--count", "HEAD"), count)
        self.assertEqual(git(self.layer, "diff", "--cached", "--name-only"), "", "nothing is staged")
        self.assertNotEqual(git(self.layer, "status", "--porcelain"), "")

    def test_the_base_symlink_follows_its_directory_and_names_this_base(self):
        self.assertEqual(self.migrate().returncode, 0)
        link = os.path.join(self.layer, ".groundwork", "base")
        self.assertTrue(os.path.islink(link))
        self.assertFalse(os.path.isabs(os.readlink(link)))
        self.assertEqual(os.path.realpath(link), os.path.realpath(os.path.dirname(BIN)))

    def test_a_link_to_a_middle_layer_is_kept_and_an_explicit_base_wins(self):
        middle = os.path.join(self.tmp.name, "middle")
        write(os.path.join(middle, "hafen-layer.toml"), 'schema = 1\nname = "mid"\n')
        link = os.path.join(self.layer, ".hafen", "base")
        os.unlink(link)
        os.symlink(os.path.relpath(middle, os.path.join(self.layer, ".hafen")), link)
        git(self.layer, "add", "-A")
        git(self.layer, *GIT_IDENT, "commit", "-q", "-m", "chore(layer): middle")
        done = self.migrate()
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertEqual(os.path.realpath(os.path.join(self.layer, ".groundwork", "base")),
                         os.path.realpath(middle))
        self.assertIn("old-style layer that is not a base", done.stdout)

    def test_an_explicit_base_must_be_a_groundwork_base(self):
        done = self.migrate("--base", self.old_base, "--dry-run")
        self.assertEqual(done.returncode, 1)
        self.assertIn("is not a groundwork base", done.stdout)
        done = self.migrate("--base", os.path.dirname(BIN), "--dry-run")
        self.assertEqual(done.returncode, 0, done.stdout)

    def test_only_exact_mechanism_references_change(self):
        prose = ("Hafenwasser and the domain hafen.de and linkhafen.de and x.hafen.de stay.\n"
                 "Prose about heimathafen and Heimathafen stays, so do `hafen` alone and the hh program.\n"
                 "A citation of `hafen.just:292` and `bin/hh.py:109,762` and `hafen-layer.toml:30-33` is history.\n"
                 "A path .hafenx and a name my.hafen and ~/.claude/hafen-backup are not ours.\n"
                 "A line citation `hh.py:1007` and a package src/hafen and the word hafen/ are history.\n")
        note = os.path.join(self.layer, "standards", "notes.md")
        write(note, prose)
        git(self.layer, "add", "-A")
        git(self.layer, *GIT_IDENT, "commit", "-q", "-m", "docs(standards): add a note")
        self.assertEqual(self.migrate().returncode, 0)
        self.assertEqual(read_file(os.path.join(self.layer, "standards", "notes.md")), prose)

    def test_script_cli_and_relative_assembly_references_are_migrated(self):
        note = os.path.join(self.layer, "standards", "notes.md")
        write(note, "Run `hh.py map --check` or `bin/hh.py link`; `hafen publish-check` and `hafen doctor`;\n"
                    "handles in `hafen/<NN>-<name>`, `hafen/ROOTS` and `hafen/INDEX.md`.\n")
        git(self.layer, "add", "-A")
        git(self.layer, *GIT_IDENT, "commit", "-q", "-m", "docs(standards): add a note")
        self.assertEqual(self.migrate().returncode, 0)
        self.assertEqual(read_file(note),
                         "Run `gwk.py map --check` or `bin/gwk.py link`; `just publish-check` and `just doctor`;\n"
                         "handles in `groundwork/<NN>-<name>`, `groundwork/ROOTS` and `groundwork/INDEX.md`.\n")

    def test_crlf_files_keep_their_line_endings(self):
        write(os.path.join(self.layer, "standards", "crlf.md"), "line one\r\nsee `.hafen/base`\r\n")
        git(self.layer, "add", "-A")
        git(self.layer, *GIT_IDENT, "commit", "-q", "-m", "docs(standards): crlf")
        self.assertEqual(self.migrate().returncode, 0)
        self.assertEqual(read_file(os.path.join(self.layer, "standards", "crlf.md")),
                         "line one\r\nsee `.groundwork/base`\r\n")

    def test_a_binary_file_is_never_rewritten(self):
        def content():
            with open(os.path.join(self.layer, "image.bin"), "rb") as f:
                return f.read()
        before = content()
        self.assertEqual(self.migrate().returncode, 0)
        self.assertEqual(content(), before)

    def test_a_dirty_tree_is_refused_and_a_dry_run_only_warns(self):
        write(os.path.join(self.layer, "standards", "wip.md"), "uncommitted\n")
        before = snapshot(self.layer)
        done = self.migrate()
        self.assertEqual(done.returncode, 1)
        self.assertIn("working tree is not clean", done.stdout)
        self.assertEqual(snapshot(self.layer), before)
        done = self.migrate("--dry-run")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("a real run would refuse", done.stdout)
        self.assertEqual(snapshot(self.layer), before)

    def test_a_directory_that_is_not_a_git_repository_is_refused(self):
        shutil_root = os.path.join(self.tmp.name, "plain")
        os.makedirs(shutil_root)
        for name in os.listdir(self.layer):
            if name != ".git":
                target = os.path.join(self.layer, name)
                subprocess.run(["cp", "-a", target, shutil_root], check=True)
        before = snapshot(shutil_root)
        done = self.migrate(layer=shutil_root)
        self.assertEqual(done.returncode, 1)
        self.assertIn("not the top of a git repository", done.stdout)
        self.assertEqual(snapshot(shutil_root), before)

    def test_a_second_run_finds_nothing_to_do(self):
        self.assertEqual(self.migrate().returncode, 0)
        git(self.layer, "add", "-A")
        git(self.layer, *GIT_IDENT, "commit", "-q", "-m", "chore(layer): migrate")
        done = self.migrate()
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("already migrated", done.stdout)
        self.assertEqual(git(self.layer, "status", "--porcelain"), "")

    def test_a_half_finished_migration_is_refused_before_anything_is_written(self):
        write(os.path.join(self.layer, "groundwork-layer.toml"), "schema = 1\n")
        git(self.layer, "add", "-A")
        git(self.layer, *GIT_IDENT, "commit", "-q", "-m", "chore(layer): both names")
        before = snapshot(self.layer)
        done = self.migrate()
        self.assertEqual(done.returncode, 1)
        self.assertIn("both hafen-layer.toml and groundwork-layer.toml exist", done.stdout)
        self.assertEqual(snapshot(self.layer), before)

    def test_an_old_base_is_refused_even_though_it_has_the_legacy_names(self):
        subprocess.run(["git", "init", "-q", "-b", "main", self.old_base], check=True)
        git(self.old_base, "add", "-A")
        git(self.old_base, *GIT_IDENT, "commit", "-q", "-m", "chore(base): start")
        before = snapshot(self.old_base)
        done = self.migrate(layer=self.old_base)
        self.assertEqual(done.returncode, 1)
        self.assertIn("this is an old base", done.stdout)
        self.assertEqual(snapshot(self.old_base), before)

    def test_a_directory_that_is_no_layer_is_refused(self):
        empty = os.path.join(self.tmp.name, "empty")
        os.makedirs(empty)
        done = self.migrate(layer=empty)
        self.assertEqual(done.returncode, 1)
        self.assertIn("not a layer", done.stdout)

    def add_notes(self, files):
        for relative, text in files.items():
            write(os.path.join(self.layer, relative), text)
        git(self.layer, "add", "-A")
        git(self.layer, *GIT_IDENT, "commit", "-q", "-m", "docs(standards): add notes")

    RECORD = "Quoted then: `.hafen/base` and `~/.claude/hafen/ROOTS`.\n"

    def test_dated_records_are_kept_as_written_by_default(self):
        self.add_notes({"SESSION_LOG.md": self.RECORD,
                        "standards/audit-2026-10-03.md": self.RECORD,
                        "standards/deep/rulings-2026-09-20.md": self.RECORD,
                        "standards/living.md": self.RECORD})
        done = self.migrate("--dry-run")
        self.assertEqual(done.returncode, 0, done.stdout)
        for line in ("would keep     SESSION_LOG.md  [dated record; not rewritten: assembly-path x1, state-dir x1]",
                     "would keep     standards/audit-2026-10-03.md  [dated record;",
                     "would keep     standards/deep/rulings-2026-09-20.md  [dated record;",
                     "would rewrite  standards/living.md",
                     "kept as written:    3  (6 replacement(s) not made, excluded)"):
            self.assertIn(line, done.stdout)
        self.assertNotIn("would rewrite  SESSION_LOG.md", done.stdout)
        self.assertEqual(self.migrate().returncode, 0)
        for kept in ("SESSION_LOG.md", "standards/audit-2026-10-03.md", "standards/deep/rulings-2026-09-20.md"):
            self.assertEqual(read_file(os.path.join(self.layer, kept)), self.RECORD, kept)
        self.assertEqual(read_file(os.path.join(self.layer, "standards", "living.md")),
                         "Quoted then: `.groundwork/base` and `~/.claude/groundwork/ROOTS`.\n")

    def test_only_a_valid_iso_date_in_the_name_makes_a_record(self):
        for relative, record in (("SESSION_LOG.md", True), ("vault/x/SESSION_LOG.md", True),
                                 ("a/audit-2026-10-03.md", True), ("a/rulings-2026-09-20-final.md", True),
                                 ("DESIGN-2026-09-18.md", True),
                                 ("a/Capability Matrix 2026-08-12.md", False),   # "as of", kept current
                                 ("a/audit-2026-13-03.md", False), ("a/audit-2026-10-32.md", False),
                                 ("a/audit-2026-10-03.txt", False), ("a/audit-20261003.md", False),
                                 ("a/audit-2026-10-031.md", False), ("a/2026-10-03.md", False),
                                 ("a/SESSION_LOG.md.bak", False), ("a/2026-10-03/notes.md", False)):
            self.assertEqual(gwk.is_dated_record(relative), record, relative)

    def test_an_explicit_exclude_matches_a_name_at_any_depth_or_a_path_from_the_root(self):
        self.add_notes({"standards/a/keep.md": self.RECORD, "standards/b/keep.md": self.RECORD,
                        "standards/c/other.md": self.RECORD, "standards/d/other.md": self.RECORD})
        done = self.migrate("--exclude", "keep.md", "--exclude", "standards/c/*")
        self.assertEqual(done.returncode, 0, done.stdout)
        migrated = "Quoted then: `.groundwork/base` and `~/.claude/groundwork/ROOTS`.\n"
        for relative, text in (("a/keep.md", self.RECORD), ("b/keep.md", self.RECORD),
                               ("c/other.md", self.RECORD), ("d/other.md", migrated)):
            self.assertEqual(read_file(os.path.join(self.layer, "standards", relative)), text, relative)
        self.assertIn("[--exclude keep.md; not rewritten", done.stdout)
        self.assertIn("[--exclude standards/c/*; not rewritten", done.stdout)

    def test_no_default_excludes_rewrites_a_dated_record_again(self):
        self.add_notes({"SESSION_LOG.md": self.RECORD})
        self.assertEqual(self.migrate("--no-default-excludes").returncode, 0)
        self.assertEqual(read_file(os.path.join(self.layer, "SESSION_LOG.md")),
                         "Quoted then: `.groundwork/base` and `~/.claude/groundwork/ROOTS`.\n")

    def test_an_exclude_that_would_keep_the_layer_or_stack_file_is_refused(self):
        before = snapshot(self.layer)
        for pattern in ("hafen-layer.toml", "*.toml", "hafen.toml"):
            done = self.migrate("--exclude", pattern)
            self.assertEqual(done.returncode, 1, pattern)
            self.assertIn("the migration must rewrite it", done.stdout)
        self.assertEqual(snapshot(self.layer), before)

    def test_an_exclude_that_matches_nothing_changes_nothing(self):
        done = self.migrate("--exclude", "no-such-file.md", "--dry-run")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("kept as written:    0", done.stdout)

    def test_a_migrated_layer_links_and_passes_the_mechanism_checks(self):
        self.assertEqual(self.migrate().returncode, 0)
        for args in (["map", "--check"], ["imports"], ["entry"], ["direction"], ["frontmatter"],
                     ["links"], ["paths"], ["check-log"], ["link"], ["symlinks"]):
            done = run(args, layer=self.layer, home=self.home)
            self.assertEqual(done.returncode, 0, f"{args}: {done.stdout}{done.stderr}")

    def test_the_old_commit_rule_survives_the_switch(self):
        """The old mechanism never asked for `(#N)`; the migrated layer must not start to."""
        self.assertEqual(self.migrate().returncode, 0)
        done = run(["check-subject", "fix(x): no reference"], layer=self.layer)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn('commit_reference = "none"', read_file(os.path.join(self.layer, "groundwork-layer.toml")))


class DatedRecordsAreHistory(unittest.TestCase):
    """`paths` and `links` do not fail on what a dated record cites, and still fail on a living note."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.layer = self.tmp.name
        write(os.path.join(self.layer, "groundwork-layer.toml"),
              'schema = 1\nname = "x"\nnote_dirs = ["notes"]\n')
        write(os.path.join(self.layer, "notes", "target.md"), '---\ntitle: "Target"\ntype: "x"\n---\n')
        self.dead = "See `notes/gone/old.md` and [[Gone Note]], and `notes/target.md` and [[Target]].\n"

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, command):
        return run([command], layer=self.layer)

    def test_a_dated_record_with_dead_references_is_history_not_a_failure(self):
        write(os.path.join(self.layer, "notes", "audit-2026-10-03.md"), self.dead)
        for command, message in (("paths", "1 dead path reference(s) in 1 dated record(s) kept as history"),
                                 ("links", "1 dangling wikilink(s) in 1 dated record(s) kept as history")):
            done = self.check(command)
            self.assertEqual(done.returncode, 0, done.stdout)
            self.assertIn(message, done.stdout)
            self.assertIn("notes/audit-2026-10-03.md", done.stdout)

    def test_the_same_references_in_a_living_note_still_fail(self):
        write(os.path.join(self.layer, "notes", "living.md"), self.dead)
        done = self.check("paths")
        self.assertEqual(done.returncode, 1)
        self.assertIn("`notes/gone/old.md` does not exist in any layer", done.stdout)
        done = self.check("links")
        self.assertEqual(done.returncode, 1)
        self.assertIn("[[Gone Note]] resolves to nothing", done.stdout)

    def test_a_dated_record_still_has_to_have_frontmatter(self):
        write(os.path.join(self.layer, "notes", "audit-2026-10-03.md"), "# no frontmatter\n")
        done = self.check("frontmatter")
        self.assertEqual(done.returncode, 1)
        self.assertIn("audit-2026-10-03.md: no parseable frontmatter", done.stdout)

    def test_references_that_resolve_in_a_dated_record_are_not_reported_as_history(self):
        write(os.path.join(self.layer, "notes", "audit-2026-10-03.md"), "See `notes/target.md` and [[Target]].\n")
        for command in ("paths", "links"):
            done = self.check(command)
            self.assertEqual(done.returncode, 0, done.stdout)
            self.assertNotIn("kept as history", done.stdout)


class AddCommitReference(unittest.TestCase):
    def test_an_existing_key_is_left_alone(self):
        text = 'schema = 1\ncommit_reference = "issue"\n[map.x]\nheading = "h"\n'
        self.assertEqual(gwk.add_commit_reference(text), (text, 0))

    def test_the_key_goes_above_the_first_table_and_its_comment(self):
        text = 'schema = 1\nassembled = true\n\n# about the table\n[map.x]\nheading = "h"\n'
        new, added = gwk.add_commit_reference(text)
        self.assertEqual(added, 1)
        parsed = tomllib.loads(new)
        self.assertEqual(parsed["commit_reference"], "none")
        self.assertEqual(parsed["map"]["x"]["heading"], "h")
        self.assertNotIn("commit_reference", parsed["map"]["x"])
        self.assertIn('commit_reference = "none"\n\n# about the table\n[map.x]', new)

    def test_a_file_without_tables_gets_the_key_at_the_end(self):
        new, added = gwk.add_commit_reference('schema = 1\nname = "x"\n')
        self.assertEqual(added, 1)
        self.assertEqual(tomllib.loads(new)["commit_reference"], "none")

    def test_the_commit_reference_key_is_not_added_twice(self):
        once, _ = gwk.add_commit_reference('schema = 1\n[map.x]\nheading = "h"\n')
        self.assertEqual(gwk.add_commit_reference(once), (once, 0))


class LinkReplacesTheLegacyAssembly(unittest.TestCase):
    """`link` on a machine that was assembled by the old mechanism leaves nothing of it behind."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = os.path.join(self.tmp.name, "home")
        self.claude = os.path.join(self.home, ".claude")
        self.layer = os.path.join(self.tmp.name, "my-layer")
        self.assertEqual(run(["new-layer", self.layer], home=self.home).returncode, 0)
        # What an old `link` left: ~/.claude/hafen/ with handles into an old base, and a command
        # link into that old base that the new base has no counterpart for.
        self.old_base = make_old_base(self.tmp.name)
        write(os.path.join(self.old_base, "claude", "commands", "retired.md"), "old\n")
        legacy = os.path.join(self.claude, "hafen")
        os.makedirs(legacy)
        os.symlink(self.old_base, os.path.join(legacy, "00-base"))
        os.symlink(self.layer, os.path.join(legacy, "10-my-layer"))
        write(os.path.join(legacy, "ROOTS"), self.old_base + "\n" + self.layer + "\n")
        write(os.path.join(legacy, "INDEX.md"), "# old index\n")
        os.makedirs(os.path.join(self.claude, "commands"))
        os.symlink(os.path.join(self.old_base, "claude", "commands", "retired.md"),
                   os.path.join(self.claude, "commands", "retired.md"))

    def tearDown(self):
        self.tmp.cleanup()

    def link(self):
        return run(["link"], layer=self.layer, home=self.home)

    def test_the_old_directory_and_the_links_into_the_old_base_are_removed(self):
        done = self.link()
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertFalse(os.path.lexists(os.path.join(self.claude, "hafen")))
        self.assertFalse(os.path.lexists(os.path.join(self.claude, "commands", "retired.md")))
        self.assertTrue(os.path.isdir(os.path.join(self.claude, "groundwork", "00-base")))
        self.assertEqual(run(["symlinks"], layer=self.layer, home=self.home).returncode, 0)
        self.assertEqual(self.link().returncode, 0, "and a second run is quiet")

    def test_a_stranger_in_the_old_directory_keeps_it_and_is_reported(self):
        write(os.path.join(self.claude, "hafen", "notes.txt"), "mine\n")
        done = self.link()
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertTrue(os.path.isfile(os.path.join(self.claude, "hafen", "notes.txt")))
        self.assertFalse(os.path.lexists(os.path.join(self.claude, "hafen", "00-base")))
        self.assertIn("left alone (not ours)", done.stdout)

    def test_a_link_to_somewhere_else_is_not_ours_and_stays(self):
        elsewhere = os.path.join(self.tmp.name, "elsewhere.md")
        write(elsewhere, "x\n")
        os.symlink(elsewhere, os.path.join(self.claude, "commands", "mine.md"))
        done = self.link()
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertTrue(os.path.islink(os.path.join(self.claude, "commands", "mine.md")))
        self.assertIn("left alone (not ours): ~/.claude/commands/mine.md", done.stdout)

    def test_without_an_old_directory_nothing_is_said_about_one(self):
        shutil_home = os.path.join(self.tmp.name, "fresh-home")
        os.makedirs(shutil_home)
        done = run(["link"], layer=self.layer, home=shutil_home)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertNotIn("legacy", done.stdout)


if __name__ == "__main__":
    unittest.main()
