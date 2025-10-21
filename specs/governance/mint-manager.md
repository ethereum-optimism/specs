# MintManager

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
- [Assumptions](#assumptions)
  - [aMM-001: GovernanceToken implements required functions correctly](#amm-001-governancetoken-implements-required-functions-correctly)
    - [Mitigations](#mitigations)
  - [aMM-002: Block timestamp reliability](#amm-002-block-timestamp-reliability)
    - [Mitigations](#mitigations-1)
  - [aMM-003: Owner acts within governance constraints](#amm-003-owner-acts-within-governance-constraints)
    - [Mitigations](#mitigations-2)
- [Dependencies](#dependencies)
- [Invariants](#invariants)
  - [iMM-001: Mint cap enforcement](#imm-001-mint-cap-enforcement)
    - [Impact](#impact)
  - [iMM-002: Time-based minting restriction](#imm-002-time-based-minting-restriction)
    - [Impact](#impact-1)
  - [iMM-003: Exclusive minting authority](#imm-003-exclusive-minting-authority)
    - [Impact](#impact-2)
  - [iMM-004: Ownership transfer control](#imm-004-ownership-transfer-control)
    - [Impact](#impact-3)
  - [iMM-005: Valid successor requirement](#imm-005-valid-successor-requirement)
    - [Impact](#impact-4)
- [Function Specifications](#function-specifications)
  - [constructor](#constructor)
  - [mint](#mint)
  - [upgrade](#upgrade)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The `MintManager` contract serves as the owner of the [GovernanceToken](./gov-token.md) and controls the token
inflation schedule. It enforces a maximum annual inflation rate of 2% of the total token supply and ensures that
minting can only occur once per 365-day period. The contract is upgradeable, allowing the owner to transfer control
to a new `MintManager` implementation if changes to the inflation schedule are required.

The `MintManager` is deployed on L2 and manages the minting of governance tokens according to a predictable,
rate-limited schedule. This provides transparency and predictability for token holders while maintaining flexibility
for governance-approved changes through the upgrade mechanism.

## Definitions

**Mint Cap**
The maximum percentage of the total token supply that can be minted in a single minting operation. Set to 2%
(represented as 20/1000 with 4 decimal precision).

**Mint Period**
The minimum time interval that must elapse between consecutive minting operations. Set to 365 days.

**Mint Permitted After**
A timestamp stored in the contract that tracks when the next minting operation is allowed. After each mint, this
value is set to `block.timestamp + MINT_PERIOD`.

**First Mint**
The initial minting operation after contract deployment, which has no time restriction or cap enforcement. This is
identified by `mintPermittedAfter == 0`.

## Assumptions

### aMM-001: GovernanceToken implements required functions correctly

The `GovernanceToken` contract correctly implements the `mint(address,uint256)` function, `transferOwnership(address)`
function, and `totalSupply()` view function according to their expected behavior. Specifically:

- `mint()` increases the token balance of the specified account by the specified amount
- `totalSupply()` accurately returns the current total supply of tokens
- `transferOwnership()` transfers ownership to the specified address

#### Mitigations

- The `GovernanceToken` contract is part of the same protocol and is subject to the same security audits
- The interface is well-defined in `IGovernanceToken.sol`
- The implementation follows OpenZeppelin's standard patterns

### aMM-002: Block timestamp reliability

The EVM `block.timestamp` value is sufficiently reliable for enforcing the 365-day minting period. While miners can
manipulate timestamps within a small range (~15 seconds), this manipulation is negligible compared to the 365-day
period.

#### Mitigations

- The 365-day period is long enough that minor timestamp manipulation has no practical impact
- Ethereum consensus rules limit timestamp manipulation
- The time-based restriction is a rate limit, not a precise scheduling mechanism

### aMM-003: Owner acts within governance constraints

The contract owner (typically a governance multisig or DAO) will only call `mint()` and `upgrade()` functions in
accordance with governance decisions and the protocol's established rules. The owner will not abuse their authority
to mint excessive tokens or transfer ownership to malicious addresses.

#### Mitigations

- Owner is expected to be a governance-controlled address (e.g., multisig or Governor contract)
- All minting operations are subject to the on-chain mint cap and time restrictions
- Ownership transfers are transparent on-chain and subject to community oversight
- The upgrade mechanism allows for replacing a compromised or malicious owner

## Dependencies

This specification depends on:

- [GovernanceToken](./gov-token.md) - The ERC20Votes token that this contract has permission to mint

## Invariants

### iMM-001: Mint cap enforcement

After the first mint, no single minting operation can mint more than 2% of the current total token supply.

**Full Description:**
Once `mintPermittedAfter` has been set to a non-zero value (after the first mint), any subsequent call to `mint()`
MUST enforce that the requested mint amount does not exceed `(totalSupply * MINT_CAP) / DENOMINATOR`, which equals
2% of the current total supply. This ensures that token inflation is bounded and predictable.

#### Impact

**Severity: Critical**

If this invariant is violated, the owner could mint an unlimited number of tokens, leading to:
- Severe token dilution for existing holders
- Loss of governance voting power for existing token holders
- Destruction of the token's economic value
- Complete loss of trust in the protocol's governance system

### iMM-002: Time-based minting restriction

After the first mint, subsequent minting operations can only occur after 365 days have elapsed since the previous mint.

**Full Description:**
Once `mintPermittedAfter` has been set to a non-zero value, any call to `mint()` MUST revert if
`block.timestamp < mintPermittedAfter`. This ensures that minting operations are rate-limited to at most once per
year, preventing rapid inflation even if the owner attempts multiple mints.

#### Impact

**Severity: Critical**

If this invariant is violated, the owner could:
- Mint the maximum 2% multiple times in rapid succession
- Cause uncontrolled inflation far exceeding the intended 2% annual rate
- Undermine the predictability and transparency of the token supply schedule
- Violate the expectations of token holders regarding inflation rates

### iMM-003: Exclusive minting authority

Only the contract owner can successfully call the `mint()` function to create new governance tokens.

**Full Description:**
The `mint()` function MUST be protected by the `onlyOwner` modifier, ensuring that only the address returned by
`owner()` can execute minting operations. Any call from a non-owner address MUST revert.

#### Impact

**Severity: Critical**

If this invariant is violated:
- Unauthorized parties could mint tokens without governance approval
- The entire governance system would be compromised
- Token supply would become unpredictable and uncontrolled
- The economic security of the protocol would be destroyed

### iMM-004: Ownership transfer control

Only the current contract owner can transfer ownership of the GovernanceToken to a new MintManager.

**Full Description:**
The `upgrade()` function MUST be protected by the `onlyOwner` modifier, ensuring that only the current owner can
initiate an upgrade to a new `MintManager` implementation. This prevents unauthorized parties from taking control of
the token minting authority.

#### Impact

**Severity: Critical**

If this invariant is violated:
- Attackers could transfer ownership to a malicious contract
- The governance system would lose control over token minting
- A malicious MintManager could mint unlimited tokens or implement harmful policies
- The protocol's governance would be permanently compromised

### iMM-005: Valid successor requirement

The GovernanceToken ownership can only be transferred to a non-zero address.

**Full Description:**
When calling `upgrade()`, the `_newMintManager` parameter MUST NOT be the zero address (`address(0)`). Transferring
ownership to the zero address would permanently lock the token's minting and ownership functions, as no one could
call the owner-restricted functions.

#### Impact

**Severity: High**

If ownership is transferred to the zero address:
- No future minting would be possible
- The token supply would be permanently frozen
- No further upgrades to the MintManager would be possible
- The governance system would lose the ability to adjust the inflation schedule
- This would effectively be an irreversible shutdown of the minting mechanism

## Function Specifications

### constructor

```solidity
constructor(address _upgrader, address _governanceToken)
```

Initializes the `MintManager` contract with the specified owner and governance token.

**Parameters:**
- `_upgrader`: The address that will become the owner of this contract
- `_governanceToken`: The address of the `GovernanceToken` contract that this manager will control

**Behavior:**
- MUST call `transferOwnership(_upgrader)` to set the contract owner
- MUST set `governanceToken` to the provided `_governanceToken` address
- MUST leave `mintPermittedAfter` at its default value of 0, indicating no mints have occurred yet
- MUST NOT validate that `_upgrader` or `_governanceToken` are non-zero addresses (caller responsibility)

**State Changes:**
- Sets `owner()` to `_upgrader`
- Sets `governanceToken` to `_governanceToken`
- Leaves `mintPermittedAfter` at 0

**Events:**
- Emits `OwnershipTransferred(address(0), _upgrader)` (from OpenZeppelin's Ownable)

### mint

```solidity
function mint(address _account, uint256 _amount) public onlyOwner
```

Mints new governance tokens to the specified account, subject to time and cap restrictions.

**Parameters:**
- `_account`: The address that will receive the newly minted tokens
- `_amount`: The number of tokens to mint (in wei, with 18 decimals)

**Behavior:**
- MUST revert if caller is not the contract owner (enforced by `onlyOwner` modifier)
- If `mintPermittedAfter > 0` (not the first mint):
  - MUST revert with "MintManager: minting not permitted yet" if `block.timestamp < mintPermittedAfter`
  - MUST revert with "MintManager: mint amount exceeds cap" if
    `_amount > (governanceToken.totalSupply() * MINT_CAP) / DENOMINATOR`
- If `mintPermittedAfter == 0` (first mint):
  - MUST NOT enforce any time restriction
  - MUST NOT enforce the mint cap
- MUST set `mintPermittedAfter = block.timestamp + MINT_PERIOD` (365 days from now)
- MUST call `governanceToken.mint(_account, _amount)` to perform the actual minting

**State Changes:**
- Updates `mintPermittedAfter` to `block.timestamp + MINT_PERIOD`

**External Calls:**
- Calls `governanceToken.totalSupply()` to check current supply (if not first mint)
- Calls `governanceToken.mint(_account, _amount)` to mint tokens

**Events:**
- Emits events from the `GovernanceToken` contract (Transfer event for minting)

**Reverts:**
- If caller is not owner: "Ownable: caller is not the owner"
- If minting before permitted time: "MintManager: minting not permitted yet"
- If amount exceeds cap: "MintManager: mint amount exceeds cap"

### upgrade

```solidity
function upgrade(address _newMintManager) public onlyOwner
```

Transfers ownership of the `GovernanceToken` to a new `MintManager` contract, effectively upgrading the minting system.

**Parameters:**
- `_newMintManager`: The address of the new `MintManager` contract that will become the owner of the `GovernanceToken`

**Behavior:**
- MUST revert if caller is not the contract owner (enforced by `onlyOwner` modifier)
- MUST revert with "MintManager: mint manager cannot be the zero address" if
  `_newMintManager == address(0)`
- MUST call `governanceToken.transferOwnership(_newMintManager)` to transfer ownership

**State Changes:**
- None in this contract (state changes occur in the `GovernanceToken` contract)

**External Calls:**
- Calls `governanceToken.transferOwnership(_newMintManager)`

**Events:**
- Emits `OwnershipTransferred` event from the `GovernanceToken` contract

**Reverts:**
- If caller is not owner: "Ownable: caller is not the owner"
- If `_newMintManager` is zero address: "MintManager: mint manager cannot be the zero address"

**Post-Conditions:**
- After this function executes successfully, this `MintManager` contract will no longer be able to mint tokens or
  perform further upgrades
- The new `MintManager` at `_newMintManager` will have full control over the `GovernanceToken`
- The new `MintManager` will have its own `mintPermittedAfter` state, independent of this contract's state
