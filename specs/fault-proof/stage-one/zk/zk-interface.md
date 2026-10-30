# IZKVerifier Interface

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Interface](#interface)
- [SP1PlonkAdapter](#sp1plonkadapter)
- [Usage in `prove()`](#usage-in-prove)
- [Verifier Upgrade Path](#verifier-upgrade-path)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

`IZKVerifier` is the on-chain interface that decouples `ZKDisputeGame` from any specific
proving system. The game always casts the configured verifier address to `IZKVerifier` and calls
`verify()` through the interface, rather than depending on a concrete verifier type.

The verifier is the [`SP1PlonkAdapter`](#sp1plonkadapter) singleton deployed with each OPCM release. It wraps
Succinct's PLONK verifier for [SP1](../../zk-proof-system.md#sp1-plonk) (SP1 PLONK v6.1.0 on Ethereum mainnet
and Sepolia).

## Interface

```solidity
interface IZKVerifier is ISemver {
    function verifierType() external view returns (string memory);

    function verify(bytes32 _programId, bytes calldata _publicValues, bytes calldata _proof) external view;
}
```

`verifierType()` returns a string identifying the proving system. For the `SP1PlonkAdapter` it is `"SP1-PLONK-"`
followed by the wrapped verifier's `VERSION()` (e.g., `"SP1-PLONK-v6.1.0"`). Callers can use it to check which
backend is deployed without inspecting the bytecode.

| Parameter | Description |
| --- | --- |
| `programId` | Corresponds to `absolutePrestate()` in the dispute game — identifies the ZK program version. |
| `publicValues` | ABI-encoded public inputs committed to by the proof (see [Usage in `prove()`](#usage-in-prove)). |
| `proof` | The raw proof blob submitted by the prover. |

The verifier MUST revert on an invalid proof. A call that returns without reverting is treated as
proof acceptance; the game will set `claimData.prover = msg.sender` and transition
`claimData.status` to `UnchallengedAndValidProofProvided` or `ChallengedAndValidProofProvided`.

## SP1PlonkAdapter

`SP1PlonkAdapter` (version `1.0.0`) implements `IZKVerifier` on top of an SP1 PLONK verifier. It is deployed as a
non-proxied singleton once per OPCM release.

- The constructor takes the wrapped `ISP1Verifier` and MUST revert with `SP1PlonkAdapter_InvalidVerifier()` if the
  given address has no code.
- `sp1Verifier()` returns the wrapped `ISP1Verifier`.
- `verify(programId, publicValues, proof)` forwards its arguments unchanged to
  `ISP1Verifier.verifyProof(programId, publicValues, proof)` and reverts if that call reverts.

The wrapped verifier's `VERIFIER_HASH()` identifies the PLONK circuit it accepts proofs for. It MUST match the
circuit used by the prover's SP1 SDK, otherwise every proof fails verification. OPCM release verification
(`VerifyOPCM`) checks both the wrapped verifier address and its `VERIFIER_HASH()`.

## Usage in `prove()`

`ZKDisputeGame.prove()` constructs `publicValues` from on-chain game state and forwards them
to the verifier:

```solidity
function prove(bytes calldata _proofBytes) external returns (ProposalStatus) {
    bytes memory publicValues = abi.encode(
        l1Head(),
        startingProposal.root,
        rootClaim(),
        l2SequenceNumber(),
        msg.sender
    );

    IZKVerifier(verifier()).verify(
        absolutePrestate(),
        publicValues,
        _proofBytes
    );

    // record proof submission and transition claimData.status
}
```

| Field | Source | Description |
| --- | --- | --- |
| `l1Head` | CWIA (immutable) | L1 block hash captured at game creation. Authenticates all observed L1 data. |
| `startingProposal.root` | Storage (set in `initialize`) | Super root hash of the parent game's claim, or the anchor state if `parentIndex == type(uint32).max`. |
| `rootClaim` | CWIA (immutable) | Super root hash being asserted by this game. |
| `l2SequenceNumber` | CWIA (immutable) | Super root timestamp corresponding to `rootClaim`. |
| `msg.sender` | Transaction | Address of the prover. Binds the proof to the submitter, preventing front-running: a proof is generated for a specific address and cannot be re-submitted by a different address without regenerating the entire proof. |

All public values come from immutable CWIA data or storage set during `initialize()`, so no
caller-supplied data beyond `_proofBytes` affects what the verifier checks. `l1Head` is captured
as `blockhash(block.number - 1)` by `DisputeGameFactory.create()` and packed into the clone's
CWIA data.

Chain scoping is provided by the `SuperRootProof` preimage committed to by `rootClaim`; the
`(chainId, outputRoot)` pairs in that preimage cover every chain in the interop set (or a single
entry in standalone deployments), so no separate `l2ChainId` field is needed in the public values.
See [ZK Program Inputs](../../zk-proof-system.md#inputs) for the full public values
specification.

## Verifier Upgrade Path

The `verifier` and `absolutePrestate` fields live in the CWIA game args (see
[CWIA Layout](zk-dispute-game.md#cwia-layout)). They are not configured the same way:

- `verifier` is not chain-configurable. OPCM always fills it with the OPCM release's `SP1PlonkAdapter`
  (see [ZKDisputeGameConfig](zk-dispute-game.md#zkdisputegameconfig)). Rotating the verifier requires a new OPCM
  release that deploys a new adapter, followed by an `upgrade()` for each chain.
- `absolutePrestate` is chain-configurable through `ZKDisputeGameConfig`. If the ZK program changes, the chain
  computes a new `absolutePrestate` and applies it with an OPCM `upgrade()`.

Existing game clones keep the `verifier` and `absolutePrestate` stored in their own CWIA data, so in-progress
games play out under the old configuration. New games use the updated game args.
