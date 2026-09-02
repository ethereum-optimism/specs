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
  - [iOPD-002: `startingAnchorRoot` equals the committed starting anchor root](#iopd-002-startinganchorroot-equals-the-committed-starting-anchor-root)
    - [Impact](#impact-1)
  - [iOPD-003: `absolutePrestate` matches the committed chain config](#iopd-003-absoluteprestate-matches-the-committed-chain-config)
    - [Impact](#impact-2)
  - [iOPD-004: A permissionless deployment requires a committed prestate](#iopd-004-a-permissionless-deployment-requires-a-committed-prestate)
    - [Impact](#impact-3)
  - [iOPD-005: The reserved fallback prestate is never a selected prestate](#iopd-005-the-reserved-fallback-prestate-is-never-a-selected-prestate)
    - [Impact](#impact-4)
  - [iOPD-006: The artifact bundles never change between `prepare` and `continue`](#iopd-006-the-artifact-bundles-never-change-between-prepare-and-continue)
    - [Impact](#impact-5)
  - [iOPD-007: The deployment broadcast is exactly one call to the pinned OPCM](#iopd-007-the-deployment-broadcast-is-exactly-one-call-to-the-pinned-opcm)
    - [Impact](#impact-6)
- [Pipeline](#pipeline)
  - [prepare](#prepare)
  - [prestate](#prestate)
  - [continue](#continue)
  - [Relationship to `apply`](#relationship-to-apply)
- [Deployment guards](#deployment-guards)
- [Genesis block header fields](#genesis-block-header-fields)
- [depsets.json](#depsetsjson)
- [Failure modes](#failure-modes)
- [Developer experience](#developer-experience)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

op-deployer orchestrates PCD by computing all chain artifacts off-chain before broadcasting, then submitting
`OPCM.deploy()` with the real [starting anchor root](./overview.md#starting-anchor-root) and
[selected prestate](./overview.md#selected-prestate).

The pipeline is three stages: `prepare` (off-chain computation), `prestate` (commit the prestate hash), and `continue`
(re-validate and broadcast). This page specifies the orchestration and the behavior of the three commands. The
Solidity surface changes the pipeline drives are specified in [Contracts](./contracts.md).

## Definitions

### op-deployer state

`state.json` is op-deployer's canonical state file, written to the working directory alongside `intent.toml`. It is
the only channel between the off-chain computation and the eventual broadcast. `prepare` records the predicted L1
addresses, the L2 allocs, the anchor block reference, the genesis block hash, and the starting anchor root.
`prestate` records the prestate hash. `continue` reads these to run its preflight, set `startingAnchorRoot` and
`absolutePrestate`, and broadcast `OPCM.deploy()`.

### Anchor offset (`X`)

The number of seconds added to the [anchor block](./overview.md#anchor-block) timestamp to set the L2 genesis
timestamp: `genesis_time = l1AnchorBlock.timestamp + X`. The operator commits to `X` at deploy time.
Every artifact that is built down the pipeline
derives deterministically from it.

`X` sizes the [deployment window](#deployment-window). It has to cover address prediction, the external prestate
build, and the broadcast.

### Deployment window

The interval between fixing `genesis_time` and the `OPCM.deploy()` transaction being mined. Everything from
predicting the L1 addresses through building the prestate runs inside this window. Correctness requires `genesis_time`
to still be in the future when `OPCM.deploy()` is mined (see [FM5](#failure-modes)).

## Assumptions

### aOPD-001: Off-chain derivation is deterministic

Given the same [anchor block](./overview.md#anchor-block), [anchor offset](#anchor-offset-x), chain config, and L1
state, the pipeline reproduces identical artifacts: the predicted L1 addresses, the
[L2 allocs](./overview.md#l2-allocs), the [genesis block](./overview.md#genesis-block), its
[starting anchor root](./overview.md#starting-anchor-root), and the prestate hash.

#### Mitigations

- The deployment logic is pinned to a specific monorepo commit, covering both `L2Genesis.s.sol` and the
  `OPCM.deploy()` code path.
- Address prediction reuses the same `DeployOPChain` script that performs the broadcast (see
  [aPCD-001](./contracts.md#apcd-001-opcm-address-determinism)).
- The CREATE2 salt is generated once and persisted in state, so re-runs cannot derive a different one (see
  [Salt Mixer](./overview.md#salt-mixer)).
- The prestate comes from the reproducible `reproducible-prestate-kona` recipe (see
  [aOPD-004](#aopd-004-the-prestate-build-is-reproducible)).

### aOPD-002: The anchor block is not reorg'd during the deployment window

The [anchor block](./overview.md#anchor-block) chosen during `prepare` stays on the canonical L1 chain until
`OPCM.deploy()` is mined. A reorg past it invalidates both `rollup.json` and the prestate.

#### Mitigations

- Only blocks at the `safe` tag or deeper are eligible. Any attempt to use a shallower block fails the pipeline with a
  clear error.
- An anchor supplied by hash is re-fetched by number and compared, since a hash lookup alone can return a block that
  has already been reorg'd out.
- `continue` re-fetches the `safe` tag and re-verifies the pinned anchor is canonical at its height immediately before
  each broadcast, aborting the broadcast on drift (see [FM1](#failure-modes)).
- The deployment receipt's block is checked to be canonical after the transaction is mined, catching a reorg that
  lands after the pre-broadcast check.

### aOPD-003: op-deployer state is trusted

The artifacts and hashes that `prepare` and `prestate` write are not tampered with before `continue` reads them. The
[state](#op-deployer-state) is the only channel between the off-chain computation and the eventual broadcast. The
artifact bundles the state references are outside this assumption.

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
  [FM4](#failure-modes)). This is the only check that catches a prestate that is set but incorrect.

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

### iOPD-002: `startingAnchorRoot` equals the committed starting anchor root

The `startingAnchorRoot` passed to `OPCM.deploy()` MUST equal the
[starting anchor root](./overview.md#starting-anchor-root) recomputed from the committed
[genesis block](./overview.md#genesis-block). Both the root and its `l2SequenceNumber` MUST match, and what they hold
depends on the game family:

- **Output root games.** The root is the chain's own genesis output root and `l2SequenceNumber` is `0`, the L2 genesis
  block number.
- **Super root games.** The root is one [super root](./overview.md#super-root) over the whole dependency set and
  `l2SequenceNumber` is that super root's timestamp. Every member chain is seeded with the same pair.

#### Impact

**Severity: Critical**

A wrong anchor seeds `AnchorStateRegistry` with a state that never existed. Honest proposals that descend from the real
genesis cannot be proven, and fault proofs are broken from block 0.

### iOPD-003: `absolutePrestate` matches the committed chain config

The prestate hash written to the [state](#op-deployer-state) and carried into the enabled permissionless
`disputeGameConfigs` entry MUST equal the hash reproduced from the committed `genesis.json`, `rollup.json`, and
`depsets.json`. Re-running `prepare` MUST invalidate a stale prestate before `continue` proceeds.

#### Impact

**Severity: Critical**

A mismatched prestate makes the two sides of a dispute disagree on the starting state. Fault proofs are broken from
block 0. Recovering from this is expensive. See [FM4](#failure-modes) and [FM6](#failure-modes).

### iOPD-004: A permissionless deployment requires a committed prestate

`continue` MUST halt any attempt to make a permissionless deployment when the prestate is unset.
A permissioned-only deployment has no committed prestate and MUST be able to proceed without one, carrying the
[selected prestate](./overview.md#selected-prestate) its chain configuration already supplies.

#### Impact

**Severity: High**

The deployment cannot succeed, since the enabled permissionless game would have no prestate to commit to. The failure
surfaces during the deployment attempt rather than before any transaction is prepared.

### iOPD-005: The reserved fallback prestate is never a selected prestate

The [fallback prestate](./overview.md#fallback-prestate) value is reserved for the guardian fallback game. It MUST
never be committed as the [selected prestate](./overview.md#selected-prestate) of a permissionless deployment.

#### Impact

**Severity: Critical**

The respected game would be seeded with a prestate that commits to no real fault-proof program, leaving it unplayable
from block 0. Fault proofs are broken exactly as in
[iOPD-003](#iopd-003-absoluteprestate-matches-the-committed-chain-config).

### iOPD-006: The artifact bundles never change between `prepare` and `continue`

The L1 and L2 artifact bundles resolved at `continue` MUST have the content digests that `prepare` recorded for the
locators it froze. A digest covers every file path and file content in a bundle, so re-resolving the same locator to
different contents MUST abort the run before any transaction is prepared.

[aOPD-003](#aopd-003-op-deployer-state-is-trusted) covers the state file only. The bundles the state references are a
separate trust surface, and this invariant is what covers them. Resolving a locator carries no integrity
check of its own, so this comparison is the only thing that ties a locator to the contents it
returns.

#### Impact

**Severity: Critical**

The failure is different for both L1 and L2 bundles. The L1 bundle backs the forked simulation that
enforces [iOPD-001](#iopd-001-the-deployed-l1-system-matches-the-committed-artifacts), so a
substituted bundle makes the preflight compare predicted addresses against code the operator never
predicted against, and the check passes while proving nothing. The L2 bundle is what the committed
genesis and [starting anchor root](./overview.md#starting-anchor-root) were derived from, so a
substituted bundle leaves a genesis that no reviewed artifact set explains. Either way the chain is
deployed from two different versions of the artifacts, which is the condition
[iOPD-001](#iopd-001-the-deployed-l1-system-matches-the-committed-artifacts) exists to rule out.

### iOPD-007: The deployment broadcast is exactly one call to the pinned OPCM

Simulating the deployment MUST produce exactly one broadcast: a call, to the OPCM pinned by `prepare`, sent from the
deployer pinned by `prepare`. A simulation that produces no broadcast, more than one, or one that differs in type,
target, or sender MUST abort before anything is sent.

#### Impact

**Severity: Critical**

Any broadcast beyond the single pinned call is a transaction the operator never reviewed, signed by the deployer key. A
modified or compromised deploy script could deploy a contract of its own, call an address other than the pinned OPCM,
or repeat `OPCM.deploy()`, and the deployed system would no longer be the one the frozen snapshot describes. Because
the check runs against the simulation rather than the receipt, it aborts before the key signs anything.

## Pipeline

The three commands run in order around the prestate boundary. Each command's output MUST be set before the next
command can run.

### prepare

Off-chain computation of the genesis block and the starting anchor root. Everything it derives goes into
[op-deployer state](#op-deployer-state).

`prepare` predicts against an already-deployed OPCM rather than deploying one, so the intent MUST pin both
`opcmAddress` and `superchainConfigProxy`. `prepare` reads the implementation set and the game mode
(`SUPER_ROOT_GAMES_MIGRATION`) off that OPCM and records them, and rejects a chain whose requested game type belongs
to the other mode before doing any further work.

- **Pick the anchor block.** Choose an L1 anchor block at the `safe` tag or deeper to avoid reorg invalidation. Its
  hash is baked into `rollup.json` and the prestate.
- **Fix the genesis timestamp.** Set `genesis_time = l1AnchorBlock.timestamp + X`, where `X` is the
  [anchor offset](#anchor-offset-x). The genesis timestamp is a direct input to the genesis block header, `stateRoot`,
  output root, and prestate hash. A different timestamp changes every downstream artifact.
- **Predict the L1 addresses.** Call the [contracts prediction path](./contracts.md#address-prediction), using the
  same `from` address as the eventual `OPCM.deploy()` broadcast.
- **Compute the L2 allocs.** Execute `L2Genesis.s.sol` with the predicted L1 addresses.
- **Build the genesis block** from the allocs, chain config, and `genesis_time`.
- **Compute the [starting anchor root](./overview.md#starting-anchor-root).**
- **Build the dependency set.**

`prepare` MUST pin each chain's anchor block and genesis time on its first run and reuse that pair on every later run,
so re-runs stay idempotent. It MUST fail when a per-chain `l1StartBlockHash` override conflicts with an already-pinned
anchor, and when the pinned genesis time has fallen outside the [deployment window](#deployment-window).

Any `prepare` run MUST invalidate every artifact derived from the predicted addresses for the chains it re-prepares:
the committed prestate, the starting anchor root, the L2 allocs, and the genesis block hash. A
re-run that reuses the pinned anchor still clears them, so **every `prepare` re-run forces a `prestate` re-run** (see
[FM6](#failure-modes)).

### prestate

The prestate is built **externally** by the monorepo's `reproducible-prestate-kona` recipe, from the `genesis.json`,
`rollup.json`, and `depsets.json` rendered from the prepared state. The `prestate` command does not compile or hash
anything itself. It only commits the built hash into op-deployer state, which `continue` reads.

- MUST write the prestate hash to op-deployer state from any of three sources:
  - the `--dispute-absolute-prestate` **command flag**, or the matching environment variable,
  - a **global intent override**, `globalDeployOverrides.faultGameAbsolutePrestate`, or
  - a **per-chain intent override**, the chain's `deployOverrides.faultGameAbsolutePrestate`.
- MUST fail when two or more sources are set and disagree.
- MUST fail if no source is provided for a chain whose game type requires a prestate.
- MUST reject the reserved [fallback prestate](./overview.md#fallback-prestate) value as a selected prestate (see
  [iOPD-005](#iopd-005-the-reserved-fallback-prestate-is-never-a-selected-prestate)).
- A permissioned-only chain MUST be left without a committed prestate. Its respected game keeps the
  [selected prestate](./overview.md#selected-prestate) the chain configuration supplies.

### continue

`continue` deploys from the frozen `preparedDeployment` snapshot. It validates every pending chain before broadcasting
any of them, so a configuration error stops the run before it can produce a partial deployment.

**Before broadcasting any transaction:**

- MUST verify the current intent still agrees with the frozen snapshot, and that the dependency set still matches.
- MUST re-resolve both artifact locators recorded by `prepare` and verify the resolved bundles' content digests
  against the frozen values (see
  [iOPD-006](#iopd-006-the-artifact-bundles-never-change-between-prepare-and-continue)).
- MUST fail when the deployer or OPCM differs from the one recorded by `prepare`.
- MUST halt a permissionless deployment when the prestate is unset or holds the reserved fallback value (see
  [iOPD-005](#iopd-005-the-reserved-fallback-prestate-is-never-a-selected-prestate)). The prestate gate is conditional
  on a permissionless game type: a **permissioned-only** deployment has no committed prestate and proceeds
  without one.
- MUST halt a permissionless deployment when the starting anchor root is unset or still holds the `0xdead` placeholder.
- MUST re-check the predicted addresses by simulating the deployment against a fresh fork of L1 (pre-broadcast
  preflight) and abort on mismatch.
- MUST verify the simulated broadcast is exactly one call, to the pinned OPCM, from the pinned deployer (see
  [iOPD-007](#iopd-007-the-deployment-broadcast-is-exactly-one-call-to-the-pinned-opcm)).
- SHOULD warn, without halting, when the committed genesis time has already elapsed against the L1 head. `prepare`
  refuses an elapsed [deployment window](#deployment-window), measured against the safe head. Elapsing it later costs
  empty blocks, not correctness (see [FM5](#failure-modes)).

**Broadcasting:**

- MUST re-validate the pinned anchor block immediately before each send (see
  [aOPD-002](#aopd-002-the-anchor-block-is-not-reorgd-during-the-deployment-window)).
- MUST submit `OPCM.deploy()` with the `startingAnchorRoot` and `absolutePrestate` committed in state.
- MUST verify the deployment receipt's block is canonical.

**After broadcasting:**

- MUST run post-deploy validation against live L1 state. This covers the deployed addresses and their code, the
  starting anchor root and its `l2SequenceNumber`, the enabled game configurations and the prestate of both the
  respected game and its guardian fallback, the `SystemConfig` / `OptimismPortal` / `AnchorStateRegistry` wiring, the
  proxy implementations against the OPCM's own `implementations()`, the proxy admin owner, and the `SuperchainConfig`
  attachment and guardian.

Carrying the real anchor root and the prestate into `OPCM.deploy()` requires two changes on the op-deployer side:

- The Go input struct for the OP Chain deployment gains a `StartingAnchorRoot` field and a second prestate field for
  the guardian fallback game.
- op-deployer's chain orchestration code wires those fields through into the `FullConfig` eventually passed to OPCM.

The matching Solidity changes, the `DeployOPChain` script and the relaxation that accepts a permissionless game type at
initial deployment, are specified in [Contracts](./contracts.md#change-specification).

### Relationship to `apply`

`apply` remains the path for permissioned-only deployments and
still broadcasts the `0xdead` placeholder anchor. It MUST reject a permissionless game type and direct the operator to
the `prepare` flow.

The two flows MUST NOT be mixed on one working directory. `prepare` MUST refuse a state produced by `apply`, and
`apply` MUST refuse a prepared state.

A permissioned-only chain may still go through `prepare` / `prestate` / `continue`. It has no committed prestate
and broadcasts the same `0xdead` placeholder anchor that `apply` would. The real anchor root is substituted only for
permissionless deployments.

## Deployment guards

- **Pre-broadcast anchor revalidation.** The pinned anchor is re-fetched and re-checked to be canonical immediately
  before each send, and the deployment receipt's block is checked afterwards (see [FM1](#failure-modes)).
- **Preflight + post-deploy validation.** Predicted addresses are re-validated against a fresh fork before broadcast
  and the real addresses verified against live L1 after, guarding against prediction drift and compromised RPCs.
- **Frozen artifact digests.** `continue` re-verifies the artifact bundles against the digests `prepare` recorded, so
  a swapped bundle fails before broadcast.
- **On-chain config validation.** OPCM rejects a zero anchor root on any initial deployment, and rejects the `0xdead`
  placeholder root or a zero prestate once a permissionless game is enabled (see
  [OPCMv2 config validation](./contracts.md#opcmv2-config-validation)).

## Genesis block header fields

| Field | Source |
| --- | --- |
| `parentHash` | `0x00…00` (no parent) |
| `stateRoot` | `L2Genesis` output |
| `timestamp` | the fixed `genesis_time` |
| `gasLimit` | chain config |
| `number` | `0` (L2 genesis block number) |
| `baseFee` | 1 gwei |
| `withdrawalsRoot` | `L2ToL1MessagePasser` storage root, required to compute the output root |
| other | standard genesis values per hardfork |

Isthmus MUST be active at genesis. The [output root](./overview.md#output-root) reads its
`messagePasserStorageRoot` from the header's withdrawals root, and a pre-Isthmus header has none. The pipeline fails
rather than computing an output root from an incomplete header.

## depsets.json

Generation is **unchanged from the current pipeline**: a single-chain dependency set for standalone chains, and a
multi-chain depset for shared-dependency-set deployments.

`prepare` records the dependency set in the state under `interopDepSet`.

A super root deployment adds one constraint. The [super root](./overview.md#super-root) commits to a timestamp, so
every member of the dependency set MUST share the same L2 genesis timestamp. `prepare` MUST fail when members
disagree, which in practice means a per-chain `l1StartBlockHash` override that moves one chain's anchor.

`prestate` and `continue` MUST both re-validate that the intent's chain set still matches the dependency set recorded
by `prepare`.

## Failure modes

Summarized from `fma.md`. See the design doc for full mitigation and recovery detail. Each row maps to one of the
[invariants](#invariants) above.

| ID | Failure | Risk | Key mitigation |
| --- | --- | --- | --- |
| FM1 | L1 anchor reorg after selection | Low likelihood / high impact | Pre-broadcast anchor revalidation aborts the send, abort and restart |
| FM2 | Predicted ≠ deployed L1 addresses | Low / high | Same `from` and salt mixer for dry-run and broadcast, plus preflight and post-deploy validation |
| FM3 | Compromised L1 RPC | Low / high | Trusted or self-hosted RPC, preflight re-simulation, post-deploy validation |
| FM4 | Wrong prestate hash | Low / high | Source override from reproducible build, reproduce and verify before `continue` |
| FM5 | Genesis timestamp overrun | Low / low | Set `X` conservatively, `prepare` refuses an elapsed window, chain fills the gap with empty blocks |
| FM6 | Stale prestate after re-running `prepare` | Low / high | Every `prepare` run invalidates the prestate, forcing a rebuild |
| FM7 | Wrong `startingAnchorRoot` | Low / high | Recompute the anchor from committed genesis before `continue`, post-deploy anchor check |

## Developer experience

- Permissionless deployments require a prestate, built externally and committed through
  `--dispute-absolute-prestate` or a `faultGameAbsolutePrestate` intent override. This adds the prestate build time to
  the deployment.
- Permissioned-only deployments skip the prestate requirement.
- Re-running `prepare` discards the committed prestate even when the anchor is unchanged, so `prestate` has to be
  re-run before `continue`.
- `prepare` needs an already-deployed OPCM pinned in the intent. It does not bootstrap one.
