# Super ZK Dispute Game

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
  - [SuperZKDisputeGame](#superzkdisputegame)
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
  - [SuperZKDisputeGameConfig](#superzkdisputegameconfig)
- [Assumptions](#assumptions)
  - [aSZKG-001: ZK Verifier Soundness](#aszkg-001-zk-verifier-soundness)
    - [Mitigations](#mitigations)
  - [aSZKG-002: Absolute Prestate Uniquely Identifies the ZK Program](#aszkg-002-absolute-prestate-uniquely-identifies-the-zk-program)
    - [Mitigations](#mitigations-1)
  - [aSZKG-003: Parent Chaining Preserves Correctness](#aszkg-003-parent-chaining-preserves-correctness)
    - [Mitigations](#mitigations-2)
  - [aSZKG-004: Bonds Are Economically Rational](#aszkg-004-bonds-are-economically-rational)
    - [Mitigations](#mitigations-3)
  - [aSZKG-005: Guardian Acts Honestly and Timely](#aszkg-005-guardian-acts-honestly-and-timely)
    - [Mitigations](#mitigations-4)
  - [aSZKG-006: Anchor State Advances Slowly Relative to Proposal Frequency](#aszkg-006-anchor-state-advances-slowly-relative-to-proposal-frequency)
    - [Mitigations](#mitigations-5)
  - [aSZKG-007: Proof Generation Is Feasible Within the Prove Window](#aszkg-007-proof-generation-is-feasible-within-the-prove-window)
    - [Mitigations](#mitigations-6)
  - [aSZKG-008: Super Root Preimage Faithfully Represents the Chain Set](#aszkg-008-super-root-preimage-faithfully-represents-the-chain-set)
    - [Mitigations](#mitigations-7)
  - [aSZKG-009: Chain Set Is Stable During the Prove Window](#aszkg-009-chain-set-is-stable-during-the-prove-window)
    - [Mitigations](#mitigations-8)
- [Invariants](#invariants)
  - [iSZKG-001: A Valid Proof Always Wins](#iszkg-001-a-valid-proof-always-wins)
    - [Impact](#impact)
  - [iSZKG-002: A Game Without a Valid Proof and With a Challenger Resolves as CHALLENGER_WINS](#iszkg-002-a-game-without-a-valid-proof-and-with-a-challenger-resolves-as-challenger_wins)
    - [Impact](#impact-1)
  - [iSZKG-003: Bond Safety via DelayedWETH](#iszkg-003-bond-safety-via-delayedweth)
    - [Impact](#impact-2)
  - [iSZKG-004: Permissionless Participation](#iszkg-004-permissionless-participation)
    - [Impact](#impact-3)
  - [iSZKG-005: Parent Invalidity Propagates to Children](#iszkg-005-parent-invalidity-propagates-to-children)
    - [Impact](#impact-4)
  - [iSZKG-006: closeGame Reverts When Paused](#iszkg-006-closegame-reverts-when-paused)
    - [Impact](#impact-5)
  - [iSZKG-007: Only Finalized Games Can Close](#iszkg-007-only-finalized-games-can-close)
    - [Impact](#impact-6)
  - [iSZKG-008: Blacklisted and Retired Games Enter REFUND Mode](#iszkg-008-blacklisted-and-retired-games-enter-refund-mode)
    - [Impact](#impact-7)
  - [iSZKG-009: Child Resolution Requires Resolved Parent](#iszkg-009-child-resolution-requires-resolved-parent)
    - [Impact](#impact-8)
  - [iSZKG-010: At Most One Challenge Per Game](#iszkg-010-at-most-one-challenge-per-game)
    - [Impact](#impact-9)
  - [iSZKG-011: Bond Conservation](#iszkg-011-bond-conservation)
    - [Impact](#impact-10)
  - [iSZKG-012: Monotonic State Progression](#iszkg-012-monotonic-state-progression)
    - [Impact](#impact-11)
  - [iSZKG-013: rootClaimByChainId Consistency](#iszkg-013-rootclaimbychainid-consistency)
    - [Impact](#impact-12)
  - [iSZKG-014: rootClaim Matches SuperRootProof Preimage](#iszkg-014-rootclaim-matches-superrootproof-preimage)
    - [Impact](#impact-13)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The `SuperZKDisputeGame` is a dispute game that resolves disputes in a single round using ZK
(zero-knowledge) proofs, registered as game type `SUPER_ZK_GAME_TYPE`. It integrates into the OP
Stack dispute infrastructure — `DisputeGameFactory`, `AnchorStateRegistry`, `DelayedWETH`, and
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

The proving system is accessed through the generic [`IZKVerifier`](super-zk-interface.md)
interface. The first supported backend is SP1 (PLONK) by Succinct. See
[Super ZK Fault Proof VM](../../super-zk-fault-proof-vm.md) for details on the off-chain proving
component.

For the full game lifecycle and bond accounting see
[Super ZK Game Mechanics](super-zk-game-mechanics.md).

## Definitions

### SuperZKDisputeGame

The smart contract implementing the single-round super-root ZK dispute protocol. Each game
instance is a lightweight [MCP clone](#mcp-clone) of a shared implementation contract, deployed
by `DisputeGameFactory`.

### MCP Clone

A minimal proxy clone (ERC-1167) created by `DisputeGameFactory` that shares the
`SuperZKDisputeGame` implementation bytecode but has its own per-chain configuration appended as
immutable constructor arguments via the Clones-with-Immutable-Args (CWIA) pattern.

### Game Args (CWIA)

The per-chain configuration bytes appended to each MCP clone by `DisputeGameFactory`. A single
implementation contract serves every deployment. See [CWIA Layout](#cwia-layout) for the full
field breakdown.

### Super Root

A `bytes32` hash that commits to the output roots of all chains in the interop set at a given
timestamp. Computed as `hashSuperRootProof(superRootProof)`. The `rootClaim` of every
`SuperZKDisputeGame` is a super root.

### SuperRootProof

An ABI-encoded struct that is the preimage of a super root. It carries the timestamp and the list
of per-chain output roots that the super root commits to. Its hash MUST equal `rootClaim`.

The `(chainId, outputRoot)` pairs MUST be sorted in strictly ascending order by `chainId`.
Encoding the same logical chain set in a different order produces a different hash and therefore a
different super root. Proposers who submit an unsorted preimage will fail the
`hashSuperRootProof(decode(extraData.superRootProof)) == rootClaim()` check in `initialize()`, and
any ZK proof generated over the correct (sorted) super root will not verify against it.

### Chain Set

The set of chains whose output roots are committed to by a super root. Defined by the
`SuperRootProof` preimage in `extraData`. In a standalone deployment the chain set contains
exactly one chain.

### L2 Sequence Number

The super root timestamp asserted by a game's `rootClaim`. Used to validate parent–child ordering.
Unlike the classic output-root model where this field holds an L2 block number, here it is a
timestamp, following `SuperFaultDisputeGame` convention. The value MUST fit within a `uint64`.

### Parent Game

A previously created `SuperZKDisputeGame` whose proven super root serves as the starting state
for a new game's ZK proof. A game with `parentIndex == type(uint32).max` starts from the anchor
state directly.

### Challenge Deadline

The timestamp after which a game can no longer be challenged. Computed as
`createdAt + maxChallengeDuration`.

### Prove Deadline

The timestamp after which a challenged game can no longer receive a proof submission. Set to
`block.timestamp + maxProveDuration` when `challenge()` is called, resetting the prior challenge
deadline.

### Absolute Prestate

A `bytes32` value that uniquely identifies the ZK program version being proven. It is the program
identity passed to `IZKVerifier.verify()` and is injected into each game instance via the CWIA
game args. See [Absolute Prestate](../../super-zk-fault-proof-vm.md#absolute-prestate) for
details.

### Game Over

The condition under which a game can be resolved. `gameOver()` returns `true` when:

- `claimData.prover != address(0)` (a valid proof has been submitted), or
- `claimData.deadline < block.timestamp` (the current deadline has expired).

## Contracts Involved

| Contract | Role |
| --- | --- |
| **SuperZKDisputeGame** (clones) | Per-proposal game instance. Runs the challenge → prove → resolve lifecycle and tracks bond accounting. |
| **SuperZKDisputeGame** (implementation) | Shared bytecode base for MCP clones. Deployed and upgraded by OPCM. |
| **DisputeGameFactory** | Creates MCP clones via `create(...)`. Appends per-chain `gameArgs` (CWIA). |
| **AnchorStateRegistry** | Source of truth for finalization, anchor state, respected game type, and blacklisting. Enforces pause checks. |
| **DelayedWETH** | Bond custody with a deposit → unlock → withdraw lifecycle. Provides a time window for the Guardian to freeze funds post-resolution. |
| **IZKVerifier** | Generic verifier interface. The concrete deployment for the initial release uses Succinct's PLONK verifier. |

## Actors

| Actor | Role |
| --- | --- |
| **Proposer** | Fully permissionless. Creates games via `DisputeGameFactory.create()` with the required `initBond`. |
| **Challenger** | Fully permissionless. Disputes a proposal by calling `challenge()` and depositing `challengerBond`. |
| **Prover** | Fully permissionless. Submits a valid ZK proof via `prove(proofBytes)`. May be the same address as the proposer or the challenger. |
| **Guardian** | Pauses the system, blacklists games, sets the respected game type, and retires old games via `updateRetirementTimestamp()`. |
| **OPCM / ProxyAdmin Owner** | Deploys implementations, configures game types in the factory, and manages `absolutePrestate` and verifier versions. |

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
| `gameType` | `0x54` | `uint32` | Game type identifier (`SUPER_ZK_GAME_TYPE`) |

### Variable extraData

Starting at offset `0x58`. The total byte count is returned by `_extraDataByteCount()`.

| Field | Type | Description |
| --- | --- | --- |
| `l2SequenceNumber` | `uint256` | Super root timestamp. Constrained to `uint64` range. |
| `parentIndex` | `uint32` | Index of the parent game; `type(uint32).max` if starting from the anchor state. |
| `superRootProof` | `bytes` | ABI-encoded `SuperRootProof` preimage committed to by `rootClaim`. Variable length. |

`_preExtraDataByteCount()` returns the byte count of the fixed prefix (`0x58`).
`_extraDataByteCount()` returns the total byte count of the variable extraData section.
All game args fields use dynamic offsets computed from these helpers.

### Dynamic Game Args

Fields at dynamic offsets, after `extraData`. Injected by `OPCM._makeGameArgs()`.

| Field | Type | Description |
| --- | --- | --- |
| `absolutePrestate` | `bytes32` | Super-root ZK program identity (e.g., SP1 verification key) |
| `verifier` | `address` | Address of the `IZKVerifier` contract |
| `maxChallengeDuration` | `Duration` | Time window for challenges after game creation |
| `maxProveDuration` | `Duration` | Time window for proof submission after a challenge |
| `challengerBond` | `uint256` | Bond required to challenge a proposal |
| `anchorStateRegistry` | `address` | Address of `AnchorStateRegistry` |
| `weth` | `address` | Address of per-chain `DelayedWETH` |

`anchorStateRegistry` and `weth` are injected by `OPContractManager._makeGameArgs()` directly
from the chain's existing deployment.

## rootClaim Semantics

`rootClaim` is always a **super root hash**: the result of `hashSuperRootProof(superRootProof)`,
where `superRootProof` is the ABI-encoded `SuperRootProof` struct stored in `extraData`.

The `SuperRootProof` preimage carries:
- The super root timestamp (`l2SequenceNumber`).
- A list of `(chainId, outputRoot)` pairs for every chain in the interop set, sorted in strictly
  ascending order by `chainId`.

In a standalone deployment, this list contains exactly one entry. In an interop set, it contains
one entry per chain. The contract does not distinguish between these cases; the preimage size is
the only difference.

> **Note on chain ordering:** The ZK program identified by `absolutePrestate` is compiled to
> produce and verify proofs over preimages with chains sorted ascending by `chainId`. A proposer
> who submits an unsorted preimage will produce a `rootClaim` that differs from any super root a
> correct prover can generate a proof for — the game will expire unchallenged only if no one
> notices, but any subsequent `prove()` call against the correctly sorted super root will not
> match `rootClaim` and will therefore revert.

`rootClaim` MUST NOT be interpreted as an L2 output root for any specific chain. Per-chain output
roots are extracted via [`rootClaimByChainId`](#rootclaimbychain-id).

## rootClaimByChainId

```solidity
function rootClaimByChainId(uint256 _chainId) public view returns (Claim rootClaim_)
```

Decodes the `SuperRootProof` preimage from `extraData` and iterates over the `outputRoots` array
to find the entry matching `_chainId`. Returns the corresponding output root as a `Claim`.

MUST revert with `UnknownChainId` if `_chainId` is not present in the preimage.

`OptimismPortal` calls this function during withdrawal verification (via
`GameTypes.isSuperGame()`) to extract the per-chain output root from the super root commitment.
Adding `SUPER_ZK_GAME_TYPE` to the `isSuperGame` allowlist is required for Portal withdrawal
finalization to work correctly.

## initialize Invariants

In addition to the standard parent validation described in
[Super ZK Game Mechanics — Parent Validation](super-zk-game-mechanics.md#parent-validation),
`initialize()` enforces the following:

- `hashSuperRootProof(decode(extraData.superRootProof)) MUST equal rootClaim()`. A mismatch MUST
  revert.
- `l2SequenceNumber() MUST be strictly greater than startingProposal.l2SequenceNumber`.
- `l2SequenceNumber() MUST fit within uint64` (i.e., `<= type(uint64).max`).
- The calldata size MUST match the expected length derived from `_extraDataByteCount()` to prevent
  UUID collisions in the factory from extra or missing bytes in `extraData`.

## OPCM Integration

`SuperZKDisputeGame` integrates into OPCM v2 as game type `SUPER_ZK_GAME_TYPE` through
`DisputeGameConfig`, following the same pattern as other game types.

Three additions are required:

1. `SuperZKDisputeGame` is deployed once via the `DeployImplementations` script and tracked in
   `OPContractsManagerContainer.Implementations`.
2. A `SuperZKDisputeGameConfig` struct carries the per-chain parameters that the caller provides.
   OPCM's `_makeGameArgs()` decodes it, injects the chain-specific values it already knows, and
   packs the final variable-length CWIA bytes for the factory.
3. `SUPER_ZK_GAME_TYPE` is added to the `validGameTypes` array in `_assertValidFullConfig()` and
   to `GameTypes.isSuperGame()`.

### SuperZKDisputeGameConfig

```solidity
struct SuperZKDisputeGameConfig {
    Claim absolutePrestate;
    address verifier;
    Duration maxChallengeDuration;
    Duration maxProveDuration;
    uint256 challengerBond;
}
```

```solidity
if (_gcfg.gameType.raw() == GameTypes.SUPER_ZK_GAME_TYPE.raw()) {
    SuperZKDisputeGameConfig memory cfg = abi.decode(_gcfg.gameArgs, (SuperZKDisputeGameConfig));
    return abi.encodePacked(
        cfg.absolutePrestate,
        cfg.verifier,
        cfg.maxChallengeDuration,
        cfg.maxProveDuration,
        cfg.challengerBond,
        uint256(0), // l2ChainId; zero for parity with SuperFaultDisputeGame — chain scoping is provided by the SuperRootProof preimage
        address(_anchorStateRegistry),
        address(_delayedWETH)
    );
}
```

## Assumptions

### aSZKG-001: ZK Verifier Soundness

The `IZKVerifier` implementation is sound: it is computationally infeasible to produce a proof
that passes `verify()` for an incorrect state transition.

#### Mitigations

- The PLONK verifier for SP1 is independently audited.
- The verifier address comes from `gameArgs`, managed by OPCM. Governance controls upgrades.
- The `IZKVerifier` interface intentionally decouples the game from any specific proving system.
  A verifier can be swapped without redeploying the game implementation.

### aSZKG-002: Absolute Prestate Uniquely Identifies the ZK Program

The `absolutePrestate` value uniquely identifies the ZK program version. Two different programs
MUST NOT share the same `absolutePrestate`.

#### Mitigations

- For SP1, `absolutePrestate` corresponds to the program's verification key, which is derived from
  the program binary and circuit structure.
- OPCM manages `absolutePrestate` per deployment; program updates require a corresponding
  `absolutePrestate` update via governance.

### aSZKG-003: Parent Chaining Preserves Correctness

A chain of `SuperZKDisputeGame` instances resolving as `DEFENDER_WINS` implies that the final
`rootClaim` is a valid super root, provided the initial parent started from a known-good anchor
state.

#### Mitigations

- Each proof commits to `startingProposal.root` (the parent's super root claim) as a public
  value, which cryptographically links consecutive games.
- Parent validation at creation time prevents games from chaining off blacklisted, retired, or
  `CHALLENGER_WINS` parents.
- If a parent is blacklisted or retired after child games have been created, the Guardian MUST
  individually blacklist or retire those child games to place them in REFUND mode.

### aSZKG-004: Bonds Are Economically Rational

The `initBond`, `challengerBond`, `maxChallengeDuration`, and `maxProveDuration` values are set
such that honest participation is economically rational and griefing is costly.

#### Mitigations

- `challengerBond`, `maxChallengeDuration`, and `maxProveDuration` are in `gameArgs` and can be
  tuned per deployment by OPCM without redeploying the implementation. `initBond` is a factory
  parameter updated separately.
- Benchmark proving costs and document standard values for common configurations.
- Bonds too low invite spam; bonds too high discourage honest participation. Durations must be
  long enough to allow super-root proof generation but short enough to preserve withdrawal latency
  benefits.

### aSZKG-005: Guardian Acts Honestly and Timely

The Guardian is trusted to pause the system, blacklist invalid games, and retire superseded game
types before fraudulent games achieve Valid Claims.

#### Mitigations

- The `DISPUTE_GAME_FINALITY_DELAY_SECONDS` airgap between resolution and `closeGame` provides
  the Guardian a window to act.
- `DelayedWETH` provides an additional window after `closeGame` to freeze funds.

### aSZKG-006: Anchor State Advances Slowly Relative to Proposal Frequency

There is no technical mechanism that enforces the anchor state to advance slowly — any resolved
game that passes the finality delay can call `closeGame()` and advance it. However, the minimum
time for a game to advance the anchor state is `maxChallengeDuration + DISPUTE_GAME_FINALITY_DELAY_SECONDS`
(12+ hours in practice), and under normal operation this is expected to be much larger than
typical proposal frequency. Orphan risk from parent validation is therefore negligible.

#### Mitigations

- A rational proposer would never use a parent whose `l2SequenceNumber` is below the anchor, as
  it unnecessarily increases the proving range.
- Parent validation requires the parent's `l2SequenceNumber` to be strictly above the anchor
  state, preventing chains from building on stale starting points.

### aSZKG-007: Proof Generation Is Feasible Within the Prove Window

A prover with access to the required L1 and L2 data for all chains in the interop set can
generate a valid super-root proof within `maxProveDuration` under normal operating conditions.

#### Mitigations

- `maxProveDuration` must be set with headroom above worst-case proving times for the full
  interop set, accounting for prover network latency, queue depth, and hardware variability.
- Multiple independent provers reduce the risk of a single point of failure in proof delivery.
- Off-chain monitoring on the ratio of successful `prove()` calls to challenged games can detect
  when proving infrastructure is unable to keep up with the configured window.

### aSZKG-008: Super Root Preimage Faithfully Represents the Chain Set

The `SuperRootProof` preimage stored in `extraData` faithfully lists every chain in the interop
set with correct chain IDs and output roots. No chain is omitted, duplicated, or misidentified.

#### Mitigations

- `initialize()` enforces `hashSuperRootProof(decode(extraData.superRootProof)) == rootClaim()`.
  An incorrect preimage cannot produce a matching hash.
- The ZK program independently verifies that the output roots in the preimage match the actual
  chain states (see [iSZKVM-002](../../super-zk-fault-proof-vm.md#iszkvm-002-super-root-preimage-must-commit-to-all-chain-outputs)).
- The ZK program (identified by `absolutePrestate`) is compiled to produce and verify proofs over
  preimages with chains sorted in strictly ascending order by `chainId`. An unsorted preimage
  produces a different hash and therefore a different `rootClaim`; no valid proof can be generated
  for it, so verification will always fail for such proposals.

### aSZKG-009: Chain Set Is Stable During the Prove Window

The interop set (the set of chains committed to by a super root) does not change between game
creation and proof submission.

#### Mitigations

- The `SuperRootProof` preimage is immutable once embedded in `extraData` at creation time.
- The `absolutePrestate` encodes which chain set the ZK program was compiled for. A chain set
  change requires a new program and a new `absolutePrestate`, gated by governance.

## Invariants

### iSZKG-001: A Valid Proof Always Wins

If a valid ZK proof is submitted before the current deadline, the game MUST resolve as
`DEFENDER_WINS` (assuming a valid parent chain).

#### Impact

**Severity: High**

A violation lets a correct proposer be cheated out of their bond, which breaks the economic
security of the game and the correctness of withdrawal finalization.

### iSZKG-002: A Game Without a Valid Proof and With a Challenger Resolves as CHALLENGER_WINS

If a game was challenged and the prove deadline expires without a valid proof, `resolve()` MUST
produce `CHALLENGER_WINS`.

#### Impact

**Severity: High**

A violation would allow invalid super roots to be finalized on L1 and bridge funds to be stolen.

### iSZKG-003: Bond Safety via DelayedWETH

All bonds MUST be deposited into and withdrawn from `DelayedWETH`. The game contract MUST NOT
hold raw ETH bonds.

#### Impact

**Severity: Critical**

Raw ETH bonds held directly in a game clone cannot be recovered — each clone is an immutable
proxy instance with no upgrade path, so any ETH stuck in it is permanently lost. This also
bypasses the Guardian's ability to freeze funds post-resolution.

### iSZKG-004: Permissionless Participation

`create()`, `challenge()`, `prove()`, and `resolve()` MUST be callable by any address. No
`AccessManager` or allowlist MAY gate these functions.

#### Impact

**Severity: High**

Permissioned access would reduce censorship resistance and deviate from the Stage 1 security
model.

### iSZKG-005: Parent Invalidity Propagates to Children

If a parent game resolves as `CHALLENGER_WINS`, all child games MUST also resolve as
`CHALLENGER_WINS`, regardless of whether a valid proof was submitted for the child.

#### Impact

**Severity: High**

Failure to propagate would allow a chain of games to finalize a super root that descends from an
invalid state. Funds that do not exist on L2 could be withdrawn.

### iSZKG-006: closeGame Reverts When Paused

`closeGame()` MUST revert if `AnchorStateRegistry` reports the system as paused.

#### Impact

**Severity: High**

Allowing bond distribution while paused would bypass the Guardian's ability to freeze funds
during an active security incident.

### iSZKG-007: Only Finalized Games Can Close

`closeGame()` MUST revert unless `AnchorStateRegistry.isGameFinalized(this)` returns `true`.

#### Impact

**Severity: High**

Closing before the finality delay would remove the Guardian's window to blacklist or pause the
game before funds are distributed.

### iSZKG-008: Blacklisted and Retired Games Enter REFUND Mode

If a game is blacklisted or retired, `closeGame()` MUST enter REFUND mode: bonds are returned to
the original depositors rather than distributed to winners.

#### Impact

**Severity: High**

Failure to refund would cause honest participants to lose bonds when the Guardian must invalidate
a game for safety reasons unrelated to the game's correctness.

### iSZKG-009: Child Resolution Requires Resolved Parent

`resolve()` MUST revert if the parent game's `status == GameStatus.IN_PROGRESS`. The resolution
dependency chain MUST be honored in topological order.

#### Impact

**Severity: Critical**

Without this, iSZKG-005 cannot hold. A child could resolve as `DEFENDER_WINS` and finalize a
withdrawal before the parent is invalidated. Funds could be withdrawn against a super root that
descends from an invalid state.

### iSZKG-010: At Most One Challenge Per Game

`challenge()` MUST revert if `claimData.status != ProposalStatus.Unchallenged`.

#### Impact

**Severity: High**

A second challenge could reset the prove deadline and give challengers unbounded time to delay
resolution, overwrite the original challenger's address and steal their bond credit, or produce
double the bond liability in `DelayedWETH` with only one `challengerBond` deposited.

### iSZKG-011: Bond Conservation

For any resolved game, the sum of all bonds distributed plus any amount sent to `address(0)` MUST
equal `initBond + challengerBond` (or `initBond` alone if the game was never challenged). No value
may be created from nothing or permanently locked beyond the defined burn path.

#### Impact

**Severity: High**

A violation means either fund loss for participants (bonds locked forever with no recipient) or an
exploitable source of unbacked ETH withdrawals from `DelayedWETH`.

### iSZKG-012: Monotonic State Progression

`claimData.status` MUST only advance forward through the `ProposalStatus` state machine. No
transition from a later state back to an earlier one is permitted. `status` (`GameStatus`) MUST
only transition from `IN_PROGRESS` to a terminal state (`CHALLENGER_WINS` or `DEFENDER_WINS`).

#### Impact

**Severity: High**

State regression would corrupt deadline logic and bond accounting. Functions that use status as a
guard could be re-entered in unexpected ways if the state can regress.

### iSZKG-013: rootClaimByChainId Consistency

`rootClaimByChainId(_chainId)` MUST return the output root for `_chainId` as committed to in the
`SuperRootProof` preimage of `rootClaim`. If `_chainId` is not present in the preimage, the
function MUST revert with `UnknownChainId`.

#### Impact

**Severity: High**

An inconsistency between what `rootClaimByChainId` returns and what the super root actually
commits to would allow the Portal to finalize withdrawals against an output root that was never
proven, and allow bridge funds to be stolen.

### iSZKG-014: rootClaim Matches SuperRootProof Preimage

`hashSuperRootProof(decode(extraData.superRootProof))` MUST equal `rootClaim()` at all times
after `initialize()`. This is enforced at initialization and cannot change thereafter (both values
are immutable).

#### Impact

**Severity: Critical**

A mismatch would mean `rootClaimByChainId` is decoding a preimage that does not correspond to the
proven claim. Arbitrary output roots could be returned to the Portal regardless of what was
actually proven.
