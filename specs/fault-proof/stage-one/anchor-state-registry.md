# Anchor State Registry

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
  - [Perspective](#perspective)
- [Definitions](#definitions)
  - [Dispute game](#dispute-game)
  - [Likely valid game](#likely-valid-game)
  - [Finalized game](#finalized-game)
  - [Dispute game finality delay](#dispute-game-finality-delay)
  - [Valid game](#valid-game)
  - [Blacklisted game](#blacklisted-game)
  - [Retired valid game](#retired-valid-game)
  - [Validity timestamp](#validity-timestamp)
  - [Anchor state](#anchor-state)
  - [Anchor game](#anchor-game)
  - [Withdrawal](#withdrawal)
  - [Authorized input](#authorized-input)
- [Assumptions](#assumptions)
  - [aFDG-001: Fault dispute games correctly report their properties](#afdg-001-fault-dispute-games-correctly-report-their-properties)
    - [Mitigations](#mitigations)
  - [aFDG-002: Fault dispute games with correct claims resolve correctly at some regular rate](#afdg-002-fault-dispute-games-with-correct-claims-resolve-correctly-at-some-regular-rate)
    - [Mitigations](#mitigations-1)
  - [aDGF-001: Dispute game factory correctly identifies the games it created](#adgf-001-dispute-game-factory-correctly-identifies-the-games-it-created)
  - [Mitigations](#mitigations-2)
  - [aDGF-002: Games created by the DisputeGameFactory will be monitored](#adgf-002-games-created-by-the-disputegamefactory-will-be-monitored)
    - [Mitigations](#mitigations-3)
  - [aASR-001: Incorrectly resolving games will be blacklisted within the dispute game finality delay period](#aasr-001-incorrectly-resolving-games-will-be-blacklisted-within-the-dispute-game-finality-delay-period)
    - [Mitigations](#mitigations-4)
  - [aASR-002: Larger bugs in dispute game mechanics will be expired within the dispute game finality delay period](#aasr-002-larger-bugs-in-dispute-game-mechanics-will-be-expired-within-the-dispute-game-finality-delay-period)
    - [Mitigations](#mitigations-5)
  - [aASR-003: The AnchorStateRegistry will be correctly initialized at deployment](#aasr-003-the-anchorstateregistry-will-be-correctly-initialized-at-deployment)
    - [Mitigations](#mitigations-6)
  - [aSC-001: SuperchainConfig correctly reports its guardian address](#asc-001-superchainconfig-correctly-reports-its-guardian-address)
    - [Mitigations](#mitigations-7)
- [Top-Level Invariants](#top-level-invariants)
- [System Invariants](#system-invariants)
  - [iASR-001: Claims about L2 state are validated before they're used by dependents.](#iasr-001-claims-about-l2-state-are-validated-before-theyre-used-by-dependents)
- [Component Invariants](#component-invariants)
  - [iASR-000: Only "truly" **valid games** will be represented as **valid games**.](#iasr-000-only-truly-valid-games-will-be-represented-as-valid-games)
    - [Impact](#impact)
    - [Dependencies](#dependencies)
- [Function-Level Invariants](#function-level-invariants)
  - [`constructor`](#constructor)
  - [`initialize`](#initialize)
  - [`getLatestValidGame`](#getlatestvalidgame)
  - [`updateAnchorGame`](#updateanchorgame)
  - [`getAnchorGame`](#getanchorgame)
  - [`registerLikelyValidGame`](#registerlikelyvalidgame)
  - [`tryUpdateAnchorGame`](#tryupdateanchorgame)
  - [`isGameBlacklisted`](#isgameblacklisted)
  - [`isGameLikelyValid`](#isgamelikelyvalid)
  - [`isGameFinalized`](#isgamefinalized)
  - [`isGameValid`](#isgamevalid)
  - [`setRespectedGameType`](#setrespectedgametype)
  - [`retireAllExistingGames`](#retireallexistinggames)
  - [`setGameBlacklisted`](#setgameblacklisted)
  - [`getGameFinalityDelay`](#getgamefinalitydelay)
- [Implementation](#implementation)
  - [`constructor`](#constructor-1)
  - [`initialize`](#initialize-1)
  - [`anchors` / `getLatestAnchorState`](#anchors--getlatestanchorstate)
  - [`registerMaybeValidGame`](#registermaybevalidgame)
  - [`updateLatestValidGame`](#updatelatestvalidgame)
  - [`tryUpdateLatestValidGame`](#tryupdatelatestvalidgame)
  - [`setGameBlacklisted`](#setgameblacklisted-1)
  - [`setRespectedGameType`](#setrespectedgametype-1)
  - [`isGameInvalid`](#isgameinvalid)
  - [`isGameValid`](#isgamevalid-1)
  - [`disputeGameFinalityDelaySeconds`](#disputegamefinalitydelayseconds)
  - [`disputeGameFactory`](#disputegamefactory)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

### Perspective

The whole point of the fault proof system is to create correctly resolving games whose claims we can depend on to
finalize withdrawals (or other L2-to-L1 dependents). Indeed, everything about the system, from the contract mechanics to
bond incentives, is engineered to provide complete confidence that the outcome of a resolved game is correct. Yet, there
are corner cases where the resolved game rebukes its platonic, game-theoretic ideal, resolving incorrectly. The anchor
state registry appreciates this and affords games and their dependents probabalistic validity by enforcing a game
finality delay, and adding additional dependencies like blacklisting and game retirement. These concessions improve the
confidence in resolved games, and calcify the assumptions upon which withdrawals and other dependents rest.

<!--
The anchor state registry supports the fault proof system in two critical ways:
- It manages the gap between the ideal, game theoretic claim
- It gives new dispute games a starting point.

The motivation for the fault proof system is to enable the operation of things on L1 that depend on state in L2, and a perfect fault proof system arrives at truth via dispute games.

The fault proof system exists to facilitate the arrival at truth of l2 state claims. With true claims, we can enable the operation of things that depend on true claims.

The fault proof system exists to ensure the validity of L2 state claims, which enables the operation of components dependent on true claims.

The Anchor State Registry (ASR) is the central authority within the fault proof system for managing and exposing the validity of dispute games and anchor states. It serves multiple critical roles:

- Facilitating withdrawals via valid state proofs.
- Providing the latest valid anchor states for initializing or resolving dispute games.
- Acting as a safeguard in incident response by invalidating or expiring games.

Multiple contracts in the fault proof system have critical dependencies on things outside them:

- The Portal needs to know whether a withdrawal's proof is based on a **valid** dispute game.
- A new dispute game needs to initialize with the **latest valid anchor state**.
- An existing dispute game needs to know whether it is **invalid**, so it can refund its bonds.

The AnchorStateRegistry is these contracts' source of truth, managing and exposing dispute game and anchor state
validity to moderate dispute games and withdrawals.

Furthermore, the AnchorStateRegistry is a crucial player in incident response. It can invalidate dispute games, thereby
invalidating withdrawals and dispute games founded on an incorrect root claim. -->

## Definitions

### Dispute game

> See [Fault Dispute Game](fault-dispute-game.md)

A dispute game is a contract that resolves an L2 state claim.

### Likely valid game

A **likely valid game** is a dispute game that correctly resolved in favor of the defender. However, the system concedes
a possibility that it's not correct, and so it's not yet ready to be used as a **valid game** by dependents. A likely
valid game meets the following conditions:

- Game was created by the dispute game factory.
- Game is not **blacklisted**.
- Game was created while it was the respected game type.
- Game status is not `CHALLENGER_WINS`.
- Game was created after the **validity timestamp**.

### Finalized game

A finalized dispute game is a game that has been resolved in favor of either the challenger or defender. Furthermore, it
has passed the **dispute game finality delay** and can be used by dependents. A finalized game meets the following
conditions:

- Game status is `CHALLENGER_WINS` or `DEFENDER_WINS`.
- Game `resolvedAt` timestamp is not zero.
- Game `resolvedAt` timestamp is more than `dispute game finality delay` seconds ago.

### Dispute game finality delay

> Also known as "air gap."

The dispute game finality delay is the period of time between a dispute game
resolving and a dispute game becoming finalized. It's set via **authorized input**.

### Valid game

A game is a **valid game** if it, among other qualitifcations, has resolved in favor of the defender and has also matured past
the finality delay. In other words, it meets the conditions of both a **likely valid game** and a **finalized game**.

### Blacklisted game

A blacklisted game is a game that has been set as blacklisted via **authorized action**. It must not be considered
valid, and must not be used for finalizing withdrawals or any other dependent L2-to-L1 action.

### Retired valid game

A retired valid game is a dispute game whose `createdAt` timestamp is older than the **validity timestamp**.

### Validity timestamp

The validity timestamp is a timestamp internal to the contract that partly determines game validity and can only be
adjusted via **authorized input**.

### Anchor state

> See [Fault Dispute Game -> Anchor State](fault-dispute-game.md#anchor-state).

An anchor state is a state root from L2.

### Anchor game

An **anchor game** is a game upon which other games should build. It was a **valid game** when it was set, but may have
since been retired.

### Withdrawal

> See [Withdrawals](../../protocol/withdrawals.md).

A withdrawal is a cross-chain transaction initiated on L2, and finalized on L1.

### Authorized input

An authorized input is an input for which there is social consensus, i.e. coming from governance.

## Assumptions

> **NOTE:** Assumptions are utilized by specific invariants and do not apply globally. Invariants typically only rely on
> a subset of the following assumptions. Different invariants may rely on different assumptions. Refer to individual
> invariants for their dependencies.

### aFDG-001: Fault dispute games correctly report their properties

We assume that a fault dispute game will correctly report the following properties:

- its game type.
- whether its game type was the respected game type when created (also assumes this is set once and never changes).
- the l2BlockNumber of its root claim.
- its `createdAt` timestamp.
- its `resolvedAt` timestamp.

#### Mitigations

- Existing audit on `FaultDisputeGame`. Note: Existing audit does not yet cover the second property above (that a game correctly reports whether its game type was the respected game type when created).
- Integration testing.

### aFDG-002: Fault dispute games with correct claims resolve correctly at some regular rate

We assume that fault dispute games will regularly resolve in favor of the defender correctly. While the system
can handle games that resolve in favor of the challenger, as well as incorrect resolutions, there must be other games that resolve correctly to maintain the system's integrity.

#### Mitigations

- Existing incentives in fault proof system design.

### aDGF-001: Dispute game factory correctly identifies the games it created

We assume that DisputeGameFactory will correctly identify whether it created a game (i.e. whether the game is "factory-registered").

### Mitigations

- Existing audit on the `DisputeGameFactory`.
- Integration testing.

### aDGF-002: Games created by the DisputeGameFactory will be monitored

We assume that games created by the DisputeGameFactory will be monitored for incorrect resolution.

#### Mitigations

- Stakeholder incentives.

### aASR-001: Incorrectly resolving games will be blacklisted within the dispute game finality delay period

We assume that games that resolve incorrectly will be blacklisted via **authorized action** within the dispute game finality delay period. This further depends on [aDGF-002](#adgf-002-games-created-by-the-disputegamefactory-will-be-monitored).

#### Mitigations

- Stakeholder incentives / processes.

### aASR-002: Larger bugs in dispute game mechanics will be expired within the dispute game finality delay period

We assume that a larger bug affecting many games will be noticed via monitoring ([aDGF-002](#adgf-002-games-created-by-the-disputegamefactory-will-be-monitored)) and will be expired within the dispute game finality delay period.

#### Mitigations

- Stakeholder incentives / processes.

### aASR-003: The AnchorStateRegistry will be correctly initialized at deployment

We assume that the AnchorStateRegistry will be correctly initialized at deployment, including:

- Address of initial anchor game.
- Address of `DisputeGameFactory`.
- An appropriate `DISPUTE_GAME_FINALITY_DELAY`.
- Address of `SuperchainConfig`.

#### Mitigations

- Verify the configured values in the deployment script.

### aSC-001: SuperchainConfig correctly reports its guardian address

We assume the SuperchainConfig contract correctly returns its guardian address.

#### Mitigations

- Existing audit on the `SuperchainConfig`.
- Integration testing.

## Top-Level Invariants

- When asked for a **valid game**, the contract will only serve games that truly resolved correctly to its dependents.
- The latest anchor game must never serve the output root of a blacklisted game.
- The latest anchor game must be recent enough so that the game doesn't break (run out of memory) in op-challenger.
- The validity timestamp must start at zero.

## System Invariants

### iASR-001: Claims about L2 state are validated before they're used by dependents.

## Component Invariants

### iASR-000: Only "truly" **valid games** will be represented as **valid games**.

When asked for a **valid game** by its dependents, the contract will only serve **valid games** that "truly" resolved in
favor of defender.

#### Impact

**Severity: High**

If this invariant is broken, an L2 state that's different from what dependents can be tricked into finalizing withdrawals based on incorrect state roots.

#### Dependencies

[FaultDisputeGame](./fault-dispute-game.md) depends on this contract for an **anchor game** against which to
resolve its claim. The contract assumes this **anchor game**'s state root is correct, and that it's recent enough that
proposer software doesn't run out of memory.

[OptimismPortal](./optimism-portal.md) depends on this contract to correctly report game validity as the basis for
proving and finalizing withdrawals.

- Can this dispute game can be used to prove a withdrawal? (Is the dispute game a **likely valid game**?)
- Can this dispute game can be used to finalize a withdrawal? (Is the dispute game a **valid game**?)

## Function-Level Invariants

### `constructor`

The constructor must disable the initializer on the implementation contract.

### `initialize`

- Initial anchor state must be an **authorized input**.
- Dispute game factory must be an **authorized input**.
- `dispute game finality delay` must be an **authorized input**.
- Superchain config must be an **authorized input**.

### `getLatestValidGame`

Returns **latest valid game**, or reverts if there is no **latest valid game**.

### `updateAnchorGame`

- Game must be a **valid game**.
- Game's block number must be higher than current **latest anchor game**.
- This function is the ONLY way to update the **latest anchor game** (after initialization).

### `getAnchorGame`

Returns the **latest anchor game**.

- Must revert if the **latest anchor game** is blacklisted.
- Must maintain the property that the timestamp of the game is not too old.
  - TODO: How old is too old?

### `registerLikelyValidGame`

Stores the address of a **maybe valid game** in an array as a candidate for `latestValidGame`.

- Callable only by a **maybe valid game**.
- Calling game must only register itself (and not some other game).
  - TODO: determine any invariants around registry ordering.

### `tryUpdateAnchorGame`

Try to update **latest valid game** using registry of **maybe valid games**.

- Callable by anyone.
- Find the latest (comparing on l2BlockNumber) valid game you can find in the register within a fixed amount of gas.
  - Fixed gas amount ensures that this function does not get more expensive to call as time goes on.
- Use this as input to `update latest valid game`.

### `isGameBlacklisted`

Returns whether the game is a **blacklisted game**.

### `isGameLikelyValid`

Returns whether the game is a **likely valid game**.

### `isGameFinalized`

Returns whether the game is a **finalized game**.

### `isGameValid`

Returns whether the game is a **valid game**.

Assumes

### `setRespectedGameType`

- Must be **authorized** by guardian role.

### `retireAllExistingGames`

Retires all games that exist.

- Must be **authorized** by guardian role.

### `setGameBlacklisted`

Blacklists a game.

- Must be **authorized** by guardian role.

### `getGameFinalityDelay`

Returns **authorized** finality delay duration in seconds. No external dependents; public getter for convenience.

## Implementation

### `constructor`

### `initialize`

### `anchors` / `getLatestAnchorState`

### `registerMaybeValidGame`

### `updateLatestValidGame`

### `tryUpdateLatestValidGame`

### `setGameBlacklisted`

### `setRespectedGameType`

### `isGameInvalid`

### `isGameValid`

### `disputeGameFinalityDelaySeconds`

### `disputeGameFactory`
