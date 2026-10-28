# Practices

How the work is done, as the repository records it. Each current file's text is folded under its line; superseded ones are named with the commit that removed them.

## ci (2): what runs on every push or pull request

<details><summary><code>.github/workflows/codeql-analysis.yml</code> · since 2022-03-11 · 25 changes · CodeQL</summary>

```yaml
name: "CodeQL"

on:
  push:
    branches: [ master, develop ]
  pull_request:
    # The branches below must be a subset of the branches above
    branches: [ master, develop ]
  schedule:
    - cron: '27 5 * * 6'
  workflow_dispatch:

jobs:
  analyze:
    name: Analyze
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write

    strategy:
      fail-fast: false
      matrix:
        language: [ 'javascript' ]

    steps:
    - name: Checkout repository
      uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1

    # Initializes the CodeQL tools for scanning.
    - name: Initialize CodeQL
      uses: github/codeql-action/init@9b3254085494b55a0f7c4c2b3d2d52cc712ce370 # v4.39.1
      with:
        languages: ${{ matrix.language }}
        # If you wish to specify custom queries, you can do so here or in a config file.
        # By default, queries listed here will override any specified in a config file.
        # Prefix the list here with "+" to use these queries and those in the config file.
        # queries: ./path/to/local/query, your-org/your-repo/queries@main

    # (No build steps needed with current project setup.)

    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@9b3254085494b55a0f7c4c2b3d2d52cc712ce370 # v4.39.1
```

</details>

<details><summary><code>.github/workflows/tests.yml</code> · since 2019-08-30 · 39 changes · build</summary>

```yaml
name: build

on: [push, pull_request, workflow_dispatch]

permissions:
  contents: read

jobs:
  test:
    name: Test on node ${{ matrix.node-version }} and ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        node-version: [22.x, 24.x, 26.x]
        os: [ubuntu-latest, windows-latest, macos-latest]

    steps:
    - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
    - name: Use Node.js ${{ matrix.node-version }}
      uses: actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1 # v7.1.0
      with:
        cache: 'npm'
        node-version: ${{ matrix.node-version }}
    # Use separate run commands so command status handled correctly on Windows
    - name: npm install
      run: npm ci
    - name: npm test
      run: npm test
    - name: npm run check
      run: npm run check
```

</details>

## contributing (3): how changes are proposed and reviewed

<details><summary><code>.github/PULL_REQUEST_TEMPLATE.md</code> · since 2019-08-13 · 5 changes · The text in these markdown comments is instructions that will not appear in the displayed pull request,</summary>

```markdown
<!--
The text in these markdown comments is instructions that will not appear in the displayed pull request,
and can be deleted.

Please submit pull requests against the develop branch.

Follow the existing code style. Check the tests succeed, including format and lint.
  npm run test
  npm run check

Don't update the CHANGELOG or package version number. That gets done by maintainers when preparing the release.

See also the guides to Contributing and AI Policy:
  https://github.com/tj/commander.js/blob/master/CONTRIBUTING.md#pull-requests
  https://github.com/tj/commander.js/blob/master/AI_POLICY.md#pull-requests

-->

## Problem

<!--
What problem are you solving?
What Issues does this relate to?
Show the broken output if appropriate.
-->

## Solution

<!--
How did you solve the problem? 
Show the fixed output if appropriate.

There are a lot of forms of documentation which could need updating for a change in functionality. It
is ok if you want to show us the code to discuss before doing the extra work, and
you should say so in your comments so we focus on the concept first before talking about all the other pieces:

- TypeScript typings
- JSDoc documentation in code
- tests
- README
- examples/
-->

## ChangeLog

<!--
Optional. Suggest a line for adding to the CHANGELOG to summarise your change.
-->
```

</details>

<details><summary><code>CONTRIBUTING.md</code> · since 2019-08-13 · 4 changes · New issues are welcome, whether questions or suggestions or reporting bugs.</summary>

```markdown
# Contributing

## Issues

New issues are welcome, whether questions or suggestions or reporting bugs.
You are also welcome to contribute by adding helpful comments on an existing issue.

We love reproducible code examples in questions and answers.

If you get a satisfactory reply to a question then please close your issue, but it is ok to leave an issue open for more replies or interest. Inactive issues may get closed after one month if they have an answer,
or after six months otherwise.

## Pull Requests

To limit the number of open Pull Requests so maintainers are not overwhelmed:

- If there is not already an issue, please open an issue first rather than starting with a pull request.
- Don't open a Pull Request unless invited to do so by a maintainer.
- Don't open a Pull Request entirely or largely generated by AI, as it would be easier for the maintainer to do it themselves.
  - See also the [AI Policy](./AI_POLICY.md).
- Unsolicited Pull Requests may be closed without discussion.

Please submit pull requests against the develop branch.

Follow the existing code style. Check the tests succeed, including format and lint.

- `npm run test`
- `npm run check`

Don't update the CHANGELOG or command version number. That gets done by maintainers when preparing the release.

Useful things to include in your request description are:

- what problem are you solving?
- what Issues does this relate to?
- suggested summary for CHANGELOG

There are a lot of forms of documentation which could need updating for a change in functionality. It
is ok if you want to show us the code to discuss before doing the extra work, and
you should say so in your comments so we focus on the concept first before talking about all the other pieces:

- TypeScript typings
- JSDoc documentation in code
- tests
- README
- examples/

Commander currently has zero production dependencies. That isn't a hard requirement, but is a simple story. Requests which add a dependency are much less likely to be accepted, and we are likely to ask for alternative approaches to avoid the dependency.

- <https://devrant.com/rants/1854993/package-tsunami>
- <https://dev.to/leoat12/the-nodemodules-problem-29dc>
```

</details>

<details><summary><code>SECURITY.md</code> · since 2019-07-27 · 19 changes · Security Policy</summary>

```markdown
# Security Policy

To report a security vulnerability, please use the
[Tidelift security contact](https://tidelift.com/security).
Tidelift will coordinate the fix and disclosure.

Please do not report security vulnerabilities through public GitHub issues or pull requests.
```

</details>

## quality (3): linters and formatters the code is held to

<details><summary><code>.editorconfig</code> · since 2019-04-16 · 1 changes · EditorConfig is awesome: http://EditorConfig.org</summary>

```
# EditorConfig is awesome: http://EditorConfig.org

# top-most EditorConfig file
root = true

[*]
end_of_line = lf
insert_final_newline = true
indent_style = space
indent_size = 2
tab_width = 2
# trim_trailing_whitespace = true
```

</details>

<details><summary><code>.prettierrc.js</code> · since 2024-04-04 · 3 changes · export default {</summary>

```js
export default {
  singleQuote: true,
  overrides: [
    {
      files: ['tsconfig*.json'],
      options: { parser: 'jsonc' },
    },
  ],
};
```

</details>

<details><summary><code>eslint.config.js</code> · since 2024-04-04 · 11 changes · import globals from 'globals';</summary>

```js
import globals from 'globals';
import esLintjs from '@eslint/js';
import { defineConfig } from 'eslint/config';
import tseslint from 'typescript-eslint';
import prettier from 'eslint-config-prettier';
import nodeTest from 'eslint-node-test';

// Only run tseslint on the files that we have included for TypeScript.
const tsconfigTsFiles = ['**/*.{ts,mts}']; // match "include" in tsconfig.ts.json;
const tsconfigJsFiles = ['*.{js,mjs}', 'lib/**/*.{js,mjs}']; // match "include" in tsconfig.js.json

// Using tseslint.config adds some type safety and `extends` to simplify customising config array.
export default defineConfig(
  // Add recommended rules.
  esLintjs.configs.recommended,
  // tseslint with different setup for js/ts
  {
    files: tsconfigJsFiles,
    extends: [tseslint.configs.recommended],
    languageOptions: {
      parserOptions: { project: './tsconfig.js.json' },
    },
    rules: {
      '@typescript-eslint/no-var-requires': 'off', // tseslint does not autodetect commonjs context
      '@typescript-eslint/no-require-imports': 'off', // tseslint does not autodetect commonjs context
    },
  },
  {
    files: tsconfigTsFiles,
    extends: [tseslint.configs.recommended],
    languageOptions: {
      parserOptions: { project: './tsconfig.ts.json' },
    },
  },
  prettier, // Do Prettier last so it can override previous configs.

  // Customise rules.
  {
    files: ['**/*.{js,mjs,cjs}', '**/*.{ts,mts,cts}'],
    rules: {
      'no-else-return': ['error', { allowElseIf: false }],
    },
    languageOptions: {
      globals: {
        ...globals.node,
      },
    },
  },
  {
    files: ['**/*.test.{js,mjs,cjs}'],
    rules: {
      'no-unused-vars': 'off', // lots in tests, minimise churn for now
    },
  },
  {
    files: [...tsconfigTsFiles, ...tsconfigJsFiles],
    rules: {
      '@typescript-eslint/ban-ts-comment': [
        'error',
        {
          'ts-expect-error': 'allow-with-description',
          'ts-ignore': 'allow-with-description',
          'ts-nocheck': true,
          'ts-check': true,
        },
      ],
    },
  },
  {
    files: ['**/*.js'],
    plugins: {
      'node-test': nodeTest,
    },
    extends: ['node-test/recommended'],
    rules: {
      'node-test/prefer-test-context-assert': 'off', // we use callback parameter t to generate mocks, but do not want to use t.assertX (as t.assertX not automatically strict)
      'node-test/no-useless-assertion': 'off', // we use `assert.doesNotThrow()` as only assert in multiple tests (so removing that assert triggers a different lint error)
      'node-test/no-process-env-mutation': 'off', // we manage env in ways node-test does not recognise
      'node-test/require-hook': 'error', // Detect code, especially loops with embedded tests, at top level of describe as runs at file load time.
    },
  },
);
```

</details>

## dependencies (1): bots that keep dependencies current

<details><summary><code>.github/dependabot.yml</code> · since 2022-05-24 · 7 changes · package-ecosystem: "npm"</summary>

```yaml
version: 2
updates:
  - package-ecosystem: "npm"
    target-branch: "develop"
    directory: "/"
    schedule:
      interval: "monthly"
    ignore:
      - dependency-name: "@types/node"
        update-types:
          - "version-update:semver-major"
  - package-ecosystem: "github-actions"
    target-branch: "develop"
    directory: "/"
    schedule:
      interval: "weekly"
    groups:
      codeql-actions:
        patterns:
          - "github/codeql-action/*"
```

</details>

## Superseded (5)

- ci: `.travis.yml` from 2011-11-24, removed 2020-11-10 in 2f7aa3384
- contributing: `.github/CONTRIBUTING.md` from 2019-06-09, removed 2019-08-13 in fea94a9fe
- quality: `.eslintrc` from 2018-01-23, removed 2018-10-08 in 700130ee5
- quality: `.eslintrc.js` from 2020-03-04, removed 2024-04-04 in 6fc933e3b
- quality: `.eslintrc.json` from 2018-10-08, removed 2020-03-04 in f14df0709
