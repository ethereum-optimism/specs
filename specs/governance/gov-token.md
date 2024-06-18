# Governance Token

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
  - [Hook-based Integration with Alligator](#hook-based-integration-with-alligator)
  - [Token Minting](#token-minting)
  - [Token Burning](#token-burning)
  - [Voting Power](#voting-power)
    - [Queries](#queries)
  - [Delegation](#delegation)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

| Constants    | Value                                        |
|--------------|----------------------------------------------|
| Address      | `0x4200000000000000000000000000000000000042` |
| Token name   | `Optimism`                                   |
| Token symbol | `OP`                                         |

`GovernanceToken` is an [ERC20](https://eips.ethereum.org/EIPS/eip-20) token contract that inherits from `ERC20Burnable`,
`ERC20Votes`, and `Ownable`. It allows token holders to delegate their voting power to other addresses, enabling a representative
voting system. The contract integrates with the `Alligator` contract through a hook-based approach to support subdelegations.

### Hook-based Integration with Alligator

Subdelegations allow for advanced delegation use cases, such as partial, time-constrained & block-based delegations, relative
& fixed allowances, and custom rules. The `_afterTokenTransfer` function in the `GovernanceToken` is modified to call the
`afterTokenTransfer` function in the `Alligator` contract, allowing the `Alligator` contract to consume the hooks and update
its delegation and checkpoint mappings accordingly.

If the call to the `Alligator`'s `afterTokenTransfer` function fails, the token transfer MUST revert. This ensures that the
`Alligator` remains in sync with the `GovernanceToken`. Otherwise, the `GovernanceToken` could be left in an inconsistent
state relative to the `Alligator`, such as when a token transfer is successful but the delegation state is not updated.

All delegation-related state, including the `delegates`, `checkpoints`, and `numCheckpoints` mappings, is gradually
shifted from the `GovernanceToken` to the `Alligator` contract through transactions that call the `Alligator`'s hook
(e.g. transfers). In the hook, the `Alligator` should check if the `to` and `from` addresses have been migrated.
If an address hasn't been migrated, the `Alligator` should write the data from the `GovernanceToken`'s mappings for that
address to its own state. When reading delegation data in the `Alligator` for a delegator that hasn't been migrated,
the `Alligator` should pull the data from the `GovernanceToken`'s state.

For backwards compatibility, the getter methods in the `GovernanceToken` MUST check if the data of a given address has been
migrated or not. If the data has been migrated, the `GovernanceToken` MUST forward the call to the `Alligator` contract.
Otherwise, the `GovernanceToken` MUST read from its state.

The `delegate` and `delegateBySig` functions in the `GovernanceToken` MUST forward the calls to the `Alligator` contract,
which implements the required delegation logic.

### Token Minting

`GovernanceToken` MUST have a `mint(address,uint256)` function with external visibility that allows the contract owner
to mint an arbitrary number of new tokens to a specific address. This function MUST only be called by the contract
owner, the `MintManager`, as enforced by the `onlyOwner` modifier inherited from the `Ownable` contract. When tokens
are minted, the voting power of the recipient address MUST be updated accordingly in the `Alligator` contract via the
`afterTokenTransfer` hook. The total token supply is capped to `2^208^ - 1` to prevent overflow risks in the voting
system. If the total supply exceeds this limit, `_mint(address,uint256)`, as inherited from `ERC20Votes`, MUST revert.

### Token Burning

The contract MUST allow token holders to burn their own tokens using the inherited `burn(uint256)` or
`burnFrom(address,uint256)` functions inherited from `ERC20Burnable`. When tokens are burned, the total supply and the
holder's voting power MUST be reduced accordingly in the `Alligator` contract via the `afterTokenTransfer` hook.

### Voting Power

Each token corresponds to one unit of voting power.
By default, token balance does not account for voting power. To have their voting power counted, token holders MUST delegate
their voting power to an address (can be their own address).
The contract MUST offer public accessors for querying voting power, as outlined below.

#### Queries

- The `getVotes()(uint256)` function MUST retrieve the current voting power of an address from the `Alligator` contract.
- The `getPastVotes(address,uint256)(uint256)` function MUST allow querying the voting power of an address at a specific
  block number in the past from the `Alligator` contract.
- The `getPastTotalSupply(uint256)(uint256)` function MUST return the total voting power at a specific block number in
  the past from the `Alligator` contract.

### Delegation

Vote power can be delegated either by calling the `delegate(address)` function directly (to delegate as the `msg.sender`)
or by providing a signature to be used with function `delegateBySig(address,uint256,uint256,uint8,bytes32,bytes32)`,
as inherited from `ERC20Votes`. These functions are modified to forward the calls to the `Alligator` contract which
implements the required logic.

With subdelegations, delegators can distribute their voting power among multiple delegatees in a fractional manner,
while also allowing delegatees to further delegate their received voting power to other delegatees based on predefined
rules and constraints.

The `Alligator` contract maintains the necessary invariants, such as preventing circular delegation chains, ensuring vote
weight consistency, and managing checkpoints. It is incorporated as a predeploy of the OP stack to avoid manual deployments
across the Superchain.
