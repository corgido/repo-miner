"""A tiny document model rendered two ways: Markdown (REPORT.md, for agents and editors) and HTML (report.html, for people).

Inline text may use `code`, **bold** and [links](url). Everything else is escaped.
"""
from __future__ import annotations

import html
import re
from typing import List, Optional, Sequence, Union

Block = tuple


class Doc:
    def __init__(self) -> None:
        self.blocks: List[Block] = []

    def h(self, level: int, text: str, anchor: Optional[str] = None) -> "Doc":
        self.blocks.append(("h", level, text, anchor or slug(text)))
        return self

    def p(self, text: str) -> "Doc":
        self.blocks.append(("p", text))
        return self

    def note(self, text: str) -> "Doc":
        self.blocks.append(("note", text))
        return self

    def ul(self, items: Sequence[str]) -> "Doc":
        if items:
            self.blocks.append(("ul", list(items)))
        return self

    def ol(self, items: Sequence[str]) -> "Doc":
        if items:
            self.blocks.append(("ol", list(items)))
        return self

    def table(self, header: Sequence[str], rows: Sequence[Sequence[object]], numeric: Sequence[int] = ()) -> "Doc":
        if rows:
            self.blocks.append(("table", list(header), [list(map(_cell, r)) for r in rows], set(numeric)))
        return self

    def code(self, text: str, lang: str = "") -> "Doc":
        self.blocks.append(("code", text, lang))
        return self

    def details(self, summary: str, body: Union["Doc", Sequence[Block]]) -> "Doc":
        self.blocks.append(("details", summary, body.blocks if isinstance(body, Doc) else list(body)))
        return self

    def html_only(self, markup: str) -> "Doc":
        self.blocks.append(("html", markup))
        return self

    def extend(self, other: "Doc") -> "Doc":
        self.blocks += other.blocks
        return self


def _cell(v: object) -> str:
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:,.2f}"
    if isinstance(v, int) and not isinstance(v, bool):
        return f"{v:,}"
    return str(v)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", re.sub(r"[`*]", "", text.lower())).strip("-")[:60]


# ─────────────────────────────────────────────────────────────── Markdown


def to_markdown(blocks: List[Block]) -> str:
    out: List[str] = []
    for b in blocks:
        kind = b[0]
        if kind == "h":
            out += ["#" * b[1] + " " + b[2], ""]
        elif kind in ("p", "note"):
            out += [("> " if kind == "note" else "") + b[1], ""]
        elif kind in ("ul", "ol"):
            out += [(f"{i + 1}. " if kind == "ol" else "- ") + x for i, x in enumerate(b[1])] + [""]
        elif kind == "table":
            _, header, rows, numeric = b
            esc = lambda s: s.replace("|", "\\|").replace("\n", " ")
            out.append("| " + " | ".join(header) + " |")
            out.append("|" + "|".join("---:" if i in numeric else "---" for i in range(len(header))) + "|")
            out += ["| " + " | ".join(esc(c) for c in r) + " |" for r in rows]
            out.append("")
        elif kind == "code":
            fence = "~~~~" if "```" in b[1] else "```"
            out += [fence + b[2], b[1].rstrip("\n"), fence, ""]
        elif kind == "details":
            out += [f"<details><summary>{inline_html(b[1])}</summary>", "", to_markdown(b[2]).rstrip("\n"), "", "</details>", ""]
        elif kind == "html":
            continue
    return "\n".join(out).rstrip("\n") + "\n"


# ─────────────────────────────────────────────────────────────── HTML

_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*(.+?)\*\*")


# a web address or a relative path; any other scheme (javascript:, data:) stays plain text
_LINK_ANY = re.compile(r"\[((?:`[^`]+`|[^\]])+)\]\(((?:https?://|(?![A-Za-z][\w+.-]*:))[^)\s]+)\)")


def inline_html(text: str) -> str:
    # links first, so a link whose label is code ([`a1b2c3d`](url)) is not split apart by the code spans
    links: List[str] = []

    def hold(m: "re.Match[str]") -> str:
        links.append(f'<a href="{html.escape(m.group(2))}">{inline_html(m.group(1))}</a>')
        return f"\x00{len(links) - 1}\x00"
    text = _LINK_ANY.sub(hold, text)
    parts = _CODE.split(text)
    out = []
    for i, part in enumerate(parts):
        if i % 2:
            out.append(f"<code>{html.escape(part)}</code>")
            continue
        s = html.escape(part, quote=False)
        s = _BOLD.sub(r"<b>\1</b>", s)
        out.append(s)
    return re.sub(r"\x00(\d+)\x00", lambda m: links[int(m.group(1))], "".join(out))


def to_html(blocks: List[Block]) -> str:
    out: List[str] = []
    for b in blocks:
        kind = b[0]
        if kind == "h":
            out.append(f'<h{b[1]} id="{b[3]}">{inline_html(b[2])}</h{b[1]}>')
        elif kind == "p":
            out.append(f"<p>{inline_html(b[1])}</p>")
        elif kind == "note":
            out.append(f'<p class="note">{inline_html(b[1])}</p>')
        elif kind in ("ul", "ol"):
            out.append(f"<{kind}>" + "".join(f"<li>{inline_html(x)}</li>" for x in b[1]) + f"</{kind}>")
        elif kind == "table":
            _, header, rows, numeric = b
            th = "".join(f'<th{" class=n" if i in numeric else ""}>{inline_html(h)}</th>' for i, h in enumerate(header))
            trs = "".join("<tr>" + "".join(f'<td{" class=n" if i in numeric else ""}>{inline_html(c)}</td>' for i, c in enumerate(r)) + "</tr>"
                          for r in rows)
            head = f"<thead><tr>{th}</tr></thead>" if any(header) else ""
            out.append(f'<div class="scroll"><table>{head}<tbody>{trs}</tbody></table></div>')
        elif kind == "code":
            out.append(f"<pre><code>{html.escape(b[1].rstrip())}</code></pre>")
        elif kind == "details":
            out.append(f"<details><summary>{inline_html(b[1])}</summary><div>{to_html(b[2])}</div></details>")
        elif kind == "html":
            out.append(b[1])
    return "\n".join(out)
