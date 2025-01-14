# AnchorStateRegistry

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
  - [Dispute Game](#dispute-game)
  - [Respected Game Type](#respected-game-type)
  - [Registered Game](#registered-game)
  - [Respected Game](#respected-game)
  - [Blacklisted Game](#blacklisted-game)
  - [Retired Game](#retired-game)
  - [Proper Game](#proper-game)
  - [Resolved Game](#resolved-game)
  - [Airgapped Game](#airgapped-game)
  - [Finalized Game](#finalized-game)
  - [Valid Claim](#valid-claim)
  - [Truly Valid Claim](#truly-valid-claim)
  - [Starting Anchor State](#starting-anchor-state)
  - [Anchor Game](#anchor-game)
- [Assumptions](#assumptions)
  - [aASR-001: Dispute Game contracts properly report important properties](#aasr-001-dispute-game-contracts-properly-report-important-properties)
    - [Mitigations](#mitigations)
  - [aASR-002: Dispute Game Factory properly reports its created games](#aasr-002-dispute-game-factory-properly-reports-its-created-games)
    - [Mitigations](#mitigations-1)
  - [aASR-003: OptimismPortal properly reports respected game type, blacklist, and retirement time](#aasr-003-optimismportal-properly-reports-respected-game-type-blacklist-and-retirement-time)
    - [Mitigations](#mitigations-2)
  - [aASR-004: Incorrectly resolving games will be invalidated within the airgap delay period](#aasr-004-incorrectly-resolving-games-will-be-invalidated-within-the-airgap-delay-period)
    - [Mitigations](#mitigations-3)
- [Invariants](#invariants)
  - [iASR-001: Games are represented as Proper Games accurately](#iasr-001-games-are-represented-as-proper-games-accurately)
    - [Impact](#impact)
    - [Dependencies](#dependencies)
  - [iASR-002: All Valid Claims are Truly Valid Claims](#iasr-002-all-valid-claims-are-truly-valid-claims)
    - [Impact](#impact-1)
    - [Dependencies](#dependencies-1)
  - [iASR-003: The Anchor Game is a Truly Valid Claim](#iasr-003-the-anchor-game-is-a-truly-valid-claim)
    - [Impact](#impact-2)
    - [Dependencies](#dependencies-2)
- [Function Specification](#function-specification)
  - [isGameRegistered](#isgameregistered)
  - [isGameRespected](#isgamerespected)
  - [isGameBlacklisted](#isgameblacklisted)
  - [isGameRetired](#isgameretired)
  - [isGameProper](#isgameproper)
  - [isGameResolved](#isgameresolved)
  - [isGameAirgapped](#isgameairgapped)
  - [isGameFinalized](#isgamefinalized)
  - [getAnchorRoot](#getanchorroot)
  - [anchors](#anchors)
  - [setAnchorState](#setanchorstate)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The `AnchorStateRegistry` was designed as a registry where `DisputeGame` contracts could store and
register their results so that these results could be used as the starting states for new
`DisputeGame` instances. These starting states, called "anchor states", allow new `DisputeGame`
contracts to use a newer starting state to bound the size of the execution trace for any given
game.

We are generally aiming to shift the `AnchorStateRegistry` to act as a unified source of truth for
the validity of `DisputeGame` contracts and their corresponding root claims. This specification
corresponds to the first iteration of the `AnchorStateRegistry` that will move us in this
direction.

## Definitions

### Dispute Game

> See [Fault Dispute Game](fault-dispute-game.md)

A Dispute Game is a smart contract that makes a determination about the validity of some claim. In
the context of the OP Stack, the claim is generally assumed to be a claim about the value of an
output root at a given L2 block height.

### Respected Game Type

The `OptimismPortal` contract defines a "respected game type" which is the Dispute Game type that
the portal allows to be used for the purpose of proving and finalizing withdrawals. This mechanism
allows the system to use multiple game types simultaneously while still ensuring that the
`OptimismPortal` contract only trusts respected games specifically.

### Registered Game

A Dispute Game is considered to be a **Registered Game** if the game contract was created by the
system's `DisputeGameFactory` contract.

### Respected Game

A Dispute Game is considered to be a **Respected Game** if the game contract's game type **was**
the `respectedGameType` defined by the `OptimismPortal` contract at the time of the game's
creation. Games that are not Respected Games cannot be used as an Anchor Game. See
[Respected Game Type](#respected-game-type) for more information.

### Blacklisted Game

A Dispute Game is considered to be a **Blacklisted Game** if the game contract's address is marked
as blacklisted inside of the `OptimismPortal` contract.

### Retired Game

A Dispute Game is considered to be a **Retired Game** if the game contract was created before the
retirement timestamp (`respectedGameTypeUpdatedAt`) defined in the `OptimismPortal` contract.

### Proper Game

A Dispute Game is considered to be a **Proper Game** if all of the following are true:

- Game is a Registered Game
- Game is a Respected Game
- Game is not a Blacklisted Game
- Game is not a Retired Game

### Resolved Game

A Dispute Game is considered to be a **Resolved Game** if the game has resolved a result in favor
of either the Challenger or the Defender.

### Airgapped Game

A Dispute Game is considered to be an **Airgapped Game** if the game resolved a result more than
the airgap delay seconds ago as defined by the `disputeGameFinalityDelaySeconds` variable in the
`OptimismPortal` contract.

### Finalized Game

A Dispute Game is considered to be a **Finalized Game** if all of the following are true:

- The game is a Resolved Game
- The game is an Airgapped Game

### Valid Claim

A Dispute Game is considered to have a **Valid Claim** if all of the following are true:

- The game is a Proper Game
- The game is a Finalized Game

### Truly Valid Claim

A Truly Valid Claim is a claim that accurately represents the correct root for the L2 block height
on the L2 system as would be reported by a perfect oracle for the L2 system state.

### Starting Anchor State

The Starting Anchor State is the anchor state (root and L2 block height) that is used as the
starting state for new Dispute Game instances when there is no current Anchor Game. The Starting
Anchor State is set during the initialization of the `AnchorStateRegistry` contract.

### Anchor Game

The Anchor Game is a game whose claim is used as the starting state for new Dispute Game instances.
A Game can become the Anchor Game if it has a Valid Claim and the claim's L2 block height is
greater than the claim of the current Anchor Game. If there is no current Anchor Game, a Game can
become the Anchor Game if it has a Valid Claim and the claim's L2 block height is greater than the
current Starting Anchor State's L2 block height.

After a Game becomes the Anchor Game, it will remain the Anchor Game until it is replaced by some
other Game. A Game that is retired after becoming the Anchor Game will remain the Anchor Game. A
Game that is blacklisted after becoming the Anchor Game must not be used as the Anchor Game.

## Assumptions

> **NOTE:** Assumptions are utilized by specific invariants and do not apply globally. Invariants
> typically only rely on a subset of the following assumptions. Different invariants may rely on
> different assumptions. Refer to individual invariants for their dependencies.

### aASR-001: Dispute Game contracts properly report important properties

We assume that the `FaultDisputeGame` and `PermissionedDisputeGame` contracts properly and
faithfully report the following properties:

- Game type
- L2 block number
- Root claim value
- Creation timestamp
- Resolution timestamp

#### Mitigations

- Existing audit on the `FaultDisputeGame` contract
- Integration testing

### aASR-002: Dispute Game Factory properly reports its created games

We assume that the `DisputeGameFactory` contract properly and faithfully reports the games it has
created.

#### Mitigations

- Existing audit on the `DisputeGameFactory` contract
- Integration testing

### aASR-003: OptimismPortal properly reports respected game type, blacklist, and retirement time

We assume that the `OptimismPortal` contract properly and faithfully reports the respected game
type, blacklist, and retirement timestamp.

#### Mitigations

- Existing audit on the `OptimismPortal` contract
- Integration testing

### aASR-004: Incorrectly resolving games will be invalidated within the airgap delay period

We assume that any games that are resolved incorrectly will be invalidated within the airgap delay
period. Invalidation happens within the `OptimismPortal` contract.

#### Mitigations

- Stakeholder incentives / processes
- Incident response plan
- Monitoring

## Invariants

### iASR-001: Games are represented as Proper Games accurately

When asked if a game is a Proper Game, the `AnchorStateRegistry` must serve a response that is
identical to the response that would be given by a perfect oracle for this query.

#### Impact

**Severity: High**

If this invariant is broken, the Anchor Game could be set to an incorrect value, which would cause
future Dispute Game instances to use an incorrect starting state. This would lead games to resolve
incorrectly. Additionally, this could cause a `FaultDisputeGame` to incorrectly choose the wrong
bond refunding mode.

#### Dependencies

- [aASR-001](#aasr-001-dispute-game-contracts-properly-report-important-properties)
- [aASR-002](#aasr-002-dispute-game-factory-properly-reports-its-created-games)
- [aASR-003](#aasr-003-optimismportal-properly-reports-respected-game-type-blacklist-and-retirement-time)

### iASR-002: All Valid Claims are Truly Valid Claims

When asked if a game has a Valid Claim, the `AnchorStateRegistry` must serve a response that is
identical to the response that would be given by a perfect oracle for this query. However, it is
important to note that we do NOT say that all Truly Valid Claims are Valid Claims. It is possible
that a game has a Truly Valid Claim but the `AnchorStateRegistry` reports that the claim is not
a Valid Claim. This permits the `AnchorStateRegistry` and system-wide safety net actions to err on
the side of caution.

In a nutshell, the set of Valid Claims is a subset of the set of Truly Valid Claims.

#### Impact

**Severity: High**

If this invariant is broken, the Anchor Game could be set to an incorrect value, which would cause
future Dispute Game instances to use an incorrect starting state. This would lead games to resolve
incorrectly. If the `OptimismPortal` contract is updated to use the `AnchorStateRegistry` as the
source of truth for the validity of claims, the severity of this invariant will be increased to
Critical.

Fundamentally, this invariant depends on the safety net mechanisms in the `OptimismPortal` contract
being used correctly.

#### Dependencies

- [aASR-001](#aasr-001-dispute-game-contracts-properly-report-important-properties)
- [aASR-002](#aasr-002-dispute-game-factory-properly-reports-its-created-games)
- [aASR-003](#aasr-003-optimismportal-properly-reports-respected-game-type-blacklist-and-retirement-time)
- [aASR-004](#aasr-004-incorrectly-resolving-games-will-be-invalidated-within-the-airgap-delay-period)

### iASR-003: The Anchor Game is a Truly Valid Claim

We require that the Anchor Game is a Truly Valid Claim. This makes it possible to use the Anchor
Game as the starting state for new Dispute Game instances. Notably, given the allowance that not
all Truly Valid Claims are Valid Claims, this invariant does not imply that the Anchor Game is a
Valid Claim.

We allow retired games to be used as the Anchor Game because the retirement mechanism is broad in a
way that commonly causes Truly Valid Claims to no longer be considered Valid Claims. However, we
explicitly disallow blacklisted games from being used as the Anchor Game. If a game is blacklisted,
it should no longer be used as the Anchor Game.

#### Impact

**Severity: High**

If this invariant is broken, an invalid Anchor Game could be used as the starting state for new
Dispute Game instances. This would lead games to resolve incorrectly.

#### Dependencies

- [aASR-001](#aasr-001-dispute-game-contracts-properly-report-important-properties)
- [aASR-002](#aasr-002-dispute-game-factory-properly-reports-its-created-games)
- [aASR-003](#aasr-003-optimismportal-properly-reports-respected-game-type-blacklist-and-retirement-time)
- [aASR-004](#aasr-004-incorrectly-resolving-games-will-be-invalidated-within-the-airgap-delay-period)

## Function Specification

### isGameRegistered

Determines if a game is a Registered Game.

- MUST return `true` if and only if the game was created by the system's `DisputeGameFactory` contract.

### isGameRespected

Determines if a game is a Respected Game.

- MUST return `true` if and only if the game's game type is the respected game type defined by the
  `OptimismPortal` contract as per a call to `OptimismPortal.respectedGameType()`.

### isGameBlacklisted

Determines if a game is a Blacklisted Game.

- MUST return `true` if and only if the game's address is marked as blacklisted inside of the
  `OptimismPortal` contract as per a call to `OptimismPortal.disputeGameBlacklist(game)`.

### isGameRetired

Determines if a game is a Retired Game.

- MUST return `true` if and only if the game was created before the retirement timestamp defined by
  the `OptimismPortal` contract as per a call to `OptimismPortal.respectedGameTypeUpdatedAt()`.
  Check should be a strict comparison that the creation is less than the retirement timestamp.

### isGameProper

Determines if a game is a Proper Game.

- MUST return `true` if and only if `isGameRegistered(game)` and `isGameRespected(game)` are both
  `true` and `isGameBlacklisted(game)` and `isGameRetired(game)` are both `false`.

### isGameResolved

Determines if a game is a Resolved Game.

- MUST return `true` if and only if the game has resolved a result in favor of either the
  Challenger or the Defender as determined by the `FaultDisputeGame.status()` function.

### isGameAirgapped

Determines if a game is an Airgapped Game.

- MUST return `true` if and only if the game has resolved a result more than the airgap delay
  seconds ago as defined by the `disputeGameFinalityDelaySeconds` variable in the `OptimismPortal`
  contract.

### isGameFinalized

Determines if a game is a Finalized Game.

- MUST return `true` if and only if `isGameResolved(game)` and `isGameAirgapped(game)` are both
  `true`.

### getAnchorRoot

Retrieves the current anchor root.

- MUST return the root hash and L2 block height of the current anchor state.

### anchors

Legacy function. Accepts a game type as a parameter but does not use it.

- MUST return the current value of `getAnchorRoot()`.

### setAnchorState

Allows any address to attempt to update the Anchor Game with a new Game as input.

- MUST revert if the provided game is not a Proper Game for any reason.
- MUST revert if the provided game is not a Finalized Game for any reason.
- MUST not update the anchor state if the game corresponds to an L2 block height that is less than
  or equal to the current anchor state's L2 block height.
- MUST otherwise update the anchor state to match the game's result.
