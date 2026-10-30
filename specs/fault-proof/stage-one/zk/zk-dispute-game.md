# ZK Dispute Game

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
  - [ZKDisputeGame](#zkdisputegame)
  - [MCP Clone](#mcp-clone)
  - [Game Args (CWIA)](#game-args-cwia)
  - [Super Root](#super-root)
  - [SuperRootProof](#superrootproof)
  - [Chain Set](#chain-set)
  - [L2 Sequence Number](#l2-sequence-number)
  - [Parent Game](#parent-game)
  - [Challenge Deadline](#challenge-deadline)
  - [Prove Deadline](#prove-deadline)
  - [Absolute Prestate](#absolute-prestate)
  - [Game Over](#game-over)
- [Contracts Involved](#contracts-involved)
- [Actors](#actors)
- [CWIA Layout](#cwia-layout)
  - [Fixed Prefix](#fixed-prefix)
  - [Variable extraData](#variable-extradata)
  - [Dynamic Game Args](#dynamic-game-args)
- [rootClaim Semantics](#rootclaim-semantics)
- [rootClaimByChainId](#rootclaimbychainid)
- [initialize Invariants](#initialize-invariants)
- [OPCM Integration](#opcm-integration)
  - [ZKDisputeGameConfig](#zkdisputegameconfig)
  - [Configuration Validation](#configuration-validation)
  - [Standard Configuration](#standard-configuration)
- [Interface](#interface)
  - [Functions](#functions)
  - [Events](#events)
  - [Errors](#errors)
- [Assumptions](#assumptions)
  - [aZKG-001: ZK Verifier Soundness](#azkg-001-zk-verifier-soundness)
    - [Mitigations](#mitigations)
  - [aZKG-002: Absolute Prestate Uniquely Identifies the ZK Program](#azkg-002-absolute-prestate-uniquely-identifies-the-zk-program)
    - [Mitigations](#mitigations-1)
  - [aZKG-003: Parent Chaining Preserves Correctness](#azkg-003-parent-chaining-preserves-correctness)
    - [Mitigations](#mitigations-2)
  - [aZKG-004: Bonds Are Economically Rational](#azkg-004-bonds-are-economically-rational)
    - [Mitigations](#mitigations-3)
  - [aZKG-005: Guardian Acts Honestly and Timely](#azkg-005-guardian-acts-honestly-and-timely)
    - [Mitigations](#mitigations-4)
  - [aZKG-006: Anchor State Advances Slowly Relative to Proposal Frequency](#azkg-006-anchor-state-advances-slowly-relative-to-proposal-frequency)
    - [Mitigations](#mitigations-5)
  - [aZKG-007: Proof Generation Is Feasible Within the Prove Window](#azkg-007-proof-generation-is-feasible-within-the-prove-window)
    - [Mitigations](#mitigations-6)
  - [aZKG-008: Super Root Preimage Faithfully Represents the Chain Set](#azkg-008-super-root-preimage-faithfully-represents-the-chain-set)
    - [Mitigations](#mitigations-7)
  - [aZKG-009: Chain Set Is Stable During the Prove Window](#azkg-009-chain-set-is-stable-during-the-prove-window)
    - [Mitigations](#mitigations-8)
  - [aZKG-010: Valid Claims Are Provable](#azkg-010-valid-claims-are-provable)
    - [Mitigations](#mitigations-9)
- [Invariants](#invariants)
  - [iZKG-001: A Valid Proof Always Wins](#izkg-001-a-valid-proof-always-wins)
    - [Impact](#impact)
  - [iZKG-002: A Game Without a Valid Proof and With a Challenger Resolves as CHALLENGER_WINS](#izkg-002-a-game-without-a-valid-proof-and-with-a-challenger-resolves-as-challenger_wins)
    - [Impact](#impact-1)
  - [iZKG-003: Bond Safety via DelayedWETH](#izkg-003-bond-safety-via-delayedweth)
    - [Impact](#impact-2)
  - [iZKG-004: Permissionless Participation](#izkg-004-permissionless-participation)
    - [Impact](#impact-3)
  - [iZKG-005: Parent Invalidity Propagates to Children](#izkg-005-parent-invalidity-propagates-to-children)
    - [Impact](#impact-4)
  - [iZKG-006: closeGame Reverts When Paused](#izkg-006-closegame-reverts-when-paused)
    - [Impact](#impact-5)
  - [iZKG-007: Only Finalized Games Can Close](#izkg-007-only-finalized-games-can-close)
    - [Impact](#impact-6)
  - [iZKG-008: Blacklisted and Retired Games Enter REFUND Mode](#izkg-008-blacklisted-and-retired-games-enter-refund-mode)
    - [Impact](#impact-7)
  - [iZKG-009: Child Resolution Requires Resolved Parent](#izkg-009-child-resolution-requires-resolved-parent)
    - [Impact](#impact-8)
  - [iZKG-010: At Most One Challenge Per Game](#izkg-010-at-most-one-challenge-per-game)
    - [Impact](#impact-9)
  - [iZKG-011: Bond Conservation](#izkg-011-bond-conservation)
    - [Impact](#impact-10)
  - [iZKG-012: Monotonic State Progression](#izkg-012-monotonic-state-progression)
    - [Impact](#impact-11)
  - [iZKG-013: rootClaimByChainId Consistency](#izkg-013-rootclaimbychainid-consistency)
    - [Impact](#impact-12)
  - [iZKG-014: rootClaim Matches SuperRootProof Preimage](#izkg-014-rootclaim-matches-superrootproof-preimage)
    - [Impact](#impact-13)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The `ZKDisputeGame` is a dispute game that resolves disputes in a single round using ZK
(zero-knowledge) proofs, registered as game type `ZK_DISPUTE_GAME` (`GameType.wrap(10)`). It integrates
into the OP Stack dispute infrastructure — `DisputeGameFactory`, `AnchorStateRegistry`, `DelayedWETH`, and
`OPContractsManager`.

Unlike the classic output-root model, the game commits to a **super root**: a hash of the
consistent state of all chains in the interop set at a given timestamp. This design works
identically in both deployment contexts:

- Standalone (single chain): the `SuperRootProof` preimage contains exactly one chain entry.
- Interop set (multiple chains): the preimage contains one entry per chain. No mode flag or
  branching logic exists in the contract; the chain set size is the only difference.

A proposer posts a super root with a bond. Anyone can challenge it by depositing a challenger
bond. If no challenge is submitted before the challenge window expires, the proposer wins by
default. If a challenge is submitted, either a prover submits a valid ZK proof to defend the
claim and the proposer wins, or the proving window expires without a valid proof and the challenger
wins. Resolution is permissionless once the game is over and the parent game is resolved.

The proving system is accessed through the generic [`IZKVerifier`](zk-interface.md)
interface. The first supported backend is SP1 (PLONK) by Succinct. See
[ZK Proof System](../../zk-proof-system.md) for details on the off-chain proving
component.

For the full game lifecycle and bond accounting see
[Game Mechanics](game-mechanics.md).

## Definitions

### ZKDisputeGame

The smart contract implementing the single-round super-root ZK dispute protocol. Each game
instance is a lightweight [MCP clone](#mcp-clone) of a shared implementation contract, deployed
by `DisputeGameFactory`.

### MCP Clone

A minimal proxy clone (ERC-1167) created by `DisputeGameFactory` that shares the
`ZKDisputeGame` implementation bytecode but has its own per-chain configuration appended as
immutable constructor arguments via the Clones-with-Immutable-Args (CWIA) pattern.

### Game Args (CWIA)

The per-chain configuration bytes appended to each MCP clone by `DisputeGameFactory`. A single
implementation contract serves every deployment. See [CWIA Layout](#cwia-layout) for the full
field breakdown.

### Super Root

A `bytes32` hash that commits to the output roots of all chains in the interop set at a given
timestamp. Computed as `hashSuperRootProof(superRootProof)`. The `rootClaim` of every
`ZKDisputeGame` is a super root.

### SuperRootProof

The preimage of a super root. It carries the timestamp and the list of per-chain output roots that the super root
commits to. Its `keccak256` hash MUST equal `rootClaim`. It uses the packed encoding of
`Encoding.encodeSuperRootProof`:

| Field | Size | Description |
| --- | --- | --- |
| `version` | `bytes1` | Encoding version. MUST be `0x01`. |
| `timestamp` | `bytes8` | Super root timestamp (the game's `l2SequenceNumber`). |
| `chainId` | `bytes32` | Chain ID of an output root. Repeated `n` times together with `outputRoot`, `n ≥ 1`. |
| `outputRoot` | `bytes32` | Output root of the chain identified by the preceding `chainId`. |

The `(chainId, outputRoot)` pairs MUST be sorted in strictly ascending order by `chainId` for the claim to be
provable. The contract does **not** check the ordering. An unsorted preimage whose hash equals `rootClaim` is
accepted by `initialize()`, but no proof can be produced for it, because the ZK program rejects chain IDs that are
not strictly increasing. An honest challenger therefore challenges such a game and it resolves `CHALLENGER_WINS`.
Every chain ID MUST also fit in a `uint64` for the claim to be provable, because the ZK program rejects larger
chain IDs.

### Chain Set

The set of chains whose output roots are committed to by a super root. Defined by the
`SuperRootProof` preimage in `extraData`. In a standalone deployment the chain set contains
exactly one chain.

### L2 Sequence Number

The super root timestamp asserted by a game's `rootClaim`. Used to validate parent–child ordering.
Unlike the classic output-root model where this field holds an L2 block number, here it is a
timestamp, following `SuperFaultDisputeGame` convention. It is stored as an 8-byte field of the preimage, so it
always fits in a `uint64`.

### Parent Game

A previously created `ZKDisputeGame` whose proven super root serves as the starting state
for a new game's ZK proof. A game with `parentIndex == type(uint32).max` starts from the anchor
state directly.

### Challenge Deadline

The timestamp after which a game can no longer be challenged. Computed as
`createdAt + maxChallengeDuration`. A challenge at exactly the deadline is still accepted.

### Prove Deadline

The timestamp after which a challenged game can no longer receive a proof submission. Set to
`block.timestamp + maxProveDuration` when `challenge()` is called, resetting the prior challenge
deadline.

### Absolute Prestate

A `bytes32` value that uniquely identifies the ZK program version being proven. It is the program
identity passed to `IZKVerifier.verify()` and is injected into each game instance via the CWIA
game args. See [Absolute Prestate](../../zk-proof-system.md#absolute-prestate) for
details.

### Game Over

The condition under which a game can be resolved. `gameOver()` returns `true` when:

- `claimData.prover != address(0)` (a valid proof has been submitted), or
- `claimData.deadline < block.timestamp` (the current deadline has expired).

## Contracts Involved

| Contract | Role |
| --- | --- |
| **ZKDisputeGame** (clones) | Per-proposal game instance. Runs the challenge → prove → resolve lifecycle and tracks bond accounting. |
| **ZKDisputeGame** (implementation) | Shared bytecode base for MCP clones. Deployed and upgraded by OPCM. |
| **DisputeGameFactory** | Creates MCP clones via `create(...)`. Appends per-chain `gameArgs` (CWIA). |
| **AnchorStateRegistry** | Source of truth for finalization, anchor state, respected game type, and blacklisting. Enforces pause checks. |
| **DelayedWETH** | Bond custody with a deposit → unlock → withdraw lifecycle. Provides a time window for the Guardian to freeze funds post-resolution. |
| **IZKVerifier** | Generic verifier interface. The verifier is the OPCM release's [`SP1PlonkAdapter`](zk-interface.md#sp1plonkadapter), which wraps Succinct's SP1 PLONK verifier. |

## Actors

| Actor | Role |
| --- | --- |
| **Proposer** | Fully permissionless. Creates games via `DisputeGameFactory.create()` with the required `initBond`. |
| **Challenger** | Fully permissionless. Disputes a proposal by calling `challenge()` and depositing `challengerBond`. |
| **Prover** | Fully permissionless. Submits a valid ZK proof via `prove(proofBytes)`. May be the same address as the proposer or the challenger. |
| **Guardian** | Pauses the system, blacklists games, sets the respected game type, and retires old games via `updateRetirementTimestamp()`. |
| **OPCM / ProxyAdmin Owner** | Deploys implementations, configures game types in the factory, and manages `absolutePrestate` per chain. The verifier is fixed by the OPCM release. |

## CWIA Layout

The CWIA calldata is structured in three sections. Offsets after `extraData` are dynamic and
computed via `_preExtraDataByteCount()` and `_extraDataByteCount()` helpers, following the same
pattern as `SuperFaultDisputeGame`.

### Fixed Prefix

Fields at fixed offsets, present before `extraData`:

| Field | Offset | Type | Description |
| --- | --- | --- | --- |
| `gameCreator` | `0x00` | `address` | Creator of the dispute game |
| `rootClaim` | `0x14` | `bytes32` | Super root hash asserted by this game |
| `l1Head` | `0x34` | `bytes32` | L1 block hash at game creation |
| `gameType` | `0x54` | `uint32` | Game type identifier (`ZK_DISPUTE_GAME`) |

### Variable extraData

Starting at offset `0x58`. The total byte count is returned by `_extraDataByteCount()`.

| Field | Type | Description |
| --- | --- | --- |
| `parentIndex` | `uint32` | Index of the parent game; `type(uint32).max` if starting from the anchor state. |
| `superRootProof` | `bytes` | Packed `SuperRootProof` encoding (see [SuperRootProof](#superrootproof)) committed to by `rootClaim`. Variable length. The L2 sequence number (super root timestamp) is part of this preimage and is exposed by the contract via `l2SequenceNumber()` for convenience. |

`_preExtraDataByteCount()` returns the byte count of the fixed prefix (`0x58`).
`_extraDataByteCount()` returns the total byte count of the variable extraData section.
All game args fields use dynamic offsets computed from these helpers.

### Dynamic Game Args

Fields at dynamic offsets, after `extraData`. Injected by `OPContractsManagerUtils.makeGameArgs()`.

| Field | Type | Description |
| --- | --- | --- |
| `absolutePrestate` | `bytes32` | Super-root ZK program identity (e.g., SP1 verification key) |
| `verifier` | `address` | Address of the `IZKVerifier` contract: the OPCM release's `SP1PlonkAdapter` |
| `maxChallengeDuration` | `Duration` | Time window for challenges after game creation |
| `maxProveDuration` | `Duration` | Time window for proof submission after a challenge |
| `challengerBond` | `uint256` | Bond required to challenge a proposal |
| `anchorStateRegistry` | `address` | Address of `AnchorStateRegistry` |
| `weth` | `address` | Address of per-chain `DelayedWETH` |

`verifier`, `anchorStateRegistry` and `weth` are injected by `OPContractsManagerUtils.makeGameArgs()`: the
verifier from the OPCM release, the other two from the chain's existing deployment.

## rootClaim Semantics

`rootClaim` is always a **super root hash**: the result of `hashSuperRootProof(superRootProof)`,
where `superRootProof` is the packed [`SuperRootProof`](#superrootproof) encoding stored in `extraData`.

The `SuperRootProof` preimage carries:
- The super root timestamp (`l2SequenceNumber`).
- A list of `(chainId, outputRoot)` pairs for every chain in the interop set, which MUST be sorted in strictly
  ascending order by `chainId` for the claim to be provable.

In a standalone deployment, this list contains exactly one entry. In an interop set, it contains
one entry per chain. The contract does not distinguish between these cases; the preimage size is
the only difference.

> **Note on chain ordering:** The ZK program identified by `absolutePrestate` only produces proofs for preimages
> with chains sorted in strictly ascending order by `chainId`. `initialize()` does not check the ordering, so a
> game whose preimage is unsorted can be created, but its claim can never be proven. If it is challenged, it
> resolves `CHALLENGER_WINS` once the prove deadline passes.

`rootClaim` MUST NOT be interpreted as an L2 output root for any specific chain. Per-chain output
roots are extracted via [`rootClaimByChainId`](#rootclaimbychainid).

## rootClaimByChainId

```solidity
function rootClaimByChainId(uint256 _chainId) public pure returns (Claim outputRootClaim_)
```

Decodes the `SuperRootProof` preimage from `extraData` and iterates over the `outputRoots` array
to find the entry matching `_chainId`. Returns the corresponding output root as a `Claim`.

MUST revert with `UnknownChainId` if `_chainId` is not present in the preimage.

`OptimismPortal` calls this function during withdrawal verification to extract the per-chain output root from the
super root commitment. It does so for every game type for which `GameTypes.isSuperGame()` returns `true`, which
includes `ZK_DISPUTE_GAME`.

## initialize Invariants

In addition to the standard parent validation described in
[Game Mechanics — Parent Validation](game-mechanics.md#parent-validation),
`initialize()` enforces the following:

- `extraData` length MUST equal `4 + 1 + 8 + 64n` bytes for some `n ≥ 1` (parent index, version, timestamp and
  `n` `(chainId, outputRoot)` pairs), otherwise `initialize()` MUST revert with `BadExtraData`. This prevents
  UUID collisions in the factory from extra or missing bytes in `extraData`.
- The `SuperRootProof` version byte MUST be `0x01`, otherwise `initialize()` MUST revert with
  `Encoding_InvalidSuperRootVersion`.
- `hashSuperRootProof(decode(extraData.superRootProof)) MUST equal rootClaim()`. A mismatch MUST
  revert with `BadExtraData`.
- `l2SequenceNumber() MUST be strictly greater than startingProposal.l2SequenceNumber`. Otherwise
  `initialize()` MUST revert with `UnexpectedRootClaim(rootClaim)`.

## OPCM Integration

`ZKDisputeGame` integrates into OPCM v2 as game type `ZK_DISPUTE_GAME` through
`DisputeGameConfig`, following the same pattern as other game types:

1. `DeployImplementations` deploys the `ZKDisputeGame` implementation and the
   [`SP1PlonkAdapter`](zk-interface.md#sp1plonkadapter) singleton once per OPCM release. Both are stored in
   `OPContractsManagerContainer.Implementations` as `zkDisputeGameImpl` and `sp1PlonkAdapterImpl`.
2. `UpgradeInput.disputeGameConfigs` holds exactly six `DisputeGameConfig` entries, in the fixed
   `VALID_GAME_TYPES` order: `CANNON`, `PERMISSIONED_CANNON`, `CANNON_KONA`, `SUPER_PERMISSIONED`,
   `SUPER_CANNON_KONA`, `ZK_DISPUTE_GAME`.
3. For the `ZK_DISPUTE_GAME` entry, `gameArgs` is `abi.encode(ZKDisputeGameConfig)`. When the entry is enabled,
   OPCM calls `DisputeGameFactory.setImplementation(ZK_DISPUTE_GAME, zkDisputeGameImpl, makeGameArgs(...))` and
   `DisputeGameFactory.setInitBond(ZK_DISPUTE_GAME, initBond)`. When the entry is disabled, OPCM sets the
   implementation to `address(0)` with empty game args and the init bond to `0`, which removes the game type.
4. `GameTypes.isSuperGame()` includes `ZK_DISPUTE_GAME`, so the `OptimismPortal` reads per-chain output roots
   through [`rootClaimByChainId`](#rootclaimbychainid).

### ZKDisputeGameConfig

The caller provides the per-chain ZK parameters as `abi.encode(ZKDisputeGameConfig)`:

```solidity
struct ZKDisputeGameConfig {
    Claim absolutePrestate;
    Duration maxChallengeDuration;
    Duration maxProveDuration;
    uint256 challengerBond;
}
```

`OPContractsManagerUtils.makeGameArgs()` decodes it and packs the game args. The encoded config MUST be exactly
128 bytes, otherwise `makeGameArgs()` MUST revert with `OPContractsManagerUtils_InvalidZKGameArgsLength(uint256)`.
The verifier slot is always filled with the OPCM release's `SP1PlonkAdapter` (`impls.sp1PlonkAdapterImpl`):

```solidity
} else if (rawGT == GameTypes.ZK_DISPUTE_GAME.raw()) {
    if (_gcfg.gameArgs.length != ZK_DISPUTE_GAME_CONFIG_LENGTH) {
        revert IOPContractsManagerUtils.OPContractsManagerUtils_InvalidZKGameArgsLength(_gcfg.gameArgs.length);
    }
    IOPContractsManagerUtils.ZKDisputeGameConfig memory parsedInputArgs =
        abi.decode(_gcfg.gameArgs, (IOPContractsManagerUtils.ZKDisputeGameConfig));
    return abi.encodePacked(
        parsedInputArgs.absolutePrestate,
        impls.sp1PlonkAdapterImpl,
        parsedInputArgs.maxChallengeDuration,
        parsedInputArgs.maxProveDuration,
        parsedInputArgs.challengerBond,
        address(_anchorStateRegistry),
        address(_delayedWETH)
    );
}
```

The packed game args are 140 bytes: `absolutePrestate` (32), `verifier` (20), `maxChallengeDuration` (8),
`maxProveDuration` (8), `challengerBond` (32), `anchorStateRegistry` (20) and `weth` (20).

### Configuration Validation

OPCM's `_assertValidFullConfig` MUST revert with `OPContractsManagerV2_InvalidGameConfigs()` when an enabled
`ZK_DISPUTE_GAME` config:

- is part of an initial deployment (`ZK_DISPUTE_GAME` can only be enabled through `upgrade()`);
- has `absolutePrestate == bytes32(0)`;
- has a `maxChallengeDuration` or `maxProveDuration` outside `(0, type(uint32).max]`;
- has `challengerBond == 0`; or
- has `initBond == 0`.

The `type(uint32).max` cap exists because deadlines are computed as `uint64(block.timestamp + duration)`. A larger
duration could overflow the `uint64` cast and produce a deadline in the past. The game args checks are
implemented by `_isValidZKDisputeGameConfig` in `OPContractsManagerUtilsCaller`.

### Standard Configuration

`OPContractsManagerStandardValidator` checks a registered `ZK_DISPUTE_GAME` with the following error codes:

| Code | Condition checked |
| --- | --- |
| `ZKDG-GARGS-10` | The game args registered in the factory are 140 bytes long. |
| `ZKDG-20` | The registered implementation has the same `version()` as the OPCM release's `zkDisputeGameImpl`. |
| `ZKDG-150` | The registered implementation is the OPCM release's `zkDisputeGameImpl`. |
| `ZKDG-70` | `absolutePrestate` is non-zero. |
| `ZKDG-80` | `verifier` is the OPCM release's `sp1PlonkAdapterImpl` and has code. |
| `ZKDG-90` | `maxChallengeDuration` is in `(0, type(uint32).max]`. |
| `ZKDG-100` | `maxProveDuration` is in `(0, type(uint32).max]`. |
| `ZKDG-110` | `challengerBond` is non-zero. |
| `ZKDG-120` | The `AnchorStateRegistry` in the game args has a non-zero anchor root. |
| `ZKDG-160` | `DisputeGameFactory.initBonds(ZK_DISPUTE_GAME)` is non-zero. |
| `ZKDG-DWETH-*` | The `DelayedWETH` in the game args passes the same checks as for other dispute games. |
| `ZKDG-ANCHORP-*` | The `AnchorStateRegistry` in the game args passes the same checks as for other dispute games. |

`ASR-RGT` accepts `ZK_DISPUTE_GAME` as the respected game type only when `ZK_DISPUTE_GAME` is registered in the
`DisputeGameFactory`. In super-root mode, the validator also requires `SUPER_PERMISSIONED` and `SUPER_CANNON_KONA`
to remain registered (`SPDG-SHAPE` and `SCKDG-SHAPE`), so `ZK_DISPUTE_GAME` is standard only as an additional game
type.

## Interface

This section summarizes the public interface of `ZKDisputeGame` (`version` `2.1.0`). Behavior is specified in
[Game Mechanics](game-mechanics.md).

### Functions

| Function | Behavior | Reverts |
| --- | --- | --- |
| `initialize() external payable` | Validates the proposal and records the creator's bond. See [Creation](game-mechanics.md#creation). | `AlreadyInitialized`, `BadExtraData`, `Encoding_InvalidSuperRootVersion`, `InvalidParentGame`, `UnexpectedGameType`, `AnchorRootNotFound`, `UnexpectedRootClaim` |
| `challenge() external payable returns (ProposalStatus)` | Challenges the claim. See [Challenge](game-mechanics.md#challenge). | `GameOver`, `ClaimAlreadyChallenged`, `IncorrectBondAmount` |
| `prove(bytes calldata _proofBytes) external returns (ProposalStatus)` | Verifies a proof for the claim. See [Proving](game-mechanics.md#proving). | `ClaimAlreadyResolved`, `InvalidParentGame`, `GameOver`, or the verifier's revert |
| `resolve() external returns (GameStatus)` | Resolves the game and allocates credit. See [Resolution](game-mechanics.md#resolution). | `ClaimAlreadyResolved`, `ParentGameNotResolved`, `GameNotOver`, `InvalidProposalStatus` |
| `closeGame() public` | Sets the bond distribution mode and tries to update the anchor state. See [Closing](game-mechanics.md#closing). | `InvalidBondDistributionMode`, `GamePaused`, `GameNotResolved`, `GameNotFinalized` |
| `claimCredit(address _recipient) external` | Closes the game if needed, then unlocks or withdraws the recipient's credit. See [Closing](game-mechanics.md#closing). | `closeGame()` errors, `InvalidBondDistributionMode`, `NoCreditToClaim`, `BondTransferFailed` |
| `gameOver() public view returns (bool gameOver_)` | See [Game Over](#game-over). | — |
| `credit(address _recipient) external view returns (uint256 credit_)` | Returns `refundModeCredit[_recipient]` in REFUND mode, otherwise `normalModeCredit[_recipient]`. | — |
| `rootClaimByChainId(uint256 _chainId) public pure returns (Claim outputRootClaim_)` | See [rootClaimByChainId](#rootclaimbychainid). | `UnknownChainId` |
| `startingSequenceNumber() external view returns (uint256 startingSequenceNumber_)` | Returns `startingProposal.l2SequenceNumber`. | — |
| `startingRootHash() external view returns (Hash startingRootHash_)` | Returns `startingProposal.root`. | — |
| `gameData() external pure returns (GameType gameType_, Claim rootClaim_, bytes memory extraData_)` | Returns the components of the game's UUID preimage. | — |
| CWIA getters: `gameCreator`, `rootClaim`, `l1Head`, `gameType`, `parentIndex`, `l2SequenceNumber`, `absolutePrestate`, `verifier`, `maxChallengeDuration`, `maxProveDuration`, `challengerBond`, `anchorStateRegistry`, `weth`, `extraData` | Return the values in the [CWIA Layout](#cwia-layout). | — |
| Storage getters: `createdAt`, `resolvedAt`, `status`, `claimData`, `normalModeCredit`, `refundModeCredit`, `startingProposal`, `bondDistributionMode`, `wasRespectedGameTypeWhenCreated`, `disputeGameFactory`, `totalBonds` | Return the game's state variables. | — |

`claimData` returns the `ClaimData` struct:

```solidity
struct ClaimData {
    uint32 parentIndex; // 4 bytes
    ProposalStatus status; // 1 byte
    address challenger; // 20 bytes |-- slot 1 (25 bytes)
    address prover; // 20 bytes
    Timestamp deadline; // 8 bytes  |-- slot 2 (28 bytes)
    Claim claim; // 32 bytes |-- slot 3
}
```

### Events

| Event | Emitted by |
| --- | --- |
| `Challenged(address indexed challenger)` | `challenge()` |
| `Proved(address indexed prover)` | `prove()` |
| `Resolved(GameStatus indexed status)` (inherited from `IDisputeGame`) | `resolve()` |
| `GameClosed(BondDistributionMode bondDistributionMode)` | `closeGame()`, including when called from `claimCredit()` |

### Errors

| Error | Raised by | Condition |
| --- | --- | --- |
| `AlreadyInitialized` | `initialize()` | The game is already initialized. |
| `BadExtraData` | `initialize()` | `extraData` has the wrong length, or the preimage hash does not equal `rootClaim`. |
| `Encoding_InvalidSuperRootVersion` | `initialize()` | The `SuperRootProof` version byte is not `0x01`. |
| `Encoding_EmptySuperRoot` | `Encoding.decodeSuperRootProof` | The preimage has no output roots. Not reachable once the `BadExtraData` length check passes. |
| `Encoding_InvalidSuperRootEncoding` | `Encoding.decodeSuperRootProof` | The preimage length is malformed. Not reachable once the `BadExtraData` length check passes. |
| `InvalidParentGame` | `initialize()`, `prove()` | `initialize()`: the parent resolved `CHALLENGER_WINS`, is blacklisted or retired, was not respected while the child is, or is at or below the anchor. `prove()`: the parent resolved `CHALLENGER_WINS`. |
| `UnexpectedGameType` | `initialize()` | The parent is not a `ZK_DISPUTE_GAME`. |
| `AnchorRootNotFound` | `initialize()` | There is no parent and the anchor root is zero. |
| `UnexpectedRootClaim(Claim rootClaim)` | `initialize()` | `l2SequenceNumber` is not above the starting proposal's sequence number. |
| `GameOver` | `challenge()`, `prove()` | `gameOver()` returns `true`. |
| `ClaimAlreadyChallenged` | `challenge()` | `claimData.status` is not `Unchallenged`. |
| `IncorrectBondAmount` | `challenge()`, `DisputeGameFactory.create()` | `msg.value` is not `challengerBond` (challenge) or the factory's `initBond` (creation). |
| `ClaimAlreadyResolved` | `prove()`, `resolve()` | The game is already resolved. |
| `ParentGameNotResolved` | `resolve()` | The parent game is still `IN_PROGRESS`. |
| `GameNotOver` | `resolve()` | The parent did not resolve `CHALLENGER_WINS` and `gameOver()` returns `false`. |
| `InvalidProposalStatus` | `resolve()` | `claimData.status` is not a resolvable status (sanity check). |
| `InvalidBondDistributionMode` | `closeGame()`, `claimCredit()` | The bond distribution mode is not a known value (sanity check). |
| `GamePaused` | `closeGame()` | The `AnchorStateRegistry` is paused and the game is not closed yet. |
| `GameNotResolved` | `closeGame()` | The game is not resolved. |
| `GameNotFinalized` | `closeGame()` | `AnchorStateRegistry.isGameFinalized` returns `false`. |
| `NoCreditToClaim` | `claimCredit()` | The recipient has no credit and no pending `DelayedWETH` withdrawal, and the game was already closed before the call. |
| `BondTransferFailed` | `claimCredit()` | The ETH transfer to the recipient failed. |
| `UnknownChainId` | `rootClaimByChainId()` | The chain ID is not in the preimage. |

## Assumptions

### aZKG-001: ZK Verifier Soundness

The `IZKVerifier` implementation is sound: it is computationally infeasible to produce a proof
that passes `verify()` for an incorrect state transition.

#### Mitigations

- The PLONK verifier for SP1 is independently audited.
- The verifier is fixed per OPCM release: OPCM always installs the release's `SP1PlonkAdapter`, and the release is
  approved by governance. The verifier can only be swapped by a new OPCM release.
- The `IZKVerifier` interface intentionally decouples the game from any specific proving system.
  A verifier can be swapped without redeploying the game implementation.

### aZKG-002: Absolute Prestate Uniquely Identifies the ZK Program

The `absolutePrestate` value uniquely identifies the ZK program version. Two different programs
MUST NOT share the same `absolutePrestate`.

#### Mitigations

- For SP1, `absolutePrestate` corresponds to the program's verification key, which is derived from
  the program binary and circuit structure.
- OPCM manages `absolutePrestate` per deployment; program updates require a corresponding
  `absolutePrestate` update via governance.

### aZKG-003: Parent Chaining Preserves Correctness

A chain of `ZKDisputeGame` instances resolving as `DEFENDER_WINS` implies that the final
`rootClaim` is a valid super root, provided the initial parent started from a known-good anchor
state.

#### Mitigations

- Each proof commits to `startingProposal.root` (the parent's super root claim) as a public
  value, which cryptographically links consecutive games.
- Parent validation at creation time prevents games from chaining off blacklisted, retired, or
  `CHALLENGER_WINS` parents.
- If a parent is blacklisted or retired after child games have been created, the Guardian MUST
  individually blacklist or retire those child games to place them in REFUND mode.

### aZKG-004: Bonds Are Economically Rational

The `initBond`, `challengerBond`, `maxChallengeDuration`, and `maxProveDuration` values are set
such that honest participation is economically rational and griefing is costly.

#### Mitigations

- `challengerBond`, `maxChallengeDuration`, and `maxProveDuration` are in `gameArgs` and can be
  tuned per deployment by OPCM without redeploying the implementation. `initBond` is part of the same OPCM
  `DisputeGameConfig`, is applied through `DisputeGameFactory.setInitBond`, and MUST be non-zero.
- OPCM bounds-checks the durations and bonds (see [Configuration Validation](#configuration-validation)).
- Benchmark proving costs and document standard values for common configurations.
- Bonds too low invite spam; bonds too high discourage honest participation. Durations must be
  long enough to allow super-root proof generation but short enough to preserve withdrawal latency
  benefits.

### aZKG-005: Guardian Acts Honestly and Timely

The Guardian is trusted to pause the system, blacklist invalid games, and retire superseded game
types before fraudulent games achieve Valid Claims.

#### Mitigations

- The `disputeGameFinalityDelaySeconds` review period between resolution and `closeGame` provides
  the Guardian a window to act.
- `DelayedWETH` provides an additional window after `closeGame` to freeze funds.

### aZKG-006: Anchor State Advances Slowly Relative to Proposal Frequency

There is no technical mechanism that enforces the anchor state to advance slowly — any resolved
game that passes the finality delay can call `closeGame()` and advance it. However, the minimum
time for a game to advance the anchor state is `maxChallengeDuration + disputeGameFinalityDelaySeconds`
(12+ hours in practice), and under normal operation this is expected to be much larger than
typical proposal frequency. Orphan risk from parent validation is therefore negligible.

#### Mitigations

- A rational proposer would never use a parent whose `l2SequenceNumber` is below the anchor, as
  it unnecessarily increases the proving range.
- Parent validation requires the parent's `l2SequenceNumber` to be strictly above the anchor
  state, preventing chains from building on stale starting points.

### aZKG-007: Proof Generation Is Feasible Within the Prove Window

A prover with access to the required L1 and L2 data for all chains in the interop set can
generate a valid super-root proof within `maxProveDuration` under normal operating conditions.

#### Mitigations

- `maxProveDuration` must be set with headroom above worst-case proving times for the full
  interop set, accounting for prover network latency, queue depth, and hardware variability.
- Multiple independent provers reduce the risk of a single point of failure in proof delivery.
- Off-chain monitoring on the ratio of successful `prove()` calls to challenged games can detect
  when proving infrastructure is unable to keep up with the configured window.
- Proof generation can also fail because of resource limits rather than time (see
  [aZKG-010](#azkg-010-valid-claims-are-provable)).

### aZKG-008: Super Root Preimage Faithfully Represents the Chain Set

The `SuperRootProof` preimage stored in `extraData` faithfully lists every chain in the interop
set with correct chain IDs and output roots. No chain is omitted, duplicated, or misidentified.

#### Mitigations

- `initialize()` enforces `hashSuperRootProof(decode(extraData.superRootProof)) == rootClaim()`.
  An incorrect preimage cannot produce a matching hash.
- The ZK program independently verifies that the output roots in the preimage match the actual
  chain states (see [iZKVM-002](../../zk-proof-system.md#izkvm-002-super-root-preimage-must-commit-to-all-chain-outputs)).
- Chain ordering is enforced by the ZK program (identified by `absolutePrestate`), not by `initialize()`. The
  program only proves preimages with chains sorted in strictly ascending order by `chainId`, so no valid proof
  can be generated for an unsorted preimage and such proposals can never be proven.

### aZKG-009: Chain Set Is Stable During the Prove Window

The interop set (the set of chains committed to by a super root) does not change between game
creation and proof submission.

#### Mitigations

- The `SuperRootProof` preimage is immutable once embedded in `extraData` at creation time.
- The chain set is taken from the starting super root preimage and MUST equal the dependency set compiled into the
  program identified by `absolutePrestate`. A chain set change requires a new program and a new
  `absolutePrestate`, gated by governance.

### aZKG-010: Valid Claims Are Provable

A valid claim can always be proven within the prover's resource limits.

A sound ZK program may still be unable to prove an honest claim. Each proving request has witness size, memory,
cycle and proving gas limits, and the smallest unit of work is one chain at one timestamp. Adversarial L2
content, for example a large number of interop messages, can inflate proving cost. If a challenged valid claim
cannot be proven, it resolves `CHALLENGER_WINS`, and so do all of its descendants.

#### Mitigations

- The `log-commitment` program lets initiating messages be checked without loading the block's receipts.
- Provers split a span into chunks, and split a single timestamp by chain, to keep each request within limits.
- The Guardian can blacklist games or pause the system, and the dispute game finality delay gives time to do so.
- Off-chain monitoring of challenged games that remain unproven can detect claims that cannot be proven.

## Invariants

### iZKG-001: A Valid Proof Always Wins

If a valid ZK proof is submitted before the current deadline, the game MUST resolve as
`DEFENDER_WINS` (assuming a valid parent chain).

#### Impact

**Severity: High**

A violation lets a correct proposer be cheated out of their bond, which breaks the economic
security of the game and the correctness of withdrawal finalization.

### iZKG-002: A Game Without a Valid Proof and With a Challenger Resolves as CHALLENGER_WINS

If a game was challenged and the prove deadline expires without a valid proof, `resolve()` MUST
produce `CHALLENGER_WINS`.

#### Impact

**Severity: High**

A violation would allow invalid super roots to be finalized on L1 and bridge funds to be stolen.

### iZKG-003: Bond Safety via DelayedWETH

All bonds MUST be deposited into and withdrawn from `DelayedWETH`. The game contract MUST NOT
hold raw ETH bonds.

#### Impact

**Severity: Critical**

Raw ETH bonds held directly in a game clone cannot be recovered — each clone is an immutable
proxy instance with no upgrade path, so any ETH stuck in it is permanently lost. This also
bypasses the Guardian's ability to freeze funds post-resolution.

### iZKG-004: Permissionless Participation

`create()`, `challenge()`, `prove()`, and `resolve()` MUST be callable by any address. No
`AccessManager` or allowlist MAY gate these functions.

#### Impact

**Severity: High**

Permissioned access would reduce censorship resistance and deviate from the Stage 1 security
model.

### iZKG-005: Parent Invalidity Propagates to Children

If a parent game resolves as `CHALLENGER_WINS`, all child games MUST also resolve as
`CHALLENGER_WINS`, regardless of whether a valid proof was submitted for the child.

#### Impact

**Severity: High**

Failure to propagate would allow a chain of games to finalize a super root that descends from an
invalid state. Funds that do not exist on L2 could be withdrawn.

### iZKG-006: closeGame Reverts When Paused

`closeGame()` MUST revert if `AnchorStateRegistry` reports the system as paused while
`bondDistributionMode` is `UNDECIDED`.

Once the mode is set, `closeGame()` returns early without checking the pause. This is intentional,
and matches `FaultDisputeGame` and `SuperFaultDisputeGame`: `claimCredit()` can still unlock credit
for a closed game during a pause, but `DelayedWETH.withdraw` reverts until the system is unpaused.

#### Impact

**Severity: High**

Closing an undecided game while paused would put it into REFUND mode, because
`AnchorStateRegistry` treats every game as improper while paused. A valid game would refund bonds
instead of paying the winners.

### iZKG-007: Only Finalized Games Can Close

`closeGame()` MUST revert unless `AnchorStateRegistry.isGameFinalized(this)` returns `true`.

#### Impact

**Severity: High**

Closing before the finality delay would remove the Guardian's window to blacklist or pause the
game before funds are distributed.

### iZKG-008: Blacklisted and Retired Games Enter REFUND Mode

If a game is blacklisted or retired, `closeGame()` MUST enter REFUND mode: bonds are returned to
the original depositors rather than distributed to winners.

#### Impact

**Severity: High**

Failure to refund would cause honest participants to lose bonds when the Guardian must invalidate
a game for safety reasons unrelated to the game's correctness.

### iZKG-009: Child Resolution Requires Resolved Parent

If a game references a parent (`parentIndex != type(uint32).max`), `resolve()` MUST revert
while that parent's `status == GameStatus.IN_PROGRESS`. The resolution dependency chain MUST
be honored in topological order.

#### Impact

**Severity: Critical**

Without this, iZKG-005 cannot hold. A child could resolve as `DEFENDER_WINS` and finalize a
withdrawal before the parent is invalidated. Funds could be withdrawn against a super root that
descends from an invalid state.

### iZKG-010: At Most One Challenge Per Game

`challenge()` MUST revert if `claimData.status != ProposalStatus.Unchallenged`.

#### Impact

**Severity: High**

A second challenge could reset the prove deadline and give challengers unbounded time to delay
resolution, overwrite the original challenger's address and steal their bond credit, or produce
double the bond liability in `DelayedWETH` with only one `challengerBond` deposited.

### iZKG-011: Bond Conservation

For any resolved game, the sum of all bonds distributed plus any amount sent to `address(0)` MUST
equal `initBond + challengerBond` (or `initBond` alone if the game was never challenged). No value
may be created from nothing or permanently locked beyond the defined burn path.

#### Impact

**Severity: High**

A violation means either fund loss for participants (bonds locked forever with no recipient) or an
exploitable source of unbacked ETH withdrawals from `DelayedWETH`.

### iZKG-012: Monotonic State Progression

`claimData.status` MUST only advance forward through the `ProposalStatus` state machine. No
transition from a later state back to an earlier one is permitted. `status` (`GameStatus`) MUST
only transition from `IN_PROGRESS` to a terminal state (`CHALLENGER_WINS` or `DEFENDER_WINS`).

#### Impact

**Severity: High**

State regression would corrupt deadline logic and bond accounting. Functions that use status as a
guard could be re-entered in unexpected ways if the state can regress.

### iZKG-013: rootClaimByChainId Consistency

`rootClaimByChainId(_chainId)` MUST return the output root for `_chainId` as committed to in the
`SuperRootProof` preimage of `rootClaim`. If `_chainId` is not present in the preimage, the
function MUST revert with `UnknownChainId`.

#### Impact

**Severity: High**

An inconsistency between what `rootClaimByChainId` returns and what the super root actually
commits to would allow the Portal to finalize withdrawals against an output root that was never
proven, and allow bridge funds to be stolen.

### iZKG-014: rootClaim Matches SuperRootProof Preimage

`hashSuperRootProof(decode(extraData.superRootProof))` MUST equal `rootClaim()` at all times
after `initialize()`. This is enforced at initialization and cannot change thereafter (both values
are immutable).

#### Impact

**Severity: Critical**

A mismatch would mean `rootClaimByChainId` is decoding a preimage that does not correspond to the
proven claim. Arbitrary output roots could be returned to the Portal regardless of what was
actually proven.
