"""One brief per chapter, ready to hand to an agent that writes that chapter's history."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from .privacy import Writer
from .util import DAY, date, parse_time, pct

TEMPLATE = Path(__file__).parent / "templates" / "chapter-brief.md"


def write(R: Dict, out: Writer, prefix: str, anonymised: bool) -> List[str]:
    chapters = R["timeline"].get("chapters", [])
    template = TEMPLATE.read_text(encoding="utf-8")
    made = []
    for c in chapters:
        roles = c["roles"]
        live = sum(roles.get(k, 0) for k in ("human", "agent")) or 1
        facts = [
            f"- {c['events']:,} events ({pct(c['share'])} of the record) over {c['span']}; "
            f"{pct(roles.get('agent', 0) / live)} by AI agents; {c['fixes']:,} fixes.",
            f"- Mostly: {c['label']}.",
        ]
        if c["areas"]:
            facts.append("- Areas: " + ", ".join(f"`{a}`" for a in c["areas"]) + ".")
        if c["people"]:
            facts.append("- People: " + ", ".join(c["people"]) + ".")
        if c["lifts"]:
            facts.append("- More of than elsewhere: " + "; ".join(f"{x['facet']} `{x['value']}` ({x['count']} of {x['of']})" for x in c["lifts"]) + ".")
        facts += [f"- Heavy commit: `{x['ref']}` {x['date']} \"{x['title']}\" ({x['lines']:,} lines)." for x in c["heaviest"]]
        inside = [f for f in R["findings"] if any(c["from"] <= d <= c["to"] for d in _dates(f.title))]
        facts += [f"- Stands out: {f.title}." for f in inside[:4]]
        text = (template.replace("{REPO}", R["name"]).replace("{N}", str(c["n"])).replace("{CHAPTERS}", str(len(chapters)))
                .replace("{FROM}", c["from"]).replace("{TO}", c["to"])
                .replace("{UNTIL}", date(parse_time(c["to"]) + DAY)).replace("{FACTS}", "\n".join(facts))
                .replace("{REPO_PATH}", str(R["path"])).replace("{OUT}", str(out.root)).replace("{PREFIX}", prefix)
                .replace("{PEOPLE_RULE}", " (as aliases: keep them)" if anonymised else ""))
        rel = f"{prefix}briefs/chapter-{c['n']:02d}.md"
        out.text(rel, text)
        made.append(rel)
    return made


def _dates(text: str) -> List[str]:
    import re
    return re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", text)
