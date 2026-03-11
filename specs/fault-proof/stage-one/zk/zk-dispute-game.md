# ZK Dispute Game

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
  - [ZKDisputeGame](#zkdisputegame)
  - [MCP Clone](#mcp-clone)
  - [Game Args (CWIA)](#game-args-cwia)
  - [L2 Sequence Number](#l2-sequence-number)
  - [Parent Game](#parent-game)
  - [Challenge Deadline](#challenge-deadline)
  - [Prove Deadline](#prove-deadline)
  - [Absolute Prestate](#absolute-prestate)
  - [Game Over](#game-over)
- [Contracts Involved](#contracts-involved)
- [Actors](#actors)
- [Game Args Layout](#game-args-layout)
- [OPCM Integration](#opcm-integration)
  - [ZKDisputeGameConfig](#zkdisputegameconfig)
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

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The `ZKDisputeGame` is a dispute game that resolves disputes in a single round using ZK
(zero-knowledge) proofs, registered as game type `10`. It integrates into the same OP Stack
dispute infrastructure — `DisputeGameFactory`, `AnchorStateRegistry`, `DelayedWETH`, and
`OPContractsManager`.

A proposer posts an output root with a bond. Anyone can challenge it by depositing a challenger
bond. If no challenge is submitted before the challenge window expires, the proposer wins by
default. If a challenge is submitted, there are two possible outcomes: either a prover submits a
valid ZK proof to defend the claim and the proposer wins, or the proving window expires without a
valid proof and the challenger wins. Resolution is permissionless once the game is over and the
parent game is resolved.

The proving system is accessed through the generic [`IZKVerifier`](zk-interface.md) interface.
The first supported backend is SP1 (PLONK) by Succinct. See [ZK Fault Proof VM](../../zk-fault-proof-vm.md)
for details on the off-chain proving component.

For the full game lifecycle and bond accounting see [Game Mechanics](game-mechanics.md).

## Definitions

### ZKDisputeGame

The smart contract implementing the single-round ZK dispute protocol. Each game instance is a
lightweight [MCP clone](#mcp-clone) of a shared implementation contract, deployed by
`DisputeGameFactory`.

### MCP Clone

A minimal proxy clone (ERC-1167) created by `DisputeGameFactory` that shares the `ZKDisputeGame`
implementation bytecode but has its own per-chain configuration appended as immutable constructor
arguments via the Clones-with-Immutable-Args (CWIA) pattern.

### Game Args (CWIA)

The per-chain configuration bytes appended to each MCP clone by `DisputeGameFactory`. Enable a
single implementation contract to serve every chain. See [Game Args Layout](#game-args-layout)
for the full field breakdown.

### L2 Sequence Number

The L2 block number asserted by a game's root claim. Used to validate parent–child ordering and
to verify that a parent's proven state falls within or above the anchor state.

### Parent Game

A previously created `ZKDisputeGame` whose proven output root serves as the starting state for a
new game's ZK proof. A game with `parentIndex == type(uint32).max` starts from the anchor state
directly.

### Challenge Deadline

The timestamp after which a game can no longer be challenged. Computed as
`createdAt + maxChallengeDuration`.

### Prove Deadline

The timestamp after which a challenged game can no longer receive a proof submission. Set to
`block.timestamp + maxProveDuration` when `challenge()` is called, resetting the prior challenge
deadline.

### Absolute Prestate

A `bytes32` value that uniquely identifies the ZK program version being proven. It serves as the
program identity passed to `IZKVerifier.verify()` and is injected into each game instance via the
CWIA game args. See [Absolute Prestate](../../zk-fault-proof-vm.md#absolute-prestate) for details.

### Game Over

The condition under which a game can be resolved. `gameOver()` returns `true` when:

- `status` is `UnchallengedAndValidProofProvided` or `ChallengedAndValidProofProvided`, or
- The current deadline has expired.

## Contracts Involved

| Contract                           | Role                                                                                                                                |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **ZKDisputeGame** (clones)         | Per-proposal game instance. Runs the challenge → prove → resolve lifecycle and tracks bond accounting.                              |
| **ZKDisputeGame** (implementation) | Shared bytecode base for MCP clones. Deployed and upgraded by OPCM.                                                                 |
| **DisputeGameFactory**             | Creates MCP clones via `create(...)`. Appends per-chain `gameArgs` (CWIA).                                                          |
| **AnchorStateRegistry**            | Source of truth for finalization, anchor state, respected game type, and blacklisting. Enforces pause checks.                       |
| **DelayedWETH**                    | Bond custody with a deposit → unlock → withdraw lifecycle. Provides a time window for the Guardian to freeze funds post-resolution. |
| **IZKVerifier**                    | Generic verifier interface. The concrete deployment for the initial release uses Succinct's PLONK verifier.                         |

## Actors

| Actor                       | Role                                                                                                                        |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **Proposer**                | Fully permissionless. Creates games via `DisputeGameFactory.create()` with the required `initBond`.                         |
| **Challenger**              | Fully permissionless. Disputes a proposal by calling `challenge()` and depositing `challengerBond`.                         |
| **Prover**                  | Fully permissionless. Submits a valid ZK proof via `prove(proofBytes)`. May be the same address as the proposer.            |
| **Guardian**                | Pauses the system, blacklists games, sets the respected game type, and retires old games via `updateRetirementTimestamp()`. |
| **OPCM / ProxyAdmin Owner** | Deploys implementations, configures game types in the factory, and manages `absolutePrestate` and verifier versions.        |

## Game Args Layout

The following fields are packed into `gameArgs` in order:

| Field                  | Type       | Description                                                            |
| ---------------------- | ---------- | ---------------------------------------------------------------------- |
| `absolutePrestate`     | `bytes32`  | ZK program identity (e.g., SP1 verification key)                       |
| `verifier`             | `address`  | Address of the `IZKVerifier` contract                                  |
| `maxChallengeDuration` | `Duration` | Time window for challenges after game creation                         |
| `maxProveDuration`     | `Duration` | Time window for proof submission after a challenge                     |
| `challengerBond`       | `uint256`  | Bond required to challenge a proposal                                  |
| `anchorStateRegistry`  | `address`  | Address of `AnchorStateRegistry`                                       |
| `weth`                 | `address`  | Address of per-chain `DelayedWETH`                                     |
| `l2ChainId`            | `uint256`  | L2 chain identifier, sourced from `SystemConfig`                       |

`anchorStateRegistry`, `weth`, and `l2ChainId` are injected by `OPContractManager._makeGameArgs()`
directly from the chain's existing deployment.

## OPCM Integration

`ZKDisputeGame` integrates into OPCM v2 as game type `10` (`ZK_GAME_TYPE`) through the existing
`DisputeGameConfig`, reusing the same pattern as Cannon and Permissioned Cannon.

Three additions are required:

1. `ZKDisputeGame` is deployed once via the `DeployImplementations` script and tracked in
   `OPContractsManagerContainer.Implementations` alongside existing fault game implementations.
2. A `ZKDisputeGameConfig` struct carries the per-chain parameters that the caller provides.
   OPCM's `_makeGameArgs()` decodes it, injects the chain-specific values it already knows,
   and packs the final CWIA bytes for the factory.
3. `ZK_GAME_TYPE` is added to the `validGameTypes` array in `_assertValidFullConfig()`.

### ZKDisputeGameConfig

```solidity
struct ZKDisputeGameConfig {
    Claim absolutePrestate;
    address verifier;
    Duration maxChallengeDuration;
    Duration maxProveDuration;
    uint256 challengerBond;
}
```

```solidity
if (_gcfg.gameType.raw() == GameTypes.ZK_GAME_TYPE.raw()) {
    ZKDisputeGameConfig memory cfg = abi.decode(_gcfg.gameArgs, (ZKDisputeGameConfig));
    return abi.encodePacked(
        cfg.absolutePrestate,
        cfg.verifier,
        cfg.maxChallengeDuration,
        cfg.maxProveDuration,
        cfg.challengerBond,
        address(_anchorStateRegistry),
        address(_delayedWETH),
        _l2ChainId
    );
}
```

## Assumptions

### aZKG-001: ZK Verifier Soundness

The `IZKVerifier` implementation is sound: it is computationally infeasible to produce a proof
that passes `verify()` for an incorrect state transition.

#### Mitigations

- The PLONK verifier for SP1 is independently audited.
- The verifier address comes from `gameArgs`, managed by OPCM. Governance controls upgrades.
- The `IZKVerifier` interface intentionally decouples the game from any specific proving system,
  enabling a verifier swap without redeploying the game implementation.

### aZKG-002: Absolute Prestate Uniquely Identifies the ZK Program

The `absolutePrestate` value uniquely identifies the ZK program version. Two different programs
MUST NOT share the same `absolutePrestate`.

#### Mitigations

- For SP1, `absolutePrestate` corresponds to the program's verification key, which is derived from
  the program binary and circuit structure.
- OPCM manages `absolutePrestate` per chain; program updates require a corresponding
  `absolutePrestate` update via governance.

### aZKG-003: Parent Chaining Preserves Correctness

A chain of `ZKDisputeGame` instances resolving as `DEFENDER_WINS` implies that the final
`rootClaim` is a valid output root, provided the initial parent started from a known-good anchor
state.

#### Mitigations

- Each proof commits to `startingOutputRoot` (the parent's claim) as a public value,
  cryptographically linking consecutive games.
- [Parent validation](game-mechanics.md#parent-validation) at creation time prevents games from
  chaining off blacklisted, retired, or `CHALLENGER_WINS` parents.
- If a parent is blacklisted or retired after child games have been created, the Guardian MUST
  individually blacklist or retire those child games to place them in REFUND mode.

### aZKG-004: Bonds Are Economically Rational

The `initBond`, `challengerBond`, `maxChallengeDuration`, and `maxProveDuration` values are set
such that honest participation is economically rational and griefing is costly.

#### Mitigations

- All bond and duration parameters are in `gameArgs` and can be tuned per chain by OPCM without
  redeploying the implementation.
- Benchmark proving costs and document standard values for common chain configurations,
  analogous to how fault proof bonds are standardized today.
- Bonds too low invite spam; bonds too high discourage honest participation. Durations must be
  long enough to allow proof generation but short enough to preserve withdrawal latency benefits.

### aZKG-005: Guardian Acts Honestly and Timely

The Guardian is trusted to pause the system, blacklist invalid games, and retire superseded game
types before fraudulent games achieve Valid Claims.

#### Mitigations

- The `DISPUTE_GAME_FINALITY_DELAY_SECONDS` airgap between resolution and `closeGame` provides
  the Guardian a window to act.
- `DelayedWETH` provides an additional window after `closeGame` to freeze funds.

### aZKG-006: Anchor State Advances Slowly Relative to Proposal Frequency

Under normal operation, the anchor state advances on a timescale (12+ hours minimum) that is much
larger than typical proposal frequency (e.g., 1 hour), making orphan risk from parent validation
negligible.

#### Mitigations

- A rational proposer would never use a parent whose `l2SequenceNumber` is below the anchor, as
  it unnecessarily increases the proving range.
- [Parent validation](game-mechanics.md#parent-validation) requires the parent's
  `l2SequenceNumber` to be at or above the anchor state, preventing chains from building on stale
  starting points.

## Invariants

### iZKG-001: A Valid Proof Always Wins

If a valid ZK proof is submitted before the current deadline, the game MUST resolve as
`DEFENDER_WINS` (assuming a valid parent chain).

#### Impact

**Severity: Critical**

A violation lets a correct proposer be cheated out of their bond, breaking the economic security
of the game and the correctness of withdrawal finalization.

### iZKG-002: A Game Without a Valid Proof and With a Challenger Resolves as CHALLENGER_WINS

If a game was challenged and the prove deadline expires without a valid proof, `resolve()` MUST
produce `CHALLENGER_WINS`.

#### Impact

**Severity: Critical**

A violation would allow invalid output roots to be finalized on L1, enabling theft of funds from
the bridge.

### iZKG-003: Bond Safety via DelayedWETH

All bonds MUST be deposited into and withdrawn from `DelayedWETH`. The game contract MUST NOT
hold raw ETH bonds.

#### Impact

**Severity: High**

Raw ETH bonds would bypass the Guardian's ability to freeze funds post-resolution, removing the
last line of defense against exploitation of a newly discovered bug.

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

**Severity: Critical**

Failure to propagate would allow a chain of games to finalize an output root that descends from
an invalid state, enabling withdrawal of funds that do not exist on L2.

### iZKG-006: closeGame Reverts When Paused

`closeGame()` MUST revert if `AnchorStateRegistry` reports the system as paused.

#### Impact

**Severity: High**

Allowing bond distribution while paused would bypass the Guardian's ability to freeze funds
during an active security incident.

### iZKG-007: Only Finalized Games Can Close

`closeGame()` MUST revert unless
`block.timestamp - resolvedAt > DISPUTE_GAME_FINALITY_DELAY_SECONDS`.

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
