"""Small shared pieces: dates, durations, numbers and tables. All times are UTC."""
from __future__ import annotations

import datetime as dt
from typing import Iterable, List, Sequence

DAY = 86_400


def date(t: float) -> str:
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%d")


def when(t: float) -> str:
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%d %H:%M")


def parse_time(s: str) -> float:
    """An ISO date or time (a bare date is midnight UTC)."""
    s = s.strip().replace("Z", "+00:00")
    d = dt.datetime.fromisoformat(s if "T" in s or " " in s else s + "T00:00:00+00:00")
    return (d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)).timestamp()


def duration(seconds: float) -> str:
    h = seconds / 3600
    if h < 1:
        return f"{max(1, round(seconds / 60))} min"
    if h < 48:
        return f"{h:.1f} h" if h < 10 else f"{round(h)} h"
    d = h / 24
    if d < 60:
        return f"{d:.1f} days" if d < 10 else f"{round(d)} days"
    if d < 730:
        return f"{d / 30.44:.1f} months" if d < 300 else f"{round(d / 30.44)} months"
    return f"{d / 365.25:.1f} years"


def n(x: float) -> str:
    return f"{x:,.0f}"


def pct(x: float) -> str:
    return f"{100 * x:.0f}%"


def plural(k: int, word: str, words: str = "") -> str:
    return f"{k:,} {word if k == 1 else (words or word + 's')}"


def tsv(header: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    clean = lambda v: str("" if v is None else v).replace("\t", " ").replace("\n", " ")
    return "\n".join("\t".join(map(clean, r)) for r in [header, *rows]) + "\n"


def top(items: List, k: int) -> List:
    return items[:k] if len(items) > k else items
