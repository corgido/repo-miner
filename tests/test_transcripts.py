"""Claude Code transcripts: only what a person typed and what an agent visibly said is read, it is redacted, and the
session running the miner is left out."""
import json
import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from helpers import demo
from repo_miner import transcripts
from repo_miner.miner import Options, mine

SECRET = "sk-" + "Q" * 30


def line(kind, text, when, **extra):
    content = [{"type": "text", "text": text}] if kind == "assistant" else text
    return json.dumps({"type": kind, "uuid": f"{kind}-{when}-{len(text)}", "timestamp": when, "sessionId": extra.pop("session", "s1"),
                       "message": {"content": content}, **extra})


class TranscriptsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="repo-miner-sessions-"))
        self.repo = demo.build(self.tmp / "src")
        self.home = self.tmp / "home"
        folder = self.home / ".claude" / "projects" / transcripts.re.sub(r"[^A-Za-z0-9]", "-", str(self.repo.resolve()))
        folder.mkdir(parents=True)
        old = folder / "old-session.jsonl"
        old.write_text("\n".join([
            line("user", "Why does the billing ledger need a retry? I think the settlement window is too short.", "2024-03-02T10:00:00Z",
                 origin={"kind": "human"}),
            line("assistant", f"Because the bank API times out. I will add a retry. Key {SECRET}", "2024-03-02T10:01:00Z"),
            line("assistant", "", "2024-03-02T10:02:00Z"),
            json.dumps({"type": "assistant", "uuid": "t1", "timestamp": "2024-03-02T10:03:00Z",
                        "message": {"content": [{"type": "thinking", "thinking": "private reasoning here"},
                                                {"type": "tool_use", "name": "Bash", "input": {"command": "cat .env"}}]}}),
            line("user", "<system-reminder>injected</system-reminder>", "2024-03-02T10:04:00Z", isMeta=True),
        ]) + "\n")
        past = time.time() - 3600
        os.utime(old, (past, past))
        (folder / "live-session.jsonl").write_text(line("user", "Use repo-miner on this repository and tell me what happened.",
                                                        "2026-10-28T09:00:00Z", origin={"kind": "human"}, session="live") + "\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_miner(self, env):
        with mock.patch.dict(os.environ, {"HOME": str(self.home), **env}):    # restored afterwards, popped keys too
            os.environ.pop("CLAUDE_CODE_SESSION_ID", None)
            return mine(Options([str(self.repo)], out=str(self.tmp / "out"), quiet=True))

    def test_reads_people_and_replies_only_and_skips_the_live_session(self):
        self.run_miner({"CLAUDECODE": "1"})
        out = self.tmp / "out"
        report = (out / "REPORT.md").read_text()
        self.assertIn("Agent sessions", report)
        everything = "".join(p.read_text(errors="ignore") for p in out.rglob("*") if p.is_file())
        self.assertNotIn(SECRET, everything)
        self.assertNotIn("private reasoning", everything)
        self.assertNotIn("cat .env", everything)
        self.assertNotIn("Use repo-miner on this repository", everything)   # the live session is not history
        chapters = json.loads((out / "data" / "timeline.json").read_text())["chapters"]
        self.assertLessEqual(chapters[-1]["to"], "2024-05-11")

    def test_read_classifies_events(self):
        folder = next((self.home / ".claude" / "projects").iterdir())
        with mock.patch.dict(os.environ, {"CLAUDECODE": "1"}):
            events = transcripts.read(folder, "sessions")
        kinds = sorted((e["role"], e["kind"]) for e in events)
        self.assertEqual(kinds, [("agent", "reply"), ("human", "message"), ("system", "injected")])
        self.assertEqual([e["text"] for e in events if e["role"] == "system"], [""])

    def test_none_turns_them_off(self):
        with mock.patch.dict(os.environ, {"HOME": str(self.home)}):
            mine(Options([str(self.repo)], out=str(self.tmp / "out"), transcripts="none", quiet=True))
        self.assertNotIn("Agent sessions", (self.tmp / "out" / "REPORT.md").read_text())


if __name__ == "__main__":
    unittest.main()
