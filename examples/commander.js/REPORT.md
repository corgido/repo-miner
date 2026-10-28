# commander.js: what the history says

> Made by repo-miner 0.1.0 from the git record: every branch, up to 2026-10-26. No AI model wrote this report. Every number is counted, and every claim points to a commit or a path you can check.

## In short

**commander.js** has 1,598 commits on 8 branches, from 2011-08-14 to 2026-10-26 (15.2 years), by 207 people, AI agents (2 commits) and 1 bot. Most of the work is in `lib`, `tests` and `test`. The history falls into 8 chapters; the latest (2022-09-06 to 2026-10-26) is mostly lib · prettier, checks, tsconfig. 8 things stand out, and 4 questions can only be answered by the people who were there.

|  |  |
|---|---|
| Commits | 1,598 (289 merges) on every branch |
| Branches | 8; default `master`, busiest `develop` |
| People | 207 authors who are people |
| AI agents | 1 commit by agents, 1 with an agent co-author |
| Bots | `dependabot[bot]` (149 commits) |
| First and last | 2011-08-14 to 2026-10-26 |
| Files now | 219 on `master`, 1.0 MB; mostly .js (156), no extension (23), .md (12), .cjs (6) |
| Releases | 126 tags, latest v15.0.0 (2026-05-29) |
| Remote | `https://github.com/tj/commander.js` |

## What stands out

<details><summary><b>1.</b> <code>test/</code> (96 files, 124 commits) is gone: built from 2011-08-14, removed 2019-09-20</summary>

- Last files removed in [`d7f9cd443`](https://github.com/tj/commander.js/commit/d7f9cd443): "Move to Jest as testing framework (#1035)", 8.1 years after it began.
- Worked on by Person C, Person B.

Dig:

```sh
git -C ~/.cache/repo-miner/clones/commander.js show --stat d7f9cd443 | head -40
git -C ~/.cache/repo-miner/clones/commander.js log --all --oneline -- test/ | head -20
```

**Ask:** What replaced `test/`, and why was it removed?

</details>

<details><summary><b>2.</b> 10 changes were reverted, 1 of them within two days</summary>

- [`f3431d157`](https://github.com/tj/commander.js/commit/f3431d157) (2023-08-12) reverted [`14fb52918`](https://github.com/tj/commander.js/commit/14fb52918): "Fix version() parameter type" after 9.5 days
- [`891e23d49`](https://github.com/tj/commander.js/commit/891e23d49) (2021-01-11) reverted "Test coverage (#1433)"
- [`517ee439b`](https://github.com/tj/commander.js/commit/517ee439b) (2019-06-24) reverted [`2c3cf60b1`](https://github.com/tj/commander.js/commit/2c3cf60b1): "add executable arguments to spawn in win32" after 2.3 years
- [`ce35c35e9`](https://github.com/tj/commander.js/commit/ce35c35e9) (2016-09-20) reverted "For a required option, when even option flag is not given throw error."
- [`8e75320e6`](https://github.com/tj/commander.js/commit/8e75320e6) (2015-04-17) reverted "multiline descriptions support"
- [`2d68cf40b`](https://github.com/tj/commander.js/commit/2d68cf40b) (2015-03-23) reverted [`854cfd8a0`](https://github.com/tj/commander.js/commit/854cfd8a0): "Added .npmignore" after 2.6 days

Dig:

```sh
git -C ~/.cache/repo-miner/clones/commander.js show f3431d157
git -C ~/.cache/repo-miner/clones/commander.js show --stat 14fb52918
```

**Ask:** What went wrong with "Fix version() parameter type" (2023-08-12)?

</details>

<details><summary><b>3.</b> <code>changelogs/</code> (6 files, 6 commits) is gone: built from 2019-12-07, removed 2021-12-21</summary>

- Last files removed in [`19c8041a3`](https://github.com/tj/commander.js/commit/19c8041a3): "Combine back into single CHANGELOG to simplify searches (#1656)", 2.0 years after it began.
- Worked on by Person A.

Dig:

```sh
git -C ~/.cache/repo-miner/clones/commander.js show --stat 19c8041a3 | head -40
git -C ~/.cache/repo-miner/clones/commander.js log --all --oneline -- changelogs/ | head -20
```

**Ask:** What replaced `changelogs/`, and why was it removed?

</details>

<details><summary><b>4.</b> <code>examples/using-esm-from-commonjs/</code> (12 files, 3 commits) is gone: built from 2026-02-19, removed 2026-05-22</summary>

- Last files removed in [`01ce5d0cd`](https://github.com/tj/commander.js/commit/01ce5d0cd): "Remove jest esm examples (#2517)", 3.0 months after it began.
- Worked on by Person A.

Dig:

```sh
git -C ~/.cache/repo-miner/clones/commander.js show --stat 01ce5d0cd | head -40
git -C ~/.cache/repo-miner/clones/commander.js log --all --oneline -- examples/using-esm-from-commonjs/ | head -20
```

**Ask:** What replaced `examples/using-esm-from-commonjs/`, and why was it removed?

</details>

<details><summary><b>5.</b> 1 area rests on one person's knowledge</summary>

- `tests`: 88% of 81 commits by Person A

Dig:

```sh
git -C ~/.cache/repo-miner/clones/commander.js shortlog -sn --no-merges -- tests
```

</details>

<details><summary><b>6.</b> <code>1bdc749ac</code> (2024-04-05) changed 132 files at once: "Reformat code with Prettier (#2180)"</summary>

- Shape: edits across many files (a reformat, rename or upgrade?); 0 added, 0 deleted, 5,216 lines.

Dig:

```sh
git -C ~/.cache/repo-miner/clones/commander.js show --stat 1bdc749ac | head -40
```

</details>

<details><summary><b>7.</b> <code>d7f9cd443</code> (2019-09-20) changed 127 files at once: "Move to Jest as testing framework (#1035)"</summary>

- Shape: files moved or renamed; 48 added, 75 deleted, 11,596 lines.

Dig:

```sh
git -C ~/.cache/repo-miner/clones/commander.js show --stat d7f9cd443 | head -40
```

</details>

<details><summary><b>8.</b> <code>f4bd47000</code> (2026-02-19) changed 191 files at once: "Switching to esm-only (#2464)"</summary>

- Shape: edits across many files (a reformat, rename or upgrade?); 16 added, 7 deleted, 2,649 lines.

Dig:

```sh
git -C ~/.cache/repo-miner/clones/commander.js show --stat f4bd47000 | head -40
```

</details>

## Questions for the people

The record shows what changed; these are the things it cannot say. Ask whoever was there.

1. What replaced `test/`, and why was it removed?
2. What went wrong with "Fix version() parameter type" (2023-08-12)?
3. What replaced `changelogs/`, and why was it removed?
4. What replaced `examples/using-esm-from-commonjs/`, and why was it removed?

## Chapters

The record cut where it falls silent or changes character (who works, on what, where). Labels are the area and words a chapter has more of than the rest of the record.

| # | From | To | Span | Events | People | Mostly |
|---:|---|---|---|---:|---:|---|
| 1 | 2011-08-14 | 2012-01-17 | 5.1 months | 155 | 10 | examples · docs, password, defaults |
| 2 | 2012-04-11 | 2013-04-09 | 12 months | 60 | 16 | lib · setrawmode, printing, tty |
| 3 | 2013-06-13 | 2015-06-23 | 2.0 years | 251 | 46 | test · unused, revert, bug |
| 4 | 2015-09-12 | 2015-10-15 | 33 days | 15 | 3 | text, filtering, post-processing |
| 5 | 2015-12-21 | 2017-04-09 | 16 months | 43 | 23 | test · given, build, win32 |
| 6 | 2017-06-16 | 2018-10-21 | 16 months | 124 | 39 | typings · newline, emit, prefix |
| 7 | 2018-12-28 | 2022-07-14 | 3.5 years | 548 | 48 | tests · tests, typescript, rework |
| 8 | 2022-09-06 | 2026-10-26 | 4.1 years | 253 | 33 | lib · prettier, checks, tsconfig |

<details><summary>Each chapter in detail</summary>

<details><summary>1. 2011-08-14 to 2012-01-17: examples · docs, password, defaults</summary>

- More of: area `examples` (23 of 53, +2.02 bits); area `lib` (38 of 120, +1.57 bits); area `test` (14 of 65, +1.01 bits)
- Its words: docs (68), password (8), defaults (7), misc (6), styling (6), clean (6)
- People: Person B, Person M, Person V
- Made by: human 155; 19 fixes
- Heaviest: [`672c7d01d`](https://github.com/tj/commander.js/commit/672c7d01d) 2011-08-14 "Initial commit" (619 lines)
- Heaviest: [`3080b90f5`](https://github.com/tj/commander.js/commit/3080b90f5) 2011-10-19 "docs" (566 lines)
- Heaviest: [`3bd6bbcda`](https://github.com/tj/commander.js/commit/3bd6bbcda) 2011-10-23 "@someone public only" (224 lines)
- Runs from [`672c7d01d`](https://github.com/tj/commander.js/commit/672c7d01d) to [`8e2618815`](https://github.com/tj/commander.js/commit/8e2618815)

</details>

<details><summary>2. 2012-04-11 to 2013-04-09: lib · setrawmode, printing, tty</summary>

- More of: area `lib` (16 of 120, +1.69 bits); area `examples` (4 of 53, +0.87 bits)
- Its words: setrawmode (6), printing (4), tty (4), take (4), lib (4), don't (3)
- People: Person B, Person O, Person R
- Made by: human 60; 16 fixes
- Heaviest: [`2a2165584`](https://github.com/tj/commander.js/commit/2a2165584) 2012-11-17 "Release 1.1.0" (2,267 lines)
- Heaviest: [`21b416939`](https://github.com/tj/commander.js/commit/21b416939) 2012-11-17 "add git-style executable subcommand support. Closes #94" (126 lines)
- Heaviest: [`7ab5bd186`](https://github.com/tj/commander.js/commit/7ab5bd186) 2012-11-05 "remove messy/broken test" (123 lines)
- Runs from [`f2060ffcf`](https://github.com/tj/commander.js/commit/f2060ffcf) to [`3261f3e20`](https://github.com/tj/commander.js/commit/3261f3e20); starts after a silence

</details>

<details><summary>3. 2013-06-13 to 2015-06-23: test · unused, revert, bug</summary>

- More of: area `test` (25 of 65, +1.15 bits)
- Its words: unused (12), revert (13), bug (11), sub-commands (7), allowunknown (6), license (6)
- People: Person C, Person B, Person E
- Made by: human 251; 70 fixes
- Heaviest: [`b7b558ed1`](https://github.com/tj/commander.js/commit/b7b558ed1) 2014-12-07 "index: Update documentation via `$ make docs`" (2,127 lines)
- Heaviest: [`bf5e1f5ec`](https://github.com/tj/commander.js/commit/bf5e1f5ec) 2013-07-19 "remove input methods (.prompt, .confirm, etc)" (499 lines)
- Heaviest: [`8d1711f43`](https://github.com/tj/commander.js/commit/8d1711f43) 2014-12-29 "update doc for v2.6.0" (172 lines)
- Runs from [`a3b353ab4`](https://github.com/tj/commander.js/commit/a3b353ab4) to [`0af40a523`](https://github.com/tj/commander.js/commit/0af40a523); starts after a silence

</details>

<details><summary>4. 2015-09-12 to 2015-10-15: text, filtering, post-processing</summary>

- Its words: text (9), filtering (5), post-processing (5), alignment (4), brace (4)
- People: Person C, Person FU, Person DG
- Made by: human 15; 2 fixes
- Heaviest: [`89e77c2ef`](https://github.com/tj/commander.js/commit/89e77c2ef) 2015-10-15 "Add chinese Readme file" (343 lines)
- Heaviest: [`c140367b1`](https://github.com/tj/commander.js/commit/c140367b1) 2015-10-13 "update doc" (279 lines)
- Heaviest: [`8024df2a3`](https://github.com/tj/commander.js/commit/8024df2a3) 2015-10-12 "fix nohelp test" (33 lines)
- Runs from [`4d421f9fd`](https://github.com/tj/commander.js/commit/4d421f9fd) to [`e741c1847`](https://github.com/tj/commander.js/commit/e741c1847); starts after a silence

</details>

<details><summary>5. 2015-12-21 to 2017-04-09: test · given, build, win32</summary>

- More of: area `test` (6 of 65, +1.64 bits)
- Its words: given (5), build (4), win32 (3)
- People: Person C, Person E, Person AD
- Made by: human 43; 13 fixes
- Heaviest: [`81577a654`](https://github.com/tj/commander.js/commit/81577a654) 2016-06-06 "Support the alias of Git style sub-command" (69 lines)
- Heaviest: [`975e5a42f`](https://github.com/tj/commander.js/commit/975e5a42f) 2016-02-11 "For a required option, when even option flag is not given throw error. Fixes tests accordingly." (43 lines)
- Heaviest: [`ce35c35e9`](https://github.com/tj/commander.js/commit/ce35c35e9) 2016-09-20 "Revert "For a required option, when even option flag is not given throw error."" (43 lines)
- Runs from [`a33ad704a`](https://github.com/tj/commander.js/commit/a33ad704a) to [`20493bb59`](https://github.com/tj/commander.js/commit/20493bb59); starts after a silence

</details>

<details><summary>6. 2017-06-16 to 2018-10-21: typings · newline, emit, prefix</summary>

- More of: area `typings` (7 of 46, +0.83 bits); area `test` (9 of 65, +0.69 bits)
- Its words: newline (8), emit (7), prefix (7), feat (6), older (6), behavior (5)
- People: Person D, Person I, Person J
- Made by: human 123, agent 1; 24 fixes
- Heaviest: [`4c9b4b8ee`](https://github.com/tj/commander.js/commit/4c9b4b8ee) 2018-01-23 "resolves #754 add linter configuration to project" (2,039 lines)
- Heaviest: [`aaa447a8f`](https://github.com/tj/commander.js/commit/aaa447a8f) 2018-07-03 "npm update (#823)" (1,431 lines)
- Heaviest: [`001d560f5`](https://github.com/tj/commander.js/commit/001d560f5) 2018-05-10 "Update eslint to resolve vulnerabilities in lodash" (1,409 lines)
- Runs from [`648629f86`](https://github.com/tj/commander.js/commit/648629f86) to [`27aeac1c2`](https://github.com/tj/commander.js/commit/27aeac1c2); starts after a silence

</details>

<details><summary>7. 2018-12-28 to 2022-07-14: tests · tests, typescript, rework</summary>

- More of: area `tests` (61 of 81, +0.99 bits); area `typings` (25 of 46, +0.52 bits); area `"docs` (4 of 5, +1.08 bits)
- Its words: tests (157), typescript (59), rework (42), changelog (102), example (86), argument (59)
- People: Person A, Person D, Person L
- Made by: human 548; 55 fixes
- Heaviest: [`d7f9cd443`](https://github.com/tj/commander.js/commit/d7f9cd443) 2019-09-20 "Move to Jest as testing framework (#1035)" (11,596 lines)
- Heaviest: [`08e65d355`](https://github.com/tj/commander.js/commit/08e65d355) 2021-12-21 "Upgrade package-lock.json to lockfile@2 (#1659)" (10,406 lines)
- Heaviest: [`177cc6e6d`](https://github.com/tj/commander.js/commit/177cc6e6d) 2022-07-13 "Update dependencies (#1767)" (7,831 lines)
- Runs from [`cec57f550`](https://github.com/tj/commander.js/commit/cec57f550) to [`82fcb98cc`](https://github.com/tj/commander.js/commit/82fcb98cc); starts after a silence

</details>

<details><summary>8. 2022-09-06 to 2026-10-26: lib · prettier, checks, tsconfig</summary>

- More of: area `lib` (53 of 120, +1.34 bits); area `.github` (20 of 39, +1.55 bits); area `docs` (8 of 14, +1.71 bits); area `tests/fixtures` (3 of 3, +2.52 bits); area `typings` (14 of 46, +0.8 bits)
- Its words: prettier (9), checks (11), tsconfig (7), broken (8), config (8), negative (7)
- People: Person A, Person F, Person D
- Made by: human 253; 30 fixes
- Heaviest: [`3dd608610`](https://github.com/tj/commander.js/commit/3dd608610) 2026-01-11 "Switch from Jest to Node.js built-in test runner (#2463)" (12,148 lines)
- Heaviest: [`b3e6795dc`](https://github.com/tj/commander.js/commit/b3e6795dc) 2026-01-13 "Add describe wrappers so test output makes sense without filenames (#2472)" (10,716 lines)
- Heaviest: [`1bdc749ac`](https://github.com/tj/commander.js/commit/1bdc749ac) 2024-04-05 "Reformat code with Prettier (#2180)" (5,216 lines)
- Runs from [`84d9201e9`](https://github.com/tj/commander.js/commit/84d9201e9) to [`a09ea496b`](https://github.com/tj/commander.js/commit/a09ea496b)

</details>

</details>

<details><summary>Surprises in the timeline</summary>

- **46 in one day** 2011-08-14: 46 events against 1.9 in an average active day. (151.9 bits)
- **19 of 1,158 commits** hold 51% of all lines changed (Gini 0.89). The heaviest: "Switch from Jest to Node.js built-in test runner (#2463)" (12,148 lines). (5.9 bits)

</details>

## People

| Who | Commits | Share | First | Last | Mostly in | Status | With an agent |
|---|---:|---:|---|---|---|---|---:|
| Person A | 532 | 41% | 2019-04-06 | 2026-10-26 | `(top level)`, `tests`, `lib` |  |  |
| Person B | 159 | 12% | 2011-08-14 | 2014-03-29 | `(top level)`, `lib`, `examples` | quiet |  |
| Person C | 78 | 6% | 2014-09-26 | 2016-09-20 | `(top level)`, `test`, `examples` | quiet |  |
| Person D | 75 | 6% | 2017-06-19 | 2026-05-29 | `(top level)`, `.github`, `test` |  |  |
| Person F | 21 | 2% | 2023-07-28 | 2023-08-13 | `lib`, `tests`, `(top level)` |  |  |
| Person H | 9 | 1% | 2013-10-23 | 2015-03-26 | `(top level)`, `test` |  |  |
| Person I | 8 | 1% | 2018-01-05 | 2018-01-31 | `(top level)` |  |  |
| Person J | 6 | 0% | 2017-07-23 | 2017-11-28 | `(top level)`, `typings` |  |  |
| Person K | 6 | 0% | 2018-08-02 | 2018-09-29 | `(top level)`, `test` |  |  |
| Person L | 6 | 0% | 2019-08-08 | 2020-02-12 | `(top level)` |  |  |
| Person M | 5 | 0% | 2011-11-20 | 2011-11-23 | `examples`, `test` |  |  |
| Person N | 4 | 0% | 2017-11-07 | 2021-04-12 | `(top level)` |  |  |
| Person O | 4 | 0% | 2012-05-04 | 2012-07-03 | `lib` |  |  |
| Person Q | 4 | 0% | 2014-04-20 | 2014-05-07 | `(top level)` |  |  |
| Person R | 4 | 0% | 2012-07-03 | 2013-04-09 | `(top level)`, `lib` |  |  |

And 192 more; all of them are in `data/people.tsv`.

Not people: `dependabot[bot]` (bot, 149), `Jules Randolph` (agent, 1).

"Quiet" means no commits in the last stretch of the record (a fifth of its span, at least 90 days) from someone who made at least 2% of the commits. It is a fact about the record, not about the person.

## Where the work is

| Area | Commits | People | Main author | Ask now | Fixes | By agents | Last change |
|---|---:|---:|---|---|---:|---:|---|
| `(top level)` | 862 | 142 | Person A (45%) | Person A, Person D | 11% | 0% | 2026-10-09 |
| `lib` | 120 | 30 | Person A (31%) | Person A, Person F | 22% | 0% | 2026-10-19 |
| `tests` | 81 | 8 | Person A (88%) | Person A, Person F | 5% | 0% | 2026-10-25 |
| `test` | 65 | 25 | Person C (32%) | Person C, Person B (not recent) | 31% | 0% | 2019-09-20 |
| `.github` | 56 | 5 | Person A (54%) | Person A, Person D | 2% | 0% | 2026-10-26 |
| `examples` | 53 | 6 | Person A (45%) | Person A | 17% | 0% | 2026-05-22 |
| `typings` | 46 | 15 | Person A (60%) | Person A, Person BK | 17% | 4% | 2026-08-11 |
| `docs` | 14 | 4 | Person A (79%) | Person A, Person F | 21% | 0% | 2026-10-25 |
| `"docs` | 5 | 5 | Person FM (20%) | Person FQ | 0% | 0% | 2026-09-21 |
| `tests/fixtures` | 3 | 1 | Person A (100%) | Person A | 33% | 0% | 2023-10-07 |
| `changelogs` | 2 | 1 | Person A (100%) | Person A (not recent) | 0% | 0% | 2021-12-21 |
| `tests/fixtures-extensions` | 1 | 1 | Person A (100%) | Person A (not recent) | 0% | 0% | 2021-01-30 |

"Ask now" is whoever committed most to the area in the last year of the record (or a quarter of its span, if longer).

<details><summary>The files that change most</summary>

| File | Commits | Fixes | People | Lines churned | First | Last | Still there |
|---|---:|---:|---:|---:|---|---|---|
| `package.json` | 243 | 14 | 26 | 1,116 | 2011-08-14 | 2026-10-05 | yes |
| `index.js` | 240 | 52 | 78 | 13,168 | 2011-08-14 | 2026-10-25 | yes |
| `Readme.md` | 237 | 24 | 57 | 4,048 | 2011-08-14 | 2026-10-05 | yes |
| `typings/index.d.ts` | 137 | 15 | 23 | 3,704 | 2017-07-23 | 2026-10-25 | yes |
| `lib/command.js` | 95 | 15 | 14 | 4,891 | 2021-05-25 | 2026-10-19 | yes |
| `lib/commander.js` | 82 | 16 | 15 | 2,760 | 2011-08-14 | 2012-11-17 | no |
| `typings/index.test-d.ts` | 55 | 3 | 8 | 1,103 | 2021-01-31 | 2026-02-19 | yes |
| `Readme_zh-CN.md` | 53 | 7 | 21 | 3,163 | 2015-10-15 | 2026-10-05 | yes |
| `History.md` | 52 | 2 | 5 | 704 | 2011-08-14 | 2017-07-24 | no |
| `.github/workflows/tests.yml` | 39 | 0 | 4 | 125 | 2019-08-30 | 2026-10-17 | yes |
| `typings/commander-tests.ts` | 36 | 2 | 3 | 1,142 | 2017-07-23 | 2021-01-31 | no |
| `.travis.yml` | 30 | 1 | 11 | 86 | 2011-11-24 | 2020-11-10 | no |
| `tests/command.exitOverride.test.js` | 29 | 0 | 4 | 1,583 | 2019-09-20 | 2026-07-27 | yes |
| `lib/help.js` | 29 | 3 | 7 | 1,263 | 2021-05-25 | 2026-10-12 | yes |
| `lib/option.js` | 27 | 2 | 5 | 544 | 2021-05-25 | 2026-09-28 | yes |

Lock files, changelogs and build output are left out.

</details>

## Branches and releases

- Default `master`: 1,517 commits, tip [`ba6d13ddb`](https://github.com/tj/commander.js/commit/ba6d13ddb) (2026-05-29).
- Busiest `develop`: 1,562 commits.
- 4 branches hold commits `master` lacks; 3 are fully merged.
- Release lines: `release/16.x`, `release/15.x`, `release/14.x`, `release/13.x`, `release/2.x`.
- 126 tags from 0.0.1 (2011-08-14) to v15.0.0 (2026-05-29); 0 commits on `master` since.

<details><summary>Unmerged branches (4)</summary>

| Branch | Own commits | Behind | First own | Last own | Authors |
|---|---:|---:|---|---|---:|
| `develop` | 45 | 0 | 2026-06-13 | 2026-10-26 | 12 |
| `release/16.x` | 27 | 0 | 2026-06-13 | 2026-09-28 | 7 |
| `gh-pages` | 26 | 1,064 | 2011-10-18 | 2015-10-13 | 4 |
| `release/2.x` | 3 | 890 | 2019-09-28 | 2019-10-11 | 2 |

</details>

## How the work is done

- Commit messages: 4% follow Conventional Commits, 24% have a body, 6% say almost nothing.
- 817 commits name a pull request (#5 to #2666): the discussion behind them is on the forge, not in git.

| Kind | File | Since | Changes | What it is |
|---|---|---|---:|---|
| ci | `.github/workflows/codeql-analysis.yml` | 2022-03-11 | 25 | CodeQL |
| ci | `.github/workflows/tests.yml` | 2019-08-30 | 39 | build |
| contributing | `.github/PULL_REQUEST_TEMPLATE.md` | 2019-08-13 | 5 | The text in these markdown comments is instructions that will not appear in the displayed pull request, |
| contributing | `CONTRIBUTING.md` | 2019-08-13 | 4 | New issues are welcome, whether questions or suggestions or reporting bugs. |
| contributing | `SECURITY.md` | 2019-07-27 | 19 | Security Policy |
| quality | `.editorconfig` | 2019-04-16 | 1 | EditorConfig is awesome: http://EditorConfig.org |
| quality | `.prettierrc.js` | 2024-04-04 | 3 | export default { |
| quality | `eslint.config.js` | 2024-04-04 | 11 | import globals from 'globals'; |
| dependencies | `.github/dependabot.yml` | 2022-05-24 | 7 | package-ecosystem: "npm" |

The full text of each is folded in [`practices/INDEX.md`](practices/INDEX.md).

<details><summary>Practices that were dropped (5)</summary>

- ci: `.travis.yml` from 2011-11-24, removed 2020-11-10 in `2f7aa3384`
- contributing: `.github/CONTRIBUTING.md` from 2019-06-09, removed 2019-08-13 in `fea94a9fe`
- quality: `.eslintrc` from 2018-01-23, removed 2018-10-08 in `700130ee5`
- quality: `.eslintrc.js` from 2020-03-04, removed 2024-04-04 in `6fc933e3b`
- quality: `.eslintrc.json` from 2018-10-08, removed 2020-03-04 in `f14df0709`

</details>

## Read next

The repository's own documents, best first, copied here with secrets and private paths removed. They describe intent; the record above shows what happened.

| Document | Path | Branch | Copy |
|---|---|---|---|
| Commander.js | `Readme.md` | master | [open](docs/Readme.md) |
| Contributing | `CONTRIBUTING.md` | master | [open](docs/CONTRIBUTING.md) |
| Changelog | `CHANGELOG.md` | master | [open](docs/CHANGELOG.md) |
| Deprecated | `docs/deprecated.md` | master | [open](docs/docs__deprecated.md) |
| Help in Depth | `docs/help-in-depth.md` | master | [open](docs/docs__help-in-depth.md) |
| Options in Depth | `docs/options-in-depth.md` | master | [open](docs/docs__options-in-depth.md) |
| Parsing life cycle and hooks | `docs/parsing-and-hooks.md` | master | [open](docs/docs__parsing-and-hooks.md) |
| Release Policy | `docs/release-policy.md` | master | [open](docs/docs__release-policy.md) |
| Terminology | `docs/terminology.md` | master | [open](docs/docs__terminology.md) |
| Commander.js | `Readme_zh-CN.md` | master | [open](docs/Readme_zh-CN.md) |
| Security Policy | `SECURITY.md` | master | [open](docs/SECURITY.md) |

Where things start: `package.json`.

`package.json` scripts: `check`, `check:format`, `check:lint`, `check:type`, `check:type:js`, `check:type:ts`, `fix`, `fix:format`, `fix:lint`, `test`, `test-all`.

## Activity by year

<details><summary>16 years, from 2011 to 2026</summary>

| Period | Commits | People | By people | By agents | With an agent | Bots | Lines |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2011 | 152 | 9 | 152 | 0 | 0 | 0 | 4,421 |
| 2012 | 59 | 14 | 59 | 0 | 0 | 0 | 3,027 |
| 2013 | 31 | 12 | 31 | 0 | 0 | 0 | 753 |
| 2014 | 125 | 26 | 125 | 0 | 0 | 0 | 3,774 |
| 2015 | 116 | 23 | 116 | 0 | 0 | 0 | 1,797 |
| 2016 | 32 | 17 | 32 | 0 | 0 | 0 | 355 |
| 2017 | 62 | 28 | 61 | 1 | 0 | 0 | 2,139 |
| 2018 | 73 | 21 | 73 | 0 | 0 | 0 | 6,769 |
| 2019 | 214 | 21 | 214 | 0 | 0 | 0 | 23,243 |
| 2020 | 177 | 13 | 177 | 0 | 0 | 0 | 41,985 |
| 2021 | 109 | 10 | 109 | 0 | 0 | 0 | 40,294 |
| 2022 | 68 | 14 | 65 | 0 | 0 | 3 | 18,140 |
| 2023 | 125 | 5 | 93 | 0 | 0 | 32 | 16,980 |
| 2024 | 88 | 6 | 48 | 0 | 0 | 40 | 18,438 |
| 2025 | 87 | 10 | 32 | 0 | 0 | 55 | 10,722 |
| 2026 | 80 | 16 | 61 | 0 | 1 | 19 | 32,422 |

</details>

## What is in this folder

| File | What |
|---|---|
| `REPORT.md` | this report (also `report.html`, with the activity chart) |
| `findings.json` | every finding with its evidence, commands and question |
| `data/commits.tsv` | every commit: sha, date, author, role, area, chapter, lines, subject |
| `data/branches.tsv` | every branch: commits, ahead, behind, orphan, first and last own commit |
| `data/people.tsv`, `data/areas.tsv`, `data/files.tsv` | the tables above, in full |
| `data/timeline.json` | chapters, surprises and activity bins |
| `docs/` | the repository's documents, redacted |
| `practices/` | the current practice files, with `INDEX.md` |
| `briefs/` | one brief per chapter, for an agent to write that chapter's history |

## How this was made

<details><summary>Method and limits</summary>

- Read with `git` only, every branch and tag, without checking anything out or running the project's code.
- Roles: an author whose name matches a known AI coding tool is an agent, a known automation account is a bot, anyone else is a person. A person's commit with an agent `Co-Authored-By` trailer counts as made with an agent.
- Areas: the top-level folder a commit touches most, one level deeper inside a folder that holds over a quarter of all changes.
- Chapters: cut at silences six times longer than the record's 90th-percentile gap (at least 4 hours), then wherever the mix of roles, areas and repositories changes by more information than a BIC-style penalty allows. Deterministic.
- Renames count as a deletion and an addition. Authors are merged by `.mailmap` when the repository has one; otherwise one person with two names counts twice.
- Redacted before writing: e-mail addresses, keys and tokens, secret assignments, connection strings, private IP addresses, home-directory paths. People are shown as aliases.
- Not read: pull requests, issues, chat and tickets. Agent transcripts only when Claude Code kept them on this machine.

</details>
