<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

**Table of Contents**

- [Anchor State Registry](#anchor-state-registry)
  - [Overview](#overview)
    - [Perspective](#perspective)
  - [Definitions](#definitions)
  - [Top-Level Invariants](#top-level-invariants)
    - [Contract Dependents](#contract-dependents)
    - [Contract Dependencies](#contract-dependencies)
      - [FaultDisputeGame](#faultdisputegame)
  - [Function-Level Invariants](#function-level-invariants)
    - [`initialize`](#initialize)
    - [`getLatestValidGame`](#getlatestvalidgame)
    - [`updateLatestValidGame`](#updatelatestvalidgame)
    - [`getLatestAnchorState`](#getlatestanchorstate)
    - [`registerGameResult`](#registergameresult)
    - [`tryUpdateLatestValidGame`](#tryupdatelatestvalidgame)
    - [`isGameInvalid`](#isgameinvalid)
    - [`isGameFinalized`](#isgamefinalized)
    - [`isGameValid`](#isgamevalid)
    - [`isGameBlacklisted`](#isgameblacklisted)
    - [`setRespectedGameType`](#setrespectedgametype)
    - [`updateValidityTimestamp`](#updatevaliditytimestamp)
    - [`setGameBlacklisted`](#setgameblacklisted)
    - [`getGameFinalityDelay`](#getgamefinalitydelay)
  - [Implementation](#implementation)
    - [`constructor`](#constructor)
    - [`initialize`](#initialize-1)
    - [`anchors` / `getLatestAnchorState`](#anchors--getlatestanchorstate)
    - [`registerMaybeValidGame`](#registermaybevalidgame)
    - [`updateLatestValidGame`](#updatelatestvalidgame-1)
    - [`tryUpdateLatestValidGame`](#tryupdatelatestvalidgame-1)
    - [`setGameBlacklisted`](#setgameblacklisted-1)
    - [`setRespectedGameType`](#setrespectedgametype-1)
    - [`isGameInvalid`](#isgameinvalid-1)
    - [`isGameValid`](#isgamevalid-1)
    - [`disputeGameFinalityDelaySeconds`](#disputegamefinalitydelayseconds)
    - [`disputeGameFactory`](#disputegamefactory)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Anchor State Registry

## Overview

### Perspective

Multiple contracts in the fault proof system have hard dependencies on things outside them:

- The Portal needs to know whether a withdrawal's proof is based on a **valid** dispute game.
- A new dispute game needs to initialize with a **valid** anchor state.
- An existing dispute game needs to know whether it is **invalid**, so it can refund its bonds.

The AnchorStateRegistry is these contracts' source of truth, managing and exposing dispute game and anchor state validity to moderate dispute games and withdrawals.

Furthermore, the AnchorStateRegistry is a crucial player in incident response. It can invalidate dispute games and withdrawals, effectively mitigating consequences from dispute games that resolve incorrectly.

## Definitions

- **Anchor state**
  - See [Fault Dispute Game -> Anchor State](fault-dispute-game.md#anchor-state).
- **Authorized input**
  - An input for which there is social consensus, i.e. coming from governance.
- **Blacklisted game**
  - A dispute game is blacklisted if it is set as blacklisted via **authorized input**.
- **Validity timestamp**
  - The validity timestamp is an **authorized input** that partly determines game validity.
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
- **Valid game**
  - A game is a **Valid game** if it is not an **Invalid game**, and is a **Finalized game**.
- **Latest valid game**
  - The latest valid game is a game whose anchor state is used to initialize new Fault Dispute Games. It was known to be a **valid game** when set. It will continue to be the latest valid game until updated with a more recent valid game, or blacklisted.
- **Latest valid anchor state**
  - The latest valid anchor state is the output root of the latest valid game.

## Top-Level Invariants

- The contract will only assert **valid games** are valid.
- The latest valid anchor state must never serve the output root of a blacklisted game.
- The latest valid anchor state must be recent enough so that the game doesn't break (run out of memory) in op-challenger.
- The validity timestamp must start at zero.

### Contract Dependents

This contract manages and exposes dispute game validity so that other contracts can do things like validate withdrawals and initialize dispute games correctly.

- This contract is the source of truth for the validity of an **anchor state**.
  - [FaultDisputeGame](fault-dispute-game.md) and PermissionedDisputeGame depend on this contract for a **latest valid anchor state** against which to resolve a claim. These contracts assume the state is valid.
- Optimism Portal depends on this contract for accurate fault dispute game results.
  - Can this dispute game can be used to prove a withdrawal? (Is the dispute game not an **invalid game**?)
  - Can this dispute game can be used to finalize a withdrawal? (Is the dispute game a **valid game**?)

### Contract Dependencies

#### FaultDisputeGame

- Only sets that special boolean if it actually is the respected game type.
- And the boolean never changes after it’s been set.
- Reports its game type correctly.
- Reports its l2BlockNumber correctly.
- Reports its createdAt timestamp correctly.

## Function-Level Invariants

### `initialize`

- Initial anchor state must be an **authorized input**.
- Dispute game factory must be an **authorized input**.
- `dispute game finality delay` must be an **authorized input**.
- Superchain config must be an **authorized input**.

### `getLatestValidGame`

Gets **latest valid game**.

- Throws an error if the game is not valid.
  - Depends on the condition that `update latest valid game` is the only method to update the “latest valid game” state variable and that it will only update the state variable with a **valid game**. Still, it is possible for the once valid game to become invalid (via blacklisting or `update validity timestamp`).

### `updateLatestValidGame`

- Game must be **valid**.
- Block number for latest valid game must be higher than current latest valid game.
- This function is the ONLY way to update the latest valid game (after initialization).

### `getLatestAnchorState`

- If the **latest valid game** is not blacklisted, return its root claim and l2 block number.
- If the **latest valid game** is blacklisted, throw an error.
- Must maintain the property that the timestamp of the game is not too old.
  - TODO: How old is too old?

### `registerGameResult`

Stores the address of a not invalid dispute game in an array as a candidate for `latestValidGame`.

- Callable only by a not invalid game.
- Calling game must only register itself.
- TODO:

### `tryUpdateLatestValidGame`

Try update latest valid game based on previous game results.

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

- Must be **authorized** by <some role>.

### `updateValidityTimestamp`

- Must be **authorized** by <some role>.
- Must be greater than previous validity timestamp.
- Cannot be greater than current block timestamp.

### `setGameBlacklisted`

Blacklists a game.

- Must be **authorized** by <some role>.

### `getGameFinalityDelay`

Returns **authorized** finality delay duration in seconds. No external dependent; public getter for convenience.

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
