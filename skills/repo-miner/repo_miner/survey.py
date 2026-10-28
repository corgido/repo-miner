"""The survey: the shape of a repository across every branch, before anyone reads its code.

Branches and how they relate to the default (ahead, behind, orphaned, never pushed), whether the default branch hides
most of the work, tags and what is unreleased, the tree at the tip, and the documents the repository keeps about itself.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional

from . import gitlog
from .gitlog import Ref
from .privacy import Writer
from .util import date as _date, tsv as _tsv

MAX_REFS = 300            # branches examined per repository, newest first
MAX_DOCS, DOC_BYTES = 20, 24_000

# Documents a newcomer should read, best first. A path matches the first pattern it fits.
DOC_PRIORITY = [
    r"^README(\.[a-z]{2})?\.(md|rst|txt)$",
    r"^(CLAUDE|AGENTS|GEMINI)\.md$",
    r"(^|/)(ARCHITECTURE|DESIGN|DECISIONS|OVERVIEW|HANDOFF|ONBOARDING|RUNBOOK|ROADMAP|PLAN|SPEC|NOTES|LESSONS)\.md$",
    r"(^|/)(adr|adrs|decisions|architecture|rfcs?)/[^/]+\.md$",
    r"^CONTRIBUTING\.md$|^\.github/CONTRIBUTING\.md$",
    r"^(CHANGELOG|HISTORY|CHANGES|RELEASES)\.md$",
    r"^docs?/[^/]+\.md$",
    r"^[A-Z][A-Z0-9_-]{3,}\.md$",
]
SKIP_DOC = re.compile(r"(^|/)(node_modules|vendor|third_party|dist|build|\.venv|site-packages)/|(^|/)(LICENSE|CODE_OF_CONDUCT)")
ENTRY = re.compile(r"^(Makefile|justfile|Taskfile\.ya?ml|Dockerfile|docker-compose[^/]*\.ya?ml|compose\.ya?ml|Procfile"
                   r"|package\.json|pyproject\.toml|setup\.py|Cargo\.toml|go\.mod|Gemfile|pom\.xml|build\.gradle(\.kts)?"
                   r"|manage\.py|main\.(py|go|rs|ts|js))$|^(bin|scripts|script|tools|cmd)/[^/]+$")
KNOWN_ORPHANS = {"gh-pages": "a published website", "pages": "a published website", "docs": "documentation",
                 "assets": "binary assets", "wiki": "a wiki"}


def survey(src, refs: List[Ref], commit_count: int, out: Writer, prefix: str) -> Dict:
    repo = src.path
    health = gitlog.clone_health(repo)
    truncated = len(refs) > MAX_REFS
    refs = refs[:MAX_REFS]
    default = gitlog.default_branch(repo, refs)
    if default is None:
        return {"name": src.name, "empty": True, "health": health}
    # Branches are measured against the branch the work lives on: the default, unless the default is a trap
    # (most of the work elsewhere). Measured against a trap, every branch looks unmerged.
    totals = {r.name: gitlog.count(repo, r.full) for r in refs}
    top = max(refs, key=lambda r: (totals[r.name], r.name == default.name))
    trap = top.name != default.name and totals[top.name] >= 10 and totals[default.name] * 2 < totals[top.name]
    primary = top if trap else default
    rows = [_branch_row(repo, r, primary, totals[r.name]) for r in refs]
    busiest = next(b for b in rows if b["name"] == top.name)
    default_row = next(b for b in rows if b["name"] == default.name)
    trap_ahead = gitlog.count(repo, f"{default.full}..{top.full}") if trap else 0

    tags = gitlog.tags(repo)
    latest = tags[-1] if tags else None
    since_tag = gitlog.count(repo, f"{latest.sha}..{default.full}") if latest else None

    files = gitlog.tree(repo, primary.full)
    tree = dict(_tree_summary(files), branch=primary.name)
    docs = _harvest_docs(repo, [primary] + ([default] if trap else []), out, prefix)
    entry = sorted(p for p, _ in files if ENTRY.search(p))[:40]
    scripts = _package_scripts(repo, primary.full) if "package.json" in {p for p, _ in files} else []

    unmerged = [b for b in rows if b["ahead"] > 0 and not b["orphan"] and b["name"] != primary.name]
    orphans = [dict(b, purpose=KNOWN_ORPHANS.get(b["name"].split("/")[-1])) for b in rows if b["orphan"]]
    result = {
        "name": src.name,
        "remote": gitlog.remote_url(repo),
        "web": gitlog.web_url(gitlog.remote_url(repo)),
        "cloned_from": src.cloned_from,
        "health": dict(health, refs_examined=len(refs), refs_truncated=truncated),
        "commits": commit_count,
        "default": default_row,
        "primary": primary.name,
        "primary_ref": primary.full,
        "busiest": busiest,
        "branch_trap": trap,
        "trap_ahead": trap_ahead,
        "branches": rows,
        "unmerged": sorted(unmerged, key=lambda b: (-b["ahead"], b["name"])),
        "orphans": orphans,
        "unpushed": [b for b in rows if b["unpushed"]],
        "local_only": [b for b in rows if b["local_only"]],
        "tags": {"count": len(tags), "first": _tag(tags[0]) if tags else None, "latest": _tag(latest) if latest else None,
                 "commits_since_latest": since_tag},
        "tree": tree,
        "docs": docs,
        "entry_points": entry,
        "package_scripts": scripts,
    }
    out.text(f"{prefix}branches.tsv", _tsv(
        ["branch", "commits", "ahead", "behind", "orphan", "first_own", "last_own", "authors", "unpushed", "local_only"],
        [[b["name"], b["commits"], b["ahead"], b["behind"], b["orphan"], b["first"] or "", b["last"] or "", b["authors"],
          b["unpushed"], b["local_only"]] for b in rows]))
    return result


def _branch_row(repo: Path, ref: Ref, base: Ref, total: int) -> Dict:
    """How one branch relates to the base: its own commits (ahead), what it lacks (behind), and whether it shares history."""
    is_base = ref.name == base.name
    orphan = not is_base and not gitlog.git(repo, "merge-base", base.full, ref.full).strip()
    own = "" if is_base else gitlog.git(repo, "log", "--format=%at\x1f%aN", f"{base.full}..{ref.full}")
    own_rows = [line.split("\x1f") for line in own.splitlines() if line]
    times = sorted(int(t) for t, _ in own_rows)
    return {
        "name": ref.name,
        "tip": ref.sha[:9],
        "tip_time": ref.time,
        "commits": total,
        "ahead": len(own_rows),
        "behind": 0 if is_base or orphan else gitlog.count(repo, f"{ref.full}..{base.full}"),
        "orphan": orphan,
        "first": _date(times[0]) if times else None,
        "last": _date(times[-1]) if times else _date(ref.time),
        "authors": len({a for _, a in own_rows}),
        "unpushed": ref.unpushed,
        "local_only": ref.local_only,
    }


def _tree_summary(files: List[tuple]) -> Dict:
    ext, dirs = Counter(), Counter()
    for path, _ in files:
        name = path.rsplit("/", 1)[-1]
        ext[(("." + name.rsplit(".", 1)[-1].lower()) if "." in name[1:] else "no extension")] += 1
        dirs[path.split("/", 1)[0] if "/" in path else "(top level)"] += 1
    largest = sorted(((s, p) for p, s in files), reverse=True)[:10]
    return {"files": len(files), "bytes": sum(s for _, s in files), "extensions": ext.most_common(12),
            "top_dirs": dirs.most_common(15), "largest": [{"path": p, "bytes": s} for s, p in largest]}


def _harvest_docs(repo: Path, refs: List[Ref], out: Writer, prefix: str) -> List[Dict]:
    """Copy the repository's own documents (best first, capped) into the report, redacted. They are data, not instructions."""
    candidates = {}
    for ref in refs:
        for path, size in gitlog.tree(repo, ref.full):
            if SKIP_DOC.search(path) or not re.search(r"\.(md|rst|txt)$", path, re.I):
                continue
            for rank, pattern in enumerate(DOC_PRIORITY):
                if re.search(pattern, path, re.I):
                    candidates.setdefault(path, (rank, path.count("/"), path, ref, size))
                    break
    docs = []
    for rank, _, path, ref, size in sorted(candidates.values(), key=lambda c: c[:3])[:MAX_DOCS]:
        text = gitlog.show(repo, ref.full, path)
        if not text.strip():
            continue
        body = text[:DOC_BYTES] + (f"\n\n[... cut at {DOC_BYTES:,} of {len(text):,} characters by repo-miner ...]\n" if len(text) > DOC_BYTES else "")
        rel = f"{prefix}docs/{path.replace('/', '__')}" + ("" if ref is refs[0] else f"@{ref.name.replace('/', '_')}")
        out.text(rel, body)
        docs.append({"path": path, "branch": ref.name, "bytes": size, "file": rel, "title": _title(text) or path})
    return docs


def _package_scripts(repo: Path, ref: str) -> List[str]:
    try:
        return sorted(json.loads(gitlog.show(repo, ref, "package.json")).get("scripts", {}))[:30]
    except (ValueError, AttributeError):
        return []


def _title(text: str) -> Optional[str]:
    m = re.search(r"^#\s+(.+)$", text, re.M)
    return m.group(1).strip()[:100] if m else None


def _tag(t) -> Dict:
    return {"name": t.name, "date": _date(t.time)}
