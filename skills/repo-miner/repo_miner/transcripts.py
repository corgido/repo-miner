"""Claude Code session transcripts, when the machine that built the repository still has them.

They hold what the commit record cannot: why. Only two kinds of text are read: what a person typed, and what an agent
visibly replied. Reasoning, tool calls and tool output are never read. Injected text (reminders, hook output,
notifications) becomes a textless system event. Everything read is redacted before it is written.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from .util import parse_time

INJECTED = re.compile(r"<(system-reminder|local-command-[\w-]+|command-[\w-]+|task-notification)\b[^>]*>[\s\S]*?</\1>")


def projects_dir() -> Path:
    return Path.home() / ".claude" / "projects"


def find(repo: Path) -> Optional[Path]:
    """Claude Code keeps a project's sessions under ~/.claude/projects/<the path with every non-alphanumeric as ->."""
    folder = projects_dir() / re.sub(r"[^A-Za-z0-9]", "-", str(repo.resolve()))
    return folder if folder.is_dir() else None


LIVE_MINUTES = 10


def live_session_filter(files: List[Path]) -> List[Path]:
    """Leave out the session that is running the miner: when an agent runs repo-miner from inside the repository, its own
    conversation sits in this same folder and would read as the latest chapter of the project's history. Skipped by the
    session id Claude Code exports, and, inside Claude Code, any session written to in the last few minutes."""
    import os
    import time
    own = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    inside = bool(own or os.environ.get("CLAUDECODE"))
    cutoff = time.time() - LIVE_MINUTES * 60
    keep = []
    for f in files:
        if own and own in str(f):
            continue
        if inside and f.stat().st_mtime > cutoff:
            continue
        keep.append(f)
    return keep


def read(folder: Path, source: str) -> List[Dict]:
    files = [folder] if folder.is_file() else live_session_filter(sorted(folder.rglob("*.jsonl")))
    seen, events = set(), []
    for file in files:
        side_file = "/subagents/" in str(file)
        with open(file, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if not line.startswith("{"):
                    continue
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                if o.get("type") not in ("user", "assistant"):
                    continue
                uid = o.get("uuid") or hashlib.sha1(line.encode()).hexdigest()
                if uid in seen:
                    continue
                seen.add(uid)
                try:
                    t = parse_time(o.get("timestamp", ""))
                except ValueError:
                    continue
                content = (o.get("message") or {}).get("content")
                blocks = [{"type": "text", "text": content}] if isinstance(content, str) else content if isinstance(content, list) else []
                text = "\n\n".join(b["text"] for b in blocks if isinstance(b, dict) and b.get("type") == "text"
                                   and isinstance(b.get("text"), str)).strip()
                side = side_file or o.get("isSidechain") is True
                if o["type"] == "assistant":
                    role, kind = "agent", "agent reply" if side else "reply"
                elif o.get("isCompactSummary"):
                    role, kind = "agent", "summary"
                elif side:
                    role, kind = "agent", "brief"
                elif _typed_by_person(o, text):
                    role, kind = "human", "message"
                else:
                    role, kind, text = "system", "injected", ""
                text = INJECTED.sub("", text).strip()
                if not text and role != "system":
                    continue
                session = hashlib.sha1(str(o.get("sessionId") or file).encode()).hexdigest()[:8]
                events.append({"t": t, "role": role, "kind": kind, "source": source, "area": "(sessions)", "session": session,
                               "title": text.split("\n", 1)[0][:120], "text": text, "weight": len(text.split()),
                               "ref": f"session:{session}/{hashlib.sha1(uid.encode()).hexdigest()[:10]}"})
    return events


def _typed_by_person(o: Dict, text: str) -> bool:
    if o.get("isMeta"):
        return False
    origin = o.get("origin")
    if isinstance(origin, dict):
        return origin.get("kind") == "human"
    return not re.match(r"^(<|\[Request interrupted|Caveat:)", text)
