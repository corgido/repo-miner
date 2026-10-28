"""The measures, all in bits. Nothing here knows what an event is about: it sees times, roles, kinds, facets and words.

  stratify       cut a time-ordered record into chapters: first at its silences (gaps far longer than its own rhythm), then
                 where its composition changes, keeping a cut only when the information it gains beats a BIC-style penalty
  lifts          what a chapter has more of than the whole: lift = log2(p(value | chapter) / p(value))
  own_terms      the words a chapter owns: used often overall, and mostly inside it
  poisson_tail   how surprising a burst is, in bits
  concentration  how few events hold half the weight, and the Gini coefficient
  regime_changes a value that is absent for a long while, then common
"""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Callable, Dict, List, Optional, Sequence


def log2(x: float) -> float:
    return math.log(x, 2)


def _clog(c: int) -> float:
    return c * math.log2(c) if c > 0 else 0.0


def entropy(counts: Sequence[int]) -> float:
    n = sum(counts)
    return -sum((c / n) * log2(c / n) for c in counts if c > 0) if n else 0.0


def stratify(times: Sequence[float], values: Sequence[Sequence[str]], seam_gap: float,
             min_size: int = 8, max_strata: int = 12) -> List[Dict]:
    """Cut points of a time-ordered record. `values[i]` holds event i's value for each facet.

    Gaps of at least `seam_gap` seconds cut, the longest first, up to half of `max_strata`. Then greedy binary segmentation: the best split of any segment is taken
    while its gain (the drop in total entropy x size, summed over facets) beats 0.5 x degrees of freedom x log2(segment size).
    Layers smaller than half of `min_size` join the neighbour nearer in time; above `max_strata`, the closest neighbours join.
    """
    n = len(times)
    if not n:
        return []
    k = len(values[0]) if values else 0
    vocab = [sorted({v[j] for v in values}) for j in range(k)]
    index = [{x: i for i, x in enumerate(vs)} for vs in vocab]
    code = [[index[j][v[j]] for j in range(k)] for v in values]
    dof = sum(max(0, len(vs) - 1) for vs in vocab)

    def cost(counts: List[List[int]], size: int) -> float:  # size x entropy, summed over facets
        return sum(_clog(size) - sum(_clog(c) for c in cs) for cs in counts) if size else 0.0

    def best(a: int, b: int) -> Optional[Dict]:
        if b - a < 2 * min_size:
            return None
        left = [[0] * len(vs) for vs in vocab]
        right = [[0] * len(vs) for vs in vocab]
        for i in range(a, b):
            for j in range(k):
                right[j][code[i][j]] += 1
        whole = cost(right, b - a)
        for i in range(a, a + min_size):
            for j in range(k):
                left[j][code[i][j]] += 1
                right[j][code[i][j]] -= 1
        s_left = [sum(_clog(c) for c in cs) for cs in left]
        s_right = [sum(_clog(c) for c in cs) for cs in right]
        top = None
        for m in range(a + min_size, b - min_size + 1):
            nl, nr = m - a, b - m
            gain = whole - sum(_clog(nl) - s for s in s_left) - sum(_clog(nr) - s for s in s_right)
            score = gain + 1e-3 * (times[m] - times[m - 1])   # among near-equal gains, prefer the cut where time jumps
            if top is None or score > top["score"]:
                top = {"m": m, "gain": gain, "score": score}
            if m < b - min_size:                              # move event m from the right side to the left
                for j in range(k):
                    v = code[m][j]
                    s_left[j] += _clog(left[j][v] + 1) - _clog(left[j][v])
                    s_right[j] += _clog(right[j][v] - 1) - _clog(right[j][v])
                    left[j][v] += 1
                    right[j][v] -= 1
        penalty = 0.5 * dof * log2(b - a)
        return dict(top, penalty=penalty) if top and top["gain"] > penalty else None

    # the longest silences cut first, but they may take at most half of the chapters: in an old record the early years
    # are full of pauses, and a recent decade without one must still be cut where its character changes
    silences = sorted((i for i in range(1, n) if times[i] - times[i - 1] >= seam_gap), key=lambda i: (times[i - 1] - times[i], i))
    segs, s = [], 0
    for i in sorted(silences[:max(1, max_strata // 2)]):
        segs.append((s, i))
        s = i
    segs.append((s, n))
    cuts = [{"seg": seg, "split": best(*seg), "seam": True, "gain": None} for seg in segs]
    while len(cuts) < max_strata:
        pick = -1
        for i, c in enumerate(cuts):
            if c["split"] and (pick < 0 or c["split"]["gain"] - c["split"]["penalty"]
                               > cuts[pick]["split"]["gain"] - cuts[pick]["split"]["penalty"]):
                pick = i
        if pick < 0:
            break
        (a, b), m, gain = cuts[pick]["seg"], cuts[pick]["split"]["m"], cuts[pick]["split"]["gain"]
        cuts[pick:pick + 1] = [{"seg": (a, m), "split": best(a, m), "seam": cuts[pick]["seam"], "gain": cuts[pick]["gain"]},
                               {"seg": (m, b), "split": best(m, b), "seam": False, "gain": gain}]
    out = [{"a": c["seg"][0], "b": c["seg"][1], "seam": c["seam"], "gain": c["gain"]} for c in cuts]

    def join(i: int) -> None:
        x, y = out[i], out[i + 1]
        out[i:i + 2] = [{"a": x["a"], "b": y["b"], "seam": x["seam"], "gain": x["gain"]}]

    while len(out) > 1:
        small = next((i for i, x in enumerate(out) if x["b"] - x["a"] < max(3, min_size // 2)), -1)
        if small < 0:
            break
        if small == 0:
            join(0)
        elif small == len(out) - 1:
            join(small - 1)
        else:
            gap_left = times[out[small]["a"]] - times[out[small - 1]["b"] - 1]
            gap_right = times[out[small + 1]["a"]] - times[out[small]["b"] - 1]
            join(small - 1 if gap_left <= gap_right else small)
    while len(out) > max_strata:
        gaps = [times[out[i + 1]["a"]] - times[out[i]["b"] - 1] for i in range(len(out) - 1)]
        join(gaps.index(min(gaps)))
    return out


def lifts(all_values: List[str], inside: List[str], facet: str, min_count: int = 3) -> List[Dict]:
    """Values of one facet that a chapter has more of than the whole record, in bits, with their counts."""
    every, mine = Counter(all_values), Counter(inside)
    total, here = len(all_values), len(inside)
    rows = []
    for v, c in mine.items():
        if c < min_count or v in ("(none)", ""):
            continue
        lift = log2((c / here) / (every[v] / total))
        rows.append({"facet": facet, "value": v, "count": c, "of": every[v], "lift": round(lift, 2)})
    return sorted(rows, key=lambda r: (-r["lift"] * math.sqrt(r["count"]), r["value"]))


STOP = set("""a about above after again all also am an and any are as at be because been before being below between both but by
can could did do does doing done down during each few for from further had has have having he her here hers him his how i if in
into is it its itself just let me more most my no nor not now of off on once only or other our out over own same she should so
some such than that the their them then there these they this those through to too under until up very was we were what when
where which while who whom why will with would you your yours yes ok okay one two get got make made use used new via per like
well still even much many really need want see go going lets thats add adds added update updates updated remove removes removed
fix fixes fixed change changes changed merge merged branch pull request into from main master commit wip initial bump version
co-authored-by signed-off-by reviewed-by generated https http www com github org closes close closed resolves resolved
refs issue issues see also""".split())
TOOL_WORDS = {"claude", "opus", "sonnet", "haiku", "fable", "anthropic", "gpt", "codex", "copilot", "noreply", "dependabot"}
_WORD = re.compile(r"[^\W\d_][\w'’-]{2,}", re.U)


_BOILERPLATE = re.compile(r"^[\w-]+:\s.*$|^Merge (pull request|branch|remote-tracking branch).*$|\(#\d+\)|\bfrom [\w.-]+/[\w./-]+"
                          r"|\b(thanks|thank you|props|kudos|credit|patch|reported|suggested|contributed|reviewed|written)"
                          r"( to| from| by)?,? [\w.-]+( and [\w.-]+)?", re.I | re.M)


def tokens(text: str, exclude: frozenset = frozenset()) -> List[str]:
    """Content words. Identifiers (hashes, ids, long tokens with digits), trailers, merge boilerplate and the names of
    tools and people are not words."""
    out = []
    for w in _WORD.findall(_BOILERPLATE.sub(" ", text or "").lower()):
        w = re.sub(r"['’]s$", "", w).rstrip("'’-")
        if len(w) <= 2 or w in STOP or w in TOOL_WORDS or w in exclude or len(w) >= 16 or (re.search(r"\d", w) and len(w) >= 8) or "_" in w:
            continue
        out.append(w)
    return out


def own_terms(every: Counter, mine: Counter, min_count: int = 4, top: int = 6) -> List[Dict]:
    """Words used at least `min_count` times in the record, at least 40% of them inside this chapter (word counts in)."""
    total, here = sum(every.values()) or 1, sum(mine.values()) or 1
    rows = [{"term": w, "count": c, "share": round(c / every[w], 2), "lift": round(log2((c / here) / (every[w] / total)), 2)}
            for w, c in mine.items() if every[w] >= min_count and c >= 3 and c / every[w] >= 0.4]
    return sorted(rows, key=lambda r: (-r["count"] * r["lift"], r["term"]))[:top]


def poisson_tail_bits(x: int, lam: float) -> float:
    """-log2 P(X >= x) for a Poisson count with mean `lam`."""
    if x <= lam or lam <= 0:
        return 0.0
    log_term = -lam + x * math.log(lam) - math.lgamma(x + 1)
    total = 0.0
    for i in range(x, x + 200):
        total += math.exp(log_term)
        log_term += math.log(lam) - math.log(i + 1)
    return -log2(total) if total > 0 else 64.0


def concentration(weights: List[float], share: float = 0.5) -> Dict:
    w = sorted((x for x in weights if x > 0), reverse=True)
    total = sum(w)
    acc, k = 0.0, 0
    while k < len(w) and acc < share * total:
        acc += w[k]
        k += 1
    asc = list(reversed(w))
    g = sum((2 * (i + 1) - len(asc) - 1) * x for i, x in enumerate(asc))
    return {"k": k, "n": len(w), "held": acc / total if total else 0, "gini": g / (len(asc) * total) if total else 0}


def regime_changes(values: List[str], times: List[float], refs: List[str], facet: str,
                   min_count: int = 10, min_share: float = 0.2) -> List[Dict]:
    """A value absent from the first stretch of the record and common after it, with the bits of that absence."""
    rows = []
    n = len(values)
    for v, c in Counter(values).items():
        if c < min_count or v in ("(none)", ""):
            continue
        first = values.index(v)
        if first < min_count:
            continue
        share, p = c / (n - first), c / n
        if share < min_share or p >= 1:
            continue
        rows.append({"facet": facet, "value": v, "at": times[first], "ref": refs[first], "before": first,
                     "count": c, "share": share, "bits": -first * log2(1 - p)})
    return sorted(rows, key=lambda r: (-r["bits"], r["value"]))


def facet_values(events: List[Dict], keys: List[str]) -> List[List[str]]:
    return [[str(e.get(k, "(none)")) for k in keys] for e in events]


def usable_facets(events: List[Dict], candidates: List[str]) -> List[str]:
    """Facets with 2 to 40 values: fewer tells nothing apart, more is an identifier, not a category."""
    keep = []
    for k in candidates:
        size = len({e.get(k) for e in events})
        if 2 <= size <= 40:
            keep.append(k)
    return keep or candidates[:1]


def group(xs, key: Callable):
    out: Dict = {}
    for x in xs:
        out.setdefault(key(x), []).append(x)
    return out
