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
voting system. The contract integrates with the `Alligator` contract through a hook-based approach to enable advanced delegation
functionality, including partial delegation and subdelegations.

### Hook-based Integration with Alligator

The `GovernanceToken` contract integrates with the `Alligator` contract through a hook-based approach to enable advanced
delegation features. The `_afterTokenTransfer` function in the `GovernanceToken` is modified to call the `afterTokenTransfer`
function in the `Alligator` contract, allowing the `Alligator` to consume the hooks and update its delegation and checkpoint
mappings accordingly.

To ensure that token transfers can continue even if the call to the Alligator fails, a try-catch mechanism is implemented
in the `_afterTokenTransfer` function. If the call to the Alligator's `afterTokenTransfer` function fails, the token transfer
will still be completed, and an event will be emitted to indicate the failure. This prevents the token transfer from being
blocked due to issues with the Alligator contract.

```solidity
function _afterTokenTransfer(address from, address to, uint256 amount) internal override {
    bytes memory data = abi.encodeWithSelector(IAlligator.afterTokenTransfer.selector, from, to, amount);
    bool success;
    assembly ("memory-safe") {
        success := call(gas(), alligatorAddress, 0, add(data, 0x20), mload(data), 0, 0)
    }
    
    if (!success) emit AlligatorCallFailed(from, to, amount);
}
```

All delegation-related state, including the `delegates`, `checkpoints`, and `numCheckpoints` mappings, is shifted from the
`GovernanceToken` to the `Alligator` contract. The `Alligator` treats the original checkpoints from the `GovernanceToken`
as a starting point for its own checkpoints.

Basic delegation functions in the `GovernanceToken`, such as `delegate` and `delegateBySig`, are modified to forward the
calls to the `Alligator` contract using an advanced delegation rule that mimics basic delegation.

### Token Minting

`GovernanceToken` MUST have a `mint(address,uint256)` function with external visibility that allows the contract owner
to mint an arbitrary number of new tokens to a specific address. This function MUST only be called by the contract
owner, the `MintManager`, as enforced by the `onlyOwner` modifier inherited from the `Ownable` contract. When tokens
are minted, the voting power of the recipient address MUST be updated accordingly in the `Alligator` contract via the 
transfer hook. The total token supply is capped to `2^208^ - 1` to prevent overflow risks in the voting system. If the
total supply exceeds this limit, `_mint(address,uint256)`, as inherited from `ERC20Votes`, MUST revert.

### Token Burning

The contract MUST allow token holders to burn their own tokens using the inherited `burn(uint256)` or
`burnFrom(address,uint256)` functions inherited from `ERC20Burnable`. When tokens are burned, the total supply and the
holder's voting power MUST be reduced accordingly in the `Alligator` contract via the transfer hook.

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
as inherited from `ERC20Votes`. These functions are modified to forward the calls to the `Alligator` contract using an
advanced delegation rule that mimics basic delegation.

Advanced delegation features, such as partial delegation and subdelegations, are handled by the `Alligator` contract.
Partial delegation allows delegators to distribute their voting power among multiple delegatees in a fractional manner,
while subdelegations enable delegatees to further delegate their received voting power to other delegatees based on predefined
rules and constraints.

The `Alligator` contract maintains the necessary invariants, such as preventing circular delegation chains, ensuring vote
weight consistency, and managing checkpoints. It is incorporated as a predeploy of the OP stack to avoid manual deployments
across the Superchain.
