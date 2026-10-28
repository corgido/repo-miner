"""REPORT.md and report.html: one repository's history, written for someone who has just been handed it.

Order: the short version, what to distrust, what stands out, the questions for the people, then the reference sections
(chapters, people, areas, branches, practices, documents, activity) and how the report was made.
"""
from __future__ import annotations

import html
import re
from typing import Dict, List, Optional

from . import __version__
from .doc import Doc, to_html, to_markdown
from .findings import Finding
from .util import date, duration, pct, plural

TOP_FINDINGS = 12


class Linker:
    """Turns short commit ids into links when the repository lives on a forge with a web view."""

    def __init__(self, web: Optional[str]):
        self.web = web if web and re.match(r"^https://(github\.com|gitlab\.com|bitbucket\.org|codeberg\.org)/", web) else None

    def sha(self, sha: Optional[str]) -> str:
        if not sha:
            return "?"
        if not self.web:
            return f"`{sha}`"
        path = "commits" if "bitbucket.org" in self.web else "commit"
        return f"[`{sha}`]({self.web}/{'-/' if 'gitlab.com' in self.web else ''}{path}/{sha})"


def repo_report(R: Dict) -> Doc:
    """Links inside a repository's report are relative to its own folder (repos/<name>/ in a multi-repository run)."""
    s, h, t, pr, findings = R["survey"], R["history"], R["timeline"], R["practices"], R["findings"]
    name = R["name"]
    L = Linker(s.get("web"))
    d = Doc()
    d.h(1, f"{name}: what the history says")
    d.note(f"Made by repo-miner {__version__} from the git record: every branch, up to {h['span']['last']}. No AI model wrote "
           "this report. Every number is counted, and every claim points to a commit or a path you can check.")

    d.h(2, "In short").p(_synopsis(R)).table(["", ""], _glance(R))
    if t.get("bins", {}).get("rows"):
        d.html_only(activity_chart(t))

    warnings = _warnings(R)
    if warnings:
        d.h(2, "Before you trust this record").ul(warnings)

    d.h(2, "What stands out")
    if not findings:
        d.p("Nothing in the record crosses the thresholds this report uses. That is itself worth knowing: a tidy, linear history.")
    for i, f in enumerate(findings[:TOP_FINDINGS], 1):
        d.details(f"**{i}.** {_code_shas(f.title)}", _finding_body(f, L))
    if len(findings) > TOP_FINDINGS:
        more = Doc()
        for f in findings[TOP_FINDINGS:]:
            more.details(_code_shas(f.title), _finding_body(f, L))
        d.details(f"{len(findings) - TOP_FINDINGS} more", more)

    questions = _questions(findings)
    d.h(2, "Questions for the people")
    if questions:
        d.p("The record shows what changed; these are the things it cannot say. Ask whoever was there.").ol(questions)
    else:
        d.p("None the record raises on its own. Start with the chapters below.")

    _chapters(d, t, L)
    _people(d, h, R)
    _areas(d, h)
    _branches(d, s, L)
    _practices(d, pr, h)
    _reading(d, s, R.get("prefix", ""))
    _periods(d, h)
    _files(d)
    _method(d, R)
    return d


# ─────────────────────────────────────────────────────────────── the top


def _synopsis(R: Dict) -> str:
    s, h, t = R["survey"], R["history"], R["timeline"]
    tot, roles = h["totals"], h["roles"]
    people = sum(1 for p in h["people"] if p["role"] == "human")
    who = [plural(people, "person", "people")] if people else []
    with_agents = roles["agent"] + roles["assisted"]
    if with_agents:
        who.append(f"AI agents ({pct(roles['agent_share'])} of commits)" if roles["agent_share"] >= 0.01
                   else f"AI agents ({plural(with_agents, 'commit')})")
    if roles["bot"]:
        who.append(f"{plural(len(roles['bots']), 'bot')}")
    areas = [a["area"] for a in h["areas"] if a["area"] not in ("(none)", "(top level)")][:3]
    text = (f"**{R['name']}** has {tot['commits']:,} commits on {plural(len(s['branches']), 'branch', 'branches')}, from "
            f"{h['span']['first']} to {h['span']['last']} ({duration(h['span']['seconds'])}), by {_join(who)}. ")
    if areas:
        text += f"Most of the work is in {_join([f'`{a}`' for a in areas])}. "
    ch = t.get("chapters", [])
    if ch:
        last = ch[-1]
        text += (f"The history falls into {plural(len(ch), 'chapter')}; the latest ({last['from']} to {last['to']}) is mostly "
                 f"{last['label']}. ")
    q = len(_questions(R["findings"]))
    text += f"{plural(len(R['findings']), 'thing stands', 'things stand')} out, and {plural(q, 'question')} can only be answered by the people who were there."
    return text


def _glance(R: Dict) -> List[List[str]]:
    s, h = R["survey"], R["history"]
    roles = h["roles"]
    rows = [
        ["Commits", f"{h['totals']['commits']:,} ({h['totals']['merges']:,} merges) on every branch"],
        ["Branches", f"{len(s['branches']):,}; default `{s['default']['name']}`" + (f", busiest `{s['busiest']['name']}`" if s["busiest"]["name"] != s["default"]["name"] else "")],
        ["People", plural(sum(1 for p in h['people'] if p['role'] == 'human'), "author who is a person", "authors who are people")],
        ["AI agents", f"{plural(roles['agent'], 'commit')} by agents, {roles['assisted']:,} with an agent co-author" if roles["agent"] or roles["assisted"] else "none recorded"],
        ["Bots", ", ".join(f"`{b}`" for b in roles["bots"][:4]) + f" ({roles['bot']:,} commits)" if roles["bot"] else "none"],
        ["First and last", f"{h['span']['first']} to {h['span']['last']}"],
        ["Files now", f"{s['tree']['files']:,} on `{s['tree']['branch']}`, {s['tree']['bytes'] / 1e6:,.1f} MB; mostly "
                      + ", ".join(f"{e} ({k:,})" for e, k in s["tree"]["extensions"][:4])],
        ["Releases", f"{plural(s['tags']['count'], 'tag')}, latest {s['tags']['latest']['name']} ({s['tags']['latest']['date']})" if s["tags"]["latest"] else "no tags"],
    ]
    if R.get("sessions"):
        rows.append(["Agent sessions", f"{R['sessions']['events']:,} messages and replies from {plural(R['sessions']['count'], 'session')} (Claude Code transcripts)"])
    if s.get("remote"):
        rows.append(["Remote", f"`{s['remote']}`"])
    return rows


def _warnings(R: Dict) -> List[str]:
    s, out = R["survey"], []
    hl = s["health"]
    if hl.get("shallow"):
        out.append("**This is a shallow clone**: older history is missing, so the first dates, the people and every count are too small. "
                   "Fetch the rest with `git fetch --unshallow` (or `--deepen`), then run again.")
    if hl.get("single_branch"):
        out.append("**This clone tracks only one branch.** Work on other branches is invisible to it. Fix with "
                   "`git config remote.origin.fetch '+refs/heads/*:refs/remotes/origin/*' && git fetch origin`, then run again.")
    if not hl.get("has_remote"):
        out.append("No remote is configured: this is a local repository, and branches nobody pushed are part of the record.")
    if hl.get("refs_truncated"):
        out.append(f"Only the {hl['refs_examined']:,} most recently active branches were examined in detail; every commit was still counted.")
    if R.get("window"):
        out.append(f"Only commits {R['window']} were read.")
    linked = R["history"]["roles"].get("sessions", 0)
    if R.get("sessions") is None and linked:
        out.append(f"{R['history']['roles']['session_commits']:,} commits link to {plural(linked, 'Claude Code session')}, but no "
                   "transcripts were read: they are not on this machine. The reasons behind those changes are in the sessions; "
                   "run the miner where they are kept, or point `--transcripts` at a copy.")
    elif R.get("sessions") is None and R.get("transcripts") == "auto" and not s.get("cloned_from"):
        out.append("No Claude Code transcripts were found for this repository on this machine, so the reasons behind changes "
                   "come only from commit messages and documents.")
    return out


def _finding_body(f: Finding, L: Linker) -> Doc:
    b = Doc()
    b.ul([_link_shas(e, L) for e in f.evidence])
    if f.dig:
        b.p("Dig:").code("\n".join(f.dig), "sh")
    if f.question:
        b.p(f"**Ask:** {f.question}")
    return b


def _questions(findings: List[Finding]) -> List[str]:
    seen, out = set(), []
    for f in findings:
        if f.question and f.question not in seen:
            seen.add(f.question)
            out.append(f.question)
    return out[:12]


# ─────────────────────────────────────────────────────────────── reference sections


def _chapters(d: Doc, t: Dict, L: Linker) -> None:
    ch = t.get("chapters", [])
    if not ch:
        return
    d.h(2, "Chapters")
    d.p("The record cut where it falls silent or changes character (who works, on what, where). Labels are the area and words "
        "a chapter has more of than the rest of the record.")
    d.table(["#", "From", "To", "Span", "Events", "People", "Mostly"],
            [[c["n"], c["from"], c["to"], c["span"], c["events"], c["people_count"], c["label"]] for c in ch], numeric=[0, 4, 5])
    detail = Doc()
    for c in ch:
        body = Doc()
        lines = []
        if c["lifts"]:
            lines.append("More of: " + "; ".join(f"{x['facet']} `{x['value']}` ({x['count']} of {x['of']}, +{x['lift']} bits)" for x in c["lifts"]))
        if c["terms"]:
            lines.append("Its words: " + ", ".join(f"{x['term']} ({x['count']})" for x in c["terms"]))
        if c["people"]:
            lines.append("People: " + ", ".join(c["people"]))
        roles = c["roles"]
        lines.append("Made by: " + ", ".join(f"{k} {v:,}" for k, v in sorted(roles.items(), key=lambda kv: -kv[1])) + f"; {c['fixes']:,} fixes")
        lines += [f"Heaviest: {L.sha(x['ref'])} {x['date']} \"{x['title']}\" ({plural(x['lines'], 'line')})" for x in c["heaviest"] if x["lines"] >= 10]
        lines.append(f"Runs from {L.sha(c['first_ref'])} to {L.sha(c['last_ref'])}" + ("; starts after a silence" if c["seam"] and c["n"] > 1 else ""))
        body.ul(lines)
        detail.details(f"{c['n']}. {c['from']} to {c['to']}: {c['label']}", body)
    d.details("Each chapter in detail", detail)
    nuggets = [n for n in t.get("nuggets", []) if n["kind"] in ("burst", "concentration", "regime")]
    if nuggets:
        d.details("Surprises in the timeline", Doc().ul([f"**{n['head']}** {n['text']} ({n['bits']} bits)" for n in nuggets[:6]]))


def _people(d: Doc, h: Dict, R: Dict) -> None:
    people = [p for p in h["people"] if p["role"] == "human"]
    if not people:
        return
    d.h(2, "People")
    rows = [[p["name"], p["commits"], pct(p["share"]), p["first"] or "", p["last"] or "", ", ".join(f"`{a}`" for a in p["areas"]),
             "quiet" if p["quiet"] else "", p["assisted"] or ""] for p in people[:15]]
    d.table(["Who", "Commits", "Share", "First", "Last", "Mostly in", "Status", "With an agent"], rows, numeric=[1, 2, 7])
    if len(people) > 15:
        d.p(f"And {len(people) - 15:,} more; all of them are in `data/people.tsv`.")
    other = [p for p in h["people"] if p["role"] != "human"]
    if other:
        d.p("Not people: " + ", ".join(f"`{p['name']}` ({p['role']}, {p['commits'] + p['merges']:,})" for p in other[:8]) + ".")
    d.p("\"Quiet\" means no commits in the last stretch of the record (a fifth of its span, at least 90 days) from someone who made at "
        "least 2% of the commits. It is a fact about the record, not about the person.")


def _areas(d: Doc, h: Dict) -> None:
    areas = [a for a in h["areas"] if a["area"] != "(none)"]
    if not areas:
        return
    d.h(2, "Where the work is")
    d.table(["Area", "Commits", "People", "Main author", "Ask now", "Fixes", "By agents", "Last change"],
            [[f"`{a['area']}`", a["commits"], a["people"], f"{a['owner']} ({pct(a['owner_share'])})" if a["owner"] else "",
              ", ".join(a["ask"]) + ("" if a["ask_is_recent"] else " (not recent)"), pct(a["fix_share"]), pct(a["agent_share"]), a["last"]]
             for a in areas[:15]], numeric=[1, 2, 5, 6])
    d.p("\"Ask now\" is whoever committed most to the area in the last year of the record (or a quarter of its span, if longer).")
    hs = h.get("hotspots", [])
    if hs:
        d.details("The files that change most", Doc().table(
            ["File", "Commits", "Fixes", "People", "Lines churned", "First", "Last", "Still there"],
            [[f"`{x['path']}`", x["commits"], x["fixes"], x["people"], x["churn"], x["first"], x["last"], "yes" if x["present"] else "no"] for x in hs],
            numeric=[1, 2, 3, 4]).p("Lock files, changelogs and build output are left out."))


def _branches(d: Doc, s: Dict, L: Linker) -> None:
    d.h(2, "Branches and releases")
    lines = [f"Default `{s['default']['name']}`: {s['default']['commits']:,} commits, tip {L.sha(s['default']['tip'])} ({s['default']['last']})."]
    if s["busiest"]["name"] != s["default"]["name"]:
        lines.append(f"Busiest `{s['busiest']['name']}`: {s['busiest']['commits']:,} commits.")
    merged = sum(1 for b in s["branches"] if b["ahead"] == 0 and not b["orphan"] and b["name"] != s["primary"])
    lines.append(f"{plural(len(s['unmerged']), 'branch holds', 'branches hold')} commits `{s['primary']}` lacks; {merged:,} "
                 f"{'is' if merged == 1 else 'are'} fully merged.")
    from .findings import RELEASE_LINE
    lines_ = [b["name"] for b in s["branches"] if RELEASE_LINE.search(b["name"])]
    if lines_:
        lines.append(f"Release lines: {', '.join(f'`{x}`' for x in lines_[:8])}{' and more' if len(lines_) > 8 else ''}.")
    if s["orphans"]:
        lines.append("Unrelated histories: " + ", ".join(f"`{o['name']}`" + (f" ({o['purpose']})" if o["purpose"] else "") for o in s["orphans"]) + ".")
    t = s["tags"]
    if t["latest"]:
        span = (f"one tag, {t['latest']['name']} ({t['latest']['date']})" if t["count"] == 1 else
                f"{t['count']:,} tags from {t['first']['name']} ({t['first']['date']}) to {t['latest']['name']} ({t['latest']['date']})")
        lines.append(f"{span[0].upper()}{span[1:]}; {plural(t['commits_since_latest'], 'commit')} on `{s['default']['name']}` since.")
    d.ul(lines)
    if s["unmerged"]:
        d.details(f"Unmerged branches ({len(s['unmerged']):,})", Doc().table(
            ["Branch", "Own commits", "Behind", "First own", "Last own", "Authors"],
            [[f"`{b['name']}`", b["ahead"], b["behind"], b["first"], b["last"], b["authors"]] for b in s["unmerged"][:25]], numeric=[1, 2, 5]))


def _practices(d: Doc, pr: Dict, h: Dict) -> None:
    d.h(2, "How the work is done")
    cur, gone = pr.get("current", []), pr.get("superseded", [])
    msgs = h.get("messages", {})
    lines = []
    if msgs:
        lines.append(f"Commit messages: {pct(msgs['conventional_share'])} follow Conventional Commits, {pct(msgs['with_body_share'])} have a body, "
                     f"{pct(msgs['thin_share'])} say almost nothing.")
        if msgs.get("pr_refs"):
            lines.append(f"{msgs['pr_refs']:,} commits name a pull request (#{msgs['pr_first']} to #{msgs['pr_last']}): the discussion behind them is on the forge, not in git.")
    d.ul(lines)
    if cur:
        d.table(["Kind", "File", "Since", "Changes", "What it is"],
                [[r["kind"], f"`{r['path']}`", r["adopted"] or "", r["changed"], r["what"]] for r in cur[:30]],
                numeric=[3])
        d.p("The full text of each is folded in [`practices/INDEX.md`](practices/INDEX.md).")
    else:
        d.p("No CI, ownership, hook, linter or agent-instruction files were found on any branch.")
    if gone:
        d.details(f"Practices that were dropped ({len(gone):,})", Doc().ul(
            [f"{r['kind']}: `{r['path']}` from {r['adopted'] or '?'}, removed {r['removed_date']} in `{r['removed']}`" for r in gone[:30]]))


def _reading(d: Doc, s: Dict, prefix: str) -> None:
    docs = s.get("docs", [])
    if not docs and not s.get("entry_points"):
        return
    d.h(2, "Read next")
    if docs:
        d.p("The repository's own documents, best first, copied here with secrets and private paths removed. They describe intent; "
            "the record above shows what happened.")
        d.table(["Document", "Path", "Branch", "Copy"],
                [[x["title"], f"`{x['path']}`", x["branch"], f"[open]({x['file'][len(prefix):]})"] for x in docs])
    if s.get("entry_points"):
        d.p("Where things start: " + ", ".join(f"`{e}`" for e in s["entry_points"][:20]) + ".")
    if s.get("package_scripts"):
        d.p("`package.json` scripts: " + ", ".join(f"`{x}`" for x in s["package_scripts"]) + ".")


def _periods(d: Doc, h: Dict) -> None:
    rows = h.get("periods", {}).get("rows", [])
    if not rows:
        return
    table = Doc().table(["Period", "Commits", "People", "By people", "By agents", "With an agent", "Bots", "Lines"],
                        [[r["period"], r["commits"], r["people"], r["human"], r["agent"], r["assisted"], r["bot"], r["lines"]] for r in rows],
                        numeric=[1, 2, 3, 4, 5, 6, 7])
    d.h(2, "Activity by " + h["periods"]["unit"])
    d.details(f"{len(rows):,} {h['periods']['unit']}s, from {rows[0]['period']} to {rows[-1]['period']}", table)


def _files(d: Doc) -> None:
    d.h(2, "What is in this folder")
    d.table(["File", "What"], [
        ["`REPORT.md`", "this report (also `report.html`, with the activity chart)"],
        ["`findings.json`", "every finding with its evidence, commands and question"],
        ["`data/commits.tsv`", "every commit: sha, date, author, role, area, chapter, lines, subject"],
        ["`data/branches.tsv`", "every branch: commits, ahead, behind, orphan, first and last own commit"],
        ["`data/people.tsv`, `data/areas.tsv`, `data/files.tsv`", "the tables above, in full"],
        ["`data/timeline.json`", "chapters, surprises and activity bins"],
        ["`docs/`", "the repository's documents, redacted"],
        ["`practices/`", "the current practice files, with `INDEX.md`"],
        ["`briefs/`", "one brief per chapter, for an agent to write that chapter's history"],
    ])


def _method(d: Doc, R: Dict) -> None:
    body = Doc().ul([
        "Read with `git` only, every branch and tag, without checking anything out or running the project's code.",
        "Roles: an author whose name matches a known AI coding tool is an agent, a known automation account is a bot, anyone else "
        "is a person. A person's commit with an agent `Co-Authored-By` trailer counts as made with an agent.",
        "Areas: the top-level folder a commit touches most, one level deeper inside a folder that holds over a quarter of all changes.",
        "Chapters: cut at silences six times longer than the record's 90th-percentile gap (at least 4 hours), then wherever the mix of "
        "roles, areas and repositories changes by more information than a BIC-style penalty allows. Deterministic.",
        "Renames count as a deletion and an addition. Authors are merged by `.mailmap` when the repository has one; otherwise one "
        "person with two names counts twice.",
        "Redacted before writing: e-mail addresses, keys and tokens, secret assignments, connection strings, private IP addresses, "
        "home-directory paths" + (", and the deny list" if R.get("deny") else "") + (". People are shown as aliases." if R.get("anonymised") else "."),
        "Not read: pull requests, issues, chat and tickets. Agent transcripts only when Claude Code kept them on this machine.",
    ])
    d.h(2, "How this was made").details("Method and limits", body)


# ─────────────────────────────────────────────────────────────── many repositories


def overview(name: str, repos: List[Dict], timeline: Dict) -> Doc:
    d = Doc()
    d.h(1, f"{name}: what the history says")
    d.note(f"Made by repo-miner {__version__} from the git record of {plural(len(repos), 'repository', 'repositories')}. "
           "No AI model wrote this report. Every claim points to a commit or a path you can check.")
    d.h(2, "The repositories")
    d.table(["Repository", "Commits", "Branches", "People", "First", "Last", "Top finding", "Report"],
            [[r["name"], r["history"]["totals"]["commits"], len(r["survey"]["branches"]),
              sum(1 for p in r["history"]["people"] if p["role"] == "human"), r["history"]["span"]["first"], r["history"]["span"]["last"],
              r["findings"][0].title if r["findings"] else "", f"[open](repos/{r['slug']}/REPORT.md)"] for r in repos], numeric=[1, 2, 3])
    if timeline.get("bins", {}).get("rows"):
        d.html_only(activity_chart(timeline))
    ranked = sorted(((f, r) for r in repos for f in r["findings"]), key=lambda x: (-x[0].score, x[1]["name"], x[0].id))
    d.h(2, "What stands out across them")
    for i, (f, r) in enumerate(ranked[:TOP_FINDINGS], 1):
        d.details(f"**{i}.** {r['name']}: {_code_shas(f.title)}", _finding_body(f, Linker(r["survey"].get("web"))))
    qs = []
    for f, r in ranked:
        if f.question and len(qs) < 12:
            qs.append(f"{r['name']}: {f.question}")
    if qs:
        d.h(2, "Questions for the people").ol(qs)
    ch = timeline.get("chapters", [])
    if ch:
        d.h(2, "Chapters across all of them")
        d.table(["#", "From", "To", "Events", "Mostly"], [[c["n"], c["from"], c["to"], c["events"], c["label"]] for c in ch], numeric=[0, 3])
    return d


# ─────────────────────────────────────────────────────────────── HTML page


def activity_chart(t: Dict) -> str:
    """A stacked bar chart of activity by role, with the chapters as bands behind it. Static SVG, no script."""
    bins = t["bins"]["rows"]
    W, H, top, bottom = 1000, 200, 18, 26
    n = len(bins)
    peak = max(1, max(b["human"] + b["agent"] + b["bot"] for b in bins))
    bw = W / n
    t0, t1 = bins[0]["t"], bins[-1]["t"] + t["bins"]["step"]
    x = lambda tt: (tt - t0) / (t1 - t0) * W
    parts = []
    for c in t.get("chapters", []):
        a, b = x(max(c["start"], t0)), x(min(c["end"] + t["bins"]["step"], t1))
        tip = html.escape(f"{c['n']}. {c['from']} to {c['to']}: {c['label']}")
        parts.append(f'<rect x="{a:.1f}" y="0" width="{max(1, b - a):.1f}" height="{H - bottom}" class="band{c["n"] % 2}">'
                     f'<title>{tip}</title></rect>')
        parts.append(f'<text x="{a + 3:.1f}" y="12" class="lab">{c["n"]}</text>')
    for i, b in enumerate(bins):
        y = H - bottom
        for role in ("human", "agent", "bot"):
            v = b[role]
            if not v:
                continue
            hgt = v / peak * (H - bottom - top)
            y -= hgt
            parts.append(f'<rect x="{i * bw:.2f}" y="{y:.2f}" width="{max(bw - 0.6, 0.6):.2f}" height="{hgt:.2f}" class="{role}">'
                         f'<title>{date(b["t"])}: {v} {role}</title></rect>')
    ticks = _ticks(t0, t1)
    for tt, label in ticks:
        parts.append(f'<text x="{x(tt):.1f}" y="{H - 8}" class="tick">{label}</text>')
    legend = ('<div class="legend"><span><i class="sw human"></i>people</span><span><i class="sw agent"></i>AI agents</span>'
              '<span><i class="sw bot"></i>bots</span><span><i class="sw band1"></i>chapters</span></div>')
    unit = t["bins"]["unit"]
    return (f'<figure class="chart">{legend}<svg viewBox="0 0 {W} {H}" role="img" aria-label="Commits per {unit}, by who made them">'
            + "".join(parts) + f'</svg><figcaption>Commits per {unit}, by who made them. Shaded bands are the chapters.</figcaption></figure>')


def _ticks(t0: float, t1: float) -> List:
    import datetime as dt
    a, b = dt.datetime.fromtimestamp(t0, dt.timezone.utc), dt.datetime.fromtimestamp(t1, dt.timezone.utc)
    years = (t1 - t0) / (365 * 86400)
    out = []
    if years > 2:
        step = max(1, round(years / 8))
        for y in range(a.year + 1, b.year + 1, step):
            out.append((dt.datetime(y, 1, 1, tzinfo=dt.timezone.utc).timestamp(), str(y)))
    else:
        m = dt.datetime(a.year, a.month, 1, tzinfo=dt.timezone.utc)
        months = max(1, round(years * 12 / 8))
        k = 0
        while m.timestamp() < t1:
            if m.timestamp() > t0 and k % months == 0:
                out.append((m.timestamp(), m.strftime("%b %Y") if m.month == 1 or not out else m.strftime("%b")))
            k += 1
            m = dt.datetime(m.year + (m.month // 12), m.month % 12 + 1, 1, tzinfo=dt.timezone.utc)
    return out


CSS = """
:root{color-scheme:light;--bg:#f7f6f2;--card:#fffefa;--ink:#1c1b18;--ink2:#56524a;--ink3:#8a857a;--rule:#e2ded3;--accent:#9a3b1f;
--human:#c0512f;--agent:#2f6fa3;--bot:#a39d90;--band0:#f1eee6;--band1:#e9e4d8;--code:#efebe1;
--sans:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",sans-serif;--mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
--serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--bg:#141412;--card:#1b1b18;--ink:#ebe7dd;--ink2:#b5afa2;
--ink3:#857f73;--rule:#2f2d28;--accent:#e07b55;--human:#d9673f;--agent:#4a8fca;--bot:#6b665c;--band0:#1a1a17;--band1:#22211d;--code:#262520}}
:root[data-theme="dark"]{color-scheme:dark;--bg:#141412;--card:#1b1b18;--ink:#ebe7dd;--ink2:#b5afa2;--ink3:#857f73;--rule:#2f2d28;
--accent:#e07b55;--human:#d9673f;--agent:#4a8fca;--bot:#6b665c;--band0:#1a1a17;--band1:#22211d;--code:#262520}
*{box-sizing:border-box}html{background:var(--bg)}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 var(--sans)}
main{max-width:980px;margin:0 auto;padding:32px 16px 96px}
h1{font:600 clamp(28px,4.6vw,44px)/1.1 var(--serif);margin:8px 0 14px;letter-spacing:-.01em}
h2{font:600 22px/1.25 var(--serif);margin:44px 0 12px;padding-top:12px;border-top:1px solid var(--rule)}
h3{font:600 17px/1.3 var(--serif)}p{margin:10px 0;max-width:74ch}.note{color:var(--ink2);font-size:14px;border-left:3px solid var(--accent);padding-left:12px}
a{color:inherit;text-decoration-color:var(--ink3);text-underline-offset:3px}a:hover{text-decoration-color:var(--accent)}
code{font:13px/1.4 var(--mono);background:var(--code);padding:1px 5px;border-radius:4px;overflow-wrap:anywhere}
pre{background:var(--code);padding:12px 14px;border-radius:6px;overflow-x:auto}pre code{background:none;padding:0;font-size:13px}
ul,ol{padding-left:22px}li{margin:4px 0}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:14px;background:var(--card)}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--rule);vertical-align:top}
th{font:600 11px/1.3 var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--ink3)}
td.n,th.n{text-align:right;font-family:var(--mono);white-space:nowrap}
details{background:var(--card);border:1px solid var(--rule);border-radius:8px;margin:8px 0;padding:0 14px}
details>summary{cursor:pointer;padding:11px 0;font-weight:500;list-style-position:outside}
details>div{padding-bottom:8px}details details{background:var(--bg)}
.chart{margin:18px 0 8px;background:var(--card);border:1px solid var(--rule);border-radius:8px;padding:12px 14px}
.chart svg{display:block;width:100%;height:auto}.chart figcaption{font-size:13px;color:var(--ink3);margin-top:6px}
.human{fill:var(--human);background:var(--human)}.agent{fill:var(--agent);background:var(--agent)}.bot{fill:var(--bot);background:var(--bot)}
.band0{fill:var(--band0)}.band1{fill:var(--band1);background:var(--band1)}.band0,.band1{stroke:none}
.tick,.lab{font:11px var(--mono);fill:var(--ink3)}.legend{display:flex;flex-wrap:wrap;gap:4px 16px;font-size:13px;color:var(--ink2)}
.sw{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;vertical-align:-1px}
footer{margin-top:56px;color:var(--ink3);font-size:13px}
"""


def page(title: str, d: Doc) -> str:
    return ("<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body><main>" + to_html(d.blocks)
            + f"<footer>Made by repo-miner {__version__}. Static page: no scripts, no external requests.</footer></main></body></html>\n")


def markdown(d: Doc) -> str:
    return to_markdown(d.blocks)


# ─────────────────────────────────────────────────────────────── helpers


def _join(xs: List[str]) -> str:
    xs = [x for x in xs if x]
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1] if xs else ""


def _code_shas(text: str) -> str:
    """Short commit ids as code, outside spans that are code already."""
    parts = text.split("`")
    return "`".join(_SHA.sub(r"`\1`", p) if i % 2 == 0 else p for i, p in enumerate(parts))


_SHA = re.compile(r"(?<![\w/`\[])([0-9a-f]{9})(?![\w`\]])")


def _link_shas(text: str, L: Linker) -> str:
    return _SHA.sub(lambda m: L.sha(m.group(1)), text) if L.web else _SHA.sub(r"`\1`", text)
