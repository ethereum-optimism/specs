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
- [Invariants](#invariants)
  - [iZKVM-001: Private Inputs Must Be Anchored to Public Values](#izkvm-001-private-inputs-must-be-anchored-to-public-values)
    - [Impact](#impact)
  - [iZKVM-002: Super Root Preimage Must Commit to All Chain Outputs](#izkvm-002-super-root-preimage-must-commit-to-all-chain-outputs)
    - [Impact](#impact-1)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The ZK Fault Proof VM is a succinct proof system that verifies a super root state
transition across all chains in the interop set through a single cryptographic proof. It consists
of two components:

- ZK Program: an off-chain circuit that re-executes the derivation and state transitions for all
  chains in the interop set and produces a succinct proof of correctness.
- On-chain Verifier: a smart contract (see [`IZKVerifier`](stage-one/zk/zk-interface.md))
  that checks the proof and the committed public values in a single call.

This is the ZK analogue of `SuperFaultDisputeGame`. Where the fault proof bisects an execution
trace down to a single instruction, the ZK VM proves the entire block range across all
chains — from one super root to the next — in a single on-chain call.

In a standalone deployment (single chain), the interop set contains exactly one chain. The program
is identical; the `SuperRootProof` preimage carries one entry. No separate standalone mode exists.

## ZK Program

The ZK program is the circuit executed off-chain to generate a proof. It takes a set of
[public values](#inputs) as inputs and verifies that executing the derivation and state transitions
for every chain in the interop set, starting from `startingProposal.root` and using L1 data up to
`l1Head`, produces the super root `rootClaim` at timestamp `l2SequenceNumber`.

### Inputs

The following public values are committed to by the ZK proof. They are constructed on-chain from
game state and passed to the verifier:

| Field | Type | Description |
| --- | --- | --- |
| `l1Head` | `bytes32` | L1 block hash at which the L1 state was sampled. Authenticates all observed L1 data. |
| `startingProposal.root` | `bytes32` | Super root hash of the parent game's claim, or the anchor state if `parentIndex == type(uint32).max`. Starting point for all chain state transitions. |
| `rootClaim` | `bytes32` | The super root hash being asserted by this game. It commits to the output roots of all chains in the interop set at `l2SequenceNumber`. |
| `l2SequenceNumber` | `uint256` | Super root timestamp corresponding to `rootClaim`. Constrained to `uint64` range. |
| `proverAddress` | `address` | Address of the proof submitter (`msg.sender` in `prove()`). Binds the proof to a specific submission. |

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

For SP1 deployments, `absolutePrestate` corresponds to the program's verification key
(`programVKey`), derived deterministically from the circuit binary and structure.

Program updates (e.g. a bug fix, a new hard fork, or a change to the interop set definition)
MUST produce a new `absolutePrestate`. OPCM manages `absolutePrestate` per deployment; updates
require governance.

## Reference Implementation

### SP1 (PLONK)

The initial reference implementation uses [SP1](https://github.com/succinctlabs/sp1) by Succinct
with the PLONK backend.

- The ZK program is compiled to run inside the SP1 zkVM.
- `absolutePrestate` = the SP1 program verification key (`programVKey`).
- The on-chain verifier is Succinct's PLONK verifier, wrapped behind the `IZKVerifier` interface.

## Proof Generation

Proofs are generated off-chain by a prover that:

1. Fetches the required L1 and L2 data up to `l1Head` for all chains in the interop set.
2. Decodes the `SuperRootProof` preimage from the game's `extraData` to identify the chain set
   and their expected output roots.
3. Executes the ZK program inside the zkVM with the public values as inputs and provides the
   required L1 and L2 data as private values to the ZK program.
4. Produces a proof blob (`proofBytes`).
5. Submits the proof on-chain via `ZKDisputeGame.prove(proofBytes)`.

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
