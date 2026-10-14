# Regolith Deposits

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Changes](#changes)
  - [`isSystemTx` disabled](#issystemtx-disabled)
  - [Actual gas usage recorded](#actual-gas-usage-recorded)
  - [`depositNonce` in the receipt](#depositnonce-in-the-receipt)
  - [L1 attributes deposit](#l1-attributes-deposit)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

[deposits]: ../deposits.md

## Overview

The Regolith upgrade changes deposit processing. This page lists the changes to the
[deposit specification][deposits]. The deposit specification describes the Bedrock behavior.

## Changes

### `isSystemTx` disabled

The `isSystemTx` boolean is disabled, enforced to be `false`. System transactions now use the same
gas accounting rules as regular deposits.

### Actual gas usage recorded

The actual deposit gas-usage is recorded in the receipt, and subtracted from the L2 block gas-pool.
Unused gas of deposits is not refunded with ETH, as it is burned on L1.

Before Regolith, the execution output states a non-standard gas usage:

- If `isSystemTx` is false: the execution output states it uses `gasLimit` gas.
- If `isSystemTx` is true: the execution output states it uses `0` gas.

### `depositNonce` in the receipt

The `nonce` value of the deposit sender account, before the transaction state-transition, is recorded
in a new optional field (`depositNonce`), extending the transaction receipt. The field is not present
in pre-Regolith receipts.

The recorded `nonce` is used to correct the transaction and receipt metadata in RPC responses,
including the `contractAddress` field of deposits that deploy contracts.

### L1 attributes deposit

The L1 attributes deposit changes:

- `gasLimit` is `1,000,000` (was `150,000,000`).
- `isSystemTx` is `false` (was `true`).
