"""Nothing private reaches the output: the redactor, the aliases, the secret check and the leak scan."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT, Mined, demo
from repo_miner.privacy import Redactor, looks_secret, make_aliases, scan


class RedactorTest(unittest.TestCase):
    def test_secrets_and_addresses(self):
        r = Redactor()
        text = r.clean("mail jane.doe@corp.invalid key ghp_" + "a" * 36 + " db postgres://u:p@host/db ip 10.1.2.3 api_key=abcdefghijklmnop")
        for gone in ["jane.doe@corp.invalid", "ghp_", "postgres://", "10.1.2.3", "abcdefghijklmnop"]:
            self.assertNotIn(gone, text)
        self.assertEqual(r.counts["email"], 1)

    def test_tool_addresses_and_shared_home_paths_stay(self):
        r = Redactor()
        self.assertIn("noreply@anthropic.com", r.clean("Co-Authored-By: Claude <noreply@anthropic.com>"))
        self.assertEqual(r.clean("see /home/jane/code/app"), "see ~/code/app")
        self.assertEqual(r.clean("ran in /home/runner/work"), "ran in /home/runner/work")

    def test_deny_list_and_aliases(self):
        r = Redactor(["Kraken"], {"Ana Costa": "Person A"})
        self.assertEqual(r.clean("Ana Costa ships kraken"), "Person A ships [name]")
        self.assertEqual(r.clean("Merge pull request #3 from ana costa/fix"), "Merge pull request #3 from Person A/fix")
        self.assertEqual(r.name("Ana Costa"), "Person A")
        self.assertEqual(r.clean("Merge pull request #4 from zx81/fix (thanks @zx81)"), "Merge pull request #4 from someone/fix (thanks @someone)")
        self.assertEqual(r.clean("Co-authored-by: Kim Lee <k@x.io>\nCo-Authored-By: Claude <noreply@anthropic.com>"),
                         "Co-authored-by: someone <[email]>\nCo-Authored-By: Claude <noreply@anthropic.com>")
        self.assertEqual(Redactor().clean("bump @types/node; thanks @zx81"), "bump @types/node; thanks @zx81")  # only when anonymising

    def test_alias_labels_go_past_z(self):
        aliases = make_aliases([f"p{i}" for i in range(30)])
        self.assertEqual(aliases["p0"], "Person A")
        self.assertEqual(aliases["p25"], "Person Z")
        self.assertEqual(aliases["p26"], "Person AA")

    def test_looks_secret(self):
        self.assertTrue(looks_secret("GITHUB_TOKEN=ghp_" + "x" * 36))
        self.assertTrue(looks_secret("DB_PASSWORD=s3cr3t-value-123"))
        self.assertFalse(looks_secret("DB_PASSWORD=\nAPI_KEY=your-key-here\n"))
        self.assertFalse(looks_secret("FLASK_APP=hello\nFOO=bar\n"))
        self.assertFalse(looks_secret("registry=https://registry.npmjs.org/\npackage-lock=false\n"))


class ScanTest(unittest.TestCase):
    def test_scan_finds_without_echoing(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "a.md").write_text("contact me at real.person@company.invalid")
            Path(d, "b.md").write_text("nothing here")
            self.assertEqual(scan(Path(d)), [("a.md", "email")])
            out = subprocess.run([sys.executable, str(ROOT / "skills/repo-miner/mine.py"), "scan", d], capture_output=True, text=True)
            self.assertEqual(out.returncode, 1)
            self.assertNotIn("real.person", out.stdout + out.stderr)


class OutputPrivacyTest(unittest.TestCase):
    def test_nothing_planted_survives(self):
        m = Mined()
        try:
            text = m.everything()
            for planted in demo.PLANTED:
                self.assertNotIn(planted, text)
            self.assertEqual(m.summary["leak_scan"], "clean")
            self.assertIn("[name]", m.text("docs/README.md"))
        finally:
            m.close()

    def test_anonymised_report_names_nobody(self):
        m = Mined(anonymise=True)
        try:
            text = m.everything()
            for name in ["Ana Costa", "Ben Okafor", "Cara Lindqvist"]:
                self.assertNotIn(name, text)
            self.assertIn("Person A", m.text("REPORT.md"))
            self.assertIn("Claude", m.text("REPORT.md"))          # tools keep their names
            self.assertEqual(m.summary["leak_scan"], "clean")
        finally:
            m.close()


if __name__ == "__main__":
    unittest.main()
