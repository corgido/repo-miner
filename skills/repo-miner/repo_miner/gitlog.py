"""Read a git repository: its refs, its tags and every commit on every ref, in one pass.

Nothing here writes to the repository or runs its code. Author e-mail addresses are read only to tell people apart
(one person, several spellings of their name) and are never written anywhere.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class GitError(RuntimeError):
    pass


def git(repo: Path, *args: str, check: bool = False) -> str:
    """Run git in `repo` and return stdout. With check=False a failing command returns ''."""
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=_quiet_env(),
    )
    if check and proc.returncode:
        raise GitError(f"git {' '.join(args)}: {proc.stderr.strip()}")
    return proc.stdout if proc.returncode == 0 else ""


def _quiet_env() -> Dict[str, str]:
    import os
    env = dict(os.environ)
    env.update(GIT_TERMINAL_PROMPT="0", GIT_PAGER="cat", LC_ALL="C")
    return env


def is_repo(path: Path) -> bool:
    return git(path, "rev-parse", "--git-dir").strip() != ""


# ─────────────────────────────────────────────────────────────── refs


@dataclass
class Ref:
    name: str            # short branch name, without the remote: "main", "feature/x"
    full: str            # "refs/remotes/origin/main" or "refs/heads/main"
    sha: str
    time: int            # tip commit time (unix)
    local_only: bool = False
    unpushed: int = 0    # commits on the local branch that its remote counterpart lacks


def branches(repo: Path) -> List[Ref]:
    """Every branch, local and remote-tracking, one entry per branch name, newest tip first.

    When a branch exists both locally and on a remote, the remote copy is the record and the local copy only adds
    `unpushed` (commits nobody else can see). A local branch with no remote copy is `local_only` when a remote exists.
    """
    out = git(repo, "for-each-ref", "--format=%(refname)%00%(objectname)%00%(committerdate:unix)", "refs/heads", "refs/remotes")
    local: Dict[str, Ref] = {}
    remote: Dict[str, Ref] = {}
    for line in out.splitlines():
        full, sha, t = line.split("\0")
        if full.endswith("/HEAD"):
            continue
        if full.startswith("refs/heads/"):
            name = full[len("refs/heads/"):]
            local[name] = Ref(name, full, sha, int(t or 0))
        else:
            name = full[len("refs/remotes/"):].split("/", 1)[-1]
            # prefer origin when several remotes carry the same branch
            if name not in remote or full.startswith("refs/remotes/origin/"):
                remote[name] = Ref(name, full, sha, int(t or 0))
    refs: Dict[str, Ref] = dict(remote)
    for name, ref in local.items():
        if name in remote:
            if ref.sha != remote[name].sha:
                n = git(repo, "rev-list", "--count", f"{remote[name].full}..{ref.full}").strip()
                remote[name].unpushed = int(n or 0)
        else:
            ref.local_only = bool(remote)
            refs[name] = ref
    return sorted(refs.values(), key=lambda r: (-r.time, r.name))


def default_branch(repo: Path, refs: List[Ref]) -> Optional[Ref]:
    by_name = {r.name: r for r in refs}
    head = git(repo, "symbolic-ref", "--short", "refs/remotes/origin/HEAD").strip()
    candidates = [head.split("/", 1)[-1] if head else "", "main", "master", git(repo, "branch", "--show-current").strip()]
    for c in candidates:
        if c and c in by_name:
            return by_name[c]
    return refs[0] if refs else None


@dataclass
class Tag:
    name: str
    time: int
    sha: str


def tags(repo: Path) -> List[Tag]:
    out = git(repo, "for-each-ref", "--sort=creatordate", "--format=%(refname:short)%00%(creatordate:unix)%00%(objectname)", "refs/tags")
    rows = []
    for line in out.splitlines():
        name, t, sha = line.split("\0")
        rows.append(Tag(name, int(t or 0), sha))
    return rows


def clone_health(repo: Path) -> Dict[str, object]:
    """What a reader must know before trusting the history: is it shallow, does it track every branch, is there a remote?"""
    fetch = git(repo, "config", "--get-all", "remote.origin.fetch").split()
    return {
        "shallow": git(repo, "rev-parse", "--is-shallow-repository").strip() == "true",
        "has_remote": bool(git(repo, "remote").strip()),
        "single_branch": bool(fetch) and not any("*" in f for f in fetch),
    }


def remote_url(repo: Path) -> Optional[str]:
    """The origin URL with any credentials removed, or None."""
    url = git(repo, "remote", "get-url", "origin").strip()
    if not url:
        return None
    if "@" in url and "://" in url:
        scheme, rest = url.split("://", 1)
        url = f"{scheme}://{rest.split('@', 1)[1]}"
    return url


def web_url(remote: Optional[str]) -> Optional[str]:
    """https://host/owner/repo for GitHub, GitLab and similar remotes, so a report can link commits."""
    if not remote:
        return None
    url = remote
    if url.startswith("git@"):
        host, path = url[4:].split(":", 1)
        url = f"https://{host}/{path}"
    if not url.startswith("http"):
        return None
    return url[:-4] if url.endswith(".git") else url


# ─────────────────────────────────────────────────────────────── commits


@dataclass
class Change:
    path: str
    status: str          # A, M, D, T (merges carry no changes)
    added: int = 0
    removed: int = 0
    binary: bool = False


@dataclass
class Commit:
    sha: str
    parents: List[str]
    time: int
    author: str
    subject: str
    body: str
    changes: List[Change] = field(default_factory=list)
    email: str = field(default="", repr=False)   # identity only; never written

    @property
    def short(self) -> str:
        return self.sha[:9]

    @property
    def is_merge(self) -> bool:
        return len(self.parents) > 1

    @property
    def lines(self) -> int:
        return sum(c.added + c.removed for c in self.changes)


_SEP_COMMIT, _SEP_FIELD, _SEP_END = "\x1e", "\x1f", "\x1d"


def commits(repo: Path, since: Optional[str] = None, until: Optional[str] = None) -> List[Commit]:
    """Every commit reachable from any ref, oldest first by author time, with the files each one changed.

    Renames are read as a delete and an add (cheaper, and the report says so). `.mailmap` is honoured (%aN).
    """
    fmt = _SEP_COMMIT + _SEP_FIELD.join(["%H", "%P", "%at", "%aN", "%aE", "%s", "%b"]) + _SEP_END
    args = ["log", "--all", "--no-renames", "--raw", "--numstat", "--date-order", "--reverse", f"--format={fmt}"]
    if since:
        args.append(f"--since={since}")
    if until:
        args.append(f"--until={until}")
    out = git(repo, *args)
    result: List[Commit] = []
    for chunk in out.split(_SEP_COMMIT)[1:]:
        head, _, tail = chunk.partition(_SEP_END)
        sha, parents, at, author, email, subject, body = head.split(_SEP_FIELD)
        changes: Dict[str, Change] = {}
        for line in tail.splitlines():
            if line.startswith(":"):
                meta, _, path = line.partition("\t")
                status = meta.split()[-1][:1]
                changes[path] = Change(path, status)
            elif line and line[0] in "0123456789-":
                parts = line.split("\t", 2)
                if len(parts) != 3:
                    continue
                a, r, path = parts
                ch = changes.setdefault(path, Change(path, "M"))
                ch.binary = a == "-"
                ch.added = int(a) if a.isdigit() else 0
                ch.removed = int(r) if r.isdigit() else 0
        result.append(Commit(sha, parents.split(), int(at), author, subject, body.strip(), list(changes.values()), email.lower()))
    # git keeps parents before children, so commits with hand-set or rebased dates arrive out of time order
    result.sort(key=lambda c: c.time)
    return result


def count(repo: Path, rev_range: str) -> int:
    return int(git(repo, "rev-list", "--count", rev_range).strip() or 0)


def tree(repo: Path, ref: str) -> List[tuple]:
    """(path, size in bytes) for every file at `ref`."""
    rows = []
    for line in git(repo, "ls-tree", "-r", "-l", "--full-tree", ref).splitlines():
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if len(parts) >= 4 and parts[1] == "blob":
            rows.append((path, int(parts[3]) if parts[3].isdigit() else 0))
    return rows


def show(repo: Path, ref: str, path: str) -> str:
    return git(repo, "show", f"{ref}:{path}")


def large_blobs(repo: Path, threshold: int = 5_000_000, limit: int = 20) -> List[tuple]:
    """(size, path) of the largest blobs ever committed on any ref above `threshold` bytes."""
    objects = git(repo, "rev-list", "--objects", "--all")
    if not objects:
        return []
    proc = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "--batch-check=%(objecttype)\t%(objectsize)\t%(rest)"],
        input=objects, capture_output=True, text=True, encoding="utf-8", errors="replace", env=_quiet_env(),
    )
    found: Dict[str, int] = {}
    for line in proc.stdout.splitlines():
        kind, _, rest = line.partition("\t")
        size, _, path = rest.partition("\t")
        if kind == "blob" and size.isdigit() and int(size) >= threshold and path:
            found[path] = max(found.get(path, 0), int(size))
    return sorted(((s, p) for p, s in found.items()), reverse=True)[:limit]
