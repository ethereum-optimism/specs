# Bond Incentives

Bonds is an add-on to the core [Fault Dispute Game](./fault-dispute-game.md). The core game mechanics are
designed to ensure honesty as the best response to winning subgames. By introducing financial incentives,
Bonds makes it worthwhile for honest challengers to participate.

- Moves
- Subgame Resolution

## Moves

Moves must be adequately bonded to be added to the FDG. This document does not specify a
scheme for determining the minimum bond requirement. FDG implementations should define a function
computing the minimum bond requirement with the following:

```solidity
function getRequiredBond(Position _movePosition) public pure returns (uint256 requiredBond_)
```

As such, attacking or defending requires a check for the `getRequiredBond()` amount against the bond
attached to the move. To incentivize participation, the minimum bond should cover the cost of a possible
counter to the move being added. Thus, the minimum bond depends only on the position of the move that's added.

## Subgame Resolution

If a subgame root resolves incorrectly, then its bond is distributed to the **leftmost claimant** that countered
it. This creates an incentive to identify the earliest point of disagreement in an execution trace.

At maximum game depths, where a claimant counters a bonded claim via `step`, the bond is instead distributed
to the account that successfully called `step`.
