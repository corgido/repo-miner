"""What the commit record says happened: who did what, where, when, and what was undone.

Every figure is counted from commits; nothing is inferred by a model. The analysis reads only what git already holds:
authors (never e-mail addresses), times, subjects, bodies and the paths each commit changed.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Set

from .gitlog import Commit
from .privacy import looks_secret
from .util import DAY, date

# Who made a commit. Agents are AI coding tools; bots are automation. Both are matched on the author name.
AGENTS = r"claude|copilot|cursor|devin|codex|openai|aider|sweep|gemini|jules|windsurf|cline|lovable|bolt\.new|v0\b|amp\b"
BOTS = (r"\[bot\]$|^dependabot|^renovate|^github-actions|^greenkeeper|^snyk|^semantic-release|^allcontributors"
        r"|^mergify|^codecov|^pre-commit-ci|^imgbot|^whitesource|^deepsource|^restyled|^auto-?merge|^release-?bot")
# A commit a person made with an agent says so in a trailer.
ASSISTED = re.compile(r"^co-authored-by:\s*.*?(" + AGENTS + r")|generated with \[?(claude code|cursor|copilot|codex|aider)",
                      re.I | re.M)
FIX = re.compile(r"\b(fix(e[sd])?|bug(fix)?|hotfix|patch(ed)?|regression|broken|crash(es)?|oops|typo|revert(ed)?)\b", re.I)
REVERT_SUBJECT = re.compile(r'^Revert\s+"(.+)"', re.I)
REVERTS_SHA = re.compile(r"This reverts commit ([0-9a-f]{7,40})", re.I)
CONVENTIONAL = re.compile(r"^(feat|fix|chore|docs|refactor|test|tests|ci|build|perf|style|revert)(\([^)]*\))?!?:\s", re.I)
THIN = re.compile(r"^(wip|fix(es|ed)?|update[sd]?|changes?|stuff|tmp|temp|test(ing)?|asdf+|minor|misc|cleanup|more|again|done|"
                  r"save|commit|work|progress|\.+|-+|small fix(es)?|bug ?fix|fixed bug|initial commit|first commit)\W*$", re.I)
SESSION_LINK = re.compile(r"claude\.ai/code/session_([A-Za-z0-9]+)|^claude-session:\s*(\S+)", re.I | re.M)
PR_REF = re.compile(r"\(#(\d+)\)\s*$|^Merge pull request #(\d+)")
NOT_HOTSPOTS = re.compile(r"(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|npm-shrinkwrap\.json|Cargo\.lock|poetry\.lock"
                          r"|Pipfile\.lock|uv\.lock|go\.sum|Gemfile\.lock|composer\.lock|flake\.lock|mix\.lock|pubspec\.lock"
                          r"|bun\.lockb?|CHANGELOG(\.md)?|\.gitignore)$|(^|/)(dist|build|vendor|node_modules)/|\.min\.(js|css)$|\.snap$")
SENSITIVE = re.compile(r"(^|/)(\.env(\.(?!example|sample|template|dist|defaults)[\w.-]+)?|[^/]*\.pem|[^/]*\.key|id_(rsa|dsa|ecdsa|ed25519)"
                       r"|[^/]*\.(p12|pfx|keystore|jks|ovpn)|credentials(\.json|\.ya?ml)?|secrets?\.(ya?ml|json|toml|txt)"
                       r"|\.npmrc|\.pypirc|\.netrc|\.htpasswd|service[-_]?account[^/]*\.json|[^/]*\.tfstate(\.backup)?)$", re.I)


LOCALE = re.compile(r"(^|/)(locale|locales|i18n|l10n|translations?|lang)/|\.(po|mo|pot|xlf|xliff)$", re.I)
FIXTURE = re.compile(r"(^|/)(tests?|spec|specs|fixtures?|examples?|samples?|testdata|__tests__|mocks?|demo)/", re.I)


@dataclass
class Config:
    agents: List[str] = field(default_factory=list)      # extra author names or patterns that are agents
    bots: List[str] = field(default_factory=list)        # extra author names or patterns that are automation
    humans: List[str] = field(default_factory=list)      # names that are people even if they look like a pattern above

    def compile(self):
        extra = lambda xs: "|".join(x if x.startswith("^") or x.endswith("$") else re.escape(x) for x in xs)
        self._agents = re.compile("|".join(p for p in [AGENTS, extra(self.agents)] if p), re.I)
        self._bots = re.compile("|".join(p for p in [BOTS, extra(self.bots)] if p), re.I)
        self._humans = {h.lower() for h in self.humans}
        return self

    def role(self, author: str) -> str:
        if author.lower() in self._humans:
            return "human"
        if self._bots.search(author):
            return "bot"
        if self._agents.search(author):
            return "agent"
        return "human"


def area_namer(commits: Iterable[Commit]):
    """An area is a top-level folder, or one level deeper inside a folder that holds more than a quarter of all changes."""
    top: Counter = Counter()
    for c in commits:
        for ch in c.changes:
            top[ch.path.split("/", 1)[0] if "/" in ch.path else "(top level)"] += 1
    total = sum(top.values()) or 1
    deep = {k for k, v in top.items() if v / total > 0.25 and k != "(top level)"}

    def name(path: str) -> str:
        parts = path.split("/")
        if len(parts) == 1:
            return "(top level)"
        if parts[0] in deep and len(parts) > 2:
            return f"{parts[0]}/{parts[1]}"
        return parts[0]
    return name


def main_area(c: Commit, name) -> str:
    if not c.changes:
        return "(none)"
    counts = Counter(name(ch.path) for ch in c.changes)
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


def analyse(commits: List[Commit], cfg: Config, tip_files: Set[str], large_blobs: List[tuple],
            read: Optional[Callable[[str, str], str]] = None, mainline: Optional[Set[str]] = None) -> Dict:
    """`read(sha, path)` returns a file's text at a commit; it is used only to ask whether a secret-looking file held
    anything that looks like a credential. `mainline` holds the commits reachable from the main branch: what is gone is
    judged on its history alone, since a maintenance branch may keep editing files the main line removed."""
    if not commits:
        return {"empty": True}
    name = area_namer(commits)
    start, end = commits[0].time, commits[-1].time
    span = max(end - start, 1)
    roles = {a: cfg.role(a) for a in {c.author for c in commits}}
    work = [c for c in commits if not c.is_merge]
    for c in commits:
        c.role = roles[c.author]                                  # type: ignore[attr-defined]
        c.area = main_area(c, name)                               # type: ignore[attr-defined]
        c.assisted = c.role == "human" and bool(ASSISTED.search(c.body))  # type: ignore[attr-defined]
        c.fix = bool(FIX.search(c.subject))                       # type: ignore[attr-defined]

    result = {
        "span": {"first": date(start), "last": date(end), "seconds": span, "first_sha": commits[0].short, "last_sha": commits[-1].short},
        "totals": _totals(commits, work),
        "roles": _roles(commits),
        "people": _people(work, commits, roles, end, span, name),
        "areas": _areas(work, end, span, {name(p) for p in tip_files}),
        "hotspots": _hotspots(work, tip_files),
        "fix_share": sum(1 for c in work if c.fix) / max(1, len(work)),
        "reverts": _reverts(commits),
        "sweeping": _sweeping(work, len(tip_files)),
        "graveyard": _graveyard([c for c in work if mainline is None or c.sha in mainline], tip_files),
        "sensitive": _sensitive(work, tip_files, read),
        "large_blobs": [{"path": p, "bytes": s, "present": p in tip_files} for s, p in large_blobs],
        "messages": _messages(work, commits),
        "periods": _periods(commits),
    }
    return result


def _totals(commits: List[Commit], work: List[Commit]) -> Dict:
    return {"commits": len(commits), "merges": len(commits) - len(work), "authors": len({c.author for c in commits}),
            "lines": sum(c.lines for c in work), "files_touched": len({ch.path for c in work for ch in c.changes})}


def _roles(commits: List[Commit]) -> Dict:
    by = Counter(c.role for c in commits)
    agent = [c for c in commits if c.role == "agent" or c.assisted]
    first_agent = agent[0] if agent else None
    return {
        "human": by.get("human", 0), "agent": by.get("agent", 0), "bot": by.get("bot", 0),
        "assisted": sum(1 for c in commits if c.assisted),
        "agent_share": len(agent) / len(commits),
        "first_agent": {"sha": first_agent.short, "date": date(first_agent.time)} if first_agent else None,
        "agent_share_after_first": (sum(1 for c in commits if c.time >= first_agent.time and (c.role == "agent" or c.assisted))
                                    / max(1, sum(1 for c in commits if c.time >= first_agent.time))) if first_agent else 0,
        "bots": [a for a, _ in Counter(c.author for c in commits if c.role == "bot").most_common(8)],
        # agent conversations the commits point to; only counted, the links are never written
        "session_commits": sum(1 for c in commits if SESSION_LINK.search(c.body)),
        "sessions": len({m.group(1) or m.group(2) for c in commits for m in SESSION_LINK.finditer(c.body)}),
        "agents": [a for a, _ in Counter(c.author for c in commits if c.role == "agent").most_common(8)],
    }


def _people(work: List[Commit], commits: List[Commit], roles: Dict[str, str], end: int, span: int, name) -> List[Dict]:
    """Every author who is a person, most commits first, with where they worked and whether they have gone quiet."""
    by: Dict[str, List[Commit]] = defaultdict(list)
    for c in work:
        by[c.author].append(c)
    merges = Counter(c.author for c in commits if c.is_merge)
    human_total = sum(len(v) for a, v in by.items() if roles[a] == "human") or 1
    quiet_after = end - max(90 * DAY, int(0.2 * span))
    rows = []
    for author, cs in by.items():
        areas = Counter(c.area for c in cs)
        rows.append({
            "name": author, "role": roles[author], "commits": len(cs), "merges": merges.get(author, 0),
            "share": len(cs) / len(work) if work else 0,
            "first": date(cs[0].time), "last": date(cs[-1].time), "last_t": cs[-1].time,
            "active_days": len({date(c.time) for c in cs}),
            "areas": [a for a, _ in sorted(areas.items(), key=lambda kv: (-kv[1], kv[0]))[:3]],
            "assisted": sum(1 for c in cs if c.assisted),
            "quiet": roles[author] == "human" and cs[-1].time < quiet_after and len(cs) >= max(5, 0.02 * human_total),
        })
    for author, k in merges.items():               # people who only merged still count as people
        if author not in by:
            rows.append({"name": author, "role": roles[author], "commits": 0, "merges": k, "share": 0, "first": None, "last": None,
                         "last_t": 0, "active_days": 0, "areas": [], "assisted": 0, "quiet": False})
    return sorted(rows, key=lambda r: (-r["commits"], -r["merges"], r["name"]))


def _areas(work: List[Commit], end: int, span: int, present: Set[str]) -> List[Dict]:
    """Each area: how busy, who owns it, who is still around to ask, how much of it is fixing, how much an agent wrote."""
    by: Dict[str, List[Commit]] = defaultdict(list)
    for c in work:
        by[c.area].append(c)
    recent_from = end - max(365 * DAY, int(0.25 * span))
    rows = []
    for area, cs in by.items():
        people = Counter(c.author for c in cs if c.role == "human")
        owner, owned = (people.most_common(1)[0] if people else (None, 0))
        recent = Counter(c.author for c in cs if c.role == "human" and c.time >= recent_from)
        ask = [a for a, _ in sorted(recent.items(), key=lambda kv: (-kv[1], kv[0]))[:2]] or \
              [a for a, _ in sorted(people.items(), key=lambda kv: (-kv[1], kv[0]))[:2]]
        rows.append({
            "area": area, "commits": len(cs), "people": len(people), "owner": owner,
            "owner_share": owned / max(1, sum(people.values())),
            "agent_share": sum(1 for c in cs if c.role == "agent" or c.assisted) / len(cs),
            "fix_share": sum(1 for c in cs if c.fix) / len(cs),
            "first": date(cs[0].time), "last": date(cs[-1].time), "ask": ask, "ask_is_recent": bool(recent),
            "lines": sum(c.lines for c in cs), "present": area in present,
        })
    return sorted(rows, key=lambda r: (-r["commits"], r["area"]))


def _hotspots(work: List[Commit], tip_files: Set[str], k: int = 15) -> List[Dict]:
    """The files changed most often (lock files, changelogs and build output left out), with how often the change was a fix."""
    touches: Dict[str, List[Commit]] = defaultdict(list)
    churn: Counter = Counter()
    for c in work:
        for ch in c.changes:
            if not NOT_HOTSPOTS.search(ch.path):
                touches[ch.path].append(c)
                churn[ch.path] += ch.added + ch.removed
    rows = [{"path": p, "commits": len(cs), "people": len({c.author for c in cs if c.role == "human"}),
             "fixes": sum(1 for c in cs if c.fix), "churn": churn[p], "first": date(cs[0].time), "last": date(cs[-1].time),
             "present": p in tip_files}
            for p, cs in touches.items() if len(cs) >= 3]
    return sorted(rows, key=lambda r: (-r["commits"], -r["churn"], r["path"]))[:k]


def _reverts(commits: List[Commit]) -> Dict:
    by_sha = {c.sha: c for c in commits}
    by_subject = {}
    for c in commits:
        by_subject.setdefault(c.subject, c)
    rows = []
    for c in commits:
        m = REVERTS_SHA.search(c.body)
        s = REVERT_SUBJECT.match(c.subject)
        if not m and not s:
            continue
        original = None
        if m:
            sha = m.group(1)
            original = by_sha.get(sha) or next((x for k, x in by_sha.items() if k.startswith(sha)), None)
        if original is None and s:
            original = by_subject.get(s.group(1))
        rows.append({"sha": c.short, "date": date(c.time), "subject": c.subject, "author": c.author,
                     "original": original.short if original else None,
                     "original_subject": original.subject if original else (s.group(1) if s else None),
                     "after": (c.time - original.time) if original else None})
    return {"count": len(rows), "items": list(reversed(rows))[:12]}


def _sweeping(work: List[Commit], tree_size: int, k: int = 8) -> List[Dict]:
    """Commits that touched a large part of the repository at once: migrations, reformats, imports, mass deletions."""
    floor = max(40, int(0.15 * tree_size))
    rows, seen = [], set()
    for c in work:
        if len(c.changes) < floor or not c.parents:          # the first commit of a history is always large
            continue
        same = re.sub(r"^\[[^\]]+\]\s*", "", c.subject)      # "[4.0.x] X" is X picked onto a release line
        if same in seen:
            continue
        if sum(1 for ch in c.changes if LOCALE.search(ch.path)) >= 0.8 * len(c.changes):
            continue                                           # a translation sync is mechanical, however large
        seen.add(same)
        st = Counter(ch.status for ch in c.changes)
        shape = ("mostly additions (an import or a scaffold)" if st["A"] > 0.8 * len(c.changes) else
                 "mostly deletions" if st["D"] > 0.8 * len(c.changes) else
                 "files moved or renamed" if st["A"] > 0.3 * len(c.changes) and st["D"] > 0.3 * len(c.changes) else
                 "edits across many files (a reformat, rename or upgrade?)")
        rows.append({"sha": c.short, "date": date(c.time), "subject": c.subject, "author": c.author, "files": len(c.changes),
                     "lines": c.lines, "added": st["A"], "deleted": st["D"], "shape": shape})
    return sorted(rows, key=lambda r: (-r["files"], r["date"]))[:k]


def _graveyard(work: List[Commit], tip_files: Set[str]) -> List[Dict]:
    """Folders that were built up and are gone from the main line now: abandoned, replaced, or moved elsewhere.

    A folder whose files mostly reappear under another folder (same names and sub-paths) was moved, and says where to.
    """
    life: Dict[str, Dict] = {}
    for c in work:
        for ch in c.changes:
            row = life.setdefault(ch.path, {"last": None, "touches": []})
            row["touches"].append(c)
            if ch.status == "D":                  # the latest deletion: later edits may come from merged maintenance branches
                row["last"] = c
    tip_dirs = set()
    for p in tip_files:
        parts = p.split("/")
        for i in range(1, len(parts)):
            tip_dirs.add("/".join(parts[:i]))
    by_suffix: Dict[str, List[str]] = defaultdict(list)
    for p in tip_files:
        by_suffix[p.split("/", 1)[-1]].append(p)
        by_suffix[p.rsplit("/", 1)[-1]].append(p)
    gone: Dict[str, List[str]] = defaultdict(list)
    for path, row in life.items():
        if row["last"] is None or path in tip_files or "/" not in path:
            continue
        parts = path.split("/")
        for depth in (1, 2):
            if len(parts) > depth:
                folder = "/".join(parts[:depth])
                if folder not in tip_dirs:
                    gone[folder].append(path)
                    break
    rows = []
    for folder, paths in gone.items():
        if len(paths) < 5:
            continue
        touches = {c.sha: c for p in paths for c in life[p]["touches"]}
        ordered = sorted(touches.values(), key=lambda c: c.time)
        last = max((life[p]["last"] for p in paths), key=lambda c: c.time)
        biggest = touches[Counter(life[p]["last"].sha for p in paths).most_common(1)[0][0]]
        people = Counter(c.author for c in ordered if c.role == "human")
        rows.append({"folder": folder, "files": len(paths), "commits": len(ordered), "born": date(ordered[0].time),
                     "removed": date(last.time), "removed_by": last.short, "removed_subject": last.subject,
                     "most_by": biggest.short if biggest.sha != last.sha else None, "most_date": date(biggest.time),
                     "most_subject": biggest.subject, "lived": last.time - ordered[0].time,
                     "people": [a for a, _ in people.most_common(2)],
                     # moved, when what the final commit removed reappears elsewhere; earlier losses are told apart
                     "moved_to": _moved_to(folder, [p for p in paths if life[p]["last"].sha == last.sha], by_suffix),
                     "removed_before": sum(1 for p in paths if life[p]["last"].sha != last.sha)})
    rank = lambda r: (-r["commits"], r["folder"])
    return (sorted((r for r in rows if not r["moved_to"]), key=rank)[:10]
            + sorted((r for r in rows if r["moved_to"]), key=rank)[:5])


def _moved_to(folder: str, paths: List[str], by_suffix: Dict[str, List[str]]) -> Optional[str]:
    """Where a gone folder's files live now, when at least half of them reappear with the same sub-path."""
    homes: Counter = Counter()
    for p in paths:
        rest = p[len(folder) + 1:]
        for q in by_suffix.get(rest, []) + (by_suffix.get(p, []) if "/" in rest else []):
            if q.endswith("/" + rest):
                homes[q[: -len(rest) - 1]] += 1
                break
    if not homes:
        return None
    home, k = homes.most_common(1)[0]
    return home if k >= 0.5 * len(paths) else None


def _sensitive(work: List[Commit], tip_files: Set[str], read: Optional[Callable[[str, str], str]]) -> List[Dict]:
    """Paths that usually hold secrets and were committed at some point, and whether any version of them held text that
    looks like a credential. Only the path and that yes or no are reported; the content is never written."""
    seen: Dict[str, Dict] = {}
    for c in work:
        for ch in c.changes:
            if not SENSITIVE.search(ch.path):
                continue
            row = seen.setdefault(ch.path, {"path": ch.path, "added": c.short, "added_date": date(c.time), "removed": None,
                                            "versions": [], "looks_secret": None})
            if ch.status == "D":
                row["removed"] = c.short
            else:
                row["versions"].append(c.sha)
    for row in seen.values():
        row["present"] = row["path"] in tip_files
        row["fixture"] = bool(FIXTURE.search(row["path"]))
        if read:
            row["looks_secret"] = any(looks_secret(read(sha, row["path"])) for sha in row["versions"][-5:])
        del row["versions"]
    return sorted(seen.values(), key=lambda r: (not r["looks_secret"], not r["present"], r["added_date"], r["path"]))[:20]


def _messages(work: List[Commit], commits: List[Commit]) -> Dict:
    people = [c for c in work if c.role != "bot"]
    if not people:
        return {}
    has_body = sum(1 for c in people if any(l.strip() and not re.match(r"^[\w-]+:\s", l) for l in c.body.splitlines()))
    prs = [m.group(1) or m.group(2) for c in commits for m in [PR_REF.search(c.subject)] if m]
    thin = [c for c in people if THIN.match(c.subject.strip()) or len(c.subject.split()) <= 1]
    lengths = sorted(len(c.subject) for c in people)
    return {
        "thin": len(thin), "thin_share": len(thin) / len(people),
        "thin_examples": [c.short for c in thin[-5:]],
        "with_body_share": has_body / len(people),
        "conventional_share": sum(1 for c in people if CONVENTIONAL.match(c.subject)) / len(people),
        "median_subject": lengths[len(lengths) // 2],
        "pr_refs": len(prs), "pr_first": prs[0] if prs else None, "pr_last": prs[-1] if prs else None,
    }


def _periods(commits: List[Commit]) -> Dict:
    """Commits per period by role, with the people active in each: months for short records, then quarters, then years."""
    years = (commits[-1].time - commits[0].time) / (365 * DAY)
    unit = "month" if years <= 3 else "quarter" if years <= 10 else "year"

    def key(t: int) -> str:
        d = date(t)
        y, m = int(d[:4]), int(d[5:7])
        return d[:7] if unit == "month" else f"{y}-Q{(m - 1) // 3 + 1}" if unit == "quarter" else str(y)
    rows: Dict[str, Dict] = {}
    for c in commits:
        row = rows.setdefault(key(c.time), {"period": key(c.time), "commits": 0, "human": 0, "agent": 0, "bot": 0,
                                           "assisted": 0, "people": set(), "lines": 0})
        row["commits"] += 1
        row[c.role] += 1
        row["assisted"] += c.assisted
        row["lines"] += c.lines
        if c.role == "human":
            row["people"].add(c.author)
    out = []
    for r in sorted(rows.values(), key=lambda r: r["period"]):
        out.append(dict(r, people=len(r["people"])))
    return {"unit": unit, "rows": out}


def tip_paths(files: Optional[List[tuple]]) -> Set[str]:
    return {p for p, _ in files or []}
