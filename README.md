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

## Contributing

### Dependencies

**Rust Toolchain**

```sh
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

**`mdbook` + plugins**

```sh
cargo install mdbook mdbook-katex mdbook-linkcheck mdbook-mermaid
```

### Serving the book locally

```sh
just serve
```
