"""Findings: what stands out in a repository's record, ranked, each with its evidence, the command to dig, and the question
only the people can answer.

A finding is a fact the record shows, not a judgement. The ranking is a fixed rule (severity first, then size), so the same
record always gives the same list in the same order.
"""
from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .util import DAY, duration, pct, plural


@dataclass
class Finding:
    id: str
    score: float
    title: str                               # one line, the fact
    evidence: List[str] = field(default_factory=list)
    dig: List[str] = field(default_factory=list)
    question: Optional[str] = None
    kind: str = ""

    def to_dict(self) -> Dict:
        return self.__dict__.copy()


def find(repo_path: str, survey: Dict, history: Dict, timeline: Dict, practices: Dict) -> List[Finding]:
    g = f"git -C {shlex.quote(repo_path)}"
    out: List[Finding] = []
    add = out.append

    # ── the record itself
    sensitive = history.get("sensitive", [])
    for s in [s for s in sensitive if s["looks_secret"] is not False][:4]:
        state = f"still on `{survey['primary']}`" if s["present"] else (f"removed in {s['removed']}" if s["removed"] else "on another branch")
        held = "held text that looks like a credential" if s["looks_secret"] else "may hold secrets"
        add(Finding(f"sensitive:{s['path']}", (100 if s["present"] else 85) - (25 if s["fixture"] else 0),
                    f"`{s['path']}` {held}: committed in {s['added']} ({s['added_date']}), {state}",
                    ["Only the path and that yes or no are reported; repo-miner never prints the content.",
                     "Removing a file does not remove it from history: anyone with a clone can still read every version."]
                    + (["It sits under a test or example folder, so it may be a fixture with fake values."] if s["fixture"] else []),
                    [f"{g} log --all --oneline -- {shlex.quote(s['path'])}"],
                    f"Were the credentials in `{s['path']}` rotated after it was committed?", "security"))
    benign = [s for s in sensitive if s["looks_secret"] is False]
    if benign:
        add(Finding("sensitive-checked", 20, f"{plural(len(benign), 'file')} with a secret-sounding name held nothing that looks like a credential",
                    [f"`{s['path']}` (committed {s['added_date']})" for s in benign[:6]], [], None, "security"))

    if survey.get("branch_trap"):
        d, b = survey["default"], survey["busiest"]
        add(Finding("branch-trap", 90, f"The default branch `{d['name']}` has {plural(d['commits'], 'commit')}; `{b['name']}` has {b['commits']:,}",
                    ["Anyone who reads only the default branch (most tools, most people) sees the smaller part of the work.",
                     f"`{b['name']}`: {survey['trap_ahead']:,} commits not on `{d['name']}`, last on {b['last']}.",
                     f"The rest of this report treats `{b['name']}` as the main line."],
                    [f"{g} log --oneline {d['name']}..{_ref(survey, b['name'])} | head -30"],
                    f"Which branch is the real one: `{b['name']}` or `{d['name']}`? Why isn't the work merged?", "branches"))

    for b in survey.get("local_only", [])[:3] + survey.get("unpushed", [])[:3]:
        what = f"exists only on this machine ({b['ahead']:,} commits of its own)" if b["local_only"] else f"has {b['unpushed']:,} commits not pushed"
        add(Finding(f"local:{b['name']}", 85, f"Branch `{b['name']}` {what}",
                    ["Work that was never pushed is invisible to everyone else and is lost with the machine."],
                    [f"{g} log --oneline -10 {b['name']}"], f"Should `{b['name']}` be pushed, or is it safe to drop?", "branches"))

    # ── people
    quiet = [p for p in history.get("people", []) if p["quiet"]]
    areas = {a["area"]: a for a in history.get("areas", [])}
    span = history.get("span", {})
    halfway = _date_add(span.get("first"), span.get("seconds", 0) / 2)
    for p in quiet:
        named = [a for a in p["areas"] if a not in ("(top level)", "(none)")] or p["areas"]
        owned = [a for a in named if areas.get(a, {}).get("owner") == p["name"] and areas[a]["present"]]
        if not owned and (p["last"] or "") < halfway:
            continue                                   # left long ago and no longer the main author of anything
        add(Finding(f"quiet:{p['name']}", 60 + 20 * p["share"] + (10 if owned else 0),
                    f"{p['name']} made {p['commits']:,} commits ({pct(p['share'])}) and has been quiet since {p['last']}",
                    [f"Active {p['first']} to {p['last']} on {p['active_days']:,} days; mostly in "
                     + ", ".join(f"`{a}`" for a in p["areas"]) + "."]
                    + (["Still the main author of " + ", ".join(f"`{a}`" for a in owned) + "."] if owned else []),
                    [f"{g} log --author={shlex.quote(p['name'])} --format='%h %ad %s' --date=short | head -20"],
                    f"Who knows what {p['name']} knew about " + ", ".join(f"`{a}`" for a in (owned or named)[:2]) + "? Can they still be reached?",
                    "people"))

    lonely = [a for a in history.get("areas", []) if a["commits"] >= 20 and a["owner"] and a["owner_share"] >= 0.8 and a["present"]
              and a["area"] not in ("(top level)", "(none)")]
    if lonely:
        add(Finding("single-owner", 55, f"{plural(len(lonely), 'area rests', 'areas rest')} on one person's knowledge",
                    [f"`{a['area']}`: {pct(a['owner_share'])} of {a['commits']:,} commits by {a['owner']}" for a in lonely[:6]],
                    [f"{g} shortlog -sn --no-merges -- {shlex.quote(lonely[0]['area'])}"], None, "people"))

    roles = history.get("roles", {})
    if roles and roles.get("agent_share", 0) >= 0.2 and roles.get("first_agent"):
        add(Finding("agents", 65, f"{pct(roles['agent_share'])} of commits were written by or with AI agents "
                    f"({pct(roles['agent_share_after_first'])} since the first, {roles['first_agent']['sha']} on {roles['first_agent']['date']})",
                    [f"{roles['agent']:,} commits by agent authors, {roles['assisted']:,} by people with an agent co-author trailer."]
                    + (["Agents seen: " + ", ".join(roles["agents"]) + "."] if roles.get("agents") else [])
                    + ([f"{roles['session_commits']:,} commits link to {plural(roles['sessions'], 'agent session')} "
                        "(a `Claude-Session` trailer): the conversations behind them are there."] if roles.get("sessions") else []),
                    [f"{g} log --all --format='%h %ad %an %s' --date=short -i --grep='co-authored-by' | head -20"],
                    (f"Who can open the {plural(roles['sessions'], 'agent session')} these commits link to? The reasons for agent-written code live there."
                     if roles.get("sessions") else
                     "Where were the agents' instructions, plans and transcripts kept? The reasons for agent-written code live there, not in a person's memory."),
                    "people"))

    # ── what was undone or abandoned
    for gy in [x for x in history.get("graveyard", []) if not x["moved_to"]][:4]:
        ev = [f"Last files removed in {gy['removed_by']}: \"{gy['removed_subject']}\", {duration(gy['lived'])} after it began."]
        if gy["most_by"]:
            ev.append(f"Most of it went earlier, in {gy['most_by']} ({gy['most_date']}): \"{gy['most_subject']}\".")
        if gy["people"]:
            ev.append(f"Worked on by {', '.join(gy['people'])}.")
        add(Finding(f"graveyard:{gy['folder']}", 60 + min(30, gy["commits"] / 5),
                    f"`{gy['folder']}/` ({gy['files']:,} files, {gy['commits']:,} commits) is gone: built from {gy['born']}, removed {gy['removed']}",
                    ev, [f"{g} show --stat {gy['most_by'] or gy['removed_by']} | head -40",
                         f"{g} log --all --oneline -- {shlex.quote(gy['folder'] + '/')} | head -20"],
                    f"What replaced `{gy['folder']}/`, and why was it removed?", "abandoned"))
    moved = [x for x in history.get("graveyard", []) if x["moved_to"]]
    if moved:
        add(Finding("moved", 30, f"{plural(len(moved), 'folder')} moved: " + ", ".join(f"`{x['folder']}/` to `{x['moved_to']}/`" for x in moved[:3]),
                    [f"`{x['folder']}/` to `{x['moved_to']}/` on {x['removed']} ({x['removed_by']})"
                     + (f"; {x['removed_before']:,} of its files had been removed before the move" if x["removed_before"] else "")
                     for x in moved[:6]]
                    + ["Older history of these files is under the old path: use `git log --follow` or the old folder name."],
                    [f"{g} show --stat {moved[0]['removed_by']} | head -30"], None, "history"))

    rv = history.get("reverts", {})
    if rv.get("count"):
        quick = [r for r in rv["items"] if r["after"] is not None and r["after"] < 2 * DAY]
        ev = [f"{r['sha']} ({r['date']}) reverted " + (f"{r['original']}: " if r["original"] else "")
              + f"\"{r['original_subject'] or r['subject']}\"" + (f" after {duration(r['after'])}" if r["after"] is not None else "")
              for r in rv["items"][:6]]
        top = rv["items"][0]
        within = ("" if not quick else ", within two days" if rv["count"] == 1 else f", {len(quick)} of them within two days")
        add(Finding("reverts", 55 + min(20, rv["count"]), f"{plural(rv['count'], 'change was', 'changes were')} reverted{within}", ev,
                    [f"{g} show {top['sha']}"] + ([f"{g} show --stat {top['original']}"] if top["original"] else []),
                    f"What went wrong with \"{top['original_subject'] or top['subject']}\" ({top['date']})?", "abandoned"))

    stale_before = _date_add(span.get("last"), -max(90 * DAY, 0.1 * span.get("seconds", 0)))
    for b in [b for b in survey.get("unmerged", []) if b["ahead"] >= 5 and b["name"] != survey.get("busiest", {}).get("name")
              and b["name"].split("/")[-1] not in KNOWN_PURPOSE and not RELEASE_LINE.search(b["name"])][:4]:
        stale = (b["last"] or "") < stale_before
        add(Finding(f"unmerged:{b['name']}", (50 if stale else 35) + min(25, b["ahead"] / 4),
                    f"Branch `{b['name']}` holds {b['ahead']:,} commits never merged into `{survey['primary']}` (last {b['last']})",
                    [f"Its own work runs {b['first']} to {b['last']}; {b['behind']:,} commits behind `{survey['primary']}`; {plural(b['authors'], 'author')}."],
                    [f"{g} log --oneline {_ref(survey, survey['primary'])}..{_ref(survey, b['name'])} | head -20"],
                    f"Is `{b['name']}` abandoned, parked, or still coming?" if stale else None, "branches"))

    orphans = [o for o in survey.get("orphans", []) if not o["purpose"]]
    if len(orphans) > 2:
        add(Finding("orphans", 50, f"{len(orphans)} branches share no history with `{survey['primary']}`",
                    [f"`{o['name']}`: {plural(o['commits'], 'commit')}, {o['first'] or o['last']} to {o['last']}" for o in orphans[:12]]
                    + ["Unrelated histories: separate projects kept in one repository, imports, generated output, or fresh starts."],
                    [f"{g} log --oneline -5 {_ref(survey, o['name'])}" for o in orphans[:3]],
                    "What is each of these branches for, and which of them still matters?", "branches"))
    for o in orphans if len(orphans) <= 2 else []:
        add(Finding(f"orphan:{o['name']}", 50, f"Branch `{o['name']}` shares no history with `{survey['primary']}` ({plural(o['commits'], 'commit')})",
                    ["An unrelated history: a separate project, an import, generated output, or a fresh start."],
                    [f"{g} log --oneline -10 {_ref(survey, o['name'])}", f"{g} ls-tree --name-only {_ref(survey, o['name'])}"],
                    f"What is `{o['name']}` for?", "branches"))

    # ── where it hurts
    base = history.get("fix_share", 0)
    hot = [h for h in history.get("hotspots", []) if h["fixes"] >= 5 and h["fixes"] / h["commits"] >= max(0.35, 1.5 * base)]
    if hot:
        h = hot[0]
        add(Finding("fix-hotspots", 50 + min(15, h["fixes"] / 2), f"{plural(len(hot), 'file keeps', 'files keep')} needing fixes",
                    [f"`{x['path']}`: {x['fixes']} of {x['commits']} changes are fixes, {x['people']} people" for x in hot[:6]]
                    + [f"Across the whole repository, {pct(base)} of changes are fixes."],
                    [f"{g} log --oneline -i --grep=fix -- {shlex.quote(h['path'])} | head -20"],
                    f"Why does `{h['path']}` keep breaking?", "hotspots"))

    for s in history.get("sweeping", [])[:3]:
        add(Finding(f"sweep:{s['sha']}", 45, f"{s['sha']} ({s['date']}) changed {s['files']:,} files at once: \"{s['subject']}\"",
                    [f"Shape: {s['shape']}; {s['added']:,} added, {s['deleted']:,} deleted, {s['lines']:,} lines."],
                    [f"{g} show --stat {s['sha']} | head -40"], None, "hotspots"))

    blobs = history.get("large_blobs", [])
    if blobs:
        add(Finding("large-blobs", 50, f"{plural(len(blobs), 'file')} over 5 MB {'is' if len(blobs) == 1 else 'are'} in the history",
                    [f"`{b['path']}`: {b['bytes'] / 1e6:.0f} MB{'' if b['present'] else ' (no longer on the default branch)'}" for b in blobs[:6]],
                    [f"{g} log --all --oneline -- {shlex.quote(blobs[0]['path'])}"],
                    None, "hotspots"))

    # ── time
    long_enough = 0.02 * span.get("seconds", 0)      # a ten-day pause is news in a year's record, not in twenty years'
    for nug in [x for x in timeline.get("nuggets", []) if x["kind"] == "silence" and x["seconds"] >= long_enough][:2]:
        add(Finding(f"silence:{nug['from']}", 40 + min(15, nug["bits"] / 4), f"{nug['head']} of silence: {nug['from']} to {nug['to']}",
                    [nug["text"]], [f"{g} log --all --format='%h %ad %an %s' --date=short --since={nug['from']} | tail -5"],
                    f"What happened between {nug['from']} and {nug['to']}? A pause, a move to another repository, or work outside git?", "time"))

    # ── how it is recorded and run
    msgs = history.get("messages", {})
    if msgs and msgs.get("thin_share", 0) >= 0.2:
        add(Finding("thin-messages", 45, f"{pct(msgs['thin_share'])} of commit messages say almost nothing (\"wip\", \"fix\", one word)",
                    [f"{pct(msgs['with_body_share'])} of commits explain themselves in a body; the median subject is {msgs['median_subject']} characters."],
                    [f"{g} show --stat {msgs['thin_examples'][-1]}"] if msgs.get("thin_examples") else [],
                    "Where is the reasoning kept, if not in commits: pull requests, tickets, chat, documents?", "practice"))

    tags = survey.get("tags", {})
    if tags.get("latest") and (tags.get("commits_since_latest") or 0) >= 50:
        add(Finding("unreleased", 40, f"{tags['commits_since_latest']:,} commits on `{survey['default']['name']}` since the last tag, "
                    f"{tags['latest']['name']} ({tags['latest']['date']})", [f"{tags['count']:,} tags in all, the first {tags['first']['name']} ({tags['first']['date']})."],
                    [f"{g} log --oneline {tags['latest']['name']}..{survey['default']['name']} | head -20"],
                    "How is this released now? Is what runs in production the last tag or something newer?", "practice"))

    cur = {p["kind"] for p in practices.get("current", [])}
    gone_ci = [p for p in practices.get("superseded", []) if p["kind"] == "ci"]
    if gone_ci and "ci" not in cur:
        add(Finding("ci-removed", 55, f"CI was removed and nothing replaced it: `{gone_ci[-1]['path']}` went in {gone_ci[-1]['removed']} ({gone_ci[-1]['removed_date']})",
                    [], [f"{g} show --stat {gone_ci[-1]['removed']}"], "How are changes checked now that CI is gone?", "practice"))

    for nug in [x for x in timeline.get("nuggets", []) if x["kind"] == "regime" and x.get("facet") == "area"][:1]:
        add(Finding(f"regime:{nug['value']}", 30, nug["text"], [], [f"{g} show --stat {nug['refs'][0]}"], None, "time"))

    out.sort(key=lambda f: (-f.score, f.id))
    return out


KNOWN_PURPOSE = {"gh-pages", "pages", "docs", "assets", "wiki"}   # branches that are never meant to merge
RELEASE_LINE = re.compile(r"^(stable|release|releases|maint|maintenance|support|lts|backport)[/-]|^v?\d+(\.\d+)*(\.x)?$|[.-]x$", re.I)


def _date_add(day: Optional[str], seconds: float) -> str:
    import datetime as dt
    if not day:
        return ""
    d = dt.datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc) + dt.timedelta(seconds=seconds)
    return d.strftime("%Y-%m-%d")


def _ref(survey: Dict, name: str) -> str:
    """The name to type for a branch: the remote-tracking one when the branch is only on the remote."""
    row = next((b for b in survey.get("branches", []) if b["name"] == name), None)
    if row and not row["local_only"] and survey.get("health", {}).get("has_remote"):
        return f"origin/{name}"
    return name
