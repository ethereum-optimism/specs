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

### How to Think about Specs

The specs process is a schelling point for where core developers go to modify the OP Stack. A spec serves multiple purposes:
- Ensures that we know what we are building before we build it
- Helps code reviewers and auditors understand what the behavior is supposed to be
- Enables multiple implementations

Some guidelines for writing a good spec:
- Thoroughly describe the interfaces that other projects may interact with
- Include a light description of the problem that is being solved and the rationale but the majority of this should be recorded during the design doc phase
- Describe things in terms of state machines and invariants
- It should be clear that it solves the problem at hand

What is the difference between the specs and the [design docs](https://github.com/ethereum-optimism/design-docs)?
- The design docs describe why and the specs describe how.
- The design doc phase should be complete before the specs process is complete

### Dependencies

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

`doctoc` is used to automatically add a table of contents.

```sh
just lint-specs-toc-check
```

To fix markdown linting errors:

```sh
just lint-specs-md-fix
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

[lychee](https://github.com/lycheeverse/lychee) is used for linting links.
