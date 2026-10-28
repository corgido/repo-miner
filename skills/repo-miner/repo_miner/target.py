"""Turn what the person typed into repositories on disk: a repository, a folder of repositories, or a git URL to clone."""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .gitlog import is_repo

URL = re.compile(r"^(?:https?://|ssh://|git@|file://)")


@dataclass
class Source:
    name: str
    path: Path
    cloned_from: Optional[str] = None   # the URL, when the miner made the clone itself


def is_url(target: str) -> bool:
    return bool(URL.match(target))


def repo_name(target: str) -> str:
    tail = target.rstrip("/").split("/")[-1].split(":")[-1]
    return tail[:-4] if tail.endswith(".git") else tail


def clone(url: str, into: Path, depth: Optional[int] = None, log=print) -> Path:
    """Clone every branch (not just the default) so work hidden off the default branch is seen. Read-only afterwards."""
    if (into / ".git").exists() or (into / "HEAD").exists():
        log(f"  updating the clone in {into}")
        subprocess.run(["git", "-C", str(into), "fetch", "--quiet", "--prune", "--tags", "origin"], check=False)
        return into
    into.parent.mkdir(parents=True, exist_ok=True)
    args = ["git", "clone", "--quiet", "--no-single-branch", "--no-checkout"]
    if depth:
        args += ["--depth", str(depth)]
    log(f"  cloning {url} (every branch{f', depth {depth}' if depth else ''})")
    proc = subprocess.run([*args, url, str(into)], capture_output=True, text=True)
    if proc.returncode:
        raise SystemExit(f"repo-miner: could not clone {url}:\n{proc.stderr.strip()}")
    return into


def resolve(targets: List[str], clones: Path, depth: Optional[int] = None, log=print) -> List[Source]:
    """Every repository the targets name. A folder that is not a repository is searched one and two levels down."""
    found: List[Source] = []
    for target in targets:
        if is_url(target):
            name = repo_name(target)
            found.append(Source(name, clone(target, clones / name, depth, log), cloned_from=target))
            continue
        path = Path(target).expanduser().resolve()
        if not path.exists():
            raise SystemExit(f"repo-miner: {target} does not exist")
        if is_repo(path):
            top = Path(subprocess.run(["git", "-C", str(path), "rev-parse", "--show-toplevel"],
                                      capture_output=True, text=True).stdout.strip() or path)
            found.append(Source(top.name, top))
            continue
        nested = [p for p in sorted(path.iterdir()) if p.is_dir() and not p.name.startswith(".")]
        repos = [p for p in nested if is_repo(p)]
        for folder in (p for p in nested if p not in repos):
            repos += [q for q in sorted(folder.iterdir()) if q.is_dir() and (q / ".git").exists()]
        if not repos:
            raise SystemExit(f"repo-miner: no git repository at or under {target}")
        found += [Source(p.name, p) for p in repos]
    # two repositories with one folder name: tell them apart by their parent
    seen = {}
    for s in found:
        seen.setdefault(s.name, []).append(s)
    for same in (v for v in seen.values() if len(v) > 1):
        for s in same:
            s.name = f"{s.path.parent.name}-{s.name}"
    return found
