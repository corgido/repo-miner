# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!-- markdownlint-disable MD024 -->
<!-- markdownlint-disable MD004 -->

## [15.0.0] (2026-05-29)

Commander 15 is ESM only. This is expected to be seamless for ESM consumers, but some CommonJS consumers may hit issues with tooling requiring configuration for ESM-only dependencies. See Migration Tips below.

The release of Commander 15 moves Commander 14 into maintenance. Commander 14 will get security updates for
12 months (to May 2027). For more info see [Release Policy](./docs/release-policy.md).

### Added

- show excess command-arguments in error message ([#2384])

### Fixed

- *Breaking:* only lone `--no-*` option sets default option value to `true`, default not implicitly set when define both positive and negative option in either order ([#2405])
- update example to use compatible character for MINGW64 ([#2475])

### Changed

- *Breaking:* migrated Commander implementation from CommonJS to ESM ([#2464])
- *Breaking:* Commander 15 requires Node.js v22.12.0 or higher (for `require(esm)`).
- dev: switch tests from Jest to `node:test` test runner ([#2463])

### Deleted

- *Breaking:* removed deprecated export of `commander/esm.mjs` ([#2464])

### Migration Tips

Commander 15 is ESM only, but this does not mean you need to migrate to ESM to use it. Importing ESM from CommonJS is
supported by Node.js, and Bun, and Deno. Hopefully it Just Works for you! However, you may be using a different runtime or
some other part of your setup that may not yet natively support importing ESM from CommonJS, such as your testing framework
or bundler.

If you have problems using Commander 15 in your environment, one option is stay on Commander 14 for now. Commander 14 will
get security updates until May 2027 and things will hopefully improve for your setup in the meantime.

## [15.0.0-0] (2026-02-22)

(Released as 15.0.0)

## [14.0.3] (2026-01-31)

### Added

- Release Policy document ([#2462])
  
### Changes

- old major versions now supported for 12 months instead of just previous major version, to give predictable end-of-life date ([#2462])
- clarify typing for deprecated callback parameter to `.outputHelp()` ([#2427])
- simple readability improvements to README ([#2465])
  
## [14.0.2] (2025-10-25)

### Changed

- improve negative number auto-detection test ([#2428])
- update (dev) dependencies

## [14.0.1] (2025-09-12)

### Fixed

- broken markdown link in README ([#2369])

### Changed

- improve code readability by using optional chaining ([#2394])
- use more idiomatic code with object spread instead of `Object.assign()` ([#2395])
- improve code readability using `string.endsWith()` instead of `string.slice()` ([#2396])
- refactor `.parseOptions()` to process args array in-place ([#2409])
- change private variadic support routines from `._concatValue()` to `._collectValue()` (change code from `array.concat()` to `array.push()`) ([#2410])
- update (dev) dependencies

## [14.0.0] (2025-05-18)

### Added

- support for groups of options and commands in the help using low-level `.helpGroup()` on `Option` and `Command`, and higher-level `.optionsGroup()` and `.commandsGroup()` which can be used in chaining way to specify group title for following options/commands ([#2328])
- support for unescaped negative numbers as option-arguments and command-arguments ([#2339])
- TypeScript: add `parseArg` property to `Argument` class ([#2359])

### Fixed

- remove bogus leading space in help when option has default value but not a description ([#2348])
- `.configureOutput()` now makes copy of settings instead of modifying in-place, fixing side-effects ([#2350])

### Changed

- *Breaking:* Commander 14 requires Node.js v20 or higher
- internal refactor of `Help` class adding `.formatItemList()` and `.groupItems()` methods ([#2328])

## [13.1.0] (2025-01-21)

### Added

- support a pair of long option flags to allow a memorable shortened flag, like `.option('--ws, --workspace')` ([#2312])

## [13.0.0] (2024-12-30)

### Added

- support multiple calls to `.parse()` with default settings ([#2299])
- add `.saveStateBeforeParse()` and `.restoreStateBeforeParse()` for use by subclasses ([#2299])
- style routines like `styleTitle()` to add color to help using `.configureHelp()` or Help subclass ([#2251])
- color related support in `.configureOutput()` for `getOutHasColors()`, `getErrHasColors()`, and `stripColor()` ([#2251])
- Help property for `minWidthToWrap` ([#2251])
- Help methods for `displayWidth()`, `boxWrap()`, `preformatted()` et al ([#2251])

### Changed

- *Breaking*: excess command-arguments cause an error by default, see migration tips ([#2223])
- *Breaking*: throw during Option construction for unsupported option flags, like multiple characters after single `-` ([#2270])
  - note: support for dual long option flags added in Commander 13.1
- *Breaking*: throw on multiple calls to `.parse()` if `storeOptionsAsProperties: true` ([#2299])
- TypeScript: include implicit `this` in parameters for action handler callback ([#2197])

### Deleted

- *Breaking*: `Help.wrap()` refactored into `formatItem()` and `boxWrap()` ([#2251])

### Migration Tips

**Excess command-arguments**

It is now an error for the user to specify more command-arguments than are expected. (`allowExcessArguments` is now false by default.)

Old code:

```js
program.option('-p, --port <number>', 'port number');
program.action((options) => {
  console.log(program.args);
});
```

Now shows an error:

```console
$ node example.js a b c
error: too many arguments. Expected 0 arguments but got 3.
```

You can declare the expected arguments. The help will then be more accurate too. Note that declaring
new arguments will change what is passed to the action handler.

```js
program.option('-p, --port <number>', 'port number');
program.argument('[args...]', 'remote command and arguments'); // expecting zero or more arguments
program.action((args, options) => {
  console.log(args);
});
```

Or you could suppress the error, useful for minimising changes in legacy code.

```js
program.option('-p, --port', 'port number');
program.allowExcessArguments();
program.action((options) => {
  console.log(program.args);
});
```

**Stricter option flag parsing**

Commander now throws an error for option flag combinations that are not supported.
In particular, a short flag with multiple characters is now an error.

```js
program.option('-ws, --workspace'); // throws error
```

A short option has a single character:

```js
program.option('-w, --workspace');
```

Or from Commander 13.1 you can have an extra long flag instead of a short flag to allow a more memorable shortcut for the full name:

```js
program.option('--ws, --workspace');
```

## [13.0.0-0] (2024-12-07)

(Released in 13.0.0)

## [12.1.0] (2024-05-18)

### Added

- auto-detect special node flags `node --eval` and `node --print` when call `.parse()` with no arguments ([#2164])

### Changed

- prefix require of Node.js core modules with `node:` ([#2170])
- format source files with Prettier ([#2180])
- switch from StandardJS to directly calling ESLint for linting ([#2153])
- extend security support for previous major version of Commander ([#2150])

### Removed

- removed unimplemented Option.fullDescription from TypeScript definition ([#2191])

## [12.0.0] (2024-02-03)

### Added

- `.addHelpOption()` as another way of configuring built-in help option ([#2006])
- `.helpCommand()` for configuring built-in help command ([#2087])

### Fixed

- *Breaking:* use non-zero exit code when spawned executable subcommand terminates due to a signal ([#2023])
- *Breaking:* check `passThroughOptions` constraints when using `.addCommand` and throw if parent command does not have `.enablePositionalOptions()` enabled ([#1937])

### Changed

- *Breaking:* Commander 12 requires Node.js v18 or higher ([#2027])
- *Breaking:* throw an error if add an option with a flag which is already in use ([#2055])
- *Breaking:* throw an error if add a command with name or alias which is already in use ([#2059])
- *Breaking:* throw error when calling `.storeOptionsAsProperties()` after setting an option value ([#1928])
- replace non-standard JSDoc of `@someone private` with documented `@someone` ([#1949])
- `.addHelpCommand()` now takes a Command (passing string or boolean still works as before but deprecated) ([#2087])
- refactor internal implementation of built-in help option ([#2006])
- refactor internal implementation of built-in help command ([#2087])

### Deprecated

- `.addHelpCommand()` passing string or boolean (use `.helpCommand()` or pass a Command) ([#2087])

### Removed

- *Breaking:* removed default export of a global Command instance from CommonJS (use the named `program` export instead) ([#2017])

### Migration Tips

**global program**

If you are using the [deprecated](./docs/deprecated.md#default-import-of-global-command-object) default import of the global Command object, you need to switch to using a named import (or create a new `Command`).

```js
// const program = require('commander');
const { program } = require('commander');
```

**option and command clashes**

A couple of configuration problems now throw an error, which will pick up issues in existing programs:

- adding an option which uses the same flag as a previous option
- adding a command which uses the same name or alias as a previous command

## [12.0.0-1] (2024-01-20)

(Released in 12.0.0)

## [12.0.0-0] (2023-11-11)

(Released in 12.0.0)

## [11.1.0] (2023-10-13)

### Fixed

- TypeScript: update `OptionValueSource` to allow any string, to match supported use of custom sources ([#1983])
- TypeScript: add that `Command.version()` can also be used as getter ([#1982])
- TypeScript: add null return type to `Commands.executableDir()`, for when not configured ([#1965])
- subcommands with an executable handler and only a short help flag are now handled correctly by the parent's help command ([#1930])

### Added

- `registeredArguments` property on `Command` with the array of defined `Argument` (like `Command.options` for `Option`) ([#2010])
- TypeScript declarations for Option properties: `envVar`, `presetArg` ([#2019])
- TypeScript declarations for Argument properties: `argChoices`, `defaultValue`, `defaultValueDescription` ([#2019])
- example file which shows how to configure help to display any custom usage in the list of subcommands ([#1896])

### Changed

- (developer) refactor TypeScript configs for multiple use-cases, and enable checks in JavaScript files in supporting editors ([#1969])

### Deprecated

- `Command._args` was private anyway, but now available as `registeredArguments` ([#2010])

## [11.0.0] (2023-06-16)

### Fixed

- help command works when help option is disabled ([#1864])

### Changed

- leading and trailing spaces are now ignored by the .arguments() method ([#1874])
- refine "types" exports for ESM to follow TypeScript guidelines ([#1886])
- *Breaking:* Commander 11 requires Node.js v16 or higher

## [10.0.1] (2023-04-15)

### Added

- improvements to documentation ([#1858], [#1859], [#1860])

### Fixed

- remove unused `Option.optionFlags` property from TypeScript definition ([#1844])

### Changed

- assume boolean option intended if caller passes string instead of hash to `.implies()` ([#1854])

## [10.0.0] (2023-01-13)

### Added

- wrap command description in help ([#1804])

### Changed

- *Breaking:* Commander 10 requires Node.js v14 or higher

## [9.5.0] (2023-01-07)

### Added

- `.getOptionValueSourceWithGlobals()` ([#1832])
- `showGlobalOptions` for `.configureHelp{}` and `Help` ([#1828])

## [9.4.1] (2022-09-30)

### Fixed

- `.setOptionValue()` now also clears option source ([#1795])
- TypeScript: add `implied` to `OptionValueSource` for option values set by using `.implies()` ([#1794])
- TypeScript : add `undefined` to return type of `.getOptionValueSource()` ([#1794])

### Changed

- additions to README

## [9.4.0] (2022-07-15)

### Added

- `preSubcommand` hook called before direct subcommands ([#1763])

### Fixed

- export `InvalidOptionArgumentError` in esm ([#1756])

### Changed

- update dependencies ([#1767])

## [9.3.0] (2022-05-28)

### Added

- `.summary()` for a short summary to use instead of description when listing subcommands in help ([#1726])
- `Option.implies()` to set other option values when the option is specified ([#1724])
- updated Chinese README with 9.x changes ([#1727])

### Fixed

- TypeScript: add `string[]` to `.options()` default value parameter type for use with variadic options ([#1721])

### Deprecated

- multi-character short option flag (e.g. `-ws`) ([#1718])

## [9.2.0] (2022-04-15)

### Added

- conditional export of 'types' for upcoming TypeScript module resolution ([#1703])
- example file showing two ways to add global options to subcommands ([#1708])

### Fixed

- detect option conflicts in parent commands of called subcommand ([#1710])

### Changed

- replace deprecated `String.prototype.substr` ([#1706])

## [9.1.0] (2022-03-19)

### Added

- Option `.conflicts()` to set conflicting options which can not be specified together ([#1678])
- (developer) CodeQL configuration for GitHub Actions ([#1698])

## [9.0.0] (2022-01-28)

### Added

- simpler ECMAScript import ([#1589])
- Option.preset() allows specifying value/arg for option when used without option-argument (especially optional, but also boolean option) ([#1652])
- `.executableDir()` for custom search for subcommands ([#1571])
- throw with helpful message if pass `Option` to `.option()` or `.requiredOption()` ([#1655])
- .`error()` for generating errors from client code just like Commander generated errors, with support for  `.configureOutput()`, `.exitOverride()`, and `.showHelpAfterError()` ([#1675])
- `.optsWithGlobals()` to return merged local and global options ([#1671])

### Changed

- *Breaking:* Commander 9 requires Node.js v12.20.0 or higher
- update package-lock.json to lockfile@2 format ([#1659])
- `showSuggestionAfterError` is now on by default ([#1657])
- *Breaking:* default value specified for boolean option now always used as default value (see .preset() to match some previous behaviours) ([#1652])
- default value for boolean option only shown in help if true/false ([#1652])
- use command name as prefix for subcommand stand-alone executable name (with fallback to script name for backwards compatibility) ([#1571])
- allow absolute path with `executableFile` ([#1571])
- removed restriction that nested subcommands must specify `executableFile` ([#1571])
- TypeScript: allow passing readonly string array to `.choices()` ([#1667])
- TypeScript: allow passing readonly string array to `.parse()`, `.parseAsync()`, `.aliases()` ([#1669])

### Fixed

- option with optional argument not supplied on command line now works when option already has a value, whether from default value or from previous arguments ([#1652])

### Removed

- *Breaking:* removed internal fallback to `require.main.filename` when script not known from arguments passed to `.parse()` (can supply details using `.name()`, and `.executableDir()` or `executableFile`) ([#1571])

## [9.0.0-1] (2022-01-15)

(Released in 9.0.0)

## [9.0.0-0] (2021-12-22)

(Released in 9.0.0)

## [8.3.0] (2021-10-22)

### Added

- `.getOptionValueSource()` and `.setOptionValueWithSource()`, where expected values for source are one of 'default', 'env', 'config', 'cli' ([#1613])

### Deprecated

- `.command('*')`, use default command instead ([#1612])
- `on('command:*')`, use `.showSuggestionAfterError()` instead ([#1612])

## [8.2.0] (2021-09-10)

### Added

- `.showSuggestionAfterError()` to show suggestions after unknown command or unknown option ([#1590])
- add `Option` support for values from environment variables using `.env()` ([#1587])

### Changed

- show error for unknown global option before subcommand (rather than just help) ([#1590])

### Removed

- TypeScript declaration of unimplemented `Option` method `argumentRejected`

## [8.1.0] (2021-07-27)

### Added

- `.copyInheritedSettings()` ([#1557])
- update Chinese translations of documentation for Commander v8 ([#1570])
- `Argument` methods for `.argRequired()` and `.argOptional()` ([#1567])

## [8.0.0] (2021-06-25)

### Added

- `.argument(name, description)` for adding command-arguments ([#1490])
  - supports default value for optional command-arguments ([#1508])
  - supports custom processing function ([#1508])
- `.createArgument()` factory method ([#1497])
- `.addArgument()` ([#1490])
- `Argument` supports `.choices()` ([#1525])
- `.showHelpAfterError()` to display full help or a custom message after an error ([#1534])
- `.hook()` with support for `'preAction'` and `'postAction'` callbacks ([#1514])
- client typing of `.opts()` return type using TypeScript generics ([#1539])
- the number of command-arguments is checked for programs without an action handler ([#1502])
- `.getOptionValue()` and `.setOptionValue()` ([#1521])

### Changed

- refactor and simplify TypeScript declarations (with no default export) ([#1520])
- `.parseAsync()` is now declared as `async` ([#1513])
- *Breaking:* `Help` method `.visibleArguments()` returns array of `Argument` ([#1490])
- *Breaking:* Commander 8 requires Node.js 12 or higher ([#1500])
- *Breaking:* `CommanderError` code `commander.invalidOptionArgument` renamed `commander.invalidArgument` ([#1508])
- *Breaking:* TypeScript declaration for `.addTextHelp()` callback no longer allows result of `undefined`, now just `string` ([#1516])
- refactor `index.tab` into a file per class ([#1522])
- remove help suggestion from "unknown command" error message (see `.showHelpAfterError()`) ([#1534])
- `Command` property `.arg` initialised to empty array (was previously undefined) ([#1529])
- update dependencies

### Deprecated

- second parameter of `cmd.description(desc, argDescriptions)` for adding argument descriptions ([#1490])
  - (use new `.argument(name, description)` instead)
- `InvalidOptionArgumentError` (replaced by `InvalidArgumentError`) ([#1508])

### Removed

- *Breaking:* TypeScript declaration for default export of global `Command` object ([#1520])
  - (still available as named `program` export)

### Migration Tips

If you have a simple program without an action handler, you will now get an error if
there are missing command-arguments.

```js
program
  .option('-d, --debug')
  .arguments('<file>');
program.parse();
```

```sh
$ node trivial.js 
error: missing required argument 'file'
```

If you want to show the help in this situation, you could check the arguments before parsing:

```js
if (process.argv.length === 2)
  program.help();
program.parse();
```

Or, you might choose to show the help after any user error:

```js
program.showHelpAfterError();
```

## [8.0.0-2] (2021-06-06)

(Released in 8.0.0)

## [8.0.0-1] (2021-05-30)

(Released in 8.0.0)

## [8.0.0-0] (2021-05-23)

(Released in 8.0.0)

## [7.2.0] (2021-03-22)

### Added

- TypeScript typing for `parent` property on `Command` ([#1475])
- TypeScript typing for `.attributeName()` on `Option` ([#1483])
- support information in package ([#1477])

### Changed

- improvements to error messages, README, and tests
- update dependencies

## [7.1.0] (2021-02-15)

### Added

- support for named imports from ECMAScript modules ([#1440])
- add `.cjs` to list of expected script file extensions ([#1449])
- allow using option choices and variadic together ([#1454])

### Fixed

- replace use of deprecated `process.mainModule` ([#1448])
- regression for legacy `command('*')` and call when command line includes options ([#1464])
- regression for `on('command:*', ...)` and call when command line includes unknown options ([#1464])
- display best error for combination of unknown command and unknown option (i.e. unknown command) ([#1464])

### Changed

- make TypeScript typings tests stricter ([#1453])
- improvements to README and tests

## [7.0.0] (2021-01-15)

### Added

- `.enablePositionalOptions()` to let program and subcommand reuse same option ([#1427])
- `.passThroughOptions()` to pass options through to other programs without needing `--` ([#1427])
- `.allowExcessArguments(false)` to show an error message if there are too many command-arguments on command line for the action handler ([#1409])
- `.configureOutput()` to modify use of stdout and stderr or customise display of errors ([#1387])
- use `.addHelpText()` to add text before or after the built-in help, for just current command or also for all subcommands ([#1296])
- enhance Option class ([#1331])
  - allow hiding options from help
  - allow restricting option arguments to a list of choices
  - allow setting how default value is shown in help
- `.createOption()` to support subclassing of automatically created options (like `.createCommand()`) ([#1380])
- refactor the code generating the help into a separate public Help class ([#1365])
  - support sorting subcommands and options in help
  - support specifying wrap width (columns)
  - allow subclassing Help class
  - allow configuring Help class without subclassing

### Changed

- *Breaking:* options are stored safely by default, not as properties on the command ([#1409])
  - this especially affects accessing options on program, use `program.opts()`
  - revert behaviour with `.storeOptionsAsProperties()`
- *Breaking:* action handlers are passed options and command separately ([#1409])
- deprecated callback parameter to `.help()` and `.outputHelp()` (removed from README) ([#1296])
- *Breaking:* errors now displayed using `process.stderr.write()` instead of `console.error()`
- deprecate `.on('--help')` (removed from README) ([#1296])
- initialise the command description to empty string (previously undefined) ([#1365])
- document and annotate deprecated routines ([#1349])

### Fixed

- wrapping bugs in help ([#1365])
  - first line of command description was wrapping two characters early
  - pad width calculation was not including help option and help command
  - pad width calculation was including hidden options and commands
- improve backwards compatibility for custom command event listeners ([#1403])
  
### Deleted

- *Breaking:* `.passCommandToAction()` ([#1409])
  - no longer needed as action handler is passed options and command
- *Breaking:* "extra arguments" parameter to action handler ([#1409])
  - if being used to detect excess arguments, there is now an error available by setting `.allowExcessArguments(false)`

### Migration Tips

The biggest change is the parsed option values. Previously the options were stored by default as properties on the command object, and now the options are stored separately.

If you wish to restore the old behaviour and get running quickly you can call `.storeOptionsAsProperties()`.
To allow you to move to the new code patterns incrementally, the action handler will be passed the command _twice_,
to match the new "options" and "command" parameters (see below).

**program options**

Use the `.opts()` method to access the options. This is available on any command but is used most with the program.

```js
program.option('-d, --debug');
program.parse();
// Old code before Commander 7
if (program.debug) console.log(`Program name is ${program.name()}`);
```

```js
// New code
const options = program.opts();
if (options.debug) console.log(`Program name is ${program.name()}`);
```

**action handler**

The action handler gets passed a parameter for each command-argument you declared. Previously by default the next parameter was the command object with the options as properties. Now the next two parameters are instead the options and the command. If you
only accessed the options there may be no code changes required.

```js
program
  .command('compress <filename>')
  .option('-t, --trace')
  // Old code before Commander

[... cut at 24,000 of 62,245 characters by repo-miner ...]
