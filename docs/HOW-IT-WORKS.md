# How it works

repo-miner turns a git history into a report in four steps: read, sort, measure, write. Nothing in it is a model. Every
number is counted, every threshold is written down here, and the same history always gives the same report, byte for byte
(only `run.json`, which records when it ran, differs).

## 1. Read

| What | How |
|---|---|
| Every commit on every branch | one `git log --all --raw --numstat`: author, time, subject, body, and each file's status and lines changed |
| Branches | `git for-each-ref`: local and remote-tracking, one entry per branch name; a local branch adds what it has not pushed |
| How each branch relates to the main line | `rev-list --count` both ways, and `merge-base` for unrelated histories |
| Tags | `for-each-ref refs/tags`, and how many commits the main line has gained since the latest |
| Files now | `ls-tree` at the tip of the main line |
| Large files ever committed | `rev-list --objects --all` with `cat-file --batch-check` |
| The repository's own documents | up to 20, best first (README, agent instructions, architecture and decision records, contributing, changelog, `docs/`) |
| Practices | files matching known paths on any branch (CI, code owners, hooks, linters, dependency bots, release tooling, agent instructions and tooling), and when each was adopted or dropped |
| Agent transcripts | Claude Code keeps sessions under `~/.claude/projects/<path>`; read when present, unless `--transcripts none` |

Nothing is checked out and nothing is run. A URL is cloned once with every branch (`--no-single-branch --no-checkout`) into
`~/.cache/repo-miner/clones/` and fetched on later runs.

**The main line** is the default branch, unless the default branch is a trap: when another branch has at least ten commits
and more than twice as many, that branch is the main line, and "now" (files, what is gone, what is unmerged) is measured
against it.

**One person, one name.** Names that differ only in case or spacing are one person, and so are names that share an e-mail
address (placeholder addresses such as `you@example.com` aside). The spelling a person uses most is the one shown. A
`.mailmap` is honoured. Addresses are never written anywhere.

## 2. Sort

**Roles.** An author whose name matches a known AI coding tool (Claude, Copilot, Cursor, Devin, Codex, Aider, Gemini and
others) is an *agent*. A known automation account (`[bot]` names, Dependabot, Renovate, GitHub Actions and others) is a
*bot*. Everyone else is a *person*. A person's commit with an agent in a `Co-Authored-By` trailer is *made with an agent*.
`--agent`, `--bot` and `--human` override the rules.

**Areas.** A commit's area is the folder it touches most. Top-level folders, except that a folder holding more than a quarter
of all file changes is split one level deeper (so a repository whose code is all under `src/` gets `src/api`, `src/billing`).

**Fixes.** A commit whose subject says fix, bug, hotfix, patch, regression, broken, crash, oops, typo or revert.

## 3. Measure

### Chapters

The record of commits (and transcript messages, when read) by people and agents is cut into chapters:

1. **Silences.** A gap is a silence when it is at least six times the record's 90th-percentile gap, and at least four hours.
   The longest silences cut first, up to half the number of chapters, so the quiet early years of an old project cannot use
   up every cut.
2. **Changes of character.** Each event has a role, a kind, a repository and an area. A segment is split where the split
   gains the most information, measured as the drop in entropy (in bits, times the number of events) summed over those
   facets, while that gain beats 0.5 × degrees of freedom × log₂ n, a BIC-style penalty. Greedy binary segmentation, the
   best split anywhere first.
3. Chapters smaller than half the minimum size join the neighbour nearer in time.

The number of chapters is at most 1.4 × log₂ of the number of events, between 4 and 12. Each chapter reports what it has
more of than the whole record (lift = log₂(p(value | chapter) / p(value)), shown when at least half a bit) and the words it
owns (used at least four times in the record, at least 40% of the uses inside the chapter). Its label is its distinctive
area and its top words. Merge boilerplate, trailers, credits ("thanks to ..."), identifiers and the names of people and
tools are not words.

### Surprises

Each is scored in bits of self-information, so they can be ranked against one another:

| Surprise | Measure |
|---|---|
| Silence | gap ÷ mean gap × log₂ e (an exponential model of gaps) |
| Burst | −log₂ P(X ≥ k) for the busiest hour or day under a Poisson rate |
| Concentration | a handful of commits holding half of all lines changed (−log₂ of their share of commits) |
| Something begins | a role or area absent from the first stretch of the record and common after it |

## 4. Find

Each finding is a fixed rule. Scores rank them (higher first, ties by id), and only some findings ask a question.

| Finding | Rule | Score |
|---|---|---|
| Secret-looking file | a path such as `.env`, `*.pem`, `id_rsa`, `credentials.json`, `*.tfstate` was ever committed and one of its last five versions held text that looks like a credential (tokens, keys, connection strings, or `SECRET=...` with a real-looking value) | 100 if still there, 85 if removed; 25 less under a test or example folder |
| Branch trap | the main line is not the default branch (see above) | 90 |
| Unpushed or local-only branch | a local branch has commits its remote lacks, or exists only locally | 85 |
| Quiet person | at least 2% of commits (and at least 5), no commit in the last fifth of the record (at least 90 days), and still the main author of an area that exists, or active in the second half of the record | 60 + 20 × share, +10 if still an owner |
| Agents | at least 20% of commits by agents or made with one | 65 |
| Gone folder | at least 5 files, gone from the main line, removed by the main line's own history | 60 + commits ÷ 5 (up to 30) |
| Moved folder | the files the last removal took reappear with the same sub-paths elsewhere | 30 |
| Reverts | any `Revert "..."` or `This reverts commit ...` | 55 + count (up to 20) |
| One person's area | at least 20 commits, one person 80% or more, the area still exists | 55 |
| Unmerged branch | at least 5 commits of its own; release lines, `gh-pages` and similar are left out | 50 if stale (90 days or a tenth of the span before the end), else 35; + own commits ÷ 4 (up to 25) |
| Unrelated history | a branch with no common ancestor, not of a known purpose | 50 |
| Fix hotspot | at least 5 fixes, and a fix share of at least 35% and 1.5 × the repository's own | 50 + fixes ÷ 2 (up to 15) |
| Large files | blobs of 5 MB or more anywhere in history | 50 |
| Sweeping commit | at least 40 files or 15% of the tree, not the first commit, not a translation sync, not a backport of one already listed | 45 |
| Silence | one of the record's longest gaps, and at least 2% of its span | 40 + bits ÷ 4 (up to 15) |
| Thin messages | at least 20% of commit subjects are a word or two ("wip", "fix", "update") | 45 |
| Unreleased | 50 or more commits on the default branch since the latest tag | 40 |
| CI removed | a CI file was deleted and none exists now | 55 |
| Something begins | an area absent from the first stretch of the record and common after it (from the surprises) | 30 |
| Secret-looking names, checked | files with secret-sounding names whose last five versions held nothing that looks like a credential | 20 |

## 5. Write

Every file goes through one writer that redacts before writing. The report is built once as a small document model and
rendered twice: Markdown (`REPORT.md`) and a static HTML page (`report.html`, no scripts, no external requests; commit text
is escaped, links allow only web addresses and relative paths). After writing, the miner scans its own output for
addresses, tokens, keys, home paths, deny-list words and, with `--anonymise`, real names. The result is in `run.json` and
printed at the end.
