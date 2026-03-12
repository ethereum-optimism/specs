# ZK Fault Proof VM

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [ZK Program](#zk-program)
  - [Inputs](#inputs)
  - [Output](#output)
- [Absolute Prestate](#absolute-prestate)
- [Reference Implementation](#reference-implementation)
  - [SP1 (PLONK)](#sp1-plonk)
- [Proof Generation](#proof-generation)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

A ZK fault proof VM is a succinct proof system that verifies an L2 state transition through a single
cryptographic proof rather than an interactive bisection game. It consists of two components:

- ZK Program: an off-chain circuit that re-executes the L2 derivation and state transition and
  produces a succinct proof of correctness.
- On-chain Verifier: a smart contract (see [`IZKVerifier`](stage-one/zk/zk-interface.md)) that
  checks the proof and the committed public values in a single call.

This is the ZK analogue of the [Cannon Fault Proof VM](cannon-fault-proof-vm.md). While Cannon
bisects an execution trace down to a single MIPS instruction and proves it on L1, the ZK VM proves
the entire block range — from a starting output root to a claimed output root — in one shot.

Unlike interactive fault proofs, the ZK VM requires no multi-round on-chain interaction. A single
`prove()` call to the dispute game is sufficient to cryptographically establish correctness,
provided the verifier is sound.

## ZK Program

The ZK program is the circuit executed off-chain to generate a proof. It takes a set of
[public values](#inputs) as inputs and verifies that applying L2 derivation and executing the
resulting transactions against the starting state yields the claimed output root at the specified
L2 block number, given the observed L1 data up to `l1Head`.

The program is the ZK equivalent of the [Fault Proof Program](index.md#fault-proof-program): it
runs the same L2 derivation logic (`op-node` + `op-geth`) but inside a zkVM, producing a proof
instead of an interactive trace.

### Inputs

The following public values are committed to by the ZK proof. They are constructed on-chain from
game state and passed to the verifier:

| Field                | Type      | Description                                                                                      |
| -------------------- | --------- | ------------------------------------------------------------------------------------------------ |
| `l1Head`             | `bytes32` | L1 block hash at which the L1 state was sampled. Authenticates all observed L1 data.            |
| `startingOutputRoot` | `bytes32` | Output root of the parent game (or anchor state if `parentIndex == type(uint32).max`).           |
| `rootClaim`          | `bytes32` | The output root being asserted by this game.                                                     |
| `l2SequenceNumber`   | `uint256` | L2 block number corresponding to `rootClaim`.                                                    |
| `l2ChainId`          | `uint256` | L2 chain identifier. Replaces `rollupConfigHash` to avoid JSON serialization fragility.          |

`l2ChainId` scopes the proof to a specific chain. Config changes that affect execution semantics
(e.g. a hard fork) are absorbed into a new `absolutePrestate`, not a new `l2ChainId`.

### Output

The program produces a proof that commits to the [public values](#inputs). A proof that passes
on-chain verification is the sole signal of correctness: it means the L2 derivation from
`startingOutputRoot` under the given `l1Head` yields exactly `rootClaim` at `l2SequenceNumber`
on chain `l2ChainId`.

## Absolute Prestate

The `absolutePrestate` is a `bytes32` value that uniquely identifies the ZK program version
being proven. Two different programs MUST NOT share the same `absolutePrestate`.

It serves as the program identity in [`IZKVerifier.verify`](stage-one/zk/zk-interface.md) and is
injected into each game instance via the CWIA game args.

For SP1 deployments, `absolutePrestate` corresponds to the program's verification key
(`programVKey`), which is derived deterministically from the circuit binary and structure.

Program updates (e.g. a bug fix or a new hard fork) MUST produce a new `absolutePrestate`.
OPCM manages `absolutePrestate` per chain; updates require governance.

## Reference Implementation

### SP1 (PLONK)

The initial reference implementation uses [SP1](https://github.com/succinctlabs/sp1) by Succinct
with the PLONK backend.

- The ZK program is compiled to run inside the SP1 zkVM.
- `absolutePrestate` = the SP1 program verification key (`programVKey`).
- The on-chain verifier is Succinct's PLONK verifier, wrapped behind the `IZKVerifier` interface.

## Proof Generation

Proofs are generated off-chain by a prover that:

1. Fetches the required L1 and L2 data up to `l1Head`.
2. Executes the ZK program inside the zkVM with the public values as inputs.
3. Produces a proof blob (`proofBytes`).
4. Submits the proof on-chain via `ZKDisputeGame.prove(proofBytes)`.

Proof generation is permissionless: any party may generate and submit a proof. In practice the
proposer or a third-party proving service will act as prover.
