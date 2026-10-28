"""Privacy: one redactor every written file passes through, and a leak scan that never prints what it found.

Redacted on the way out: e-mail addresses, API keys and tokens, JWTs, secret assignments, connection strings, private IP
addresses, home-directory paths, and every word on the deny list. With aliases, people's names become "Person A", "Person B".
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

_RULES: List[Tuple[str, "re.Pattern[str]", str]] = [
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}"), "[email]"),
    ("token", re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"
                         r"|xox[abprs]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|glpat-[A-Za-z0-9_-]{20,})"), "[secret]"),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}"), "[secret]"),
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?(?:-----END [A-Z ]*PRIVATE KEY-----|$)"), "[private key]"),
    ("connection", re.compile(r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://\S+"), "[connection]"),
    ("private-ip", re.compile(r"\b(?:192\.168|10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b"), "[ip]"),
    ("home-path", re.compile(r"(?<![\w.])/(?:home|Users)/(?!user/|runner/|ubuntu/)[A-Za-z0-9._-]+"), "~"),
]
_ASSIGNMENT = re.compile(r"((?:api[_-]?key|access[_-]?key|token|secret|password|passwd|bearer)[\"']?\s*[:=]\s*[\"']?)[^\s\"',;]{12,}", re.I)

_MERGE_HANDLE = re.compile(r"(Merge pull request #\d+ from |Merge branch '[^']*' of [\w.:/-]*?)(?!someone/)[\w.-]+/")
_MENTION = re.compile(r"(?<![\w/.])@(?!someone\b)[A-Za-z0-9][\w-]*(?![\w/.-])")
_COAUTHOR = re.compile(r"(?im)^((?:co-authored-by|signed-off-by|reviewed-by|reported-by|tested-by):[ \t]*)([^<\n]+?)([ \t]*<|[ \t]*$)")
_TOOL_NAME = re.compile(r"claude|copilot|cursor|devin|codex|openai|aider|gemini|\[bot\]|bot$", re.I)

# Addresses that identify a tool, not a person: kept so trailers like Co-Authored-By stay readable.
_KEEP_EMAIL = ("noreply@anthropic.com", "users.noreply.github.com", "@example.com", "@example.org", "@localhost")


class Redactor:
    """Cleans text before it is written. Counts what it removed, by kind, so the report can say so without saying what."""

    def __init__(self, deny: Iterable[str] = (), aliases: Optional[Dict[str, str]] = None):
        words = sorted({w.strip() for w in deny if w.strip() and not w.startswith("#")}, key=len, reverse=True)
        self._deny = re.compile(r"(?<!\w)(?:" + "|".join(map(re.escape, words)) + r")(?!\w)", re.I) if words else None
        self.aliases = dict(aliases or {})
        self._folded = {k.casefold(): v for k, v in self.aliases.items()}
        names = sorted(self.aliases, key=len, reverse=True)
        # case-insensitive: a person's handle in "Merge pull request #12 from jdoe/fix" is their name in another case
        self._names = re.compile(r"(?<!\w)(?:" + "|".join(map(re.escape, names)) + r")(?!\w)", re.I) if names else None
        self.counts: Dict[str, int] = {}

    def _hit(self, kind: str) -> None:
        self.counts[kind] = self.counts.get(kind, 0) + 1

    def name(self, person: str) -> str:
        """A person's display name: their alias when aliasing is on, else the name itself (deny list still applies)."""
        return self.aliases.get(person) or self.clean(person)

    def clean(self, text: Optional[str]) -> str:
        if not text:
            return text or ""
        for kind, rx, to in _RULES:
            def sub(m: "re.Match[str]", kind: str = kind, to: str = to) -> str:
                if kind == "email" and m.group(0).lower().endswith(_KEEP_EMAIL):
                    return m.group(0)
                self._hit(kind)
                return to
            text = rx.sub(sub, text)
        text = _ASSIGNMENT.sub(lambda m: (self._hit("assignment"), m.group(1) + "[secret]")[1], text)
        if self._names:
            text = self._names.sub(lambda m: self._folded[m.group(0).casefold()], text)
            # handles that differ from a name cannot be mapped to an alias, so when anonymising they go too
            text = _MERGE_HANDLE.sub(r"\1someone/", text)
            text = _MENTION.sub("@someone", text)
            text = _COAUTHOR.sub(lambda m: m.group(0) if _TOOL_NAME.search(m.group(2)) else m.group(1) + "someone" + m.group(3), text)
        if self._deny:
            text = self._deny.sub(lambda m: (self._hit("deny"), "[name]")[1], text)
        return text


def read_deny_file(path: Optional[str]) -> List[str]:
    if not path:
        return []
    return [line.strip() for line in Path(path).expanduser().read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")]


def make_aliases(people: Iterable[str]) -> Dict[str, str]:
    """'Person A', 'Person B', ... in the order given (most commits first), then 'Person AA' and on."""
    out: Dict[str, str] = {}
    for i, person in enumerate(people):
        label, n = "", i
        while True:
            label = chr(ord("A") + n % 26) + label
            n = n // 26 - 1
            if n < 0:
                break
        out[person] = f"Person {label}"
    return out


_ENV_SECRET = re.compile(r"(?im)^[ \t]*(?:export[ \t]+)?[\w.-]*(secret|token|passw(or)?d|pwd|api[_-]?key|private[_-]?key|access[_-]?key"
                         r"|auth|credential)[\w.-]*[ \t]*[=:][ \t]*[\"']?(?!<|\$\{|your|changeme|xxx|example|placeholder|dummy|test)"
                         r"[^\s\"']{8,}")


def looks_secret(text: str) -> bool:
    """Does the text hold anything that looks like a live credential? Answers yes or no; never says what or where."""
    if not text:
        return False
    if any(rx.search(text) for kind, rx, _ in _RULES if kind in ("token", "jwt", "private-key", "connection")):
        return True
    return bool(_ENV_SECRET.search(text))


# ─────────────────────────────────────────────────────────────── leak scan

_SCAN = {
    "email": _RULES[0][1],
    "token": _RULES[1][1],
    "jwt": _RULES[2][1],
    "private-key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "home-path": _RULES[6][1],
}


def scan(root: Path, deny: Iterable[str] = ()) -> List[Tuple[str, str]]:
    """(relative path, kind) for every file under `root` that still holds something it should not. Never the match itself."""
    patterns = dict(_SCAN)
    words = [w for w in deny if w]
    if words:
        patterns["deny"] = re.compile(r"(?<!\w)(?:" + "|".join(map(re.escape, words)) + r")(?!\w)", re.I)
    hits = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for kind, rx in patterns.items():
            for m in rx.finditer(text):
                if kind == "email" and m.group(0).lower().endswith(_KEEP_EMAIL):
                    continue
                hits.append((str(path.relative_to(root)), kind))
                break
    return hits


class Writer:
    """Every file the miner writes goes through here, so nothing reaches disk unredacted."""

    def __init__(self, root: Path, redactor: Redactor):
        self.root = root
        self.redactor = redactor
        self.written: List[str] = []

    def text(self, rel: str, content: str, redact: bool = True) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.redactor.clean(content) if redact else content, encoding="utf-8")
        self.written.append(rel)
        return path

    def json(self, rel: str, data: object) -> Path:
        import json
        return self.text(rel, json.dumps(data, indent=1, ensure_ascii=False, sort_keys=False) + "\n")
