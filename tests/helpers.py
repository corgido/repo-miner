"""Shared set-up: import the package from the skill folder, and build the demo repository once per test module."""
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "repo-miner"))

from repo_miner import demo  # noqa: E402
from repo_miner.miner import Options, mine  # noqa: E402


class Mined:
    """The demo repository, mined once with the deny list. Remove with .close()."""

    def __init__(self, **options):
        self.tmp = Path(tempfile.mkdtemp(prefix="repo-miner-test-"))
        self.repo = demo.build(self.tmp / "src")
        self.deny = self.tmp / "deny.txt"
        self.deny.write_text(demo.CODENAME + "\n")
        self.out = self.tmp / "out"
        self.summary = mine(Options([str(self.repo)], out=str(self.out), deny_file=str(self.deny), quiet=True, **options))

    def json(self, rel: str):
        return json.loads((self.out / rel).read_text())

    def text(self, rel: str) -> str:
        return (self.out / rel).read_text()

    def everything(self) -> str:
        return "".join(p.read_text(errors="ignore") for p in self.out.rglob("*") if p.is_file())

    def finding(self, prefix: str):
        return next((f for f in self.json("findings.json") if f["id"].startswith(prefix)), None)

    def close(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
