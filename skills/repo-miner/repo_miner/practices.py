"""How the team works, as the repository records it: CI, ownership, contribution rules, hooks, linters, dependency bots,
release tooling, and the instructions and tooling given to AI agents.

A practice is current when it exists on some branch and its last change, on any branch, was not a deletion. Superseded
practices are listed with the commit that removed them, so "they used to run Travis" is visible, but their text is not shown.
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Dict, List

from . import gitlog
from .gitlog import Commit, Ref
from .privacy import Writer
from .util import date

KINDS = [  # kind, pattern on the path, what it tells a newcomer
    ("ci", r"^\.github/workflows/[^/]+\.ya?ml$|^\.gitlab-ci\.yml$|^\.circleci/config\.ya?ml$|^\.travis\.yml$|^Jenkinsfile$"
           r"|^azure-pipelines\.ya?ml$|^\.buildkite/[^/]+\.ya?ml$|^bitbucket-pipelines\.yml$|^appveyor\.ya?ml$|^\.drone\.ya?ml$",
     "what runs on every push or pull request"),
    ("ownership", r"^(\.github/|docs/)?CODEOWNERS$|^OWNERS$|^MAINTAINERS(\.md)?$", "who must review what"),
    ("contributing", r"^(\.github/)?(CONTRIBUTING|SECURITY)\.md$|^\.github/(PULL_REQUEST_TEMPLATE|pull_request_template)(\.md|/[^/]+\.md)$"
                     r"|^\.github/ISSUE_TEMPLATE/[^/]+$", "how changes are proposed and reviewed"),
    ("git-hooks", r"^\.husky/[^/_][^/]*$|^\.pre-commit-config\.ya?ml$|^\.githooks/[^/]+$|^lefthook\.ya?ml$|^\.lintstagedrc[^/]*$",
     "checks that run before a commit"),
    ("quality", r"^(\.eslintrc[^/]*|eslint\.config\.[cm]?[jt]s|\.prettierrc[^/]*|prettier\.config\.[cm]?js|biome\.jsonc?|ruff\.toml"
                r"|\.ruff\.toml|\.flake8|mypy\.ini|\.pylintrc|\.golangci\.ya?ml|\.rubocop\.yml|\.editorconfig|\.stylelintrc[^/]*"
                r"|rustfmt\.toml|\.clang-format|\.swiftlint\.yml)$", "linters and formatters the code is held to"),
    ("dependencies", r"^\.github/dependabot\.ya?ml$|^renovate\.json5?$|^\.renovaterc(\.json)?$|^\.github/renovate\.json5?$",
     "bots that keep dependencies current"),
    ("release", r"^\.goreleaser\.ya?ml$|^\.releaserc[^/]*$|^release\.config\.[cm]?js$|^release-please-config\.json$"
                r"|^\.changeset/config\.json$|^\.release-it\.json$", "how releases are cut"),
    ("agent-instructions", r"(^|/)(CLAUDE|AGENTS|GEMINI)\.md$|^\.cursorrules$|^\.cursor/rules/[^/]+$|^\.github/copilot-instructions\.md$"
                           r"|^\.windsurfrules$|^\.clinerules$", "standing instructions to AI coding agents"),
    ("agent-tooling", r"^\.claude/settings\.json$|^\.claude/(agents|commands)/[^/]+\.md$|^\.claude/skills/[^/]+/SKILL\.md$"
                      r"|^\.claude/hooks/[^/]+$|^\.mcp\.json$", "agent roles, commands, skills, hooks and tool servers"),
]
_PATTERNS = [(k, re.compile(p)) for k, p, _ in KINDS]
SKIP = re.compile(r"(^|/)(node_modules|vendor|third_party|dist|build)/")
LANG = {".json": "json", ".py": "python", ".sh": "bash", ".mjs": "js", ".js": "js", ".md": "markdown", ".yml": "yaml",
        ".yaml": "yaml", ".toml": "toml"}


def kind_of(path: str):
    if SKIP.search(path):
        return None
    return next((k for k, rx in _PATTERNS if rx.search(path)), None)


def harvest(repo, refs: List[Ref], commits: List[Commit], out: Writer, prefix: str, max_refs: int = 60) -> Dict:
    """Current and superseded practices with when each was adopted. Texts of current ones go to <prefix>practices/."""
    history: Dict[str, List[tuple]] = defaultdict(list)       # path -> [(time, sha, status, subject)]
    for c in commits:
        for ch in c.changes:
            if kind_of(ch.path):
                history[ch.path].append((c.time, c.short, ch.status, c.subject))
    holders: Dict[str, Ref] = {}
    for ref in refs[:max_refs]:                                # newest branch first: its copy is the one shown
        for path, _ in gitlog.tree(repo.path, ref.full):
            if kind_of(path) and path not in holders:
                holders[path] = ref
    current, superseded = [], []
    for path in sorted(set(history) | set(holders)):
        kind = kind_of(path)
        events = sorted(history.get(path, []))
        last = events[-1] if events else None
        adopted = next((e for e in events if e[2] == "A"), events[0] if events else None)
        if last and last[2] == "D" or path not in holders:
            if last:
                superseded.append({"kind": kind, "path": path, "removed": last[1], "removed_date": date(last[0]),
                                   "adopted": date(adopted[0]) if adopted else None})
            continue
        ref = holders[path]
        text = gitlog.show(repo.path, ref.full, path)
        rel = f"{prefix}practices/{kind}/{path.replace('/', '__')}"
        out.text(rel, text)
        current.append({"kind": kind, "path": path, "branch": ref.name, "lines": text.count("\n"), "file": rel,
                        "adopted": date(adopted[0]) if adopted else None, "adopted_sha": adopted[1] if adopted else None,
                        "changed": len(events), "last_change": date(last[0]) if last else None,
                        "what": _describe(kind, path, text)})
    order = [k for k, _, _ in KINDS]
    current.sort(key=lambda r: (order.index(r["kind"]), r["path"]))
    superseded.sort(key=lambda r: (order.index(r["kind"]), r["path"]))
    out.text(f"{prefix}practices/INDEX.md", _index(current, superseded, out))
    return {"current": current, "superseded": superseded}


def _describe(kind: str, path: str, text: str) -> str:
    m = re.search(r"^(?:description|name):\s*(.+)$", text, re.M)
    if m:
        return m.group(1).strip().strip("'\"")[:120]
    for line in text.splitlines():
        s = line.strip().lstrip("#/\"'*-> ").strip()
        if len(s) > 12 and not s.startswith(("!", "{", "[", "<!--")):
            return s[:120]
    return ""


def _index(current: List[Dict], superseded: List[Dict], out: Writer) -> str:
    md = ["# Practices", "", "How the work is done, as the repository records it. Each current file's text is folded under "
          "its line; superseded ones are named with the commit that removed them.", ""]
    for kind, _, why in KINDS:
        rows = [r for r in current if r["kind"] == kind]
        if not rows:
            continue
        md += [f"## {kind} ({len(rows)}): {why}", ""]
        for r in rows:
            body = (out.root / r["file"]).read_text(encoding="utf-8").rstrip("\n")
            fence = "~~~~" if "```" in body else "```"
            lang = LANG.get("." + r["path"].rsplit(".", 1)[-1], "") if "." in r["path"] else ""
            md += [f"<details><summary><code>{r['path']}</code> · since {r['adopted'] or '?'} · {r['changed']} changes"
                   f" · {r['what'].replace('<', '&lt;')}</summary>", "", f"{fence}{lang}", body, fence, "", "</details>", ""]
    if superseded:
        md += [f"## Superseded ({len(superseded)})", ""]
        md += [f"- {r['kind']}: `{r['path']}` from {r['adopted'] or '?'}, removed {r['removed_date']} in {r['removed']}" for r in superseded]
    return "\n".join(md) + "\n"
