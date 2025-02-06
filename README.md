<div align="center">
  <br />
  <br />
  <a href="https://optimism.io"><img alt="Optimism" src="https://raw.githubusercontent.com/ethereum-optimism/brand-kit/main/assets/svg/OPTIMISM-R.svg" width=600></a>
  <br />
  <h3><a href="https://optimism.io">Optimism</a> is Ethereum, scaled.</h3>
  <br />
</div>

## OP Stack Specification

This repository contains the [Specs Book](https://static.optimism.io/specs).

Please chat with us on the [discussion board](https://github.com/ethereum-optimism/specs/discussions).

## Contributing

We welcome your contributions. Read through [CONTRIBUTING.md](./CONTRIBUTING.md) for a general overview of the contributing process for this repository.

### Dependencies

#### Using `mise`

We use [`mise`](https://mise.jdx.dev/) as a dependency manager for these tools.
Once properly installed, `mise` will provide the correct versions for each tool. `mise` does not
replace any other installations of these binaries and will only serve these binaries when you are
working inside of the `optimism` directory.

##### Install `mise`

Install `mise` by following the instructions provided on the
[Getting Started page](https://mise.jdx.dev/getting-started.html#_1-install-mise-cli).

##### Install dependencies

```sh
mise install
```

#### Manual installation

**Rust Toolchain**

```sh
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

**`mdbook` + plugins**

```sh
cargo install mdbook mdbook-katex mdbook-linkcheck mdbook-mermaid
```

**`just` [installation](https://github.com/casey/just?tab=readme-ov-file#installation)**

```sh
brew install just
```

### Serving the book locally

```sh
just serve
```

### Linting

[doctoc](https://github.com/thlorenz/doctoc) is used to automatically add a table of contents.

To check the table of contents:

```sh
just lint-specs-toc
```

To fix the table of contents:

```sh
just lint-specs-toc-fix
```

[markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2) is used to check markdown linting errors.

To check markdown linting errors:

```sh
just lint-specs-md
```

To fix markdown linting errors:

```sh
just lint-specs-md-fix
```

`cspell` is used to check spelling.

To check spelling:

```sh
just lint-specs-spelling
```

To fix spelling:

```sh
just lint-specs-spelling-fix
```

[lychee](https://github.com/lycheeverse/lychee) is used to check hyperlinks.

To check all hyperlinks respond with status 200:

```sh
just lint-links
```

`find` is used to check filenames do not contain underscores.

To check filenames do not contain underscores:

```sh
just lint-filenames
```

To check all linting:

```sh
just lint
```

To fix all linting that can be automatically fixed:

```sh
just lint-fix
```

See the [markdownlint rule reference](https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md)
and an example [config file](https://github.com/DavidAnson/markdownlint/blob/main/schema/.markdownlint.jsonc).

Justification for linting rules in
[.markdownlint.json](https://github.com/ethereum-optimism/specs/blob/main/.markdownlint.json):

- _line_length_ (`!strict && stern`): don't trip up on url lines
- _no-blanks-blockquote_: enable multiple consecutive blockquotes separated by white lines
- _single-title_: enable reusing `<h1>` for content
- _no-emphasis-as-heading_: enable emphasized paragraphs

To lint links:

```sh
just lint-links
```

 is used for linting links.
