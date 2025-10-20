# Governance Token

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
  - [Voting Power](#voting-power)
  - [Delegation](#delegation)
  - [Checkpoint](#checkpoint)
- [Assumptions](#assumptions)
  - [aGT-001: Owner enforces token inflation schedule](#agt-001-owner-enforces-token-inflation-schedule)
    - [Mitigations](#mitigations)
  - [aGT-002: OpenZeppelin contract implementations are correct](#agt-002-openzeppelin-contract-implementations-are-correct)
    - [Mitigations](#mitigations-1)
  - [aGT-003: Users understand delegation requirement for voting](#agt-003-users-understand-delegation-requirement-for-voting)
    - [Mitigations](#mitigations-2)
  - [aGT-004: Governance systems query historical voting power correctly](#agt-004-governance-systems-query-historical-voting-power-correctly)
    - [Mitigations](#mitigations-3)
- [Dependencies](#dependencies)
- [Invariants](#invariants)
  - [iGT-001: Only owner can mint new tokens](#igt-001-only-owner-can-mint-new-tokens)
    - [Impact](#impact)
  - [iGT-002: Token supply can only decrease through authorized burning](#igt-002-token-supply-can-only-decrease-through-authorized-burning)
    - [Impact](#impact-1)
  - [iGT-003: Voting power accurately reflects delegated balances](#igt-003-voting-power-accurately-reflects-delegated-balances)
    - [Impact](#impact-2)
  - [iGT-004: Historical voting records are immutable](#igt-004-historical-voting-records-are-immutable)
    - [Impact](#impact-3)
  - [iGT-005: Token transfers never fail due to delegation](#igt-005-token-transfers-never-fail-due-to-delegation)
    - [Impact](#impact-4)
  - [iGT-006: Total supply never exceeds maximum](#igt-006-total-supply-never-exceeds-maximum)
    - [Impact](#impact-5)
  - [iGT-007: Delegations cannot be re-delegated](#igt-007-delegations-cannot-be-re-delegated)
    - [Impact](#impact-6)
  - [iGT-008: Delegation changes are properly tracked](#igt-008-delegation-changes-are-properly-tracked)
    - [Impact](#impact-7)
- [Function Specifications](#function-specifications)
  - [Token Minting](#token-minting)
    - [mint](#mint)
  - [Token Burning](#token-burning)
    - [burn](#burn)
    - [burnFrom](#burnfrom)
  - [Delegation Functions](#delegation-functions)
    - [delegate](#delegate)
    - [delegateBySig](#delegatebysig)
  - [Voting Power Query Functions](#voting-power-query-functions)
    - [getVotes](#getvotes)
    - [getPastVotes](#getpastvotes)
    - [getPastTotalSupply](#getpasttotalsupply)
    - [delegates](#delegates)
    - [checkpoints](#checkpoints)
    - [numCheckpoints](#numcheckpoints)
  - [ERC20 Standard Functions](#erc20-standard-functions)
    - [transfer](#transfer)
    - [transferFrom](#transferfrom)
    - [approve](#approve)
    - [allowance](#allowance)
    - [balanceOf](#balanceof)
    - [totalSupply](#totalsupply)
  - [ERC20Permit Functions](#erc20permit-functions)
    - [permit](#permit)
    - [nonces](#nonces)
    - [DOMAIN_SEPARATOR](#domain_separator)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

| Constants      | Value                                        |
|----------------|----------------------------------------------|
| Address        | `0x4200000000000000000000000000000000000042` |
| Token name     | `Optimism`                                   |
| Token symbol   | `OP`                                         |
| Token decimals | `18`                                         |

The `GovernanceToken` is an ERC20 token contract that serves as the Optimism governance token. It inherits from
OpenZeppelin's `ERC20Burnable`, `ERC20Votes`, and `Ownable` contracts, providing standard token functionality with
voting and delegation capabilities. The contract is deployed as a predeploy at a fixed address on L2.

The token enables a representative voting system where token holders can delegate their voting power to other
addresses. The contract maintains a complete history of voting power through checkpoints, allowing governance systems
to query voting power at any historical block. The contract owner, typically a `MintManager` contract, has exclusive
permission to mint new tokens according to a predetermined inflation schedule.

The `GovernanceToken` implements EIP-2612 (permit) allowing gasless approvals via signatures. It supports basic
delegation where users delegate their entire token balance to a single address, and delegations cannot be re-delegated
to another address.

## Definitions

### Voting Power

The amount of governance influence an address has, measured in token units. Voting power is derived from delegated
token balances and is tracked historically through checkpoints. An address's voting power equals the sum of all tokens
delegated to it.

### Delegation

The act of assigning one's token balance to another address (or oneself) for voting purposes. Delegation does not
transfer token ownership or restrict token transfers. Users must explicitly delegate (even to themselves) to activate
voting power tracking. Delegations are "basic" in that they assign the entire token balance and cannot be
re-delegated.

### Checkpoint

A data structure recording an address's voting power at a specific block number. Checkpoints are created whenever
voting power changes due to delegation or token transfers. The structure contains:

- `fromBlock` (uint32): The block number when this voting power became active
- `votes` (uint224): The voting power amount at that block

## Assumptions

### aGT-001: Owner enforces token inflation schedule

The contract owner (MintManager) is assumed to correctly enforce the predetermined token inflation schedule when
calling the `mint` function. The GovernanceToken contract itself does not validate minting amounts or timing.

#### Mitigations

- MintManager contract implements inflation schedule logic
- MintManager ownership is controlled by governance
- Inflation schedule is publicly documented and auditable

### aGT-002: OpenZeppelin contract implementations are correct

The GovernanceToken relies on OpenZeppelin's implementations of ERC20, ERC20Burnable, ERC20Votes, ERC20Permit, and
Ownable. These base contracts are assumed to be secure and correctly implemented.

#### Mitigations

- OpenZeppelin contracts are widely audited and battle-tested
- Specific OpenZeppelin version is pinned in dependencies
- Contract inheritance is minimal and well-understood

### aGT-003: Users understand delegation requirement for voting

Users are assumed to understand that they must explicitly delegate their tokens (even to themselves) to activate voting
power tracking. Without delegation, tokens do not contribute to any address's voting power.

#### Mitigations

- Governance interfaces guide users through delegation
- Documentation clearly explains delegation requirement
- Delegation status is queryable via `delegates` function

### aGT-004: Governance systems query historical voting power correctly

Governance systems are assumed to correctly use `getPastVotes` with appropriate block numbers to determine voting power
for proposals. Querying voting power at incorrect blocks could lead to incorrect vote tallying.

#### Mitigations

- Governance contracts specify snapshot blocks in proposals
- Historical voting power is immutable and deterministic
- Query functions revert for future blocks

## Dependencies

This specification depends on the following external standards and contracts:

- **ERC20**: Standard fungible token interface defined in [EIP-20](https://eips.ethereum.org/EIPS/eip-20)
- **ERC20Permit**: Gasless approval mechanism defined in [EIP-2612](https://eips.ethereum.org/EIPS/eip-2612)
- **ERC20Votes**: OpenZeppelin's voting and delegation extension implementing checkpoint-based vote tracking
- **ERC20Burnable**: OpenZeppelin's extension allowing token burning
- **Ownable**: OpenZeppelin's access control pattern providing owner-only functions

## Invariants

### iGT-001: Only owner can mint new tokens

New tokens MUST only be created by the contract owner through the `mint` function. No other mechanism for token
creation may exist.

#### Impact

**Severity: Critical**

Unauthorized token minting would violate the predetermined inflation schedule, dilute existing token holders, and
compromise governance integrity by allowing arbitrary voting power creation.

### iGT-002: Token supply can only decrease through authorized burning

Token supply MUST only decrease when:

- A token holder burns their own tokens via `burn`, OR
- An approved address burns tokens on behalf of a holder via `burnFrom`

No other mechanism for reducing supply or destroying tokens may exist.

#### Impact

**Severity: Critical**

Unauthorized token destruction would compromise user balances and voting power. Conversely, inability to burn tokens
would prevent supply reduction mechanisms.

### iGT-003: Voting power accurately reflects delegated balances

An address's voting power MUST always equal the sum of all token balances delegated to it. When tokens are transferred
or delegations change, voting power MUST update accordingly in the same transaction.

#### Impact

**Severity: Critical**

Inaccurate voting power would compromise governance decisions, potentially allowing minority token holders to pass
proposals or preventing legitimate proposals from passing.

### iGT-004: Historical voting records are immutable

Once a checkpoint is created for a given block, the voting power recorded for that block MUST never change. Historical
queries via `getPastVotes` and `getPastTotalSupply` MUST always return the same values for the same block number.

#### Impact

**Severity: Critical**

Mutable historical voting records would allow retroactive manipulation of governance votes, completely undermining the
integrity of the governance system.

### iGT-005: Token transfers never fail due to delegation

Token transfers MUST succeed regardless of delegation status. An active delegation MUST NOT prevent the delegator from
transferring their tokens to another address.

#### Impact

**Severity: High**

If delegation locked tokens, users would face a choice between participating in governance and maintaining token
liquidity, severely limiting governance participation.

### iGT-006: Total supply never exceeds maximum

The total token supply MUST never exceed `type(uint224).max` (2^224 - 1 = 26,959,946,667,150,639,794,667,015 tokens).
Mint operations that would exceed this limit MUST revert.

#### Impact

**Severity: High**

Exceeding the uint224 maximum would cause voting power calculations to overflow, corrupting checkpoint data and making
voting power queries unreliable.

### iGT-007: Delegations cannot be re-delegated

When address A delegates to address B, address B MUST NOT be able to further delegate A's tokens to address C. Only
direct delegation from token holders is permitted.

#### Impact

**Severity: Medium**

Re-delegation would create complex delegation chains that could be exploited to obscure voting power sources or
manipulate voting power calculations.

### iGT-008: Delegation changes are properly tracked

Every delegation change MUST emit a `DelegateChanged` event and corresponding `DelegateVotesChanged` events for
affected addresses. The `delegates` function MUST always return the current delegation target for any address.

#### Impact

**Severity: Medium**

Without proper event emission and state tracking, off-chain systems cannot accurately track delegation changes, making
governance monitoring and vote tallying unreliable.

## Function Specifications

### Token Minting

#### mint

```solidity
function mint(address _account, uint256 _amount) public onlyOwner
```

Allows the contract owner to mint new tokens to a specified address.

- MUST only be callable by the contract owner (enforced by `onlyOwner` modifier)
- MUST revert if `_account` is the zero address
- MUST revert if minting `_amount` would cause total supply to exceed `type(uint224).max`
- MUST increase `_account`'s balance by `_amount`
- MUST increase total supply by `_amount`
- MUST create a checkpoint for total supply
- MUST emit a `Transfer` event with `from` set to zero address
- MUST update voting power for the delegate of `_account` if delegation exists
- MUST emit `DelegateVotesChanged` event if `_account` has delegated

### Token Burning

#### burn

```solidity
function burn(uint256 amount) public
```

Allows a token holder to destroy their own tokens.

- MUST be callable by any address
- MUST revert if caller's balance is less than `amount`
- MUST decrease caller's balance by `amount`
- MUST decrease total supply by `amount`
- MUST create a checkpoint for total supply
- MUST emit a `Transfer` event with `to` set to zero address
- MUST update voting power for the delegate of caller if delegation exists
- MUST emit `DelegateVotesChanged` event if caller has delegated

#### burnFrom

```solidity
function burnFrom(address account, uint256 amount) public
```

Allows an approved address to destroy tokens on behalf of a token holder.

- MUST be callable by any address
- MUST revert if `account`'s balance is less than `amount`
- MUST revert if caller's allowance from `account` is less than `amount`
- MUST decrease caller's allowance from `account` by `amount`
- MUST decrease `account`'s balance by `amount`
- MUST decrease total supply by `amount`
- MUST create a checkpoint for total supply
- MUST emit a `Transfer` event with `to` set to zero address
- MUST update voting power for the delegate of `account` if delegation exists
- MUST emit `DelegateVotesChanged` event if `account` has delegated

### Delegation Functions

#### delegate

```solidity
function delegate(address delegatee) public
```

Delegates the caller's voting power to a specified address.

- MUST be callable by any address
- MUST allow `delegatee` to be the caller's own address (self-delegation)
- MUST allow `delegatee` to be the zero address (removes delegation)
- MUST update the caller's delegation target to `delegatee`
- MUST move voting power from the previous delegate to the new `delegatee`
- MUST create checkpoints for both the previous delegate and new `delegatee`
- MUST emit a `DelegateChanged` event with caller, old delegate, and new delegate
- MUST emit `DelegateVotesChanged` events for both old and new delegates if voting power changed

#### delegateBySig

```solidity
function delegateBySig(
    address delegatee,
    uint256 nonce,
    uint256 expiry,
    uint8 v,
    bytes32 r,
    bytes32 s
) public
```

Delegates voting power using an EIP-712 signature, enabling gasless delegation.

- MUST be callable by any address (relayer)
- MUST revert if `block.timestamp` is greater than `expiry`
- MUST recover the signer address from the signature using EIP-712 typed data
- MUST revert if the recovered signer's nonce does not match the provided `nonce`
- MUST increment the signer's nonce after successful validation
- MUST delegate the signer's voting power to `delegatee` (same effects as `delegate`)
- MUST emit a `DelegateChanged` event with signer, old delegate, and new delegate
- MUST emit `DelegateVotesChanged` events for both old and new delegates if voting power changed

### Voting Power Query Functions

#### getVotes

```solidity
function getVotes(address account) public view returns (uint256)
```

Returns the current voting power of an address.

- MUST return the voting power of `account` at the current block
- MUST return 0 if `account` has no checkpoints (no one has delegated to them)
- MUST return the `votes` value from the most recent checkpoint for `account`
- MUST NOT revert for any input

#### getPastVotes

```solidity
function getPastVotes(address account, uint256 blockNumber) public view returns (uint256)
```

Returns the voting power of an address at a specific historical block.

- MUST revert if `blockNumber` is greater than or equal to the current block number
- MUST return 0 if `account` had no checkpoints at or before `blockNumber`
- MUST return the voting power from the most recent checkpoint at or before `blockNumber`
- MUST use binary search to efficiently locate the appropriate checkpoint
- MUST return the same value for the same inputs across all future queries (immutability)

#### getPastTotalSupply

```solidity
function getPastTotalSupply(uint256 blockNumber) public view returns (uint256)
```

Returns the total token supply at a specific historical block.

- MUST revert if `blockNumber` is greater than or equal to the current block number
- MUST return 0 if no supply checkpoints existed at or before `blockNumber`
- MUST return the total supply from the most recent checkpoint at or before `blockNumber`
- MUST use binary search to efficiently locate the appropriate checkpoint
- MUST return the same value for the same inputs across all future queries (immutability)

#### delegates

```solidity
function delegates(address account) public view returns (address)
```

Returns the address that an account is currently delegating to.

- MUST return the current delegation target for `account`
- MUST return zero address if `account` has never delegated
- MUST return zero address if `account` has explicitly delegated to zero address
- MUST NOT revert for any input

#### checkpoints

```solidity
function checkpoints(address account, uint32 pos) public view returns (Checkpoint memory)
```

Retrieves a specific checkpoint for an address by index.

- MUST return the checkpoint at index `pos` in `account`'s checkpoint array
- MUST revert if `pos` is greater than or equal to the number of checkpoints for `account`
- MUST return a struct containing `fromBlock` (uint32) and `votes` (uint224)

#### numCheckpoints

```solidity
function numCheckpoints(address account) public view returns (uint32)
```

Returns the total number of checkpoints for an address.

- MUST return the length of `account`'s checkpoint array
- MUST return 0 if `account` has no checkpoints
- MUST NOT revert for any input

### ERC20 Standard Functions

#### transfer

```solidity
function transfer(address to, uint256 amount) public returns (bool)
```

Transfers tokens from the caller to another address.

- MUST revert if caller's balance is less than `amount`
- MUST revert if `to` is the zero address
- MUST decrease caller's balance by `amount`
- MUST increase `to`'s balance by `amount`
- MUST emit a `Transfer` event
- MUST update voting power for delegates of both caller and `to` if delegations exist
- MUST emit `DelegateVotesChanged` events for affected delegates
- MUST return true on success

#### transferFrom

```solidity
function transferFrom(address from, address to, uint256 amount) public returns (bool)
```

Transfers tokens from one address to another using an allowance.

- MUST revert if `from`'s balance is less than `amount`
- MUST revert if caller's allowance from `from` is less than `amount` (unless allowance is max uint256)
- MUST revert if `to` is the zero address
- MUST decrease caller's allowance from `from` by `amount` (unless allowance is max uint256)
- MUST decrease `from`'s balance by `amount`
- MUST increase `to`'s balance by `amount`
- MUST emit a `Transfer` event
- MUST update voting power for delegates of both `from` and `to` if delegations exist
- MUST emit `DelegateVotesChanged` events for affected delegates
- MUST return true on success

#### approve

```solidity
function approve(address spender, uint256 amount) public returns (bool)
```

Approves another address to spend tokens on behalf of the caller.

- MUST set the allowance of `spender` over caller's tokens to `amount`
- MUST emit an `Approval` event
- MUST return true on success
- MUST allow `spender` to be the zero address
- MUST allow setting allowance to 0 to revoke approval

#### allowance

```solidity
function allowance(address owner, address spender) public view returns (uint256)
```

Returns the amount of tokens that a spender is allowed to spend on behalf of an owner.

- MUST return the current allowance of `spender` over `owner`'s tokens
- MUST return 0 if no allowance has been set
- MUST NOT revert for any input

#### balanceOf

```solidity
function balanceOf(address account) public view returns (uint256)
```

Returns the token balance of an address.

- MUST return the current token balance of `account`
- MUST return 0 if `account` has never received tokens
- MUST NOT revert for any input

#### totalSupply

```solidity
function totalSupply() public view returns (uint256)
```

Returns the total token supply.

- MUST return the current total supply of tokens
- MUST equal the sum of all address balances
- MUST NOT revert

### ERC20Permit Functions

#### permit

```solidity
function permit(
    address owner,
    address spender,
    uint256 value,
    uint256 deadline,
    uint8 v,
    bytes32 r,
    bytes32 s
) public
```

Approves a spender using an EIP-2612 signature, enabling gasless approvals.

- MUST be callable by any address (relayer)
- MUST revert if `block.timestamp` is greater than `deadline`
- MUST recover the signer address from the signature using EIP-712 typed data
- MUST revert if the recovered signer does not match `owner`
- MUST revert if the nonce does not match `owner`'s current nonce
- MUST increment `owner`'s nonce after successful validation
- MUST set the allowance of `spender` over `owner`'s tokens to `value`
- MUST emit an `Approval` event

#### nonces

```solidity
function nonces(address owner) public view returns (uint256)
```

Returns the current nonce for an address, used for permit and delegateBySig.

- MUST return the current nonce for `owner`
- MUST return 0 if `owner` has never used permit or delegateBySig
- MUST increment by 1 after each successful permit or delegateBySig call
- MUST NOT revert for any input

#### DOMAIN_SEPARATOR

```solidity
function DOMAIN_SEPARATOR() public view returns (bytes32)
```

Returns the EIP-712 domain separator for this contract.

- MUST return the domain separator used for EIP-712 signature verification
- MUST be computed according to EIP-712 specification
- MUST include contract name, version, chain ID, and contract address
- MUST NOT revert
