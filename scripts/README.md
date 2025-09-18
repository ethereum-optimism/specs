## Scripts: Upgrade transaction spec generation

This folder contains tooling to generate reproducible, copy‑pasteable markdown for protocol upgrade transactions that deploy or upgrade predeploy contracts.

### What each script does

- **`gen_predeploy_docs.py`**: Core generator. It:
  - Verifies required CLIs are installed (`git`, `make`, `jq`, `cast`, plus Python `jinja2`).
  - Stashes local changes in your Optimism repo, checks out a specified commit, runs `make build-contracts`, and restores your repo state afterward.
  - Extracts contract bytecode and computes:
    - Deployed address (from `from` + `nonce`)
    - Code hash (keccak of deployed bytecode)
    - `sourceHash` using the Upgrade‑deposited scheme with intent text
    - Gas estimate via `cast estimate` against your `ETH_RPC_URL`
  - Renders a markdown section that you can paste into a derivation spec.
  - Optionally copies creation bytecode into `specs/static/bytecode/<fork>-<contract>-deployment.txt`.

- **`run_gen_predeploy_docs.sh`**: Thin wrapper that:
  - Ensures a local venv (via `uv`), installs Python deps, and runs `gen_predeploy_docs.py` with your flags.

- **`upgrades/*.sh`**: Per‑upgrade entrypoints. These call `run_gen_predeploy_docs.sh` once per contract that’s part of the upgrade, passing the right parameters. See `upgrades/gen_interop_upgrade_tx_specs.sh` for a concrete example.

### Prerequisites

- CLIs: `uv`, `git`, `jq`, `make`, Foundry (`forge`, `cast`).
- A local clone of `ethereum-optimism/optimism` (path passed via `--optimism-repo-path`).
- A working Ethereum RPC URL for gas estimation (e.g., an OP Mainnet RPC).

Tip: Ensure the repo at `--optimism-repo-path` can build with `make build-contracts` at the target commit (submodules, toolchains, etc. installed).

---

## How to use `run_gen_predeploy_docs.sh` (Interop example)

We’ll use `scripts/upgrades/gen_interop_upgrade_tx_specs.sh` as the example workflow.

### 1) Create a new upgrade script

Copy the Interop example to a new file under `scripts/upgrades/`, e.g.:

```bash
cp scripts/upgrades/gen_interop_upgrade_tx_specs.sh scripts/upgrades/gen_<yourfork>_upgrade_tx_specs.sh
```

### 2) Update variables for your upgrade

Edit your new script:

- **`GIT_COMMIT_HASH`**: The Optimism repo commit hash that defines the contracts for your upgrade.
- **`FROM_ADDRESS_NONCE`**: Usually `0` per our convention.
- **`FROM_ADDRESS`**: A unique sender for the first deployment. Convention: each deployment uses a fresh address with nonce 0. If you deploy multiple contracts in one script, increment the address between runs (see the helper in the example).
- **`FORK_NAME`**: Display name used in the rendered docs and bytecode file paths.
- **`contracts` array**: One entry per contract, `"ContractName:ProxyAddress"`. If no proxy, you can still list it or comment unused lines.
- The `--eth-rpc-url` value: An RPC that supports `eth_estimateGas` for creation.
- The `--optimism-repo-path` value: Path to your local `optimism` clone.
- Optionally keep `--copy-contract-bytecode true` to automatically write creation bytecode files.

In `scripts/upgrades/gen_interop_upgrade_tx_specs.sh` these look like:

```bash
GIT_COMMIT_HASH=71c460ec7c7c05791ddd841b97bcb664a1f0c753
FROM_ADDRESS_NONCE=0
FROM_ADDRESS=0x4220000000000000000000000000000000000000
FORK_NAME=Interop

declare -a contracts=(
    "CrossL2Inbox:0x4200000000000000000000000000000000000022"
    "L2ToL2CrossDomainMessenger:0x4200000000000000000000000000000000000023"
)
```

Note the helper that increments `FROM_ADDRESS` between iterations so each deployment uses a fresh address with nonce 0.

### 3) Run your script

From the repo root:

```bash
bash scripts/upgrades/gen_interop_upgrade_tx_specs.sh
```

It will:

- Print the rendered markdown to stdout.
- Save creation bytecode files under `specs/static/bytecode/<fork>-<contract>-deployment.txt` when `--copy-contract-bytecode true` is passed.

Tip: Capture output for review:

```bash
bash scripts/upgrades/gen_interop_upgrade_tx_specs.sh | tee /tmp/<yourfork>-gen.md
```

### 4) Paste into your derivation spec

Copy the rendered markdown blocks into your fork’s derivation spec (e.g., `specs/<your-area>/derivation.md`) at the appropriate section.

An example reference output is in the [Interop derivation spec](../specs/interop/derivation.md) starting with the “Generated with” marker (your output will include deployment and optional proxy‑update sections).

The generator also outputs instructions to verify `deployedAddress`, `sourceHash`, `data`, and `contract code hash` using `cast`, `jq`, and a specific commit of the Optimism repo.

---

## Troubleshooting

- Missing tools: Install `uv`, Foundry (`forge`, `cast`), `jq`, `make`. Ensure they’re on your `PATH`.
- Build errors: The Optimism repo must build at `GIT_COMMIT_HASH` (`make build-contracts`). Update submodules/toolchains as needed.
- RPC issues: Use a reliable RPC with gas estimation for the target network.
- Repo path: `--optimism-repo-path` must point to a valid git repo; the script stashes and restores your state.
- Bytecode files: If `--copy-contract-bytecode` is `false`, the generator prints a `jq` command to copy the creation bytecode manually.

---

## Why this flow?

Upgrades must be precisely reproducible. These scripts derive all values (addresses, code hashes, source hashes, call data, gas) from a specific repo commit and explicit inputs, then emit a uniform spec block with verification commands. This reduces copy errors and keeps derivation specs auditable.

