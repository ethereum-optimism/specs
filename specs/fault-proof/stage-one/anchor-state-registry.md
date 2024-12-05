# Anchor State Registry

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

**Table of Contents**

- [Anchor State Registry](#anchor-state-registry)
  - [Overview](#overview)
    - [Perspective](#perspective)
  - [Definitions](#definitions)
  - [Top-Level Invariants](#top-level-invariants)
    - [Contract Dependents](#contract-dependents)
      - [FaultDisputeGame](#faultdisputegame)
      - [OptimismPortal](#optimismportal)
    - [Contract Dependencies](#contract-dependencies)
      - [FaultDisputeGame](#faultdisputegame-1)
      - [DisputeGameFactory](#disputegamefactory)
      - [SuperchainConfig](#superchainconfig)
  - [Function-Level Invariants](#function-level-invariants)
    - [`initialize`](#initialize)
    - [`getLatestValidGame`](#getlatestvalidgame)
    - [`updateLatestValidGame`](#updatelatestvalidgame)
    - [`getLatestAnchorState`](#getlatestanchorstate)
    - [`registerMaybeValidGame`](#registermaybevalidgame)
    - [`tryUpdateLatestValidGame`](#tryupdatelatestvalidgame)
    - [`isGameInvalid`](#isgameinvalid)
    - [`isGameFinalized`](#isgamefinalized)
    - [`isGameValid`](#isgamevalid)
    - [`isGameBlacklisted`](#isgameblacklisted)
    - [`setRespectedGameType`](#setrespectedgametype)
    - [`invalidateAllExistingGames`](#invalidateallexistinggames)
    - [`setGameBlacklisted`](#setgameblacklisted)
    - [`getGameFinalityDelay`](#getgamefinalitydelay)
  - [Implementation](#implementation)
    - [`constructor`](#constructor)
    - [`initialize`](#initialize-1)
    - [`anchors` / `getLatestAnchorState`](#anchors--getlatestanchorstate)
    - [`registerMaybeValidGame`](#registermaybevalidgame-1)
    - [`updateLatestValidGame`](#updatelatestvalidgame-1)
    - [`tryUpdateLatestValidGame`](#tryupdatelatestvalidgame-1)
    - [`setGameBlacklisted`](#setgameblacklisted-1)
    - [`setRespectedGameType`](#setrespectedgametype-1)
    - [`isGameInvalid`](#isgameinvalid-1)
    - [`isGameValid`](#isgamevalid-1)
    - [`disputeGameFinalityDelaySeconds`](#disputegamefinalitydelayseconds)
    - [`disputeGameFactory`](#disputegamefactory-1)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

### Perspective

Multiple contracts in the fault proof system have critical dependencies on things outside them:

- The Portal needs to know whether a withdrawal's proof is based on a **valid** dispute game.
- A new dispute game needs to initialize with the **latest valid anchor state**.
- An existing dispute game needs to know whether it is **invalid**, so it can refund its bonds.

The AnchorStateRegistry is these contracts' source of truth, managing and exposing dispute game and anchor state
validity to moderate dispute games and withdrawals.

Furthermore, the AnchorStateRegistry is a crucial player in incident response. It can invalidate dispute games, thereby
invalidating withdrawals and dispute games founded on an incorrect root claim.

## Definitions

- **Anchor state**
  - See [Fault Dispute Game -> Anchor State](fault-dispute-game.md#anchor-state).
- **Authorized input**
  - An input for which there is social consensus, i.e. coming from governance.
- **Blacklisted game**
  - A dispute game is blacklisted if it is set as blacklisted via **authorized input**.
- **Validity timestamp**
  - The validity timestamp is a timestamp internal to the contract that partly determines game validity and can only be
    adjusted via **authorized input**.
- **Invalid game**
  - A dispute game is invalid if any of the following are true:
    - Game was not created by the dispute game factory.
    - Game was not created while it was the respected game type.
    - Game is **blacklisted**.
    - Game was created before the **validity timestamp**.
    - Game status is `CHALLENGER_WINS`.
- **Finalized game**
  - A dispute game is finalized if all of the following are true:
    - Game status is `CHALLENGER_WINS` or `DEFENDER_WINS`.
    - Game `resolvedAt` timestamp is not zero.
    - Game `resolvedAt` timestamp is more than `dispute game finality delay` seconds ago.
- **Maybe valid game**
  - A dispute game that is not an **invalid game** (but not yet a **finalized game**).
- **Valid game**
  - A game is a **Valid game** if it is not an **Invalid game**, and is a **Finalized game**.
- **Latest valid game**
  - The latest valid game is a game whose anchor state is used to initialize new Fault Dispute Games. It was known to be
    a **valid game** when set. It will continue to be the latest valid game until updated with a more recent valid game,
    or blacklisted.
- **Latest valid anchor state**
  - The latest valid anchor state is the output root of the latest valid game.
- **Dispute game finality delay**
  - The dispute game finality delay is an **authorized input** representing the period of time between a dispute game
    resolving and a dispute game becoming finalized or valid.
  - Also known as "air gap."

## Top-Level Invariants

- The contract will only assert **valid games** are valid.
- The latest valid anchor state must never serve the output root of a blacklisted game.
- The latest valid anchor state must be recent enough so that the game doesn't break (run out of memory) in
  op-challenger.
- The validity timestamp must start at zero.

### Contract Dependents

This contract manages and exposes dispute game validity so that other contracts can do things like correctly initialize
dispute games and validate withdrawals.

#### FaultDisputeGame

A [FaultDisputeGame](fault-dispute-game.md) depends on this contract for a **latest valid anchor state** against which
to resolve a claim and assumes its correct. Additionally, becauase proposers must gather L1 data for the window between
the anchor state and the claimed state, FaultDisputeGames depend on this contract to keep a **latest valid anchor
state** that's recent, so that proposer software is not overburdened (i.e. runs out of memory).

#### OptimismPortal

OptimismPortal depends on this contract to correctly report game validity as the basis for proving and finalizing
withdrawals.

- Can this dispute game can be used to prove a withdrawal? (Is the dispute game a **maybe valid game**?)
- Can this dispute game can be used to finalize a withdrawal? (Is the dispute game a **valid game**?)

### Contract Dependencies

#### FaultDisputeGame

Depends on FaultDisputeGame to correctly report:

- whether its game type was the respected game type when created (and that it never changes once set).
- its game type.
- its l2BlockNumber.
- its createdAt timestamp.

#### DisputeGameFactory

Depends on DisputeGameFactory to correctly report:

- whether a game was created by the DisputeGameFactory (is "factory-registered").

#### SuperchainConfig

Depends on SuperchainConfig to correctly report:

- its guardian address.

## Function-Level Invariants

### `initialize`

- Initial anchor state must be an **authorized input**.
- Dispute game factory must be an **authorized input**.
- `dispute game finality delay` must be an **authorized input**.
- Superchain config must be an **authorized input**.

### `getLatestValidGame`

Gets **latest valid game**.

- Throws an error if the game is not valid.
  - Depends on the condition that `update latest valid game` is the only method to update the “latest valid game” state
    variable and that it will only update the state variable with a **valid game**. Still, it is possible for the once
    valid game to become invalid (via blacklisting or `update validity timestamp`).

### `updateLatestValidGame`

- Game must be a **valid game**.
- Block number for candidate **valid game** must be higher than current **latest valid game**.
- This function is the ONLY way to update the **latest valid game** (after initialization).

### `getLatestAnchorState`

- If the **latest valid game** is not blacklisted, return its root claim and l2 block number.
- If the **latest valid game** is blacklisted, throw an error.
- Must maintain the property that the timestamp of the game is not too old.
  - TODO: How old is too old?

### `registerMaybeValidGame`

Stores the address of a **maybe valid game** in an array as a candidate for `latestValidGame`.

- Callable only by a **maybe valid game**.
- Calling game must only register itself (and not some other game).
  - TODO: determine any invariants around registry ordering.

### `tryUpdateLatestValidGame`

Try to update **latest valid game** using registry of **maybe valid games**.

- Callable by anyone.
- Find the latest (comparing on l2BlockNumber) valid game you can find in the register within a fixed amount of gas.
  - Fixed gas amount ensures that this function does not get more expensive to call as time goes on.
- Use this as input to `update latest valid game`.

### `isGameInvalid`

Returns whether the game is an **invalid game**.

### `isGameFinalized`

Returns whether the game is a **finalized game**.

### `isGameValid`

`return !isGameInvalid(game) && isGameFinalized(game)`

Definition of **valid** is this condition passing.

### `isGameBlacklisted`

Returns whether the game is a **blacklisted game**.

### `setRespectedGameType`

- Must be **authorized** by _some role_.

### `invalidateAllExistingGames`

Invalidates all games that exist. Note: until updated, the **latest valid game** (now invalidated) will still provide
the **latest valid anchor state**.

- Must be **authorized** by _some role_.

### `setGameBlacklisted`

Blacklists a game.

- Must be **authorized** by _some role_.

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
