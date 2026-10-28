"""The command line: targets (repository, folder, URL), determinism, output safety, identities, and the HTML's escaping."""
import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from helpers import demo
from repo_miner import cli, doc
from repo_miner.demo import Repo, day
from repo_miner.miner import Options, mine


def quiet_main(args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli.main(args)
    return code, buf.getvalue()


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="repo-miner-cli-"))
        self.repo = demo.build(self.tmp / "src")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_json_summary(self):
        code, out = quiet_main([str(self.repo), "-o", str(self.tmp / "out"), "--json"])
        self.assertEqual(code, 0)
        summary = json.loads(out)
        self.assertEqual(summary["repositories"][0]["name"], "harbour")
        self.assertTrue(Path(summary["report"]).exists())

    def test_same_record_same_report(self):
        a, b = self.tmp / "a", self.tmp / "b"
        mine(Options([str(self.repo)], out=str(a), quiet=True))
        mine(Options([str(self.repo)], out=str(b), quiet=True))
        for rel in ["REPORT.md", "report.html", "findings.json", "data/commits.tsv", "data/timeline.json", "practices/INDEX.md"]:
            self.assertEqual((a / rel).read_text().replace(str(a), ""), (b / rel).read_text().replace(str(b), ""), rel)

    def test_refuses_to_overwrite_a_folder_that_is_not_a_report(self):
        out = self.tmp / "precious"
        out.mkdir()
        (out / "thesis.txt").write_text("do not delete")
        with self.assertRaises(SystemExit):
            mine(Options([str(self.repo)], out=str(out), quiet=True))
        self.assertTrue((out / "thesis.txt").exists())
        mine(Options([str(self.repo)], out=str(self.tmp / "out"), quiet=True))
        mine(Options([str(self.repo)], out=str(self.tmp / "out"), quiet=True))  # an earlier report is replaced

    def test_folder_of_repositories(self):
        other = Repo(self.tmp / "src" / "tiny")
        for i in range(12):
            other.commit(day(f"2024-01-{i + 1:02d}"), f"step {i}", write={"a.txt": str(i)})
        summary = mine(Options([str(self.tmp / "src")], out=str(self.tmp / "out"), quiet=True))
        self.assertEqual(sorted(r["name"] for r in summary["repositories"]), ["harbour", "tiny"])
        top = (self.tmp / "out" / "REPORT.md").read_text()
        self.assertIn("repos/harbour/REPORT.md", top)
        self.assertTrue((self.tmp / "out" / "repos" / "tiny" / "REPORT.md").exists())
        inner = self.tmp / "out" / "repos" / "harbour"
        for link in re.findall(r"\[open\]\(([^)]+)\)", (inner / "REPORT.md").read_text()):
            self.assertTrue((inner / link).exists(), link)      # links resolve from the report's own folder

    def test_url_is_cloned_with_every_branch(self):
        os.environ["XDG_CACHE_HOME"] = str(self.tmp / "cache")
        try:
            summary = mine(Options([f"file://{self.repo}"], out=str(self.tmp / "out"), quiet=True))
        finally:
            del os.environ["XDG_CACHE_HOME"]
        self.assertEqual(summary["repositories"][0]["branches"], 4)
        findings = json.loads((self.tmp / "out" / "findings.json").read_text())
        self.assertTrue(any(f["id"] == "branch-trap" for f in findings))

    def test_since_until_window(self):
        summary = mine(Options([str(self.repo)], out=str(self.tmp / "out"), since="2024-01-01", quiet=True))
        self.assertLess(summary["repositories"][0]["commits"], 50)
        self.assertIn("from 2024-01-01", (self.tmp / "out" / "REPORT.md").read_text())

    def test_one_person_many_spellings(self):
        r = Repo(self.tmp / "spell")
        for i, name in enumerate(["Dana Reyes", "dana  reyes", "Dana Reyes", "DR"]):
            env = dict(os.environ, GIT_AUTHOR_EMAIL="dana@corp.example.net", GIT_COMMITTER_EMAIL="dana@corp.example.net",
                       GIT_AUTHOR_NAME=name, GIT_COMMITTER_NAME=name, GIT_AUTHOR_DATE=day(f"2024-02-{i + 1:02d}"),
                       GIT_COMMITTER_DATE=day(f"2024-02-{i + 1:02d}"))
            (r.path / "f.txt").write_text(str(i))
            subprocess.run(["git", "-C", str(r.path), "add", "-A"], check=True, env=env)
            subprocess.run(["git", "-C", str(r.path), "commit", "-qm", f"c{i}"], check=True, env=env)
        mine(Options([str(r.path)], out=str(self.tmp / "out"), quiet=True))
        people = (self.tmp / "out" / "data" / "people.tsv").read_text().splitlines()[1:]
        self.assertEqual([p.split("\t")[:3] for p in people], [["Dana Reyes", "human", "4"]])
        self.assertNotIn("dana@corp", "".join(p.read_text() for p in (self.tmp / "out").rglob("*") if p.is_file()))

    def test_demo_command(self):
        code, out = quiet_main(["demo"])
        self.assertEqual(code, 0)
        self.assertTrue(out.rstrip().endswith("demo: clean"))


class EscapingTest(unittest.TestCase):
    def test_commit_text_cannot_inject_markup(self):
        d = doc.Doc().p("subject <script>alert(1)</script> and `<b>`").table(["a"], [["<img src=x onerror=alert(1)>"]])
        html = doc.to_html(d.blocks)
        self.assertNotIn("<script>", html)
        self.assertNotIn("<img", html)
        self.assertIn("<code>&lt;b&gt;</code>", html)

    def test_links_with_code_labels(self):
        html = doc.inline_html("in [`a1b2c3d`](https://github.com/o/r/commit/a1b2c3d) and [x](javascript:alert(1))")
        self.assertIn('<a href="https://github.com/o/r/commit/a1b2c3d"><code>a1b2c3d</code></a>', html)
        self.assertNotIn('href="javascript', html)


if __name__ == "__main__":
    unittest.main()
