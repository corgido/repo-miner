# What it touches

repo-miner is meant to be run by you, on repositories you own or have been given access to. It looks for signs of
committed secrets and it can read your Claude Code transcripts, so this page lists everything it runs, reads and writes,
and where in the code each thing happens. The package is about 3,200 lines of Python using only the standard library, in
`skills/repo-miner/repo_miner/`: short enough to check this page against.

## In one table

| | What it does | Where |
|---|---|---|
| Programs it runs | `git`, and nothing else | `gitlog.py`, `target.py` |
| Network | None of its own. Given a URL, `git clone` and later `git fetch` | `target.py` |
| Your repository | Read through git, committed history only. Never written to, checked out or run | `gitlog.py`, `survey.py`, `practices.py` |
| Secret-looking files | Read in memory to answer yes or no. Content never written | `history.py`, `privacy.py` |
| Claude Code transcripts | Read for local repositories when present. Off with `--transcripts none` | `transcripts.py` |
| Environment variables | Passed to git unchanged. Three read by name | `gitlog.py`, `miner.py`, `transcripts.py` |
| Files it writes | The report folder, a clone cache, a temporary folder for the demo | `miner.py`, `privacy.py`, `demo.py` |
| Telemetry, analytics, update checks | None | |

## Programs and network

The only program repo-miner starts is `git`. The package imports no network library (no `urllib`, `http`, `socket` or
`requests`), so it has no way to send anything anywhere itself.

On a repository on disk it runs read-only git commands: `log`, `show`, `ls-tree`, `for-each-ref`, `rev-list`,
`rev-parse`, `merge-base`, `cat-file --batch-check`, `symbolic-ref`, `branch --show-current`, `remote`,
`remote get-url origin` and `config --get-all remote.origin.fetch`. None of them changes the repository.

Given a URL it runs `git clone --no-single-branch --no-checkout` into a cache folder, and `git fetch --prune --tags` in
that same cache folder on later runs. That is the only network use, and git does it, not repo-miner. Git uses your own
configuration, SSH keys and credential helper, exactly as if you had typed the clone yourself. repo-miner does not read,
store or log those credentials. If the `origin` URL of a repository has a user name or token embedded in it, that part
is cut off before the URL is used or written (`remote_url` in `gitlog.py`).

## What it reads in the repository

Everything comes from git objects: commits on every branch, the file list at each branch tip, and the content of a small
number of files through `git show <ref>:<path>`. The working tree is never opened, so uncommitted files are not read.

Files whose content is read:

- **The repository's own documents** (README, design notes, changelogs and similar, capped in number and size). They are
  copied into the report's `docs/` folder after redaction.
- **Practice files**: CI configuration, code owners, hooks, linter settings, agent instructions. Copied into
  `practices/` after redaction.
- **`package.json`**, for the names of its scripts.
- **Secret-looking files**, described next.

Author e-mail addresses are read from `git log` for one purpose: to recognise one person committing under several
names. They are dropped in memory once that is done and are never written.

## Secret-looking files

This is the part most likely to look alarming in a scan of the code, so in full:

1. Paths in the history are matched against names that usually hold secrets: `.env` (not `.env.example` and the like),
   `*.pem`, `*.key`, `id_rsa` and its siblings, `*.p12`, `*.pfx`, `*.keystore`, `credentials.json`, `secrets.yaml`,
   `.npmrc`, `.pypirc`, `.netrc`, `.htpasswd`, service account JSON, Terraform state. The list is `SENSITIVE` in
   `history.py`.
2. For each match, up to the last five committed versions are read through `git show`, into memory.
3. Each is tested against patterns for the shapes of real credentials: provider key prefixes, JWTs, private key
   headers, connection strings, and assignments with a non-placeholder value (`looks_secret` in `privacy.py`).
4. The report gets the path, the commit that added it, whether it is still present, and yes or no. The content is not
   written, logged, printed or sent anywhere, and the matched text is discarded with the rest of the file.

The point is the question the report then asks: were those credentials rotated? It cannot help you answer that without
looking, and it looks at nothing you could not already read with `git show`.

## Claude Code transcripts

When the target is a repository on disk (not a URL it cloned) and `--transcripts` is left at `auto`, repo-miner looks for
`~/.claude/projects/<that repository's path>/` and reads the `.jsonl` session files there. Nothing outside that one
project folder is read.

- Read: what a person typed, and what an agent visibly replied.
- Not read: reasoning, tool calls, tool output. Injected text (reminders, hook output, notifications) is dropped.
- Left out: the session running the miner, so the conversation that asked for the report does not become part of it.
- What reaches the report: how many sessions and messages there were, when, and the distinctive words of each chapter.
  Messages are not copied into the report.

`--transcripts none` turns it off. `--transcripts DIR` reads a folder you name instead.

## Environment variables

Git is started with your environment unchanged, because it needs `HOME`, `PATH`, your SSH agent and the rest to work as
it does for you. Three settings are added: `GIT_TERMINAL_PROMPT=0`, `GIT_PAGER=cat` and `LC_ALL=C`.

repo-miner itself reads three variables by name:

| Variable | Why |
|---|---|
| `XDG_CACHE_HOME` | where the clone cache goes |
| `CLAUDE_CODE_SESSION_ID`, `CLAUDECODE` | to recognise, and leave out, the session that is running the miner |

None of the three holds a credential. A code scanner will flag "reads the environment and starts a process": that is
this, and the process is git.

## What it writes

| Where | What | Notes |
|---|---|---|
| `~/repo-miner-reports/<name>/`, or `--out DIR` | the report | see below |
| `~/.cache/repo-miner/clones/<name>/` (or under `$XDG_CACHE_HOME`) | clones of URLs you gave it | kept between runs so the next one only fetches; delete it when you are done |
| a temporary folder | the demo's invented repository and its report | removed when the demo ends, unless `--keep` |

It never writes inside the repository it reads.

**It can delete.** If the output folder already holds an earlier repo-miner report (it has a `run.json`), that report is
removed before the new one is written. If the folder holds anything else, repo-miner refuses, unless you pass `--force`,
which empties it. Point `--out` at a folder of its own.

Every file in the report passes through one redactor (`Writer` and `Redactor` in `privacy.py`): e-mail addresses, keys
and tokens, JWTs, private keys, secret assignments, connection strings, private IP addresses, home-directory paths, and
the words in your `--deny` file. Then the finished report is scanned for the same things and `run.json` records the
result. The deny file is read; its words are never written, and `run.json` records only that one was used.

## The demo's fake secrets

`demo.py` builds an invented repository to prove that planted secrets stay out of the report. To do that the source
holds a string shaped like a GitHub token, an invented password and an invented e-mail address. They are made up, belong
to nothing, and exist so the check has something to catch. The invented repository is built in a temporary folder, with
your global git configuration switched off.

## With the skill, in Claude Code

The miner uses no model. The skill does: Claude reads `REPORT.md` and runs a handful of read-only git commands to dig
into findings. That means the report's content (commit subjects, file paths, and people's names unless you used
`--anonymise`) enters your Claude conversation, as anything Claude reads does. If that matters for a repository, run the
miner yourself from a terminal and read the report without Claude.

## People

A report says who did what, who went quiet and who to ask. Those are your colleagues or your predecessors. Use
`--anonymise` and `--deny` before a report leaves your machine, and run `repo-miner scan` on the folder first.
