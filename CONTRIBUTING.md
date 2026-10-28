# Contributing

Thanks for looking. repo-miner is small on purpose: Python's standard library and git, nothing else.

## Set up

```bash
git clone https://github.com/corgido/repo-miner && cd repo-miner
python3 -m unittest discover -s tests      # about a minute
bin/repo-miner demo                         # ends "demo: clean"
bin/repo-miner .                            # mine this repository
```

Python 3.9 is the oldest supported version, so no `match`, no `X | Y` in annotations at runtime, no newer standard-library
calls. CI runs 3.9 on macOS (the current Ubuntu runner has no 3.9), and 3.11 and 3.13 on both.

## Layout

```text
skills/repo-miner/
  SKILL.md              what Claude reads: run the miner, read the report, dig, hand over
  mine.py               entry point that needs no install
  repo_miner/
    cli.py              the command line
    miner.py            the run: read, sort, measure, write, scan
    target.py           a path, a folder of repositories, or a URL to clone
    gitlog.py           git: refs, tags, every commit with its files
    survey.py           branches, the main line, tags, tree, the repository's documents
    history.py          roles, people, areas, hotspots, reverts, gone folders, secret-looking files, messages
    practices.py        CI, ownership, hooks, linters, agent instructions; current and dropped
    transcripts.py      Claude Code sessions, when present
    measures.py         entropy, chapters, lifts, words, surprises
    timeline.py         events into chapters and surprises
    findings.py         the rules that make findings
    report.py, doc.py   REPORT.md and report.html from one document model
    briefs.py           one brief per chapter, from templates/
    privacy.py          the redactor, aliases, the secret check, the leak scan
    demo.py             the invented repository and the demo check
tests/                  unittest; most tests mine the demo repository
.claude-plugin/         plugin and marketplace manifests, icon
bin/repo-miner          launcher for a clone
```

## Rules for changes

- **Every finding has evidence and a way to check it.** A new finding needs a rule in `findings.py`, a row in
  `docs/HOW-IT-WORKS.md`, something planted for it in `demo.py`, and a test.
- **No judgements.** Findings state what the record shows. Questions are for the people, not about them.
- **Everything written goes through `Writer`.** Never `open(..., "w")` in the output folder.
- **Deterministic.** Sort with a full key (ties broken by name or id); no wall-clock time outside `run.json`.
- **Try it on real repositories** before sending a change that affects findings. Small, old, busy and agent-built ones
  all break things differently; say which you tried.

If you change the skill or the manifests, `claude plugin validate .` checks them.

## Reporting a problem

Open an issue with the command you ran, what you expected, and what you got. Please do not paste a report from a private
repository: describe the shape instead (how many commits and branches, what was found or missed).
