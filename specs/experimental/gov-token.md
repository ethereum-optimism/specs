# Governance Token

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
  - [Token Minting](#token-minting)
  - [Token Burning](#token-burning)
  - [Voting Power](#voting-power)
    - [Public Query Functions](#public-query-functions)
  - [Delegation](#delegation)
    - [Basic Delegation](#basic-delegation)
    - [Advanced Delegation](#advanced-delegation)
  - [Alligator Contract Integration](#alligator-contract-integration)
    - [After Token Transfer Hook](#after-token-transfer-hook)
    - [Delegation Logic Forwarding](#delegation-logic-forwarding)
    - [Delegation Query Forwarding](#delegation-query-forwarding)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

| Constants    | Value                                        |
|--------------|----------------------------------------------|
| Address      | `0x4200000000000000000000000000000000000042` |
| Token name   | `Optimism`                                   |
| Token symbol | `OP`                                         |

`GovernanceToken` is an [ERC20](https://eips.ethereum.org/EIPS/eip-20) token contract that inherits from `ERC20Burnable`,
`ERC20Votes`, and `Ownable`. It allows token holders to delegate their voting power to other addresses, enabling a representative
voting system. The contract integrates with the `Alligator` contract to enable advanced delegations.

### Token Minting

`GovernanceToken` MUST have a `mint(address,uint256)` function with external visibility that allows the `owner()` address
to mint an arbitrary number of new tokens to a specific address. This function MUST only be called by the contract
owner, the `MintManager`, as enforced by the `onlyOwner` modifier inherited from the `Ownable` contract. When tokens
are minted, the voting power of the recipient address MUST be updated accordingly in the `Alligator` contract via the
`afterTokenTransfer` hook. The total token supply is capped to `2^208^ - 1` to prevent overflow risks in the voting
system. If the total supply exceeds this limit, `_mint(address,uint256)`, as inherited from `ERC20Votes`, MUST revert.

### Token Burning

The contract MUST allow token holders to burn their own tokens using the inherited `burn(uint256)` or
`burnFrom(address,uint256)` functions inherited from `ERC20Burnable`. When tokens are burned, the total supply and the
holder's voting power MUST be reduced accordingly in the `Alligator` contract via the `afterTokenTransfer` hook. Burn functions
MUST NOT allow a user's balance to underflow and attempts to reduce balance below zero MUST revert.

### Voting Power

Each token corresponds to one unit of voting power. Token holders who wish to utilize their tokens for voting MUST delegate
their voting power to an address (can be their own address). An active delegation MUST NOT prevent a user from transferring
tokens. The `GovernanceToken` contract MUST offer public accessor functions for querying voting power, as outlined below.

#### Public Query Functions

- `checkpoints(address,uint32) returns (Checkpoint)`
  - MUST retrieve the n-th Checkpoint for a given address.
- `numCheckpoints(address) returns (uint32)`
  - MUST retrieve the total number of Checkpoint objects for a given address.
- `delegates(address) returns (address)`
  - MUST retrieve the address that an account is delegating to.
- `getVotes() returns (uint256)`
  - MUST retrieve the current voting power of an address.
- `getPastVotes(address,uint256) returns (uint256)`
  - MUST retrieve the voting power of an address at specific block number in the past.
- `getPastTotalSupply(uint256) returns (uint256)`
  - MUST return the total token supply at a specific block number in the past.

Above query functions MUST apply the constraints defiend in [Delegation Query Forwarding](#delegation-query-forwarding).

### Delegation

#### Basic Delegation

Vote power can be delegated either by calling the `delegate(address)` function directly (to delegate as the `msg.sender`)
or by providing a signature to be used with function `delegateBySig(address,uint256,uint256,uint8,bytes32,bytes32)`,
as inherited from `ERC20Votes`. Delegation through these functions is considered "basic delegation" as these functions will
delegate the entirety of the user's available balance to the target address. Advanced delegation is handled by the `Alligator`
contract. As of the introduction of the `Alligator` contract, delegation is no longer handled within the `GovernanceToken`
contract itself and calls to these functions are instead forwarded to the `Alligator` contract.

#### Advanced Delegation

Delegators can use the `Alligator` contract to manage advanced delegations including partial delegation to multiple delegates
and re-delegation by one delegate to another. Delegators can place custom rules and constraints on these delegations through
the `Alligator` contract. The `Alligator` contract is specified independently of the `GovernanceToken`.

### Alligator Contract Integration

With the introduction of the `Alligator` contract, delegation and voting power state is no longer handled by the `GovernanceToken`
and is managed within the `Alligator`. The `Alligator` contract enables advanded delegation use-cases such partial and
time-constrained delegations. The `Alligator` contract is specified as a separate contract to limit the total code complexity
within the `GovernanceToken`. The `GovernanceToken` makes only a limited number of assumptions about the behavior of the
`Alligator` contract as defined within this section.

#### After Token Transfer Hook

- `GovernanceToken` MUST call the `Alligator.afterTokenTransfer` function after any transfer of tokens within the `GovernanceToken`
contract. The `Alligator` contract is expected to use this hook to guarantee that delegation state and checkpoint mappings
are kept updated continuously.
- `GovernanceToken` MUST revert if the call to the `Alligator.afterTokenTransfer` function reverts. This guarantees that
the `GovernanceToken` stays in sync with the `Alligator` contract. The `Alligator.afterTokenTransfer` function MUST NOT revert
under bug-free operation.

#### Delegation Logic Forwarding

- `GovernanceToken` MUST forward calls to `delegate` and `delegateBySig` to the `Alligator` contract and MUST NOT continue
to manage delegation state internally. Existing delegation state MUST remain accessible to allow for a gradual and automatic
migration by users to the `Alligator` contract.

#### Delegation Query Forwarding

- `GovernanceToken` MUST attempt to forward all delegation-related query functions to the `Alligator` contract if the relevant
state has already been migrated to the `Alligator` contract. If the state has not been migrated to the `Alligator` contract
then the `GovernanceToken` MUST read that information from its own state instead.
