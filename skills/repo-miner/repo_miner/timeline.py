"""The timeline: every commit (and, when present, every session message) on one line, cut into chapters.

A chapter starts where the record falls silent for far longer than its own rhythm, or where what is being done changes
character (who is working, on which area, in which repository) by more than chance allows. Each chapter says what it has
more of than the whole, in bits, and which words it owns. The same record always gives the same chapters.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Dict, List

from . import measures as M
from .gitlog import Commit
from .util import DAY, date, duration, when

HOUR = 3600
LIVE = ("human", "agent")


def commit_events(commits: List[Commit], source: str) -> List[Dict]:
    return [{"t": c.time, "role": c.role, "kind": "merge" if c.is_merge else "commit", "source": source, "area": c.area,
             "author": c.author, "title": c.subject, "text": f"{c.subject}\n\n{c.body}".strip(), "weight": c.lines,
             "ref": c.short, "fix": c.fix, "assisted": c.assisted} for c in commits]


def build(events: List[Dict]) -> Dict:
    events = sorted(events, key=lambda e: (e["t"], e["ref"]))
    live = [e for e in events if e["role"] in LIVE]
    if len(live) < 2:
        return {"chapters": [], "nuggets": [], "bins": _bins(events), "events": len(events)}
    gaps = sorted(b["t"] - a["t"] for a, b in zip(live, live[1:]))
    p90 = gaps[min(len(gaps) - 1, int(0.9 * len(gaps)))]
    seam = max(4 * HOUR, 6 * p90)
    max_strata = max(4, min(12, round(1.4 * M.log2(max(2, len(live))))))
    keys = M.usable_facets(live, ["role", "kind", "source", "area"])
    segs = M.stratify([e["t"] for e in live], M.facet_values(live, keys), seam,
                      min_size=max(6, round(len(live) / 60)), max_strata=max_strata)
    names = frozenset(part for e in events if e.get("author") for part in re.findall(r"[^\W\d_]{3,}", e["author"].lower()))
    words = [Counter(M.tokens(_text(e), names)) for e in live]       # tokenised once; each chapter sums its share
    every = _total(words)
    chapters = []
    for i, s in enumerate(segs):
        inside = live[s["a"]:s["b"]]
        start = inside[0]["t"] if i else min(inside[0]["t"], events[0]["t"])
        chapters.append(_chapter(i + 1, inside, live, keys, every, _total(words[s["a"]:s["b"]]), s, start))
    # every event, mechanical ones too, belongs to the chapter whose window holds it
    starts = [c["start"] for c in chapters]
    for e in events:
        e["chapter"] = sum(1 for s in starts if e["t"] >= s) or 1
    return {"chapters": chapters, "nuggets": _nuggets(events, live, seam), "bins": _bins(events),
            "seam_gap": seam, "facets": keys, "events": len(events), "live": len(live)}


def _total(counters: List[Counter]) -> Counter:
    out: Counter = Counter()
    for c in counters:
        out.update(c)
    return out


def _text(e: Dict) -> str:
    """The words an event contributes to its chapter's vocabulary. Merges only say what was merged, not what was done."""
    return "" if e["kind"] == "merge" else e["title"] + " " + (e["text"] or "")[:2000]


def _chapter(n: int, inside: List[Dict], live: List[Dict], keys: List[str], every: Counter, own: Counter, seg: Dict,
             start: float) -> Dict:
    lifts = []
    for k in keys:
        if k == "kind":
            continue
        lifts += M.lifts([str(e.get(k)) for e in live], [str(e.get(k)) for e in inside], k)
    lifts = sorted((x for x in lifts if x["lift"] >= 0.5), key=lambda r: (-r["lift"] * r["count"] ** 0.5, r["value"]))[:5]
    terms = M.own_terms(every, own)
    areas = Counter(e["area"] for e in inside if e["kind"] == "commit")
    authors = Counter(e["author"] for e in inside if e.get("author") and e["role"] == "human")
    roles = Counter(e["role"] for e in inside)
    heaviest = sorted((e for e in inside if e["kind"] == "commit"), key=lambda e: (-e["weight"], e["t"]))[:3]
    area_lift = next((x["value"] for x in lifts if x["facet"] == "area"), None)
    main = area_lift or (areas.most_common(1)[0][0] if areas else None)
    words = ", ".join(t["term"] for t in terms[:3])
    if main in ("(top level)", "(none)") and words:
        main = None                                   # "top-level files" says nothing a chapter's words do not
    return {
        "n": n, "start": start, "end": inside[-1]["t"], "from": date(start), "to": date(inside[-1]["t"]),
        "span": duration(inside[-1]["t"] - start), "seam": seg["seam"],
        "events": len(inside), "share": len(inside) / len(live),
        "roles": dict(roles), "fixes": sum(1 for e in inside if e.get("fix")),
        "areas": [a for a, _ in areas.most_common(4)], "people": [a for a, _ in authors.most_common(3)],
        "people_count": len(authors),
        "lifts": lifts, "terms": terms,
        "label": " · ".join(x for x in [main, words] if x) or f"chapter {n}",
        "heaviest": [{"ref": e["ref"], "date": date(e["t"]), "title": e["title"], "lines": e["weight"]} for e in heaviest],
        "first_ref": inside[0]["ref"], "last_ref": inside[-1]["ref"],
    }


def _nuggets(events: List[Dict], live: List[Dict], seam: float) -> List[Dict]:
    """The surprising, each with its self-information in bits so they can be ranked against each other."""
    out = []
    span = live[-1]["t"] - live[0]["t"]
    mean_gap = span / max(1, len(live) - 1) or 1
    silences = sorted(((b["t"] - a["t"], a, b) for a, b in zip(live, live[1:])), key=lambda x: (-x[0], x[1]["t"]))[:3]
    for i, (g, a, b) in enumerate(s for s in silences if s[0] >= seam):
        out.append({"kind": "silence", "bits": round(g / mean_gap * M.log2(2.718281828), 1), "head": duration(g),
                    "text": f"Nothing from {when(a['t'])} to {when(b['t'])} UTC: {g / mean_gap:.0f} times the record's average gap.",
                    "refs": [a["ref"], b["ref"]], "from": date(a["t"]), "to": date(b["t"]), "seconds": g})
    unit, unit_name = (HOUR, "hour") if span <= 30 * DAY else (DAY, "day")
    per = Counter(int(e["t"] // unit) for e in live)
    lam = len(live) / max(1, len(per))
    (b_slot, b_count) = sorted(per.items(), key=lambda kv: (-kv[1], kv[0]))[0]
    if b_count > 2 * lam:
        inside = [e for e in live if int(e["t"] // unit) == b_slot]
        out.append({"kind": "burst", "bits": round(M.poisson_tail_bits(b_count, lam), 1), "head": f"{b_count} in one {unit_name}",
                    "text": f"{(when if unit == HOUR else date)(b_slot * unit)}: {b_count} events against {lam:.1f} in an average active {unit_name}.",
                    "refs": [e["ref"] for e in inside][:12], "from": date(b_slot * unit)})
    commits = [e for e in live if e["kind"] == "commit"]
    if len(commits) >= 20:
        c = M.concentration([e["weight"] for e in commits])
        if c["k"] and c["k"] / c["n"] < 0.05:
            heavy = sorted(commits, key=lambda e: -e["weight"])[:c["k"]]
            out.append({"kind": "concentration", "bits": round(-M.log2(c["k"] / c["n"]), 1),
                        "head": f"{c['k']} of {c['n']:,} commits", "text": f"hold {100 * c['held']:.0f}% of all lines changed "
                        f"(Gini {c['gini']:.2f}). The heaviest: \"{heavy[0]['title']}\" ({heavy[0]['weight']:,} lines).",
                        "refs": [e["ref"] for e in heavy][:8]})
    for facet in ("role", "area"):
        for r in M.regime_changes([str(e.get(facet)) for e in live], [e["t"] for e in live], [e["ref"] for e in live], facet)[:2]:
            label = {"agent": "AI agents start committing", "human": "people start committing"}.get(r["value"], f"work on `{r['value']}` begins")
            out.append({"kind": "regime", "bits": round(r["bits"], 1), "head": date(r["at"]), "text": f"{label}: none in the first "
                        f"{r['before']:,} events, then {100 * r['share']:.0f}% of everything after ({r['count']:,}).",
                        "refs": [r["ref"]], "facet": facet, "value": r["value"]})
    leads, rest, seen = [], [], set()
    for x in sorted(out, key=lambda x: (-x["bits"], x["kind"])):
        (rest if x["kind"] in seen else leads).append(x)
        seen.add(x["kind"])
    return leads + rest


def _bins(events: List[Dict]) -> Dict:
    """Activity per bin by role, for the chart: days for a record under half a year, weeks under four years, else months."""
    if not events:
        return {"unit": "day", "rows": []}
    first, last = events[0]["t"], events[-1]["t"]
    span = last - first
    unit = "day" if span <= 183 * DAY else "week" if span <= 4 * 365 * DAY else "month"
    step = DAY if unit == "day" else 7 * DAY if unit == "week" else 30.44 * DAY
    start = first - first % DAY
    count = int((last - start) // step) + 1
    rows = [{"t": start + i * step, "human": 0, "agent": 0, "bot": 0, "system": 0} for i in range(count)]
    for e in events:
        rows[min(count - 1, int((e["t"] - start) // step))][e["role"] if e["role"] in rows[0] else "system"] += 1
    return {"unit": unit, "step": step, "rows": rows}
