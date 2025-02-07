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
- [Architecture](#architecture)
  - [Authorization Flow](#authorization-flow)
  - [ETH Management](#eth-management)

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

Authorization of `OptimismPortal`s is managed by the `SuperchainConfig` contract when a chain
is added to the dependency set.
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

Withdraws a specified amount of ETH from the lockbox's liquidity pool to the `OptimismPortal` calling it.

- Only authorized `OptimismPortal` addresses MUST be allowed to interact.
- The function MUST NOT revert when called by an authorized `OptimismPortal` unless paused
- The function MUST emit the `ETHUnlocked` event with the `portal` that called it and the `amount`.
- The function MUST use `donateETH` when sending ETH to avoid triggering deposits

```solidity
function unlockETH(uint256 _value) external;
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

## Invariants

### System level invariants

- The ETH held in the SharedLockbox MUST never be less than the amount deposited but not yet withdrawn by the `OptimismPortal`s

- The ETH unlocked by any `OptimismPortal` MUST NOT exceed the available shared liquidity in the `SharedLockbox`.

- The total withdrawable ETH amount present on all the dependency set's chains MUST NEVER be more than the amount held
  by the `SharedLockbox` of the cluster
  > With "withdrawable amount", the ETH balance held on `ETHLiquidity` is excluded

### Contract level invariants

- It MUST allow only authorized portals to lock ETH

- It MUST allow only authorized portals to unlock ETH

- It MUST be in paused state if the `SuperchainConfig` is paused

- No Ether MUST flow out of the contract when in a paused state

- It MUST NOT trigger a new deposit when ETH amount is being unlocked from the `SharedLockbox` by the `OptimismPortal`

- It MUST emit:

  - An `ETHLocked` event when locking ETH

  - An `ETHUnlocked` event when unlocking ETH

## Architecture

### Authorization Flow

1. When a new chain is added to the dependency set through the `SuperchainConfig`, its `OptimismPortal` is authorized

2. The `SharedLockbox` checks portal authorization by querying the `SuperchainConfig.authorizedPortals()` function

3. Only authorized portals can lock and unlock ETH from the `SharedLockbox`

### ETH Management

- ETH is locked in the `SharedLockbox` when:

  - A portal migrates its ETH liquidity when joining the dependency set

  - A deposit is made with ETH value on an authorized portal

- ETH is unlocked from the `SharedLockbox` when:

  - An authorized portal finalizes a withdrawal that requires ETH
