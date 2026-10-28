# Changelog

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
