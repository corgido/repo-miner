# Changelog

## 0.1.1 (2026-11-11)

Tidying, no change to what the miner finds.

- Removed the `bin/` launcher. Claude Code puts a plugin's `bin/` folder on the PATH of whoever installs it, which is
  more than this plugin needs. From a clone, run `python3 skills/repo-miner/mine.py`; the skill already did.
- New: [docs/WHAT-IT-TOUCHES.md](docs/WHAT-IT-TOUCHES.md), everything the miner runs, reads and writes, including how it
  checks secret-looking files and what it takes from Claude Code transcripts.
- The README says where the plugin is installed from, and why it is not in Anthropic's plugin directory.

## 0.1.0 (2026-10-28)

First public release.

- One command for a repository, a folder of repositories, or a git URL (cloned with every branch).
- `REPORT.md` and `report.html`: the short version, warnings about the record itself, ranked findings with evidence, a
  `git` command and a question each, then chapters, people, areas, branches and releases, practices and documents.
- Findings: the default branch hiding the work, secret-looking files (checked for credential-shaped content, never
  printed), people gone quiet, one-person areas, AI agents arriving, folders removed or moved, reverts, fix hotspots
  against the repository's own baseline, unmerged and unrelated branches, sweeping commits, silences, thin commit
  messages, unreleased work, dropped CI.
- Chapters cut at silences and changes of character, measured in bits; deterministic.
- Claude Code transcripts read when present (people's words and agents' visible replies only).
- Privacy: one redacting writer, a leak scan of the output, `--deny`, `--anonymise`.
- A Claude Code plugin and skill, a no-install launcher, and a `pipx`-installable package.
