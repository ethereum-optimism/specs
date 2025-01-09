# Shared Lockbox

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Design](#design)
  - [Interface and properties](#interface-and-properties)
  - [Events](#events)
- [Invariants](#invariants)
  - [System level invariants](#system-level-invariants)
  - [Contract level invariants](#contract-level-invariants)
- [Reference implementation](#reference-implementation)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

With interoperable ETH, withdrawals will fail if the referenced `OptimismPortal` lacks sufficient ETH.
This is due to having the possibility to move ETH liquidity across the different chains and it could happen
that a chain ends up with more liquidity than its `OptimismPortal`.
The `SharedLockbox` improves the Superchain's interoperable ETH withdrawal user experience and avoids this issue.
To do so, it unifies ETH L1 liquidity in a single contract (`SharedLockbox`), enabling seamless withdrawals of ETH
from any OP chain in the Superchain, regardless of where the ETH was initially deposited.

## Design

The `SharedLockbox` contract is designed to manage the unified ETH liquidity for the Superchain.
It implements two main functions: `lockETH` for depositing ETH into the lockbox,
and `unlockETH` for withdrawing ETH from the lockbox.
These functions are called by the `OptimismPortal` contracts to manage the shared ETH liquidity
when making deposits or finalizing withdrawals.
These `OptimismPortal`s will be allowlisted by the `SuperchainConfig` using the `authorizePortal` function
when a chain is added.
The `SharedLockbox` contract is proxied and managed by the L1 `ProxyAdmin`.

### Interface and properties

**`lockETH`**

Deposits and locks ETH into the lockbox's liquidity pool.

- The function MUST accept ETH.
- Only authorized `OptimismPortal` addresses MUST be allowed to interact.
- The function MUST NOT revert when called by an authorized `OptimismPortal`
- The function MUST emit the `ETHLocked` event with the `portal` that called it and the `amount`.

```solidity
function lockETH() external payable;
```

**`unlockETH`**

Withdraws a specified amount of ETH from the lockbox's liquidity pool.

- Only authorized `OptimismPortal` addresses MUST be allowed to interact.
- The function MUST NOT revert when called by an authorized `OptimismPortal`
- The function MUST emit the `ETHUnlocked` event with the `portal` that called it and the `amount`.

```solidity
function unlockETH(uint256 _value) external;
```

**`authorizePortal`**

Grants authorization to a specific `OptimismPortal` contract.

- Only `SuperchainConfig` address MUST be allowed to interact.
- The function MUST add the specified address to the mapping of authorized portals.
- The function MUST emit the [`PortalAuthorized`](#events) event when a portal is successfully added.

```solidity
function authorizePortal(address _portal) external;
```

### Events

**`ETHLocked`**

MUST be triggered when `lockETH` is called

```solidity
event ETHLocked(address indexed portal, uint256 amount);
```

**`ETHUnlocked`**

MUST be triggered when `unlockETH` is called

```solidity
event ETHUnlocked(address indexed portal, uint256 amount);
```

**`PortalAuthorized`**

MUST be triggered when `authorizePortal` is called

```solidity
event PortalAuthorized(address indexed portal);
```

## Invariants

### System level invariants

- The ETH held in the SharedLockbox MUST never be less than the amount deposited but not yet withdrawn by the `OptimismPortal`s

- The ETH unlocked by any `OptimismPortal` MUST NOT exceed the available shared liquidity in the `SharedLockbox`.

- The total withdrawable ETH amount present on all the dependency set’s chains MUST NEVER be more than the amount held
  by the `SharedLockbox` of the cluster
  > With "withdrawable amount", the ETH balance held on `ETHLiquidity` is excluded

### Contract level invariants

- It MUST allow only authorized portals to lock ETH

- It MUST allow only authorized portals to unlock ETH

- Only the `SuperchainConfig` contract MUST be able to authorize an `OptimismPortal`

- It MUST be in paused state if the `SuperchainConfig` is paused

- No Ether MUST flow out of the contract when in a paused state

- No `OptimismPortal` can be authorized when in a paused state

- It MUST NOT trigger a new deposit when ETH amount is being unlocked from the `SharedLockbox` by the `OptimismPortal`

- It MUST emit:

  - An `ETHLocked` event when locking ETH

  - An `ETHUnlocked` event when unlocking ETH

  - A `PortalAuthorized` event when authorizing a new portal

## Reference implementation

An example implementation could look like this:

```solidity
// OptimismPortals that are part of the dependency cluster.
mapping(address _portal => bool) internal _authorizedPortals;

function lockETH() external payable {
    require(_authorizedPortals[msg.sender], "Unauthorized");

    emit ETHLocked(msg.sender, msg.value);
}

function unlockETH(uint256 _value) external {
    require(_authorizedPortals[msg.sender], "Unauthorized");

    // Using `donateETH` to not trigger a deposit
    IOptimismPortal(msg.sender).donateETH{ value: _value }();

    emit ETHUnlocked(msg.sender, _value);
}

function authorizePortal(address _portal) external {
    require(msg.sender == superchainConfig, "Unauthorized");

    _authorizedPortals[_portal] = true;

    emit PortalAuthorized(_portal);
}
```
