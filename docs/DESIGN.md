# Design

## The idea

Someone dropped into an unfamiliar repository (a new hire, a consultant, an engineer inheriting a project, an agent) needs
to know three things before reading code: what happened, who knows what, and what to ask. The commit record answers the
first two mechanically and points at the third. So repo-miner splits the work:

- **A deterministic floor.** Reading the whole record, counting, cutting it into chapters and flagging what stands out is
  mechanical. Done by a script it costs nothing and gives the same answer every time; done by a model it costs hundreds of
  thousands of tokens per repository and drifts between runs.
- **Judgement on top.** What a finding means, whether it matters, and what to do about it is the reader's job: a person,
  or an agent working from the report (the skill tells Claude to run the miner first, dig into the top findings with the
  commands the report gives, and hand over an orientation).
- **People last.** The record shows what and how. Why lives with the people who were there, so every finding the record
  cannot explain ends as a question for them.

## Principles

1. **Every claim has a source.** A finding carries commit ids, dates and counts, and a command that shows them. No
   finding is a judgement of code or people.
2. **Read only.** Nothing is checked out, built or run; nothing is written inside the repository.
3. **Privacy at the writer.** Every output file passes through one redacting writer, and the miner scans what it wrote.
   Redacting at the point of output (not at each place text is produced) is what makes it hold.
4. **The same record, the same report.** Fixed rules, fixed thresholds, stable sorting.
5. **Nothing to install.** Python's standard library and git. One runtime.

## Traps already paid for

Each of these was met on a real run. The first group came from the experimental miners repo-miner grew out of; the
second from running this version against public repositories (commander.js, Express, Flask, Django) and against itself.

| Trap | What happened | What the miner does |
|---|---|---|
| **The default branch hides the work** | On the first real run over 29 repositories, 8 showed 1 to 15 commits on their default branch and 47 to 241 on another; a 172-commit project was invisible from its front page | Reads every ref; when another branch has more than twice the commits, it becomes the main line and the report says so first (`survey.py`) |
| **Shallow clones look like short histories** | A depth-1 clone shows one commit and one author | Detects shallow and single-branch clones and puts the fix at the top of the report; clones URLs with every branch (`gitlog.clone_health`, `target.py`) |
| **Identifiers title the chapters** | A session id from a commit trailer named a chapter; then an assistant's name; then contributor handles from "Merge pull request #12 from jdoe/fix" | Chapter words skip identifiers, trailers, merge boilerplate, credits ("thanks to ..."), and the names of tools and of every author (`measures.tokens`) |
| **The wrong author gets the credit** | In one record, 258 of a person's 367 commits were a job runner reporting work, and 78 were merges | Roles by author (people, agents, bots), merges counted apart, `--bot` and `--human` to correct (`history.Config`) |
| **The why is missing** | Agent transcripts live in sessions, out of git's reach | Reads Claude Code transcripts when present (what people typed and agents visibly said, nothing else), and ends every unexplained finding with a question for the people |
| **A leak in the output** | Private names and paths survived in harvested documents and in file names after body redaction | One writer for every file; a scan of the output that names the file and kind, never the match |
| **Measured against a trap, every branch is unmerged** | A feature branch cut from `develop` showed 67 "unmerged" commits against `main`: all of `develop` | Branches are measured against the main line, not the default branch (`survey._branch_row`) |
| **Maintenance branches resurrect deleted folders** | Flask's `flask/` moved to `src/flask/` in 2019, but a maintenance branch kept editing `flask/app.py`, so it never looked deleted | "Gone" is judged on the main line's own history, dated by each file's latest deletion (`history._graveyard`) |
| **A move is not an abandonment** | Reporting `flask/` as "built and removed" invites the wrong question | If the files the last removal took reappear with the same sub-paths elsewhere, the folder moved, and is reported as such |
| **Commit order is not time order** | Rebased or hand-dated commits arrive out of time order (git keeps parents first), so "last commit" was not the latest | Commits are sorted by author time after reading (`gitlog.commits`) |
| **One person, many names** | In commander.js, one founder under two capitalisations of one name; one maintainer as a handle, a full name and the name reversed | Names equal up to case and spacing are merged, and so are names sharing an address (placeholders aside). Addresses are never written (`miner._merge_spellings`) |
| **A secret-sounding name is not a secret** | Flask's `tests/test_apps/.env` and Express's `.npmrc` topped the report; neither held a credential | Recent versions are checked for credential-shaped text (answer: yes or no, never what), and fixtures are ranked lower |
| **Release lines are not unmerged work** | Django's `stable/5.2.x` "held 461 commits never merged" | Release lines and `gh-pages`-style branches are recognised and listed apart |
| **Backports and translation syncs look like sweeping changes** | Black reformatting appeared twice (main and its `[4.0.x]` backport); a Transifex sync touched 2,460 files | Backport prefixes are folded together; translation-only commits are skipped |
| **Every commit is a "fix" somewhere** | Django's convention is "Fixed #1234 --", so every file "keeps needing fixes" | A file stands out only above 1.5 × the repository's own fix rate |
| **A ten-day pause is not news in twenty years** | Silences of a few weeks ranked high in long records | A silence must be at least 2% of the record's span to become a finding |
| **Old silences use up every chapter** | Django's quiet early years took every cut, leaving one chapter for its last eleven years | Silences may take at most half the chapters; changes of character take the rest |
| **The miner read itself** | Run by an agent from inside a repository, the miner read that agent's own live session, which appeared as a new chapter in 2026 and a two-year silence | The session running the miner is skipped (by the session id Claude Code exports, and any session written to in the last ten minutes when run inside Claude Code) |
| **Anonymised, but the handle is the name** | "Merge pull request #12 from jdoe/..." kept a name that aliasing had replaced elsewhere | Alias matching ignores case; with `--anonymise`, handles in merges, mentions and co-author trailers are scrubbed too |
| **Founders who left ten years ago** | Every long-lived project "loses" its founder, which tells a newcomer little | A quiet person is a finding only if they still own an area that exists, or left in the second half of the record |
| **Skill frontmatter can break a skill** | Pre-approving the miner with an `allowed-tools` rule that contains `${CLAUDE_SKILL_DIR}` made the skill fail to load | No pre-approval: the person approves the miner command once |

## What it deliberately does not do

- **Score code quality or people.** Facts and questions only.
- **Read pull requests, issues or chat.** They need credentials and network, and they are different for every forge.
  The report says when the record points there.
- **Follow single-file renames.** Reading renames costs far more than the history it adds; folders that moved are
  recognised, and the report says that older history sits under old paths.
- **Make content.** The experimental miners it came from also cut histories into social posts, carousels and
  time-lapses. That is a different product; this one is for orientation.
