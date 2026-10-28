# Examples

Reports made by repo-miner on public repositories, exactly as the tool wrote them.

| Report | Made with |
|---|---|
| [commander.js](commander.js/REPORT.md) ([page](commander.js/report.html)) | `repo-miner https://github.com/tj/commander.js --anonymise` |

Made with `--anonymise`, so people appear as Person A, Person B and so on: a sample published to show the tool should
not make claims about named maintainers. The repository's own documents under `docs/` are copies of commander.js's
files (MIT licence) with secrets and private paths removed, as the tool makes them.

To make your own: `bin/repo-miner <path or URL>` from a clone of this repository.
