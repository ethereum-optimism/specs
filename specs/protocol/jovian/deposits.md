# Deposits

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [User-Deposited Transactions](#user-deposited-transactions)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The `version` argument of the `TransactionDeposited` event CAN now
include a nonce, and has been renamed `nonceAndVersion`.

## User-Deposited Transactions

Each user deposit emits a `TransactionDeposited` event.

```solidity
event TransactionDeposited(address indexed from, address indexed to, uint256 indexed nonceAndVersion, bytes opaqueData);
```

The `nonceAndVersion` argument is either `uint256(0)`, or
`uint256(nonce << 128 | version)`, where `version` is `1` and `nonce` increments
by `1` for each `TransactionDeposited` event emitted.
