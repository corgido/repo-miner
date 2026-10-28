"""The run: resolve the targets, read every repository, measure, write the report, scan what was written.

Two passes. The first only reads (commits, and who is a person), so aliases can be fixed before anything is written. The
second measures and writes every file through one redacting writer.
"""
from __future__ import annotations

import datetime as dt
import os
import platform
import re
import shutil
import subprocess
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from . import __version__, briefs, findings, gitlog, history, practices, report, survey, target, timeline, transcripts
from .privacy import Redactor, Writer, make_aliases, read_deny_file, scan
from .util import date, tsv

MARKER = "run.json"


@dataclass
class Options:
    targets: List[str]
    out: Optional[str] = None
    since: Optional[str] = None
    until: Optional[str] = None
    deny_file: Optional[str] = None
    anonymise: bool = False
    transcripts: str = "auto"            # auto | none | a folder
    agents: List[str] = field(default_factory=list)
    bots: List[str] = field(default_factory=list)
    humans: List[str] = field(default_factory=list)
    depth: Optional[int] = None
    force: bool = False
    quiet: bool = False


def cache_dir() -> Path:
    return Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "repo-miner" / "clones"


def default_out(name: str) -> Path:
    return Path.home() / "repo-miner-reports" / name


def prepare_out(out: Path, force: bool) -> None:
    """Refuse to write into a folder that holds anything but an earlier report, unless forced."""
    if out.exists() and any(out.iterdir()):
        if not (out / MARKER).exists() and not force:
            raise SystemExit(f"repo-miner: {out} exists and is not a repo-miner report; choose another --out or pass --force")
        for child in out.iterdir():
            shutil.rmtree(child) if child.is_dir() else child.unlink()
    out.mkdir(parents=True, exist_ok=True)


def mine(opt: Options) -> Dict:
    log = (lambda *a: None) if opt.quiet else (lambda *a: print(*a, flush=True))
    t0 = time.time()
    sources = target.resolve(opt.targets, cache_dir(), opt.depth, log)
    single = len(sources) == 1
    name = sources[0].name if single else (Path(opt.targets[0]).name if not target.is_url(opt.targets[0]) else "repositories")
    out = Path(opt.out).expanduser().resolve() if opt.out else default_out(name)
    prepare_out(out, opt.force)
    cfg = history.Config(opt.agents, opt.bots, opt.humans).compile()

    # ── pass 1: read
    read = []
    for src in sources:
        log(f"reading {src.name}")
        refs = gitlog.branches(src.path)
        commits = gitlog.commits(src.path, opt.since, opt.until)
        read.append((src, refs, commits))
    _merge_spellings([c for _, _, cs in read for c in cs])
    people = Counter(c.author for _, _, cs in read for c in cs if cfg.role(c.author) == "human")
    aliases = make_aliases([p for p, _ in sorted(people.items(), key=lambda kv: (-kv[1], kv[0]))]) if opt.anonymise else {}
    deny = read_deny_file(opt.deny_file)
    for _, _, commits in read:                 # aliases at the source: nothing downstream sees a real name
        for c in commits:
            c.author = aliases.get(c.author, c.author)
    redactor = Redactor(deny, aliases)
    writer = Writer(out, redactor)

    # ── pass 2: measure and write
    results, all_events = [], []
    for src, refs, commits in read:
        if not commits:
            log(f"  {src.name}: no commits, skipped")
            continue
        prefix = "" if single else f"repos/{_slug(src.name)}/"
        R = _one(src, refs, commits, cfg, opt, writer, prefix, log)
        R["slug"] = _slug(src.name)
        results.append(R)
        all_events += R.pop("_events")
    if not results:
        raise SystemExit("repo-miner: no commits to read (check --since and --until)")

    if not single:
        for e in all_events:
            e.pop("chapter", None)
        tl = timeline.build(all_events)
        writer.json("data/timeline.json", tl)
        doc = report.overview(name, results, tl)
        writer.text("REPORT.md", report.markdown(doc))
        writer.text("report.html", report.page(f"{name}: what the history says", doc))

    hits = scan(out, deny + list(aliases))         # with aliases on, no real name may survive
    run = {"tool": "repo-miner", "version": __version__, "made": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "seconds": round(time.time() - t0, 1), "python": platform.python_version(), "git": _git_version(),
           "options": {**opt.__dict__, "deny_file": bool(opt.deny_file)},
           "repositories": [{"name": r["name"], "commits": r["history"]["totals"]["commits"], "cloned_from": r["survey"].get("cloned_from"),
                             "head": r["survey"]["default"]["tip"]} for r in results],
           "redactions": redactor.counts, "leak_scan": "clean" if not hits else f"{len(hits)} file(s) flagged",
           "files": sorted(set(writer.written))}
    writer.json(MARKER, run)
    summary = {"out": str(out), "report": str(out / "REPORT.md"), "html": str(out / "report.html"), "repositories": [
        {"name": r["name"], "commits": r["history"]["totals"]["commits"], "branches": len(r["survey"]["branches"]),
         "people": sum(1 for p in r["history"]["people"] if p["role"] == "human"), "chapters": len(r["timeline"]["chapters"]),
         "findings": len(r["findings"]), "questions": len({f.question for f in r["findings"] if f.question})} for r in results],
        "leak_scan": run["leak_scan"], "flagged": [p for p, _ in hits], "seconds": run["seconds"]}
    return summary


def _one(src, refs, commits, cfg, opt: Options, writer: Writer, prefix: str, log) -> Dict:
    t0 = time.time()
    S = survey.survey(src, refs, len(commits), writer, prefix)
    tip_files = history.tip_paths(gitlog.tree(src.path, S["primary_ref"]))
    mainline = set(gitlog.git(src.path, "rev-list", S["primary_ref"]).split())
    H = history.analyse(commits, cfg, tip_files, gitlog.large_blobs(src.path),
                        read=lambda sha, path: gitlog.show(src.path, sha, path), mainline=mainline)
    P = practices.harvest(src, refs, commits, writer, prefix)
    events = timeline.commit_events(commits, src.name)
    sessions = None
    folder = None if opt.transcripts == "none" or src.cloned_from else (
        transcripts.find(src.path) if opt.transcripts == "auto" else Path(opt.transcripts).expanduser())
    if folder and folder.exists():
        sev = transcripts.read(folder, "sessions")
        if sev:
            sessions = {"count": len({e["session"] for e in sev}), "events": len(sev),
                        "people": sum(1 for e in sev if e["role"] == "human")}
            events += sev
    T = timeline.build(events)
    F = findings.find(str(src.path), S, H, T, P)
    window = " and ".join(x for x in [f"from {opt.since}" if opt.since else "", f"until {opt.until}" if opt.until else ""] if x)
    R = {"name": src.name, "path": src.path, "survey": S, "history": H, "timeline": T, "practices": P, "findings": F,
         "sessions": sessions, "transcripts": opt.transcripts, "window": window, "deny": bool(opt.deny_file),
         "anonymised": opt.anonymise, "prefix": prefix}

    name = writer.redactor.name
    chapter_of = {e["ref"]: e.get("chapter") for e in events if e.get("kind") in ("commit", "merge")}
    writer.text(f"{prefix}data/commits.tsv", tsv(
        ["sha", "date", "author", "role", "with_agent", "area", "chapter", "lines", "files", "subject"],
        [[c.short, date(c.time), name(c.author), c.role, int(c.assisted), c.area, chapter_of.get(c.short, ""), c.lines,
          len(c.changes), c.subject] for c in commits]))
    writer.text(f"{prefix}data/people.tsv", tsv(
        ["who", "role", "commits", "merges", "share", "first", "last", "active_days", "areas", "with_agent", "quiet"],
        [[name(p["name"]), p["role"], p["commits"], p["merges"], f"{p['share']:.3f}", p["first"], p["last"], p["active_days"],
          " ".join(p["areas"]), p["assisted"], int(p["quiet"])] for p in H["people"]]))
    writer.text(f"{prefix}data/areas.tsv", tsv(
        ["area", "commits", "people", "owner", "owner_share", "ask", "fix_share", "agent_share", "first", "last", "lines"],
        [[a["area"], a["commits"], a["people"], name(a["owner"]) if a["owner"] else "", f"{a['owner_share']:.3f}",
          " ".join(name(x) for x in a["ask"]), f"{a['fix_share']:.3f}", f"{a['agent_share']:.3f}", a["first"], a["last"], a["lines"]]
         for a in H["areas"]]))
    writer.text(f"{prefix}data/files.tsv", tsv(
        ["path", "commits", "fixes", "people", "churn", "first", "last", "present"],
        [[x["path"], x["commits"], x["fixes"], x["people"], x["churn"], x["first"], x["last"], int(x["present"])] for x in H["hotspots"]]))
    writer.json(f"{prefix}data/timeline.json", T)
    writer.json(f"{prefix}findings.json", [f.to_dict() for f in F])
    briefs.write(R, writer, prefix, opt.anonymise)
    doc = report.repo_report(R)
    writer.text(f"{prefix}REPORT.md", report.markdown(doc))
    writer.text(f"{prefix}report.html", report.page(f"{src.name}: what the history says", doc))
    s = R["survey"]
    log(f"  {src.name}: {len(commits):,} commits on {len(s['branches']):,} branches, {len(T['chapters'])} chapters, "
        f"{len(F)} findings in {time.time() - t0:.1f} s")
    R["_events"] = events
    return R


PLACEHOLDER_EMAIL = re.compile(r"(^$|localhost|example\.(com|org)|^noreply@github\.com$|^(root|user|you|me|none)@|\(none\))")


def _merge_spellings(commits) -> None:
    """One person, one name. Names that differ only in case or spacing are one person, and so are names that share an
    e-mail address (placeholders aside). Each person keeps the spelling they use most. Addresses are not kept."""
    parent: Dict[str, str] = {}

    def find(x: str) -> str:
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    key = lambda name: "n:" + re.sub(r"\s+", " ", name.strip()).casefold()
    for c in commits:
        if c.email and not PLACEHOLDER_EMAIL.search(c.email):
            a, b = find(key(c.author)), find("e:" + c.email)
            if a != b:
                parent[b] = a
    spellings: Dict[str, Counter] = {}
    for c in commits:
        spellings.setdefault(find(key(c.author)), Counter())[c.author] += 1
    best = {k: sorted(v.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] for k, v in spellings.items()}
    for c in commits:
        c.author = best[find(key(c.author))]
        c.email = ""


def _slug(s: str) -> str:
    import re
    return re.sub(r"[^A-Za-z0-9._-]+", "-", s).strip("-") or "repo"


def _git_version() -> str:
    try:
        return subprocess.run(["git", "--version"], capture_output=True, text=True).stdout.strip()
    except OSError:
        return "missing"
