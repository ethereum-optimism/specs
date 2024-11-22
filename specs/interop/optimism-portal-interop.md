# OptimismPortal

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
  - [Interface and properties](#interface-and-properties)
  - [Integrating `SharedLockbox`](#integrating-sharedlockbox)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The `OptimismPortal` contract is upgraded to integrate the `SharedLockbox` and start using the shared ETH liquidity.

### Interface and properties

The `OptimismPortal` contract will add the following storage layout and modified functions:

**`SHARED_LOCKBOX`**

- An immutable address pointing to the `SharedLockbox` contract.
- This address MUST be immutable because all `OptimismPortals` will point to the same `SharedLockbox`,
  and this address SHOULD not change.

### Integrating `SharedLockbox`

The integration with the `SharedLockbox` involves adding extra steps when executing deposit transactions
or finalizing withdrawal transactions.
These steps include locking and unlocking ETH without altering other aspects of the current `OptimismPortal` implementation.
To implement this solution, the following changes are needed:

**`depositTransaction`**

Calls `lockETH` on the `SharedLockbox` with the `msg.value`.

- The function MUST call `lockETH` on the `SharedLockbox` if:
  - The token is `ETHER`.
  - `msg.value` is greater than zero.

**`finalizeWithdrawalTransactionExternalProof`**

Calls `unlockETH` on the `SharedLockbox` with the `tx.value`.

- The function MUST call `unlockETH` on the `SharedLockbox` if:
  - The token is `ETHER`.
  - `tx.value` is greater than zero.
- The ETH is received by the `OptimismPortal` and then sent with the withdrawal transaction
