# Predictive Chain Deployments

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Goals](#goals)
- [Non-goals](#non-goals)
- [Definitions](#definitions)
  - [Output Root](#output-root)
  - [Super Root](#super-root)
  - [Starting Anchor Root](#starting-anchor-root)
  - [Selected Prestate](#selected-prestate)
  - [Fallback Prestate](#fallback-prestate)
  - [Genesis Block](#genesis-block)
  - [L2 Allocs](#l2-allocs)
  - [Anchor Block](#anchor-block)
  - [Salt Mixer](#salt-mixer)
- [References](#references)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

Predictive Chain Deployments (PCD) eliminate the permissioned dispute game window (~7 days) that new OP Stack chains
must currently wait through before permissionless dispute games can be enabled. The window exists today because the
deployment tooling cannot seed the L1 dispute system with a real anchor at deployment time.

PCD removes the window by computing **every chain artifact off-chain before any transaction lands on L1**. This lets
`OPCM.deploy()` be submitted with the real `startingAnchorRoot` and `absolutePrestate` rather than placeholders.

PCD has two parts, each specified on its own page:

- [Contracts](./contracts.md): a Forge script that dry-runs `OPCM.deploy()` to **predict the L1 contract addresses**,
  plus updates to `DeployOPChain.s.sol` and to `OPContractsManagerV2` so a permissionless game type can be enabled at
  initial deployment.
- [op-deployer Orchestration](./op-deployer.md): the pipeline that consumes the predicted addresses. Three new commands
  (`prepare`, `prestate`, `continue`) build the L2 genesis and the starting anchor root, commit the prestate, and
  submit the deployment.

## Problem Statement

Deploying a new chain today has a cyclic dependency:

1. `OPCM.deploy()` must run first to produce the L1 contract addresses.
2. The L2 genesis requires those L1 addresses as inputs.
3. The L2 genesis output root feeds back into `OPCM.deploy()` as the `startingAnchorRoot`.

The current workaround deploys with a placeholder `startingAnchorRoot` and defers permissionless proofs until a real
dispute resolves the anchor (~7 days). PCD breaks the cycle by predicting the L1 addresses without writing any state.
The prestate and the starting anchor root are then computed before the real deployment transaction is broadcast.

## Goals

- Permissionless dispute games valid from L2 block 0 on mainnets, testnets, and devnets.
- Support both game families: per-chain output root games (`CANNON_KONA`) and super root games (`SUPER_CANNON_KONA`).
- Contain the on-chain change to OPCM's initial-deployment config validation. Permissioned deployments against an OPCM
  in the same mode remain valid (see [iPCD-002](./contracts.md#ipcd-002-permissioned-deployments-remain-valid)).
- Deterministic, reproducible artifacts (predicted addresses, genesis, anchor root, prestate) given the same inputs.

## Non-goals

- Permissionless deployment through `apply`. That command stays permissioned-only and keeps its placeholder anchor.
  Permissionless chains go through `prepare` / `prestate` / `continue`.
- Sharing one dispute game or one `AnchorStateRegistry` across chains. Every chain keeps its own registry and its own
  `DisputeGameFactory`, including in a super root deployment where all chains share a single anchor **value**.
- Enabling `ZK_DISPUTE_GAME` game type at initial deployment.

## Definitions

### Output Root

A 32-byte commitment to a single chain's L2 state:
`keccak256(version || stateRoot || messagePasserStorageRoot || blockHash)`, where `version` is 32 zero bytes.

The `messagePasserStorageRoot` is read from the genesis block header's withdrawals root, so computing a genesis output
root requires Isthmus to be active at genesis. A chain whose genesis predates Isthmus fails the pipeline.

### Super Root

A commitment to the L2 state of **every chain in a dependency set at one timestamp**, built from each member's
[output root](#output-root). Super root games (`SUPER_CANNON_KONA`, `SUPER_PERMISSIONED`) dispute super roots rather
than per-chain output roots.

A super root commits to a timestamp, so every chain in the dependency set must share the same L2 genesis timestamp.

### Starting Anchor Root

The `Proposal` seeded into a chain's `AnchorStateRegistry` at deployment, a root paired with an `l2SequenceNumber`.
What fills it depends on the game family:

| Game family | Root | `l2SequenceNumber` |
| --- | --- | --- |
| Output root (`CANNON_KONA`) | the chain's own genesis [output root](#output-root) | `0`, the L2 genesis block number |
| Super root (`SUPER_CANNON_KONA`) | one [super root](#super-root) shared by the dependency set | the super root's timestamp |
| Permissioned only | a placeholder | `0` |

Every chain keeps its own registry in all three cases. In a super root deployment the registries hold the same value.

### Selected Prestate

The absolute prestate of the game type a chain deploys as its respected game.

For a permissionless deployment the pipeline commits it: the Cannon hash of the initial MIPS machine state, produced
by compiling the Kona fault-proof program with the embedded chain config. The hash is deterministic for a given chain
config.

A permissioned-only deployment keeps the prestate the chain configuration already supplies. That value is required to
be non-zero in every case, including the super root permissioned game, which never reads it.

### Fallback Prestate

A `CANNON_KONA` deployment also enables `PERMISSIONED_CANNON` as a guardian fallback, and that game needs its own
prestate. op-deployer fills it with a reserved placeholder rather than a real prestate, because the fallback is not
meant to be played at deployment. The value is reserved and a [selected prestate](#selected-prestate) may not use it.

**Super root deployments have no fallback prestate.**

### Genesis Block

L2 block 0 (`parentHash = 0x00…00`). Header fields derive from the L2 allocs, the chain config, and the committed
genesis timestamp.

### L2 Allocs

The initial account/storage layout output by `L2Genesis.s.sol`, computed with the L1 addresses as inputs. Its Merkle
root becomes the genesis block header `stateRoot`.

### Anchor Block

The L1 block selected at the `safe` tag or deeper whose hash is baked into `rollup.json` and the prestate.

### Salt Mixer

The `saltMixer` string in [`FullConfig`](./contracts.md#fullconfig) that, together with `msg.sender`, derives the
CREATE2 salt for OPCM proxy deployments. The predicted addresses match the deployed addresses only when **the same
sender and salt mixer are used**.

## References

- [Design doc (`pcd-design.md`)](https://github.com/ethereum-optimism/design-docs/blob/main/ecosystem/op-deployer/predictive-chain-deployments/pcd-design.md)
- [Failure modes analysis (`fma.md`)](https://github.com/ethereum-optimism/design-docs/blob/main/ecosystem/op-deployer/predictive-chain-deployments/fma.md)
- [OP Contracts Manager](../op-contracts-manager.md)
