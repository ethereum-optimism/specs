# Anchor State Registry

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

**Table of Contents**

- [Anchor State Registry](#anchor-state-registry)
  - [Overview](#overview)
    - [Perspective](#perspective)
  - [Definitions](#definitions)
    - [Dispute game](#dispute-game)
    - [Likely valid game](#likely-valid-game)
    - [Finalized game](#finalized-game)
    - [Dispute game finality delay](#dispute-game-finality-delay)
    - [Valid game](#valid-game)
    - [Blacklisted game](#blacklisted-game)
    - [Invalid game](#invalid-game)
    - [Retired game](#retired-game)
    - [Acceptable invalid anchor game](#acceptable-invalid-anchor-game)
    - [Game retirement timestamp](#game-retirement-timestamp)
    - [Anchor state](#anchor-state)
    - [Anchor game](#anchor-game)
    - [Withdrawal](#withdrawal)
    - [Authorized input](#authorized-input)
  - [Assumptions](#assumptions)
    - [aFDG-001: Fault dispute games correctly report certain properties](#afdg-001-fault-dispute-games-correctly-report-certain-properties)
      - [Mitigations](#mitigations)
    - [aFDG-002: Fault dispute games with correct claims resolve correctly at some regular rate](#afdg-002-fault-dispute-games-with-correct-claims-resolve-correctly-at-some-regular-rate)
      - [Mitigations](#mitigations-1)
    - [aDGF-001: Dispute game factory correctly identifies the games it created](#adgf-001-dispute-game-factory-correctly-identifies-the-games-it-created)
      - [Mitigations](#mitigations-2)
    - [aDGF-002: Games created by the DisputeGameFactory will be monitored](#adgf-002-games-created-by-the-disputegamefactory-will-be-monitored)
      - [Mitigations](#mitigations-3)
    - [aASR-001: Incorrectly resolving games will be blacklisted within the dispute game finality delay period](#aasr-001-incorrectly-resolving-games-will-be-blacklisted-within-the-dispute-game-finality-delay-period)
      - [Mitigations](#mitigations-4)
    - [aASR-002: If a larger dispute game bug is found, all games will be retired before the first incorrect game's dispute game finality delay period has passed](#aasr-002-if-a-larger-dispute-game-bug-is-found-all-games-will-be-retired-before-the-first-incorrect-games-dispute-game-finality-delay-period-has-passed)
      - [Mitigations](#mitigations-5)
    - [aASR-003: The AnchorStateRegistry will be correctly initialized at deployment](#aasr-003-the-anchorstateregistry-will-be-correctly-initialized-at-deployment)
      - [Mitigations](#mitigations-6)
    - [aSC-001: SuperchainConfig correctly reports its guardian address](#asc-001-superchainconfig-correctly-reports-its-guardian-address)
      - [Mitigations](#mitigations-7)
  - [System Invariants](#system-invariants)
    - [iASR-001: Invalid withdrawals can never be finalized](#iasr-001-invalid-withdrawals-can-never-be-finalized)
      - [Impact](#impact)
      - [Dependencies](#dependencies)
    - [iASR-002: Valid withdrawals can be finalized within some bounded amount of time](#iasr-002-valid-withdrawals-can-be-finalized-within-some-bounded-amount-of-time)
      - [Impact](#impact-1)
      - [Dependencies](#dependencies-1)
  - [Component Invariants](#component-invariants)
    - [iASR-003: Only "truly" **valid games** will be represented as **valid games**.](#iasr-003-only-truly-valid-games-will-be-represented-as-valid-games)
      - [Impact](#impact-2)
      - [Dependencies](#dependencies-2)
    - [iASR-004: The anchor game was created recently, within some bounded time period.](#iasr-004-the-anchor-game-was-created-recently-within-some-bounded-time-period)
      - [Impact](#impact-3)
      - [Dependencies](#dependencies-3)
    - [iASR-005: The anchor game is a game whose claim is correct.](#iasr-005-the-anchor-game-is-a-game-whose-claim-is-correct)
      - [Impact](#impact-4)
      - [Dependencies](#dependencies-4)
  - [Function-Level Invariants](#function-level-invariants)
  - [Implementation Spec](#implementation-spec)
    - [`constructor`](#constructor)
    - [`initialize`](#initialize)
    - [`getRecentValidGame`](#getrecentvalidgame)
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
- Game `createdAt` timestamp is less than the **game retirement timestamp**.

### Finalized game

A finalized dispute game is a game that has been resolved in favor of either the challenger or defender. Furthermore, it
has passed the **dispute game finality delay** and can be used by dependents. A finalized game meets the following
conditions:

- Game status is `CHALLENGER_WINS` or `DEFENDER_WINS`.
- Game `resolvedAt` timestamp is not zero.
- Game `resolvedAt` timestamp is more than `dispute game finality delay` seconds ago.

### Dispute game finality delay

> Also known as "air gap."

The dispute game finality delay is the period of time between a dispute game resolving and a dispute game becoming
finalized. It's set via **authorized input**.

### Valid game

A game is a **valid game** if it, among other qualifications, has resolved in favor of the defender and has also matured
past the finality delay. In other words, it meets the conditions of both a **likely valid game** and a **finalized
game**.

### Blacklisted game

A **blacklisted game** is a game that has been set as blacklisted via **authorized action**. It must not be considered
valid, and must not be used for finalizing withdrawals or any other dependent L2-to-L1 action.

### Invalid game

An **invalid game** is a game whose claim was false, or does not meet some other **likely valid game** condition.

### Retired game

A **retired game** is a game whose `createdAt` timestamp is older than the **game retirement timestamp**. A game that
gets retired is no longer considered valid.

### Acceptable invalid anchor game

An **acceptable invalid anchor game** is an **anchor game** that was a **valid game** when set and has been made
**invalid** via **game retirement**. It meets every other condition of validity and is still acceptable to use as the
**anchor game**. This is a special case that allows the system to continue functioning even if all games are retired.

### Game retirement timestamp

The game retirement timestamp determines **retired games** and can only be adjusted via **authorized input**.

### Anchor state

> See [Fault Dispute Game -> Anchor State](fault-dispute-game.md#anchor-state).

An anchor state is a state root from L2.

### Anchor game

An **anchor game** is a **valid game** or an **acceptable invalid anchor game** that can be used by dependents as a
starting point for new dispute games.

### Withdrawal

> See [Withdrawals](../../protocol/withdrawals.md).

A withdrawal is a cross-chain transaction initiated on L2, and finalized on L1.

### Authorized input

An authorized input is an input for which there is social consensus, i.e. coming from governance.

## Assumptions

> **NOTE:** Assumptions are utilized by specific invariants and do not apply globally. Invariants typically only rely on
> a subset of the following assumptions. Different invariants may rely on different assumptions. Refer to individual
> invariants for their dependencies.

### aFDG-001: Fault dispute games correctly report certain properties

We assume that a fault dispute game will correctly report the following properties:

- its game type.
- whether its game type was the respected game type when created (also assumes this is set once and never changes).
- the l2BlockNumber of its root claim.
- its `createdAt` timestamp.
- its `resolvedAt` timestamp.

#### Mitigations

- Existing audit on `FaultDisputeGame`. Note: Existing audit does not yet cover the second property above (that a game
  correctly reports whether its game type was the respected game type when created).
- Integration testing.

### aFDG-002: Fault dispute games with correct claims resolve correctly at some regular rate

We assume that fault dispute games will regularly resolve in favor of the defender correctly. While the system can
handle games that resolve in favor of the challenger, as well as incorrect resolutions, there must be other games that
resolve correctly to maintain the system's integrity.

#### Mitigations

- Existing incentives in fault proof system design.

### aDGF-001: Dispute game factory correctly identifies the games it created

We assume that `DisputeGameFactory` will correctly identify whether it created a game (i.e. whether the game is
"factory-registered").

#### Mitigations

- Existing audit on the `DisputeGameFactory`.
- Integration testing.

### aDGF-002: Games created by the DisputeGameFactory will be monitored

We assume that games created by the `DisputeGameFactory` will be monitored for incorrect resolution.

#### Mitigations

- Stakeholder incentives.

### aASR-001: Incorrectly resolving games will be blacklisted within the dispute game finality delay period

We assume that games that resolve incorrectly will be blacklisted via **authorized action** within the dispute game
finality delay period. This further depends on
[aDGF-002](#adgf-002-games-created-by-the-disputegamefactory-will-be-monitored).

TODO: is this true?

#### Mitigations

- Stakeholder incentives / processes.
- Incident response plan.

### aASR-002: If a larger dispute game bug is found, all games will be retired before the first incorrect game's dispute game finality delay period has passed

We assume that a larger bug affecting many games will be noticed via monitoring
([aDGF-002](#adgf-002-games-created-by-the-disputegamefactory-will-be-monitored)) and will be retired within the dispute
game finality delay period.

TODO: is this true?

#### Mitigations

- Stakeholder incentives / processes.
- Incident response plan.

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

## System Invariants

### iASR-001: Invalid withdrawals can never be finalized

#### Impact

**Severity: Critical**

If this invariant is broken, the system can finalize an invalid withdrawal, causing a loss of funds and a loss of confidence.

#### Dependencies

- [aASR-001](#aasr-001-incorrectly-resolving-games-will-be-blacklisted-within-the-dispute-game-finality-delay-period)
- [aASR-002](#aasr-002-if-a-larger-dispute-game-bug-is-found-all-games-will-be-retired-before-the-first-incorrect-games-dispute-game-finality-delay-period-has-passed)
- [aASR-003](#aasr-003-the-anchorstateregistry-will-be-correctly-initialized-at-deployment)
- [aSC-001](#asc-001-superchainconfig-correctly-reports-its-guardian-address)
- [aFDG-001](#afdg-001-fault-dispute-games-correctly-report-certain-properties)
- [aFDG-002](#afdg-002-fault-dispute-games-with-correct-claims-resolve-correctly-at-some-regular-rate)
- [aDGF-001](#adgf-001-dispute-game-factory-correctly-identifies-the-games-it-created)
- [aDGF-002](#adgf-002-games-created-by-the-disputegamefactory-will-be-monitored)

### iASR-002: Valid withdrawals can be finalized within some bounded amount of time

#### Impact

**Severity: Critical**

If this invariant is broken, withdrawals can be frozen for a long period of time, causing a critical liveness failure.

#### Dependencies

- [aFDG-001](#afdg-001-fault-dispute-games-correctly-report-certain-properties)
- [aDGF-001](#adgf-001-dispute-game-factory-correctly-identifies-the-games-it-created)
- [aDGF-002](#adgf-002-games-created-by-the-disputegamefactory-will-be-monitored)
- [aASR-001](#aasr-001-incorrectly-resolving-games-will-be-blacklisted-within-the-dispute-game-finality-delay-period)
- [aASR-002](#aasr-002-if-a-larger-dispute-game-bug-is-found-all-games-will-be-retired-before-the-first-incorrect-games-dispute-game-finality-delay-period-has-passed)
- [aASR-003](#aasr-003-the-anchorstateregistry-will-be-correctly-initialized-at-deployment)
- [aSC-001](#asc-001-superchainconfig-correctly-reports-its-guardian-address)

## Component Invariants

### iASR-003: Only "truly" **valid games** will be represented as **valid games**.

When asked for a **valid game** by its dependents, the AnchorStateRegistry will only serve **valid games** representing
correct L2 state claims.

#### Impact

**Severity: High**

If this invariant is broken, the L1 will have an inaccurate view of L2 state. The `OptimismPortal` can be tricked into
finalizing withdrawals based on incorrect state roots, causing loss of funds. Other dependents would also be affected.

#### Dependencies

- [aASR-001](#aasr-001-incorrectly-resolving-games-will-be-blacklisted-within-the-dispute-game-finality-delay-period)
- [aASR-002](#aasr-002-if-a-larger-dispute-game-bug-is-found-all-games-will-be-retired-before-the-first-incorrect-games-dispute-game-finality-delay-period-has-passed)
- [aASR-003](#aasr-003-the-anchorstateregistry-will-be-correctly-initialized-at-deployment)
- [aSC-001](#asc-001-superchainconfig-correctly-reports-its-guardian-address)

### iASR-004: The anchor game was created recently, within some bounded time period.

When asked for the **anchor game** by fault dispute games, the contract will only serve an **anchor game** that is
recent within some bounded period of time.

#### Impact

**Severity: High**

If this invariant is broken, proposer software can break (run out of memory), leading to dispute game liveness issues
and incorrect game resolution.

#### Dependencies

- [aASR-003](#aasr-003-the-anchorstateregistry-will-be-correctly-initialized-at-deployment)
- [aFDG-002](#afdg-002-fault-dispute-games-with-correct-claims-resolve-correctly-at-some-regular-rate)

### iASR-005: The anchor game is a game whose claim is correct.

When asked for the **anchor game** by fault dispute games, the contract will only serve an **anchor game** that is a
valid game or a valid-retired game.

#### Impact

**Severity: High**

If this invariant is broken, dispute games can be created with incorrect starting points, leading to games that can be
used to prove false claims. This would lead to an operational failure, requiring incident response. If incident response
doesn't occur, this could lead to loss of funds.

#### Dependencies

- TODO

## Function-Level Invariants

## Implementation Spec

### `constructor`

The constructor must disable the initializer on the implementation contract.

### `initialize`

- Initial anchor state must be an **authorized input**.
- Dispute game factory must be an **authorized input**.
- `dispute game finality delay` must be an **authorized input**.
- Superchain config must be an **authorized input**.

### `getRecentValidGame`

Returns **anchor game**. Reverts if the **anchor game** has been **retired** i.e. is an **acceptable invalid anchor
game**.

### `updateAnchorGame`

- Game must be a **valid game**.
- Game's block number must be higher than current **anchor game**.
- This function is the ONLY way to update the **anchor game** (after initialization).

### `getAnchorGame`

Returns the **anchor game**.

- Must return a **valid game** or an **acceptable invalid anchor game**.
- Must revert if the **anchor game** is a **blacklisted game**.
- Must maintain the property that the timestamp of the game is not too old.
  - TODO: How old is too old?

### `registerLikelyValidGame`

Register the address of a **likely valid game** as a candidate for **anchor game**.

- Callable only by a **likely valid game**.
- Calling game must only register itself (and not some other game).
  - TODO: determine any invariants around registry ordering.

### `tryUpdateAnchorGame`

Try to update **anchor game** using registry of **likely valid games**.

- Callable by anyone.
- Find the most recent (comparing on l2BlockNumber) valid game you can find in the register within a fixed amount of gas.
  - Fixed gas amount ensures that this function does not get more expensive to call as time goes on.
- Use this as input to `updateAnchorGame`.

### `isGameBlacklisted`

Returns whether the game is a **blacklisted game**.

### `isGameLikelyValid`

Returns whether the game is a **likely valid game**.

### `isGameFinalized`

Returns whether the game is a **finalized game**.

### `isGameValid`

Returns whether the game is a **valid game**.

### `setRespectedGameType`

- Must be **authorized** by guardian role.

### `retireAllExistingGames`

Retires all currently deployed games.

- Must set the **game retirement timestamp** to the current block timestamp.
- Must be **authorized** by guardian role.

### `setGameBlacklisted`

Blacklists a game.

- Must be **authorized** by guardian role.

### `getGameFinalityDelay`

Returns **authorized** finality delay duration in seconds. No external dependents; public getter for convenience.
