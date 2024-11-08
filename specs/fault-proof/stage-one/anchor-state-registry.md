# Anchor State Registry

## Overview (What this contract is actually supposed to do)

This contract manages and communicates properties of dispute game validity to other contracts in order to facilitate withdrawals and future dispute games.

- This contract is the source of truth for the validity of an **anchor state**.
  - [FaultDisputeGame](fault-dispute-game.md) and PermissionedDisputeGame depend on this contract for a valid **anchor state** against which to resolve a claim. These contracts assume the state is valid.
    - The valid anchor state needs to be recent enough so that the game doesn't break (run out of memory) in op-challenger.
- This contract is the source of truth for the validity of a particular fault dispute game result.
  - This property is used by the [OptimismPortal](optimism-portal.md). The Portal asks two things of the Registry:
    - Can this dispute game can be used to prove a withdrawal?
    - Can this dispute game can be used to finalize a withdrawal?

## Definitions

- **Anchor state**
  - See [Fault Dispute Game -> Anchor State](fault-dispute-game.md#anchor-state).
- **Authorized input**
  - An input for which there is social consensus, i.e. coming from governance.
- **Invalid game**
  - A dispute game is invalid if any of the following are true:
    - Game was not created by the dispute game factory.
    - Game was not created while it was the respected game type.
    - Game is blacklisted.
    - Game was created before the validity timestamp.
    - Game status is `CHALLENGER_WINS`.
- **Finalized game**
  - A dispute game is finalized if all of the following are true:
    - Game status is `CHALLENGER_WINS` or `DEFENDER_WINS`.
    - Game `resolvedAt` timestamp is not zero.
    - Game `resolvedAt` timestamp is more than `dispute game finality seconds` seconds ago.
- **Valid game**
  - A game is a **Valid game** if it is not an **Invalid game**, and is a **Finalized game**.
- **Latest valid game**
  - The latest valid game is a **valid game** whose anchor state will be used to initialize new FaultDisputeGames and PermissionedDisputeGames. It represents the most recent valid representation of L2 state.

## Top-Level Invariants

- The Validity timestamp starts at zero.

## Function-Level Invariants

### `initialize`

Initialize the thing somehow.

- Initial anchor state is **authorized**.
- Need an **authorized** reference to the dispute game factory.
- Need **authorized** input for `dispute game finality seconds`.
- Need **authorized** reference to superchain config.

### `getLatestValidGame`

Get latest **valid game**.

- Throws an error if the game is not valid.
  - Depends on the condition that `update latest valid game` is the only method to update the “latest valid game” state variable and that it will only update the state variable with a **valid game**. Still, it is possible for the once valid game to become invalid.

### Update latest **valid game**

- Game must be **valid**
- Block number for latest valid game must be higher than current latest valid game
- This function is the ONLY way to update the latest valid game (after initialization)

### Get latest valid root claim

- Returns the root claim of the result of `get latest valid game` or an **authorized** anchor state if no such game exists

### Get anchor state

- Returns the root claim of the result of `get latest valid game` or an **authorized** anchor state if no such game exists
- Must maintain the property that the timestamp of the game is not too old

### Register game result

- Callable only by a game itself
- Game must not be invalid
- If game is not invalid, stores the address of the game in some array

### Try update latest valid game based on previous game results

- Callable by anyone
- Find the latest (comparing on l2BlockNumber) valid game you can find in the register within a fixed amount of gas
- Use this as input to `update latest valid game`
- Make sure this doesn’t get more expensive as time goes on

### Is this game invalid?

### Is this game finalized?

### Is this game valid?

- `return !isGameInvalid(game) && isGameFinalized(game)`
- Definition of **valid** is this condition passing

### Set respected game type

- Can only be set by <some role>

### Update validity timestamp

- Can only be set by <some role>
- Must be greater than previous validity timestamp
- Cannot be greater than current block timestamp

### Blacklist game

- Can only be set by <some role>

---

- Definition of valid is NOT invalid AND finalized
- Airgap is a condition of finalization
- Therefore airgap is a condition of validity
- Games can be blacklisted after they are valid

---

- Change respected game type
- Observe that change to respected game type is finalized
- Then change the validation timestamp
- Or just do both but make sure that respected game type change doesn’t get reorged to be after the timestamp change

### Get dispute game finality delay

- Returns **authorized** finality delay duration.

# FaultDisputeGame

- Only sets that special boolean if it actually is the respected game type
- And the boolean never changes after it’s been set
- Reports its game type correctly
- Reports its l2BlockNumber correctly
