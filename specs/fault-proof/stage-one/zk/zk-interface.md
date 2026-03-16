# IZKVerifier Interface

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Interface](#interface)
- [Usage in `prove()`](#usage-in-prove)
- [Verifier Upgrade Path](#verifier-upgrade-path)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

`IZKVerifier` is the on-chain interface that decouples `ZKDisputeGame` from any specific proving
system. The game always casts the configured verifier address to `IZKVerifier` and calls `verify()`
through the interface, rather than depending on a concrete verifier type. This allows the verifier
to be swapped without redeploying the game implementation.

The concrete deployment for the initial release uses Succinct's PLONK verifier for
[SP1](../../zk-fault-proof-vm.md#sp1-plonk).

## Interface

```solidity
interface IZKVerifier is ISemver {
    function verifierType() external pure returns (string memory);

    function verify(
        bytes32 programId,
        bytes calldata publicValues,
        bytes calldata proof
    ) external view;
}
```

`verifierType()` returns a string identifying the proving system (e.g., `"SP1_PLONK"`). Callers
can use it to check which backend is deployed without inspecting the bytecode.

| Parameter      | Description                                                                          |
| -------------- | ------------------------------------------------------------------------------------ |
| `programId`    | Corresponds to `absolutePrestate()` in the dispute game — identifies the ZK program. |
| `publicValues` | ABI-encoded public inputs committed to by the proof (see [Usage in `prove()`](#usage-in-prove)). |
| `proof`        | The raw proof blob submitted by the prover.                                          |

The verifier MUST revert on an invalid proof. A call that returns without reverting is treated as
proof acceptance; the game will transition `status` to `UnchallengedAndValidProofProvided` or
`ChallengedAndValidProofProvided` and mark itself as game over.

## Usage in `prove()`

`ZKDisputeGame.prove()` constructs `publicValues` from on-chain game state and forwards them to
the verifier:

```solidity
function prove(bytes calldata _proofBytes) external {
    bytes memory publicValues = abi.encode(
        l1Head(),
        startingOutputRoot(),
        rootClaim(),
        l2SequenceNumber(),
        l2ChainId()
    );

    IZKVerifier(verifier()).verify(
        absolutePrestate(),
        publicValues,
        _proofBytes
    );

    // record proof submission and set game over
}
```

All public values come from immutable on-chain game state, so no caller-supplied data affects what
the verifier checks. `l1Head` is captured as `blockhash(block.number - 1)` by
`DisputeGameFactory.create()` and packed into the clone's CWIA data.

See [ZK Program Inputs](../../zk-fault-proof-vm.md#inputs) for the meaning of each public value field.

## Verifier Upgrade Path

The `verifier` and `absolutePrestate` fields live in the CWIA game args (see
[Game Args Layout](zk-dispute-game.md#game-args-layout)), so they can be updated per chain
without redeploying the `ZKDisputeGame` implementation.

Upgrade process:

1. Deploy a new verifier contract.
2. If the ZK program changed, compute a new `absolutePrestate`.
3. OPCM updates the game args with the new `verifier` and/or `absolutePrestate`.
4. In-progress games play out under the old configuration.
5. New games use the updated configuration.
