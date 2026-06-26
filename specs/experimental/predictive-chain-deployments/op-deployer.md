# Predictive Chain Deployments: op-deployer Orchestration

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
  - [op-deployer state](#op-deployer-state)
  - [Anchor offset (`X`)](#anchor-offset-x)
  - [Deployment window](#deployment-window)
- [Assumptions](#assumptions)
  - [aOPD-001: Off-chain derivation is deterministic](#aopd-001-off-chain-derivation-is-deterministic)
    - [Mitigations](#mitigations)
  - [aOPD-002: The anchor block is not reorg'd during the deployment window](#aopd-002-the-anchor-block-is-not-reorgd-during-the-deployment-window)
    - [Mitigations](#mitigations-1)
  - [aOPD-003: op-deployer state is trusted](#aopd-003-op-deployer-state-is-trusted)
    - [Mitigations](#mitigations-2)
  - [aOPD-004: The prestate build is reproducible](#aopd-004-the-prestate-build-is-reproducible)
    - [Mitigations](#mitigations-3)
- [Invariants](#invariants)
  - [iOPD-001: The deployed L1 system matches the committed artifacts](#iopd-001-the-deployed-l1-system-matches-the-committed-artifacts)
    - [Impact](#impact)
  - [iOPD-002: `startingAnchorRoot` equals the genesis output root](#iopd-002-startinganchorroot-equals-the-genesis-output-root)
    - [Impact](#impact-1)
  - [iOPD-003: `absolutePrestate` matches the committed chain config](#iopd-003-absoluteprestate-matches-the-committed-chain-config)
    - [Impact](#impact-2)
  - [iOPD-004: A permissionless deployment requires a committed prestate](#iopd-004-a-permissionless-deployment-requires-a-committed-prestate)
    - [Impact](#impact-3)
- [Pipeline](#pipeline)
  - [prepare](#prepare)
  - [prestate](#prestate)
  - [continue](#continue)
- [Deployment guards](#deployment-guards)
- [Genesis block header fields](#genesis-block-header-fields)
- [depsets.json](#depsetsjson)
- [Failure modes](#failure-modes)
- [Developer experience](#developer-experience)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

op-deployer orchestrates PCD by computing all chain artifacts off-chain before broadcasting, then submitting
`OPCM.deploy()` with the real `startingAnchorRoot` and `absolutePrestate`. This replaces the previous
`startingAnchorRoot = 0xdead` flow.

The pipeline is three stages: `prepare` (off-chain computation), `prestate` (commit the prestate
hash), and `continue` (re-validate and broadcast). This page specifies the orchestration and the behavior of the
three commands. The Solidity surface changes the pipeline drives are specified in [Contracts](./contracts.md).

## Definitions

### op-deployer state

`state.json` is op-deployer's canonical state file, written to the working directory alongside `intent.toml`. It is
the only channel between the off-chain computation and the eventual broadcast. `prepare` records the predicted L1
addresses, the L2 allocs, the anchor block reference, and the genesis [output root](./overview.md#output-root).
`prestate` records the prestate hash. `continue` reads these to run its preflight, set `startingAnchorRoot` and
`absolutePrestate`, and broadcast `OPCM.deploy()`.

### Anchor offset (`X`)

The number of seconds added to the [anchor block](./overview.md#anchor-block) timestamp to set the L2 genesis
timestamp: `genesis_time = l1AnchorBlock.timestamp + X`. The operator commits to `X` at deploy time. Every artifact
that is built down the pipeline derives deterministically from it.

### Deployment window

The interval between fixing `genesis_time` and the `OPCM.deploy()` transaction being mined. Everything from
predicting the L1 addresses through building the prestate runs inside this window. Correctness requires `genesis_time`
to still be in the future when `OPCM.deploy()` is mined (see [FM5](#failure-modes)).

## Assumptions

### aOPD-001: Off-chain derivation is deterministic

Given the same [anchor block](./overview.md#anchor-block), [anchor offset](#anchor-offset-x), chain config, and L1
state, the pipeline reproduces identical artifacts: the predicted L1 addresses, the
[L2 allocs](./overview.md#l2-allocs), the [genesis block](./overview.md#genesis-block), its
[output root](./overview.md#output-root), and the prestate hash.

#### Mitigations

- The deployment logic is pinned to a specific monorepo commit, covering both `L2Genesis.s.sol` and the
  `OPCM.deploy()` code path.
- Address prediction reuses the same `DeployOPChain` script that performs the broadcast (see
  [aPCD-001](./contracts.md#apcd-001-opcm-address-determinism)).
- The prestate comes from the reproducible `reproducible-prestate-kona` recipe (see
  [aOPD-004](#aopd-004-the-prestate-build-is-reproducible)).

### aOPD-002: The anchor block is not reorg'd during the deployment window

The [anchor block](./overview.md#anchor-block) chosen during `prepare` stays on the canonical L1 chain until
`OPCM.deploy()` is mined. A reorg past it invalidates both `rollup.json` and the prestate.

#### Mitigations

- Only blocks at the `safe` tag or deeper are eligible. Any attempt to use a shallower block fails the pipeline with a
  clear error.
- A `BLOCKHASH` check in the deploy transaction reverts if the anchor is no longer retrievable, aborting before
  `OPCM.deploy()` runs (see [FM1](#failure-modes)).

### aOPD-003: op-deployer state is trusted

The artifacts and hashes that `prepare` and `prestate` write are not tampered with before `continue` reads them. The
[state](#op-deployer-state) is the only channel between the off-chain computation and the eventual broadcast.

#### Mitigations

- The state is a local file under the operator's control.
- Before `continue`, a reviewer recomputes the output root and reproduces the prestate from the committed artifacts,
  then compares both against the state (see [FM4](#failure-modes) and [FM7](#failure-modes)).

### aOPD-004: The prestate build is reproducible

Building the prestate from the committed artifacts yields the same hash for any party that runs the
`reproducible-prestate-kona` recipe. The `prestate` command commits this externally-built hash. It does not build the
prestate itself.

#### Mitigations

- The recipe embeds the chain config at compile time, so the hash is a pure function of the committed artifacts.
- A reviewer rebuilds the prestate and compares the hash against the value in the state before `continue` (see
  [FM4](#failure-modes)).

## Invariants

### iOPD-001: The deployed L1 system matches the committed artifacts

The L1 contract addresses baked into the committed artifacts MUST equal the addresses that `OPCM.deploy()` actually
deploys. The L2 genesis is built from the predicted addresses, so any divergence makes the chain unsafe to operate.

#### Impact

**Severity: Critical**

If violated, the L2 genesis encodes the wrong L1 system and the dispute system is seeded for a configuration that was
never deployed, making the chain unusable. The pre-broadcast preflight and post-deploy validation enforce this
invariant, and the on-chain determinism it depends on is
[aPCD-001](./contracts.md#apcd-001-opcm-address-determinism). See [FM2](#failure-modes) and
[FM3](#failure-modes).

### iOPD-002: `startingAnchorRoot` equals the genesis output root

The `startingAnchorRoot` passed to `OPCM.deploy()` MUST equal the [output root](./overview.md#output-root) recomputed
from the committed [genesis block](./overview.md#genesis-block), with `l2SequenceNumber = 0`.

#### Impact

**Severity: Critical**

A wrong anchor seeds `AnchorStateRegistry` with a state that never existed. Honest proposals that descend from the real
genesis cannot be proven, and fault proofs are broken from block 0.

### iOPD-003: `absolutePrestate` matches the committed chain config

The prestate hash written to the [state](#op-deployer-state) and carried into the enabled permissionless `disputeGameConfigs` entry MUST
equal the hash reproduced from the committed `genesis.json`, `rollup.json`, and `depsets.json`. Re-running `prepare`
with a different anchor MUST invalidate a stale prestate before `continue` proceeds.

#### Impact

**Severity: Critical**

A mismatched prestate makes the two sides of a dispute disagree on the starting state. Fault proofs are broken from
block 0, with no on-chain guard to catch it at deploy time. Recovering from this is expensive. See
[FM4](#failure-modes) and [FM6](#failure-modes).

### iOPD-004: A permissionless deployment requires a committed prestate

`continue` MUST halt any attempt to make a permissionless deployment when the prestate is unset. A permissioned-only
deployment carries no prestate and MUST be able to proceed without one.

#### Impact

**Severity: High**

If a permissionless deployment proceeded without a prestate, it would broadcast `OPCM.deploy()` with a missing
`absolutePrestate`. This check is conditional on a permissionless game type being enabled.

## Pipeline

The three commands run in order around the prestate boundary. Each command's output MUST be set before the next
command can run.

### prepare

Off-chain computation of the genesis block. Outputs `genesis.json`, `rollup.json`, and `depsets.json`.

- **Pick the anchor block.** Choose an L1 anchor block at the `safe` tag or deeper to avoid reorg invalidation. Its
  hash is baked into `rollup.json` and the prestate.
- **Fix the genesis timestamp.** Set `genesis_time = l1AnchorBlock.timestamp + X`, where `X` is a configured offset.
  The genesis timestamp is a direct input to the genesis block header, `stateRoot`, output root, and prestate hash. A
  different timestamp changes every downstream artifact.
- **Predict the L1 addresses.** Call the [contracts prediction path](./contracts.md#address-prediction), using the
  same `from` address as the eventual `OPCM.deploy()` broadcast.
- **Compute the L2 allocs.** Execute `L2Genesis.s.sol` with the predicted L1 addresses.
- **Build the genesis block** from the allocs, chain config, and `genesis_time`.
- **Compute the genesis [output root](./overview.md#output-root).**
- **Generate `depsets.json`.**

### prestate

The prestate is built **externally** by the monorepo's `reproducible-prestate-kona` recipe, from the `genesis.json`,
`rollup.json`, and `depsets.json` that `prepare` produces. The `prestate` command does not compile or hash anything
itself. It only commits the built hash into op-deployer state, which `continue` reads.

- MUST write the prestate hash to op-deployer state from one of two sources, treated identically:
  - a **command flag** that passes the hash directly, or
  - an **intent override** declared in the intent, which the command resolves.
- MUST fail if neither source is provided.
- If both are provided, it MUST fail when the two hashes disagree.
- Re-running `prepare` with a different anchor MUST invalidate a previously-committed prestate and force a rebuild
  before `continue` (see [FM6](#failure-modes)).

### continue

- MUST re-check the predicted addresses against current L1 state (pre-broadcast preflight) and abort on mismatch.
- MUST submit `OPCM.deploy()` with the `startingAnchorRoot` (the genesis output root) and `absolutePrestate`.
- MUST run post-deploy validation: deployed addresses match the committed genesis, the anchor is seeded with the
  genesis output root at `l2SequenceNumber = 0`, and the guardian and system-config addresses match the intent.
- The prestate gate is conditional on a permissionless game type. A permissionless deployment MUST halt if the
  prestate is unset, while a **permissioned-only** deployment can continue without one.

Carrying the real anchor root and the prestate into `OPCM.deploy()` requires two changes on the op-deployer side:

- The Go input struct for the OP Chain deployment gains a `StartingAnchorRoot` field and a prestate-hash field for the
  permissionless game.
- op-deployer's chain orchestration code wires those fields through into the `FullConfig` eventually passed to OPCM.

The matching Solidity changes, the `DeployOPChain` script and the relaxation that accepts a permissionless game type at
initial deployment, are specified in [Contracts](./contracts.md#change-specification).

## Deployment guards

- **Anchor `BLOCKHASH` check.** The deploy transaction reverts before `OPCM.deploy()` runs if the anchor block hash is
  no longer retrievable, catching an L1 reorg past the anchor (see [FM1](#failure-modes)).
- **Preflight + post-deploy validation.** Predicted addresses are re-validated before broadcast and the real addresses
  verified after, guarding against prediction drift and compromised RPCs.
- **Alternate RPC cross-check.** The dry-run that produces the predicted addresses MAY be re-run against a second,
  independent L1 RPC. A mismatch between the two flags a compromised endpoint before any transaction is broadcast (see
  [FM3](#failure-modes)).

## Genesis block header fields

| Field | Source |
| --- | --- |
| `parentHash` | `0x00…00` (no parent) |
| `stateRoot` | `L2Genesis` output |
| `timestamp` | the fixed `genesis_time` |
| `gasLimit` | chain config |
| `number` | `0` (L2 genesis block number) |
| `baseFee` | 1 gwei |
| other | standard genesis values per hardfork |

## depsets.json

Generation is **unchanged from the current pipeline**: a single-chain dependency set for standalone chains, and a
multi-chain depset for shared-dependency-set deployments. Deploying a chain directly into a shared super dispute game
is **not** supported at this time.

## Failure modes

Summarized from `fma.md`. See the design doc for full mitigation and recovery detail. Each row maps to one of the
[invariants](#invariants) above.

| ID | Failure | Risk | Key mitigation |
| --- | --- | --- | --- |
| FM1 | L1 anchor reorg after selection | Low likelihood / high impact | `BLOCKHASH` check reverts deploy, abort and restart |
| FM2 | Predicted ≠ deployed L1 addresses | Low / high | Same `from` for dry-run and broadcast, plus preflight and post-deploy validation |
| FM3 | Compromised L1 RPC | Low / high | Trusted or self-hosted RPC, cross-check against a second RPC, post-deploy validation |
| FM4 | Wrong prestate hash | Low / high | Source override from reproducible build, reproduce and verify before `continue` |
| FM5 | Genesis timestamp overrun | Low / low | Set `X` conservatively, chain fills the gap with empty blocks |
| FM6 | Stale prestate after re-running `prepare` | Low / high | `prepare` invalidates prestate, forcing rebuild |
| FM7 | Wrong `startingAnchorRoot` | Low / high | Recompute output root from committed genesis before `continue`, post-deploy anchor check |

## Developer experience

- Permissionless deployments require a prestate, built externally and committed via the `prestate` command's flag or an
  intent override. This adds the prestate build time to the deployment.
- Permissioned-only deployments skip the prestate requirement.
