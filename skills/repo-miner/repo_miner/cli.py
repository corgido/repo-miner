"""repo-miner: understand a repository from its history.

  repo-miner PATH | FOLDER | URL ...     mine one repository, every repository in a folder, or a git URL (cloned, every branch)
  repo-miner demo [--keep]               mine an invented messy repository and check what was planted is found
  repo-miner scan FOLDER [--deny FILE]   leak-scan a report folder before sharing it (exit 1 on any hit, never prints the hit)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["demo"] and not Path("demo").exists():
        from . import demo
        return demo.run(keep="--keep" in argv)
    if argv[:1] == ["scan"] and not Path("scan").exists():
        return _scan(argv[1:])

    ap = argparse.ArgumentParser(
        prog="repo-miner", description="Understand a repository from its history: what happened, who knows, and what to ask.",
        epilog="Also: 'repo-miner demo' (try it on an invented repository) and 'repo-miner scan FOLDER' (leak-scan a report). "
               "Reports go to ~/repo-miner-reports/<name>/ unless --out says otherwise.")
    ap.add_argument("targets", nargs="+", metavar="TARGET", help="a repository, a folder of repositories, or a git URL")
    ap.add_argument("-o", "--out", help="where the report goes (default ~/repo-miner-reports/<name>)")
    ap.add_argument("--since", help="only commits after this date (YYYY-MM-DD)")
    ap.add_argument("--until", help="only commits before this date")
    ap.add_argument("--deny", metavar="FILE", help="a file of words (names, codenames, clients) that must never appear in the report")
    ap.add_argument("--anonymise", "--anonymize", action="store_true", help="show people as Person A, Person B, ...")
    ap.add_argument("--transcripts", default="auto", metavar="auto|none|DIR",
                    help="Claude Code session transcripts: found automatically for local repositories (default), or none, or a folder")
    ap.add_argument("--agent", action="append", default=[], metavar="NAME", help="an author who is an AI agent (repeatable)")
    ap.add_argument("--bot", action="append", default=[], metavar="NAME", help="an author who is automation (repeatable)")
    ap.add_argument("--human", action="append", default=[], metavar="NAME", help="an author who is a person, whatever the name looks like")
    ap.add_argument("--depth", type=int, help="clone URLs with at most this many commits per branch (default: all)")
    ap.add_argument("--force", action="store_true", help="write into an --out folder that is not an earlier report (its contents are removed)")
    ap.add_argument("--json", action="store_true", help="print the run summary as JSON")
    ap.add_argument("-q", "--quiet", action="store_true", help="print only the summary")
    ap.add_argument("--version", action="version", version=f"repo-miner {__version__}")
    a = ap.parse_args(argv)

    from .miner import Options, mine
    summary = mine(Options(a.targets, out=a.out, since=a.since, until=a.until, deny_file=a.deny, anonymise=a.anonymise,
                           transcripts=a.transcripts, agents=a.agent, bots=a.bot, humans=a.human, depth=a.depth,
                           force=a.force, quiet=a.quiet or a.json))
    if a.json:
        print(json.dumps(summary, indent=1))
        return 0
    print()
    for r in summary["repositories"]:
        print(f"  {r['name']}: {r['commits']:,} commits · {r['branches']:,} branches · {r['people']:,} people · "
              f"{r['chapters']} chapters · {r['findings']} things stand out · {r['questions']} questions")
    scan = summary["leak_scan"]
    print(f"  leak scan: {scan}" + ("" if scan == "clean" else " (run 'repo-miner scan' on the folder and read those files before sharing)"))
    print(f"\n  Start here: {summary['report']}\n  In a browser: {summary['html']}\n")
    return 0


def _scan(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(prog="repo-miner scan", description="Leak-scan a folder. Prints file and kind, never the match.")
    ap.add_argument("folder")
    ap.add_argument("--deny", metavar="FILE")
    a = ap.parse_args(argv)
    from .privacy import read_deny_file, scan
    hits = scan(Path(a.folder), read_deny_file(a.deny))
    for path, kind in hits:
        print(f"{path}: {kind}")
    print("scan: clean" if not hits else f"scan: {len(hits)} hit(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
