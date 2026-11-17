"""Tests for the confidential skill: `claude/skills/confidential/`. Stdlib only.

Run with `just gwk-test`. Every test works in a temporary directory with its own HOME and a fake
local model on 127.0.0.1, and uses the `plain` store backend. All data is fictional.
"""

import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
import unittest.mock
from http.server import BaseHTTPRequestHandler, HTTPServer

SKILL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "claude", "skills", "confidential")
SCRIPT = os.path.join(SKILL, "scripts", "confidential.py")
GUARD = os.path.join(SKILL, "hooks", "guard.py")
sys.path.insert(0, os.path.join(SKILL, "scripts"))

import confidential  # noqa: E402

IBAN = "DE89 3704 0044 0532 0130 00"  # the well-known documentation example
TAX_ID = "12345678901"
NAME = "Alice Example"
EMAIL = "alice@example.invalid"
DOCUMENT = f"""ACME Revenue Office - Tax notice dated 2024-03-02
Taxpayer: {NAME}
Tax ID: {TAX_ID}
IBAN: {IBAN}
Contact: {EMAIL}
"""
VALUES = [IBAN, TAX_ID, NAME, EMAIL]

CANNED = {
    "category": "tax-notice", "date": "2024-03-02", "title": f"Tax notice for {NAME}",
    "sensitive": [{"kind": "person-name", "text": NAME, "suggested_name": "ACME_TAXPAYER"},
                  {"kind": "tax-id", "text": TAX_ID, "suggested_name": "ACME_TAX_ID"}],
    "summary": f"Notice to {NAME} (tax id {TAX_ID}) about a payment to {IBAN.replace(' ', '')}.",
}


class FakeModel:
    """A local server answering /v1/chat/completions with canned JSON, counting the requests."""

    def __init__(self, canned):
        outer = self
        self.canned, self.hits, self.last, self.finish = canned, 0, None, "stop"

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                outer.last = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                outer.hits += 1
                body = json.dumps({"choices": [{"finish_reason": outer.finish,
                                                "message": {"content": json.dumps(outer.canned)}}]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_):
                pass

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_port}/v1/chat/completions"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = os.path.realpath(self.tmp.name)
        self.home = os.path.join(self.dir, "home")
        os.makedirs(self.home)
        self.store = os.path.join(self.dir, "vault", "store.json")
        self.out = os.path.join(self.dir, "filled")
        self.model = FakeModel(CANNED)
        self.addCleanup(self.model.close)
        self.config = self.write_config()

    def write_config(self, extra="", endpoint=None):
        path = os.path.join(self.dir, "config.toml")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f'[confidential]\nenabled = true\nendpoint = "{endpoint or self.model.url}"\nmodel = "local"\n'
                    f'store = "{self.store}"\noutput_dir = "{self.out}"\nstore_backend = "plain"\n{extra}')
        return path

    def run_cli(self, *args, stdin="", config=None):
        env = dict(os.environ, HOME=self.home, GWK_CONFIDENTIAL_CONFIG=config or self.config)
        return subprocess.run([sys.executable, SCRIPT, *args], input=stdin, capture_output=True, text=True, env=env)

    def write(self, name, text):
        path = os.path.join(self.dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def stored(self):
        with open(self.store, encoding="utf-8") as f:
            return json.load(f)["entries"]

    def add(self, name, kind, value):
        proc = self.run_cli("store", "add", name, "--kind", kind, "--from-stdin", stdin=value)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def assertNoValue(self, *texts):
        for text in texts:
            for v in VALUES:
                self.assertNotIn(v, text)
                self.assertNotIn(v.replace(" ", ""), text)


class Ingest(Base):
    def test_ingest_stores_values_and_prints_only_placeholders(self):
        proc = self.run_cli("ingest", self.write("notice.txt", DOCUMENT))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNoValue(proc.stdout, proc.stderr.replace("warning: store_backend=plain", ""))
        self.assertIn("category: tax-notice", proc.stdout)
        self.assertIn("date: 2024-03-02", proc.stdout)
        self.assertIn("{{ACME_TAXPAYER}}", proc.stdout)
        self.assertIn("{{ACME_TAX_ID}}", proc.stdout)
        entries = self.stored()
        self.assertEqual(entries["ACME_TAX_ID"]["value"], TAX_ID)
        self.assertEqual({e["value"] for e in entries.values()} & set(VALUES), set(VALUES))
        self.assertEqual(entries["ACME_TAX_ID"]["kind"], "tax-id")
        self.assertEqual(entries["ACME_TAX_ID"]["source"], "notice.txt")

    def test_a_model_summary_that_leaks_an_unstored_value_is_blocked(self):
        self.model.canned = dict(CANNED, summary="Call +49 30 7654321 about {{ACME_TAX_ID}}.")
        proc = self.run_cli("ingest", self.write("notice.txt", DOCUMENT))
        self.assertEqual(proc.returncode, 1)
        self.assertRegex(proc.stdout, r"^BLOCKED: 1 matches \(kinds: phone\)$")

    def test_second_ingest_reuses_names(self):
        path = self.write("notice.txt", DOCUMENT)
        self.run_cli("ingest", path)
        before = self.stored()
        proc = self.run_cli("ingest", path)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(set(self.stored()), set(before))
        self.assertIn("names added: (none)", proc.stdout)
        self.assertIn("ACME_TAX_ID", proc.stdout.split("names reused:")[1])

    def test_label_only_category_prints_only_category_and_date(self):
        proc = self.run_cli("ingest", self.write("notice.txt", DOCUMENT),
                            config=self.write_config('label_only = ["Tax-Notice"]\n'))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip().splitlines(), ["category: tax-notice", "date: 2024-03-02"])
        self.assertIn("ACME_TAX_ID", self.stored())

    def test_unreachable_model_stores_and_prints_nothing(self):
        config = self.write_config(endpoint="http://127.0.0.1:9/v1/chat/completions")
        proc = self.run_cli("ingest", self.write("notice.txt", DOCUMENT), config=config)
        self.assertEqual(proc.returncode, confidential.EXIT_MODEL)
        self.assertEqual(proc.stdout, "")
        self.assertFalse(os.path.exists(self.store))
        self.assertNoValue(proc.stderr)

    def test_a_cut_off_reply_stores_and_prints_nothing(self):
        self.model.finish = "length"
        proc = self.run_cli("ingest", self.write("notice.txt", DOCUMENT))
        self.assertEqual(proc.returncode, confidential.EXIT_MODEL)
        self.assertIn("cut off", proc.stderr)
        self.assertEqual(proc.stdout, "")
        self.assertFalse(os.path.exists(self.store))

    def test_request_options_reach_the_model_but_cannot_replace_the_prompt(self):
        proc = self.run_cli("ingest", self.write("notice.txt", DOCUMENT),
                            config=self.write_config('request_options = { reasoning_effort = "none" }\n'))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.model.last["reasoning_effort"], "none")
        proc = self.run_cli("config", config=self.write_config('request_options = { model = "other" }\n'))
        self.assertEqual(proc.returncode, confidential.EXIT_USAGE)

    def test_remote_endpoint_is_refused(self):
        config = self.write_config(endpoint="http://models.example.invalid/v1/chat/completions")
        proc = self.run_cli("ingest", self.write("notice.txt", DOCUMENT), config=config)
        self.assertEqual(proc.returncode, confidential.EXIT_USAGE)
        self.assertIn("localhost", proc.stderr)
        self.assertEqual(self.model.hits, 0)

    def test_seed_phrase_stores_nothing_and_skips_the_model(self):
        words = "abandon ability able about above absent absorb abstract absurd abuse access accident".split()
        for name, text in (("line.txt", " ".join(words) + "\n"),
                           ("numbered.txt", "".join(f"{i}. {w}\n" for i, w in enumerate(words, 1))),
                           ("column.txt", "\n".join(words) + "\n")):
            proc = self.run_cli("ingest", self.write(name, "Recovery\n" + text))
            self.assertEqual(proc.returncode, confidential.EXIT_SEED, name)
            self.assertEqual(proc.stdout.strip(), f"seed-phrase suspected in {os.path.join(self.dir, name)}")
            for word in words:
                self.assertNotIn(word, proc.stdout.replace("suspected", "").replace("seed-phrase", "").replace(name, ""))
        self.assertFalse(os.path.exists(self.store))
        self.assertEqual(self.model.hits, 0)

    def test_ordinary_prose_is_not_a_seed_phrase(self):
        self.assertFalse(confidential.seed_phrase_suspected("The notice is due in the first week of March, so pay it."))
        self.assertFalse(confidential.seed_phrase_suspected("one\ntwo\nthree\n"))

    def test_non_text_file_runs_text_command_with_the_path(self):
        extract = self.write("extract.py", f"import sys\nprint(open(sys.argv[1]).read())\n")
        config = self.write_config(f'text_command = ["{sys.executable}", "{extract}", "{{in}}"]\n')
        proc = self.run_cli("ingest", self.write("notice.pdf", DOCUMENT), config=config)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("ACME_TAX_ID", self.stored())

    def test_non_text_file_without_text_command_fails(self):
        proc = self.run_cli("ingest", self.write("notice.pdf", DOCUMENT))
        self.assertEqual(proc.returncode, confidential.EXIT_USAGE)
        self.assertEqual(proc.stdout, "")

    def test_layer_detector_stores_its_matches(self):
        document = DOCUMENT + "Ref: ZX-4821-QQ\n"
        config = self.write_config('detectors = [{ kind = "case-ref", regex = "ZX-\\\\d{4}-[A-Z]{2}" }]\n')
        proc = self.run_cli("ingest", self.write("notice.txt", document), config=config)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual([e["kind"] for e in self.stored().values() if e["value"] == "ZX-4821-QQ"], ["case-ref"])


class Detectors(unittest.TestCase):
    def kinds(self, text):
        return [k for k, *_ in confidential.detect(text)]

    def test_iban_needs_a_valid_checksum(self):
        self.assertEqual(self.kinds(f"pay {IBAN}"), ["iban"])
        self.assertNotIn("iban", self.kinds("pay DE89 3704 0044 0532 0130 01"))

    def test_generic_kinds(self):
        self.assertEqual(self.kinds(f"mail {EMAIL}"), ["email"])
        self.assertEqual(self.kinds("0x" + "ab" * 20), ["evm-address"])
        self.assertEqual(self.kinds("bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"), ["btc-address"])
        self.assertEqual(self.kinds("bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t5"), [])
        self.assertEqual(self.kinds("due EUR 1,234.50"), ["money"])
        self.assertEqual(self.kinds("call +49 30 1234567"), ["phone"])
        self.assertEqual(self.kinds("id 12345678901"), ["digits"])

    def test_dates_and_short_numbers_are_not_findings(self):
        self.assertEqual(self.kinds("dated 2024-03-02, 03.02.2024 and page 12 of 40"), [])


class Filter(Base):
    def setUp(self):
        super().setUp()
        self.add("ACME_TAX_ID", "tax-id", TAX_ID)
        self.add("ACME_IBAN", "iban", IBAN)
        self.add("ACME_TAXPAYER", "person-name", NAME)

    def blocked(self, text):
        proc = self.run_cli("filter", stdin=text)
        self.assertEqual(proc.returncode, 1, text)
        self.assertRegex(proc.stdout, r"^BLOCKED: \d+ matches \(kinds: .+\)$")
        self.assertNoValue(proc.stdout)
        return proc

    def test_clean_text_is_echoed(self):
        text = "Pay {{ACME_TAX_ID}} by 2024-03-02. All checks passed (3 of 3).\n"
        proc = self.run_cli("filter", stdin=text)
        self.assertEqual((proc.returncode, proc.stdout), (0, text))

    def test_blocks_each_normalisation(self):
        self.blocked(f"tax id {TAX_ID}")                       # exact
        self.blocked(f"payee {NAME.upper()}")                   # case
        self.blocked(f"payee alice\n   example")                # whitespace
        self.blocked("account de89370400440532013000")         # separators dropped
        self.blocked("number 123-456-789-01")                   # digits-only, other grouping
        self.blocked("digits 123 abc 456 def 789 ghi 01")       # digits-only across other characters

    def test_blocks_a_detector_hit_that_is_not_stored(self):
        proc = self.blocked("write to bob@example.invalid")
        self.assertIn("email", proc.stdout)

    def test_placeholders_never_block(self):
        self.add("ACME_COMPANY", "org", "ACME")
        proc = self.run_cli("filter", stdin="{{ACME_COMPANY}} {{ACME_TAX_ID}}")
        self.assertEqual(proc.returncode, 0)


class Store(Base):
    def test_list_never_reveals_a_value(self):
        self.add("ACME_TAX_ID", "tax-id", TAX_ID)
        self.add("ACME_IBAN", "iban", IBAN)
        proc = self.run_cli("store", "list")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("ACME_TAX_ID\ttax-id\t11 chars, digits", proc.stdout)
        self.assertIn("27 chars, letters+digits+spaces", proc.stdout)
        self.assertNoValue(proc.stdout)
        for fragment in ("1234", "DE89", "0130"):
            self.assertNotIn(fragment, proc.stdout)

    def test_a_value_cannot_be_given_in_argv(self):
        proc = self.run_cli("store", "add", "ACME_TAX_ID", "--kind", "tax-id", TAX_ID)
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse(os.path.exists(self.store))
        proc = self.run_cli("store", "add", "ACME_TAX_ID", "--kind", "tax-id", "--from-file", self.write("v.txt", TAX_ID))
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(self.stored()["ACME_TAX_ID"]["value"], TAX_ID)

    def test_name_rule_rename_and_remove(self):
        for bad in ("acme_tax", "AB", "1ACME", "ACME-TAX"):
            self.assertNotEqual(self.run_cli("store", "add", bad, "--kind", "x", "--from-stdin", stdin="v").returncode, 0)
        self.add("ACME_TAX_ID", "tax-id", TAX_ID)
        self.assertEqual(self.run_cli("store", "rename", "ACME_TAX_ID", "ACME_TIN").returncode, 0)
        self.assertEqual(list(self.stored()), ["ACME_TIN"])
        self.assertEqual(self.run_cli("store", "remove", "ACME_TIN").returncode, 0)
        self.assertEqual(self.stored(), {})

    def test_plain_backend_warns_on_stderr(self):
        self.assertIn("unencrypted", self.run_cli("store", "list").stderr)

    def test_disabled_config_refuses(self):
        path = self.write("off.toml", '[confidential]\nenabled = false\n')
        proc = self.run_cli("store", "list", config=path)
        self.assertEqual(proc.returncode, confidential.EXIT_USAGE)
        self.assertIn("not enabled", proc.stderr)

    def test_unknown_key_is_reported(self):
        proc = self.run_cli("config", config=self.write_config("colour = 1\n"))
        self.assertEqual(proc.returncode, confidential.EXIT_USAGE)
        self.assertIn("colour", proc.stderr)

    @unittest.skipUnless(sys.platform == "darwin", "keychain backend needs macOS")
    def test_keychain_gets_the_value_on_stdin_never_in_argv(self):
        cfg = {"store": self.store, "store_backend": "keychain"}
        calls = []

        def fake_run(argv, **kwargs):
            calls.append((argv, kwargs))
            return subprocess.CompletedProcess(argv, 1 if argv[1] == "find-generic-password" else 0, "", "")

        entries = {f"ACME_{i:03d}": {"value": TAX_ID * 20} for i in range(60)}  # large enough to need several items
        with unittest.mock.patch("subprocess.run", fake_run):
            confidential._write_blob(cfg, json.dumps({"entries": entries}).encode())
        argv, kwargs = calls[-1]
        self.assertEqual(argv, ["security", "-i"])
        self.assertGreater(kwargs["input"].count("add-generic-password"), 1)
        for call_argv, call_kwargs in calls:
            self.assertNotIn(TAX_ID, " ".join(call_argv) + call_kwargs.get("input", ""))

    @unittest.skipUnless(sys.platform == "win32", "dpapi backend needs Windows")
    def test_dpapi_round_trip(self):
        cfg = {"store": self.store, "store_backend": "dpapi", "enabled": True}
        confidential.save_entries(cfg, {"ACME_TAX_ID": {"value": TAX_ID}})
        with open(self.store, "rb") as f:
            self.assertNotIn(TAX_ID.encode(), f.read())
        self.assertEqual(confidential.load_entries(cfg)["ACME_TAX_ID"]["value"], TAX_ID)


class Render(Base):
    def setUp(self):
        super().setUp()
        self.add("ACME_TAX_ID", "tax-id", TAX_ID)

    def test_render_fills_known_names_and_reports_missing(self):
        template = self.write("form.md", "Tax ID: {{ACME_TAX_ID}} again {{ACME_TAX_ID}}; bank: {{ACME_IBAN}}\n")
        proc = self.run_cli("render", template)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        target = os.path.join(self.out, "form.md")
        self.assertEqual(proc.stdout.strip(), f"wrote {target}; filled 2; missing: [ACME_IBAN]")
        self.assertNoValue(proc.stdout)
        with open(target, encoding="utf-8") as f:
            self.assertEqual(f.read(), f"Tax ID: {TAX_ID} again {TAX_ID}; bank: {{{{ACME_IBAN}}}}\n")

    def test_render_refuses_paths_outside_output_dir(self):
        template = self.write("form.md", "{{ACME_TAX_ID}}")
        outside = os.path.join(self.dir, "elsewhere.md")
        for target in (outside, os.path.join("..", "escaped.md"), self.out):
            proc = self.run_cli("render", template, target)
            self.assertEqual(proc.returncode, confidential.EXIT_USAGE, target)
            self.assertIn("outside output_dir", proc.stderr)
        self.assertFalse(os.path.exists(outside))
        self.assertFalse(os.path.exists(os.path.join(self.dir, "escaped.md")))

    @unittest.skipIf(sys.platform == "win32", "symlinks need privileges on Windows")
    def test_render_refuses_a_symlink_that_leaves_output_dir(self):
        os.makedirs(self.out)
        elsewhere = os.path.join(self.dir, "elsewhere")
        os.makedirs(elsewhere)
        os.symlink(elsewhere, os.path.join(self.out, "link"))
        proc = self.run_cli("render", self.write("form.md", "{{ACME_TAX_ID}}"), "link/x.md")
        self.assertEqual(proc.returncode, confidential.EXIT_USAGE)
        self.assertEqual(os.listdir(elsewhere), [])


class Exec(Base):
    def setUp(self):
        super().setUp()
        self.add("ACME_TAX_ID", "tax-id", TAX_ID)

    def test_exec_gives_the_script_the_value_and_filters_its_output(self):
        script = self.write("leaky.py", "from confidential import value\nprint('id is', value('ACME_TAX_ID'))\n")
        proc = self.run_cli("exec", "--", sys.executable, script)
        self.assertEqual(proc.returncode, 1)
        self.assertRegex(proc.stdout, r"^BLOCKED: \d+ matches")
        self.assertNoValue(proc.stdout, proc.stderr)

    def test_exec_passes_a_derived_answer(self):
        script = self.write("check.py", "from confidential import value\nprint('valid:', len(value('ACME_TAX_ID')) == 11)\n")
        proc = self.run_cli("exec", "--", sys.executable, script)
        self.assertEqual((proc.returncode, proc.stdout.strip()), (0, "valid: True"))

    def test_exec_filters_errors_and_keeps_the_exit_code(self):
        script = self.write("boom.py", "from confidential import value\nvalue('ACME_MISSING')\n")
        proc = self.run_cli("exec", "--", sys.executable, script)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("ACME_MISSING", proc.stdout)


class Config(Base):
    def layer(self, name, body):
        root = os.path.join(self.dir, name)
        os.makedirs(root)
        with open(os.path.join(root, "groundwork-layer.toml"), "w", encoding="utf-8") as f:
            f.write(body)
        return root

    def test_highest_ranked_layer_with_the_section_wins(self):
        base = self.layer("base", "[confidential]\nenabled = true\nmodel = \"from-base\"\n")
        mid = self.layer("mid", 'name = "mid"\n')
        top = self.layer("top", "[confidential]\nenabled = true\nmodel = \"from-top\"\n")
        os.makedirs(os.path.join(self.home, ".claude", "groundwork"))
        with open(os.path.join(self.home, ".claude", "groundwork", "ROOTS"), "w") as f:
            f.write("\n".join((base, mid, top)) + "\n")  # lowest rank first, as `just link` writes it
        env = dict(os.environ, HOME=self.home)
        env.pop("GWK_CONFIDENTIAL_CONFIG", None)
        proc = subprocess.run([sys.executable, SCRIPT, "config"], capture_output=True, text=True, env=env)
        self.assertIn("model: from-top", proc.stdout)
        self.assertIn(os.path.join(top, "groundwork-layer.toml"), proc.stdout)

    def test_a_config_with_a_byte_order_mark_is_read(self):
        path = os.path.join(self.dir, "bom.toml")
        with open(path, "w", encoding="utf-8-sig") as f:
            f.write("[confidential]\nenabled = true\nmodel = \"with-bom\"\n")
        env = dict(os.environ, HOME=self.home, GWK_CONFIDENTIAL_CONFIG=path)
        proc = subprocess.run([sys.executable, SCRIPT, "config"], capture_output=True, text=True, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("model: with-bom", proc.stdout)

    def test_no_section_means_disabled(self):
        env = dict(os.environ, HOME=self.home)
        env.pop("GWK_CONFIDENTIAL_CONFIG", None)
        proc = subprocess.run([sys.executable, SCRIPT, "store", "list"], capture_output=True, text=True, env=env)
        self.assertEqual(proc.returncode, confidential.EXIT_USAGE)
        self.assertIn("not enabled", proc.stderr)


class Guard(Base):
    def call(self, tool, tool_input, config=None, cwd=None):
        event = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input, "cwd": cwd or self.dir}
        env = dict(os.environ, HOME=self.home, GWK_CONFIDENTIAL_CONFIG=config or self.config)
        return subprocess.run([sys.executable, GUARD], input=json.dumps(event), capture_output=True, text=True, env=env)

    def denied(self, tool, tool_input, **kw):
        proc = self.call(tool, tool_input, **kw)
        self.assertEqual(proc.returncode, 2, (tool, tool_input, proc.stderr))
        self.assertIn("confidential guard", proc.stderr)

    def allowed(self, tool, tool_input, **kw):
        proc = self.call(tool, tool_input, **kw)
        self.assertEqual((proc.returncode, proc.stdout), (0, ""), (tool, tool_input, proc.stderr))

    def test_guards_windows_paths_of_a_store_on_another_host(self):
        # The store lives on a Windows machine reached over ssh; the guard runs on a non-Windows host.
        path = os.path.join(self.dir, "remote.toml")
        with open(path, "w", encoding="utf-8") as f:
            f.write("[confidential]\nenabled = true\nstore_backend = \"dpapi\"\n"
                    "store = 'Q:\\\\vault\\\\store.bin'\noutput_dir = 'Q:\\\\Shared Files\\\\filled'\n")
        self.denied("Bash", {"command": r"ssh winbox type Q:\vault\store.bin"}, config=path)
        self.denied("Bash", {"command": 'ssh winbox dir "q:/shared files/filled"'}, config=path)
        self.allowed("Bash", {"command": r"ssh winbox dir Q:\other"}, config=path)

    def test_denies_store_and_output_paths_for_every_tool(self):
        out_file = os.path.join(self.out, "form.md")
        self.denied("Read", {"file_path": self.store})
        self.denied("Read", {"file_path": out_file})
        self.denied("Edit", {"file_path": out_file, "old_string": "a", "new_string": "b"})
        self.denied("Write", {"file_path": out_file, "content": "x"})
        self.denied("NotebookEdit", {"notebook_path": os.path.join(self.out, "n.ipynb"), "new_source": "x"})
        self.denied("Grep", {"pattern": "x", "path": self.out})
        self.denied("Glob", {"pattern": os.path.join(self.out, "*.md")})
        self.denied("Bash", {"command": f"cat {self.store}"})
        self.denied("Bash", {"command": f"ls '{self.out}'"})

    def test_denies_other_spellings(self):
        self.denied("Read", {"file_path": self.store.upper()})
        self.denied("Read", {"file_path": self.store.replace("/", "\\")})
        self.denied("Bash", {"command": f"ssh alice@example.invalid cat {self.out}/form.md"})

    def test_denies_a_search_from_a_directory_above_them(self):
        self.denied("Grep", {"pattern": "x", "path": self.dir})
        self.denied("Grep", {"pattern": "x"}, cwd=self.dir)
        self.denied("Glob", {"pattern": os.path.join(self.dir, "**", "*.md")})
        self.allowed("Grep", {"pattern": "x", "path": os.path.join(self.dir, "home")})

    def test_allows_unrelated_calls(self):
        self.allowed("Read", {"file_path": os.path.join(self.dir, "notes.md")})
        self.allowed("Bash", {"command": "ls /tmp"})
        self.allowed("Read", {"file_path": self.out + "-other/x"})

    def test_allows_the_skills_own_commands_even_over_ssh(self):
        script = "~/.claude/skills/confidential/scripts/confidential.py"
        out_file = os.path.join(self.out, "form.md")
        self.allowed("Bash", {"command": f"python3 {script} render tpl.md {out_file}"})
        self.allowed("Bash", {"command": f"python3 {script} --config c.toml exec -- python3 check.py {self.out}"})
        self.allowed("Bash", {"command": f"ssh alice@example.invalid 'python3 {script} render tpl.md {out_file}'"})
        self.allowed("Bash", {"command": f"python3 {script} store list"})

    def test_own_command_exception_is_narrow(self):
        script = "~/.claude/skills/confidential/scripts/confidential.py"
        out_file = os.path.join(self.out, "form.md")
        self.denied("Bash", {"command": f"python3 {script} store add ACME_TAX_ID --kind x --from-file {self.out}/v"})
        self.denied("Bash", {"command": f"python3 {script} render tpl.md {self.store}"})
        self.denied("Bash", {"command": f"cat {out_file}; python3 {script} store list"})
        self.denied("Bash", {"command": f"python3 {script} store list && cat {out_file}"})
        self.denied("Bash", {"command": f"python3 other.py render tpl.md {out_file}"})

    def test_does_nothing_when_not_enabled(self):
        off = self.write("off.toml", "[confidential]\nenabled = false\n")
        self.allowed("Read", {"file_path": self.store}, config=off)

    def test_a_broken_config_is_a_visible_non_blocking_error(self):
        proc = self.call("Read", {"file_path": self.store}, config=self.write("bad.toml", "not toml ["))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("not guarding", proc.stderr)


if __name__ == "__main__":
    unittest.main()
