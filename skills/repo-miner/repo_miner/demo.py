"""An invented repository with a messy history, and a check that the miner sees what was planted in it.

`harbour` is a small payments service. Its default branch hides most of the work; a founder went quiet and owned one area
alone; a legacy importer was built and removed; a change was reverted two hours later; a feature branch was abandoned; an
unrelated history sits beside it; a .env file with a token was committed and removed; a seven-month silence; a reformat
that touched every file; and then an AI agent arrives. Secrets are planted in files, messages and paths: none may reach
the output.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Optional

TOKEN = "ghp_" + "Zx9Kq2Lm" * 4
EMAIL = "ana.costa@harbour-payments.invalid"
CODENAME = "Kraken"
HOME = "/home/anacosta/work/harbour"


class Repo:
    def __init__(self, path: Path):
        self.path = path
        path.mkdir(parents=True)
        self.git("init", "-q", "-b", "main")
        self.git("config", "commit.gpgsign", "false")

    def git(self, *args: str, author: str = "Ana Costa", when: str = "2023-01-02T09:00:00+00:00") -> str:
        env = dict(os.environ, GIT_AUTHOR_NAME=author, GIT_AUTHOR_EMAIL="dev@example.com", GIT_COMMITTER_NAME=author,
                   GIT_COMMITTER_EMAIL="dev@example.com", GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when,
                   GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
        return subprocess.run(["git", "-C", str(self.path), *args], check=True, capture_output=True, text=True, env=env).stdout

    def commit(self, when: str, message: str, author: str = "Ana Costa", write: Optional[Dict[str, str]] = None,
               delete=(), binary: Optional[Dict[str, bytes]] = None) -> str:
        for rel, text in (write or {}).items():
            p = self.path / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
        for rel, data in (binary or {}).items():
            p = self.path / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        for rel in delete:
            self.git("rm", "-rq", rel)
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", message, author=author, when=when)
        return self.git("rev-parse", "HEAD").strip()


def day(d: str, h: int = 10) -> str:
    return f"{d}T{h:02d}:00:00+00:00"


def build(root: Path) -> Path:
    r = Repo(root / "harbour")
    modules = {f"src/pkg/m{i:02d}.py": f"def f{i}():\n    return {i}\n" for i in range(45)}
    legacy = {f"src/legacy/importer_{i}.py": f"# legacy importer {i}\n" for i in range(7)}
    r.commit(day("2023-01-02"), "Initial import", write={
        "README.md": f"# Harbour\n\nPayments for small ports. Codename {CODENAME}.\n\nContact {EMAIL}. Notes in {HOME}/notes.\n",
        ".travis.yml": "language: python\nscript: pytest\n", "src/app.py": "print('harbour')\n", **modules, **legacy})
    r.git("tag", "v0.1", when=day("2023-01-02", 11))
    r.commit(day("2023-01-03"), "Add API skeleton", write={"src/api/routes.py": "routes = []\n"})
    r.commit(day("2023-01-04"), "Add ARCHITECTURE notes", write={"docs/ARCHITECTURE.md": "# Architecture\n\n- Never call billing from the API directly.\n"})
    r.git("checkout", "-q", "-b", "develop", when=day("2023-01-05"))

    k = 0
    for week in range(22):                                    # January to June 2023: Ana on the API and legacy, Ben on billing
        d = f"2023-{1 + (week + 1) // 4:02d}-{1 + 7 * ((week + 1) % 4):02d}"
        r.commit(day(d, 9), f"Billing: ledger step {week}", author="Ben Okafor",
                 write={"src/billing/ledger.py": f"STEP = {week}\n", f"src/billing/rule_{week % 5}.py": f"R = {week}\n"})
        r.commit(day(d, 11), "fix: route ordering bug" if week % 3 == 0 else f"API: endpoint {week}",
                 write={"src/api/routes.py": f"routes = {list(range(week + 1))}\n"})
        if week % 4 == 1:
            r.commit(day(d, 14), "Legacy importer: handle CSV dialect", write={f"src/legacy/importer_{week % 7}.py": f"# v{week}\n"})
        if week % 5 == 2:
            r.commit(day(d, 16), "wip", write={"src/app.py": f"print('harbour {week}')\n"})
        k += 1

    r.commit(day("2023-04-11"), "Add local settings", author="Ben Okafor", write={".env": f"GITHUB_TOKEN={TOKEN}\n"})
    r.commit(day("2023-04-12"), "Remove local settings", author="Ben Okafor", delete=[".env"])
    retry = r.commit(day("2023-05-09", 10), "Add retry to payments", write={"src/billing/retry.py": "RETRIES = 5\n"}, author="Ben Okafor")
    r.commit(day("2023-05-09", 12), 'Revert "Add retry to payments"', author="Ben Okafor", delete=["src/billing/retry.py"])
    # make the revert body say what git says
    r.git("commit", "-q", "--amend", "-m", f'Revert "Add retry to payments"\n\nThis reverts commit {retry}.\n\npassword = hunter2hunter2hunter2',
          author="Ben Okafor", when=day("2023-05-09", 12))
    r.commit(day("2023-05-20"), "Add demo video", binary={"assets/demo.mp4": bytes(range(256)) * 24_000})

    r.git("checkout", "-q", "-b", "feature/export", when=day("2023-03-01"))
    for i in range(8):
        r.commit(day(f"2023-03-{2 + i:02d}"), f"Export: CSV writer part {i}", write={"src/export/csv.py": f"PART = {i}\n"})
    r.git("checkout", "-q", "develop")

    # a seven-month silence, then a new person, a reformat, the legacy importer removed, CI moved
    r.commit(day("2024-02-05"), "Reformat with black", author="Cara Lindqvist",
             write={**{p: t + "\n" for p, t in modules.items()}, "src/app.py": "print('harbour')\n\n"})
    r.commit(day("2024-02-12"), "Remove legacy importer (replaced by the export service)", author="Cara Lindqvist", delete=["src/legacy"])
    r.commit(day("2024-02-13"), "Move CI to GitHub Actions", author="Cara Lindqvist", delete=[".travis.yml"],
             write={".github/workflows/ci.yml": "name: ci\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: pytest\n"})
    r.commit(day("2024-02-14"), "Add agent instructions", author="Cara Lindqvist",
             write={"CLAUDE.md": "# Working here\n\n- Always run pytest before committing.\n- Never touch src/billing without Ben.\n"})
    for i in range(30):                                       # March to May 2024: an agent and the people working with it
        d = f"2024-{3 + i // 12:02d}-{1 + (i % 12) * 2:02d}"
        if i % 3 == 0:
            r.commit(day(d, 10), f"Settlement: batch window {i}\n\nClaude-Session: https://claude.ai/code/session_demo{i % 2}",
                     author="Claude", write={"src/settle/batch.py": f"W = {i}\n"})
        else:
            who = "Cara Lindqvist" if i % 3 == 1 else "Ana Costa"
            r.commit(day(d, 15), f"Settlement: reconcile step {i}\n\nCo-Authored-By: Claude <noreply@anthropic.com>",
                     author=who, write={f"src/settle/step_{i % 4}.py": f"S = {i}\n"})
        if i % 7 == 3:
            r.commit(day(d, 17), "fix: route ordering bug again", author="Cara Lindqvist", write={"src/api/routes.py": f"routes = [{i}]\n"})

    r.git("checkout", "-q", "--orphan", "experiments", when=day("2023-08-01"))
    r.git("rm", "-rqf", ".")
    for i in range(3):
        r.commit(day(f"2023-08-0{1 + i}"), f"Notebook {i}", write={f"notebooks/n{i}.md": f"# Try {i}\n"})
    r.git("checkout", "-q", "main")
    return r.path


EXPECT = {  # finding id prefix -> what it shows
    "branch-trap": "the default branch hides most of the work",
    "sensitive:.env": "a .env file was committed",
    "quiet:Ben Okafor": "a founder went quiet",
    "single-owner": "one area rests on one person",
    "graveyard:src/legacy": "the legacy importer was removed",
    "reverts": "a change was reverted",
    "unmerged:feature/export": "a branch was abandoned",
    "orphan:experiments": "an unrelated history",
    "fix-hotspots": "a file keeps needing fixes",
    "sweep:": "a reformat touched many files",
    "silence:": "a seven-month silence",
    "agents": "AI agents arrive",
    "large-blobs": "a large file in history",
}
PLANTED = [TOKEN, EMAIL, CODENAME, "anacosta", "hunter2hunter2"]


def run(keep: bool = False) -> int:
    from .miner import Options, mine
    tmp = Path(tempfile.mkdtemp(prefix="repo-miner-demo-"))
    problems = []
    try:
        repo = build(tmp / "src")
        deny = tmp / "deny.txt"
        deny.write_text(CODENAME + "\n")
        result = mine(Options([str(repo)], out=str(tmp / "out"), deny_file=str(deny), quiet=True))
        import json
        found = [f["id"] for f in json.loads((tmp / "out" / "findings.json").read_text())]
        for prefix, what in EXPECT.items():
            ok = any(f.startswith(prefix) for f in found)
            print(f"{'ok  ' if ok else 'FAIL'} {what}")
            ok or problems.append(what)
        text = "".join(p.read_text(errors="ignore") for p in (tmp / "out").rglob("*") if p.is_file())
        leaked = [s for s in PLANTED if s in text]
        print(f"{'ok  ' if not leaked else 'FAIL'} no planted secret, address, codename or home path in the output")
        leaked and problems.append("leak")
        clean = result["leak_scan"] == "clean"
        print(f"{'ok  ' if clean else 'FAIL'} leak scan clean")
        clean or problems.append("scan")
        if keep:
            print(f"kept: {tmp}\nreport: {tmp / 'out' / 'REPORT.md'}")
    finally:
        if not keep:
            shutil.rmtree(tmp, ignore_errors=True)
    print("demo: clean" if not problems else f"demo: {len(problems)} problem(s)")
    return 1 if problems else 0
