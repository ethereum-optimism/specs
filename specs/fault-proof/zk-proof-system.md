# ZK Proof System

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
- [Invariants](#invariants)
  - [iZKVM-001: Private Inputs Must Be Anchored to Public Values](#izkvm-001-private-inputs-must-be-anchored-to-public-values)
    - [Impact](#impact)
  - [iZKVM-002: Super Root Preimage Must Commit to All Chain Outputs](#izkvm-002-super-root-preimage-must-commit-to-all-chain-outputs)
    - [Impact](#impact-1)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The ZK proof system is a succinct proof system that verifies a super root state
transition across all chains in the interop set through a single cryptographic proof. It consists
of two components:

- ZK Program: an off-chain circuit that re-executes the derivation and state transitions for all
  chains in the interop set and produces a succinct proof of correctness.
- On-chain Verifier: a smart contract (see [`IZKVerifier`](stage-one/zk/zk-interface.md))
  that checks the proof and the committed public values in a single call.

This is the ZK analogue of `SuperFaultDisputeGame`. The program proves the
[Super Root State Transition](stage-one/super-fault-dispute-game.md#super-root-state-transition) for every
timestamp from `startingTimestamp + 1` to `l2SequenceNumber`: local-safe derivation for each chain, followed by
consolidation. This is the same statement that the Super Fault Dispute Game bisects over, proven in a single
on-chain call.

In a standalone deployment (single chain), the interop set contains exactly one chain. The program
is identical; the `SuperRootProof` preimage carries one entry. No separate standalone mode exists.

## ZK Program

The ZK program is the circuit executed off-chain to generate a proof. It takes a set of
[public values](#inputs) as inputs and verifies that executing the derivation and state transitions
for every chain in the interop set, starting from `startingProposal.root` and using L1 data up to
`l1Head`, produces the super root `rootClaim` at timestamp `l2SequenceNumber`.

`rootClaim` is the consolidated (cross-safe) super root, i.e. the verified super root returned by
[`superroot_atTimestamp`](../interop/superroot.md#superroot_attimestamp). L1 data is bound to the game only
through the range proofs, each of which MUST commit to the game's `l1Head`.

### Inputs

The following public values are committed to by the ZK proof. They are constructed on-chain from
game state, ABI-encoded in table order (5 × 32 bytes), and passed to the verifier:

| Field | Type | Description |
| --- | --- | --- |
| `l1Head` | `bytes32` | L1 block hash at which the L1 state was sampled. Authenticates all observed L1 data. |
| `startingProposal.root` | `bytes32` | Super root hash of the parent game's claim, or the anchor state if `parentIndex == type(uint32).max`. Starting point for all chain state transitions. |
| `rootClaim` | `bytes32` | The super root hash being asserted by this game. It commits to the output roots of all chains in the interop set at `l2SequenceNumber`. |
| `l2SequenceNumber` | `uint256` | Super root timestamp corresponding to `rootClaim`. Constrained to `uint64` range. |
| `prover` | `address` | Address of the proof submitter (`msg.sender` in `prove()`). Binds the proof to a specific submission. |

`l2ChainId` is intentionally absent. Chain scoping is provided by the `SuperRootProof` preimage
committed to by `rootClaim` and `startingProposal.root`. In a standalone (single-chain) deployment,
the preimage contains exactly one chain entry; no separate field is needed.

### Output

The program produces a proof that commits to the [public values](#inputs). A proof that passes
on-chain verification means: executing the derivation logic for every chain in the interop set
from the state committed to in `startingProposal.root`, under the L1 data observed at `l1Head`,
yields exactly the super root `rootClaim` at timestamp `l2SequenceNumber`.

## Absolute Prestate

The `absolutePrestate` is a `bytes32` value that uniquely identifies the ZK program version being
proven. Two different programs MUST NOT share the same `absolutePrestate`.

It serves as the program identity in
[`IZKVerifier.verify`](stage-one/zk/zk-interface.md) and is injected into each game
instance via the CWIA game args.

For SP1 deployments, `absolutePrestate` is the verification key of the **aggregation program** (see
[SP1 (PLONK)](#sp1-plonk)). The aggregation program pins the range program's verification key, and the range
program pins the log-commitment program's verification key, so `absolutePrestate` commits transitively to all
three programs. It also commits to the rollup configs, L1 config and dependency set compiled into the programs.
The chain set in a proof MUST equal the compiled dependency set. No rollup config hash appears in the public
values.

Program updates (e.g. a bug fix, a new hard fork, a chain config change or a dependency set change)
MUST produce a new `absolutePrestate`. OPCM manages `absolutePrestate` per deployment; updates
require governance.

## Reference Implementation

### SP1 (PLONK)

The initial reference implementation uses [SP1](https://github.com/succinctlabs/sp1) by Succinct
with the PLONK backend.

The ZK program consists of three SP1 programs:

| Program | Role |
| --- | --- |
| `log-commitment` | Commits to the logs under each input receipts root, so that initiating messages can be checked without loading the block's receipts. |
| `super-range` | **Range mode:** derives the local-safe blocks of one or more chains for a span of timestamps against `l1Head`. **Consolidation mode:** validates cross-chain messages for a span of timestamps, using verified log-commitment proofs, and computes the resulting super roots. |
| `super-aggregation` | Verifies all range and consolidation proofs against the pinned `super-range` verification key, checks that every `(timestamp, chain)` of the claim is covered exactly once, checks that the super roots chain from `startingProposal.root` to `rootClaim`, and commits the five [public values](#inputs). |

The `log-commitment` and `super-range` proofs are SP1 compressed proofs. Only the `super-aggregation` proof is a
PLONK proof, and it is the proof submitted on-chain. It is verified by the
[`SP1PlonkAdapter`](stage-one/zk/zk-interface.md#sp1plonkadapter).

## Proof Generation

Proofs are generated off-chain by a prover that:

1. Reads `l1Head`, `startingProposal.root` (`startingRootHash()`), `rootClaim`, `l2SequenceNumber`,
   `absolutePrestate` and `verifier` from the game.
2. Fetches the verified super root for every timestamp from the starting timestamp to `l2SequenceNumber` via
   [`superroot_atTimestamp`](../interop/superroot.md#superroot_attimestamp), from a source synced past `l1Head`.
   The super root at the starting timestamp MUST equal `startingProposal.root`, the super root at
   `l2SequenceNumber` MUST equal `rootClaim`, and `verified_required_l1` MUST be at or below `l1Head`. Otherwise
   the claim is unprovable.
3. Collects the L1 data (including blobs) and the L2 witness data for every chain.
4. Generates the range, consolidation and aggregation proofs.
5. Submits the aggregation proof via `ZKDisputeGame.prove(proofBytes)` from the address committed to as
   `prover`.

Proof generation is permissionless: any party may generate and submit a proof. In practice the
proposer or a third-party proving service will act as prover.

## Invariants

### iZKVM-001: Private Inputs Must Be Anchored to Public Values

The ZK program receives private inputs (block and transaction data for all chains) that are known
only to the prover and never seen by the on-chain verifier. The ZK program MUST verify that all
private inputs are directly derived from or cryptographically linked to the public values (e.g.
by hashing block data and comparing against `l1Head`, or verifying that blocks form a chain rooted
at `startingProposal.root`). The ZK program MUST NOT trust any private input without an explicit
check against a public value.

#### Impact

**Severity: Critical**

A violation means a malicious prover can supply manipulated private inputs that lead to a proof
that verifies on-chain but represents an invalid state transition, and enable finalization of a
fraudulent super root.

### iZKVM-002: Super Root Preimage Must Commit to All Chain Outputs

The ZK program MUST verify the output root of every chain listed in the `SuperRootProof` preimage
and MUST produce a `rootClaim` that is the hash of that complete preimage. Omitting any chain from
the proof or producing a partial preimage hash MUST cause the program to fail.

#### Impact

**Severity: Critical**

A violation would allow a proof to finalize a super root that does not faithfully represent all
chains in the interop set. Funds that do not exist on L2 could be withdrawn, or the state of a
chain could be suppressed from the commitment.
