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
  - [Prestate / Prestate Hash](#prestate--prestate-hash)
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
  plus updates to `DeployOPChain.s.sol` and a minimal change to `OPContractsManagerV2` so a permissionless game type
  can be enabled at initial deployment.
- [op-deployer Orchestration](./op-deployer.md): the pipeline that consumes the predicted addresses. Three new commands
  (`prepare`, `prestate`, `continue`) build the L2 genesis and output root, commit the prestate, and submit the
  deployment.

## Problem Statement

Deploying a new chain today has a cyclic dependency:

1. `OPCM.deploy()` must run first to produce the L1 contract addresses.
2. The L2 genesis requires those L1 addresses as inputs.
3. The L2 genesis output root feeds back into `OPCM.deploy()` as the `startingAnchorRoot`.

The current workaround deploys with a placeholder `startingAnchorRoot` and defers permissionless proofs until a real
dispute resolves the anchor (~7 days). PCD breaks the cycle by predicting the L1 addresses without writing any state.
The prestate and the output root are then computed before the real deployment transaction is broadcast.

## Goals

- Permissionless dispute games valid from L2 block 0 on mainnets, testnets, and devnets.
- Minimal on-chain change, limited to relaxing OPCM's initial-deployment game-type validation. Existing permissioned
  deployments remain valid (see [iPCD-002](./contracts.md#ipcd-002-permissioned-deployments-remain-valid)).
- Deterministic, reproducible artifacts (predicted addresses, genesis, output root, prestate) given the same inputs.

## Non-goals

- Deploying a chain directly into a shared (multi-chain) super dispute game is out of scope for this milestone. A
  chain can still join a multi-chain dependency set while keeping its own per-chain dispute game.

## Definitions

### Output Root

A 32-byte commitment to L2 state:
`keccak256(version || stateRoot || messagePasserStorageRoot || blockHash)`, where `version` is 32 zero bytes. The
genesis output root is seeded into the `AnchorStateRegistry` at `l2SequenceNumber = 0`.

### Prestate / Prestate Hash

The Cannon hash of the initial MIPS machine state, produced by compiling the Kona fault-proof program with the
embedded chain config. The hash is deterministic for a given chain config.

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
sender and config are used**.

## References

- [Design doc (`pcd-design.md`)](https://github.com/ethereum-optimism/design-docs/pull/385)
- [Failure modes analysis (`fma.md`)](https://github.com/ethereum-optimism/design-docs/pull/385)
- [OP Contracts Manager](../op-contracts-manager.md)
