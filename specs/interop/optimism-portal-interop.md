# OptimismPortal Interop

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
  - [Integrating `SharedLockbox`](#integrating-sharedlockbox)
- [Interface and properties](#interface-and-properties)
  - [ETH Management](#eth-management)
    - [`migrateLiquidity`](#migrateliquidity)
  - [Internal ETH Functions](#internal-eth-functions)
    - [`_lockETH`](#_locketh)
    - [`_unlockETH`](#_unlocketh)
- [Events](#events)
  - [`ETHMigrated`](#ethmigrated)
- [Invariants](#invariants)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The `OptimismPortal` contract is extended to integrate with the `SharedLockbox`
for managing unified ETH liquidity.
This liquidity consists of every ETH balance migrated from each `OptimismPortal` when joining
the op-governed dependency set.

It is possible to upgrade to this version without being part of the op-governed dependency set. In this case,
the corresponding chain would need to deploy and manage its own `SharedLockbox` and `SuperchainConfig`.

### Integrating `SharedLockbox`

The integration with the `SharedLockbox` involves locking ETH when executing deposit transactions and unlocking ETH
when finalizing withdrawal transactions, without altering other aspects of the current `OptimismPortal` implementation.

## Interface and properties

### ETH Management

#### `migrateLiquidity`

Migrates the ETH liquidity to the SharedLockbox. This function will only be called once by the
SuperchainConfig when adding this chain to the dependency set.

```solidity
function migrateLiquidity() external;
```

- MUST only be callable by the `SuperchainConfig` contract
- MUST set the migrated flag to true
- MUST transfer all ETH balance to the `SharedLockbox`
- MUST emit an `ETHMigrated` event with the amount transferred

### Internal ETH Functions

The contract overrides two internal functions from `OptimismPortal2` to handle ETH management with the `SharedLockbox`:

#### `_lockETH`

Called during deposit transactions to handle ETH locking.

```solidity
function _lockETH() internal virtual override;
```

- MUST be called during `depositTransaction` when there is ETH value
- If not migrated, function is a no-op
- If migrated:
  - MUST lock any ETH value in the `SharedLockbox`
  - MUST NOT revert on zero value

#### `_unlockETH`

Called during withdrawal finalization to handle ETH unlocking.

```solidity
function _unlockETH(Types.WithdrawalTransaction memory _tx) internal virtual override;
```

- MUST be called during withdrawal finalization when there is ETH value
- If not migrated, function is a no-op
- If migrated:
  - MUST unlock the withdrawal value from the `SharedLockbox`
  - MUST NOT revert on zero value
  - MUST revert if withdrawal target is the `SharedLockbox`

## Events

### `ETHMigrated`

MUST be triggered when the ETH liquidity is migrated to the SharedLockbox.

```solidity
event ETHMigrated(uint256 amount);
```

## Invariants

- Before migration:

  - Deposits MUST keep the ETH in the portal

  - Withdrawals MUST use the portal's own ETH balance

- After migration:

  - Deposits MUST lock the ETH in the `SharedLockbox`

  - Withdrawals MUST unlock the ETH from the `SharedLockbox` and forward it to the withdrawal target

  - The contract MUST NOT hold any ETH balance from deposits or withdrawals

- General invariants:

  - The contract MUST be able to handle zero ETH value operations

  - The contract MUST NOT allow withdrawals to target the `SharedLockbox` address

  - The contract MUST only migrate liquidity once
