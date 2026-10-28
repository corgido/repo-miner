"""The demo repository has a known history; the report must find what was planted in it, and describe it correctly."""
import unittest

from helpers import Mined, demo


class FindingsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = Mined()

    @classmethod
    def tearDownClass(cls):
        cls.m.close()

    def test_every_planted_story_is_found(self):
        ids = [f["id"] for f in self.m.json("findings.json")]
        for prefix, what in demo.EXPECT.items():
            with self.subTest(what=what):
                self.assertTrue(any(i.startswith(prefix) for i in ids), f"missing: {what}")

    def test_findings_are_ranked_and_carry_evidence(self):
        findings = self.m.json("findings.json")
        scores = [f["score"] for f in findings]
        self.assertEqual(scores, sorted(scores, reverse=True))
        for f in findings:
            self.assertTrue(f["title"])
            if f["kind"] != "security" or f["id"] != "sensitive-checked":
                self.assertTrue(f["dig"], f["id"])

    def test_branch_trap_names_the_real_main_line(self):
        f = self.m.finding("branch-trap")
        self.assertIn("`main` has 3 commits", f["title"])
        self.assertIn("`develop` has 100", f["title"])

    def test_unmerged_branch_is_measured_against_the_main_line_not_the_trap(self):
        f = self.m.finding("unmerged:feature/export")
        self.assertIn("holds 8 commits never merged into `develop`", f["title"])
        self.assertIsNotNone(f["question"])            # last touched long before the end: abandoned or parked?

    def test_quiet_owner(self):
        f = self.m.finding("quiet:Ben Okafor")
        self.assertIn("quiet since 2023-06-15", f["title"])      # by time, not by commit order
        self.assertIn("`src/billing`", f["question"])
        self.assertNotIn("(top level)", f["question"])

    def test_graveyard_is_dated_and_not_mistaken_for_a_move(self):
        f = self.m.finding("graveyard:src/legacy")
        self.assertIn("removed 2024-02-12", f["title"])
        self.assertIsNone(self.m.finding("moved"))

    def test_revert_is_paired_with_what_it_undid(self):
        f = self.m.finding("reverts")
        self.assertIn("within two days", f["title"])
        self.assertIn("Add retry to payments", f["question"])
        self.assertIn("after 2.0 h", f["evidence"][0])

    def test_sensitive_file_is_checked_without_printing_it(self):
        f = self.m.finding("sensitive:.env")
        self.assertIn("looks like a credential", f["title"])
        self.assertNotIn(demo.TOKEN, str(f))

    def test_initial_import_is_not_a_sweeping_change(self):
        sweeps = [f for f in self.m.json("findings.json") if f["id"].startswith("sweep:")]
        self.assertTrue(sweeps)
        self.assertTrue(all("Initial import" not in f["title"] for f in sweeps))
        self.assertTrue(any("Reformat with black" in f["title"] for f in sweeps))

    def test_agents_are_counted_by_author_and_by_trailer(self):
        f = self.m.finding("agents")
        self.assertIn("10 commits by agent authors, 20 by people with an agent co-author trailer", f["evidence"][0])
        self.assertIn("10 commits link to 2 agent sessions", " ".join(f["evidence"]))
        self.assertNotIn("session_demo", self.m.everything())            # counted, never printed

    def test_questions_section_lists_unique_questions(self):
        report = self.m.text("REPORT.md")
        section = report.split("## Questions for the people", 1)[1].split("\n## ", 1)[0]
        questions = [line for line in section.splitlines() if line[:1].isdigit()]
        self.assertGreaterEqual(len(questions), 8)
        self.assertEqual(len(questions), len(set(questions)))


class ReportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = Mined()

    @classmethod
    def tearDownClass(cls):
        cls.m.close()

    def test_report_sections_in_order(self):
        report = self.m.text("REPORT.md")
        order = ["## In short", "## Before you trust this record", "## What stands out", "## Questions for the people",
                 "## Chapters", "## People", "## Where the work is", "## Branches and releases", "## How the work is done",
                 "## Read next", "## What is in this folder", "## How this was made"]
        positions = [report.index(h) for h in order]
        self.assertEqual(positions, sorted(positions))

    def test_chapters_follow_the_silence(self):
        chapters = self.m.json("data/timeline.json")["chapters"]
        self.assertGreaterEqual(len(chapters), 2)
        self.assertEqual(chapters[-1]["from"], "2024-02-05")
        self.assertIn("settle", chapters[-1]["label"])

    def test_practices_current_and_superseded(self):
        index = self.m.text("practices/INDEX.md")
        self.assertIn(".github/workflows/ci.yml", index)
        self.assertIn("CLAUDE.md", index)
        self.assertIn("ci: `.travis.yml`", index)       # superseded, named with the commit that removed it
        self.assertNotIn("language: python", index)      # its text is not shown

    def test_data_files(self):
        commits = self.m.text("data/commits.tsv").splitlines()
        self.assertEqual(commits[0].split("\t")[:4], ["sha", "date", "author", "role"])
        self.assertEqual(len(commits) - 1, self.m.summary["repositories"][0]["commits"])
        for rel in ["data/people.tsv", "data/areas.tsv", "data/files.tsv", "branches.tsv", "report.html", "run.json"]:
            self.assertTrue((self.m.out / rel).exists(), rel)

    def test_one_brief_per_chapter(self):
        chapters = self.m.json("data/timeline.json")["chapters"]
        briefs = sorted((self.m.out / "briefs").glob("chapter-*.md"))
        self.assertEqual(len(briefs), len(chapters))
        text = briefs[-1].read_text()
        self.assertNotIn("{", text.split("## Return exactly this shape")[0].replace("{FROM}", ""))  # every placeholder filled

    def test_html_is_static(self):
        page = self.m.text("report.html")
        self.assertNotIn("<script", page)
        self.assertNotIn("http://", page)
        self.assertIn("<svg", page)


if __name__ == "__main__":
    unittest.main()
