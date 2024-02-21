# Bond Incentives

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Bond Formula](#bond-formula)
  - [Cost in output root bisection game](#cost-in-output-root-bisection-game)
  - [Cost in execution game](#cost-in-execution-game)
  - [Cost at instruction step](#cost-at-instruction-step)
- [Moves](#moves)
- [Subgame Resolution](#subgame-resolution)
  - [Leftmost Claim Incentives](#leftmost-claim-incentives)
- [Fallback on System Failure](#fallback-on-system-failure)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

Bonds is an add-on to the core [Fault Dispute Game](./fault-dispute-game.md). The core game mechanics are
designed to ensure honesty as the best response to winning subgames. By introducing financial incentives,
Bonds makes it worthwhile for honest challengers to participate.
Without the bond reward incentive, the FDG will be too costly for honest players to participate in given the
cost of verifying and making claims.

Implementations may allow the FDG to directly receive bonds, or delegate this responsibility to another entity.
Regardless, there must be a way for the FDG to query and distribute bonds linked to a claim.

Bonds are integrated into the FDG in two areas:

- Moves
- Subgame Resolution

## Bond Formula

| Component         | Term | Cost (ETH)                                    | Gas (worst case)                                                               |
| ----------------- | ---- | --------------------------------------------- | ------------------------------------------------------------------------------ |
| Off-chain compute | $O$  | $0.005$                                       | n/a                                                                            |
| Move              | $M$  | $158,000\space\times\space10^9\times$ basefee | $158,000$                                                                      |
| Resolve Claim     | $R$  | $60,000\space\times\space10^9\times$ basefee  | $60,000$                                                                       |
| Step              | $S$  | $13,000\space\times\space10^9\times$ basefee  | $13,000$                                                                       |
| Submit 8MB LPP    | $P$  | 5.12                                          | n/a (assumes nominal base fee increases across each proposed leaf transaction) |

The cost of the challenger's response depends on the position of the response in the dispute game. This cost is strictly
the direct cost of participation. This does _not_ include other costs such as the opportunity costs and the deterrence
deposit.

### Cost in output root bisection game

Includes the cost of the contract interaction plus the resolution cost.

$M + R$

### Cost in execution game

Includes the cost of the contract interaction, running the FPVM natively to counter, and the resolution cost for the
resolver if the claim is invalid.

$O + M + R$

### Cost at instruction step

Includes the off-chain compute cost, the cost of the contract interaction, and the worst-case cost of submitting a
large preimage proposal, in case the instruction step requires a part of the worst-case preimage.

$O + S + P$

## Moves

Moves must be adequately bonded to be added to the FDG. This document does not specify a
scheme for determining the minimum bond requirement. FDG implementations should define a function
computing the minimum bond requirement with the following signature:

```solidity
function getRequiredBond(Position _movePosition) public pure returns (uint256 requiredBond_)
```

As such, attacking or defending requires a check for the `getRequiredBond()` amount against the bond
attached to the move. To incentivize participation, the minimum bond should cover the cost of a possible
counter to the move being added. Thus, the minimum bond depends only on the position of the move that's added.

## Subgame Resolution

If a subgame root resolves incorrectly, then its bond is distributed to the **leftmost claimant** that countered
it. This creates an incentive to identify the earliest point of disagreement in an execution trace.
The subgame root claimant gets back its bond iff it resolves correctly.

At maximum game depths, where a claimant counters a bonded claim via `step`, the bond is instead distributed
to the account that successfully called `step`.

### Leftmost Claim Incentives

There exists defensive positions that cannot be countered, even if they hold invalid claims. These positions
are located on the same level as honest claims, but situated to its right (i.e. its gindex > honest claim's).

An honest challenger can always successfully dispute any sibling claims not positioned to the right of an honest claim.
The leftmost payoff rule encourages such disputes, ensuring only one claim is leftmost at correct depths.
This claim will be the honest one, and thus bond rewards will be directed exclusively to honest claims.

## Fallback on System Failure

In the case that a dispute game resolves incorrectly in stage one while the system is nascent, the honest challenger
stands to lose a significant amount of funds for performing the correct actions. The `Guardian` role in the
`SuperchainConfig` can enable safety mode, which flags the `FaultDisputeGame` and `PermissionedDisputeGame` to return
bonds to their submitters. To allow the `Guardian` enough time to enable safety mode in the event that a game resolves
incorrectly, the `FaultDisputeGame`'s `claimCredit` function requires waiting `BOND_PAYOUT_DELAY` after the game
resolves before any credit can be claimed.

This is reflected in the `claimCredit` function of the `FaultDisputeGame`:

```solidity
/// @notice Claim the credit belonging to the recipient address.
/// @param _recipient The owner and recipient of the credit.
function claimCredit(address _recipient) external {
    // Don't allow the credit to be claimed until bond delay has expired.
    if (block.timestamp < resolvedAt.raw() + BOND_PAYOUT_DELAY.raw()) revert BondDelayNotExpired();

    // Remove the credit from the recipient prior to performing the external call.
    uint256 recipientCredit;
    if (SUPERCHAIN_CONFIG.fdgSafetyMode()) {
        recipientCredit = bonds[_recipient];
        bonds[_recipient] = 0;
    } else {
        recipientCredit = credit[_recipient];
        credit[_recipient] = 0;
    }

    // Transfer the credit to the recipient.
    (bool success,) = _recipient.call{ value: recipientCredit }(hex"");
    if (!success) revert BondTransferFailed();
}
```
