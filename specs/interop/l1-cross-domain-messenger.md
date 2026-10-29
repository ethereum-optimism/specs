# L1CrossDomainMessenger Interop

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Constants](#constants)
- [Unsafe Targets](#unsafe-targets)
- [Function Specification](#function-specification)
  - [relayUndeliveredMessage](#relayundeliveredmessage)
  - [syncETHLiquidityPause](#syncethliquiditypause)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

With interop, the `L1CrossDomainMessenger` gains two functions. Each sends one fixed call to one fixed L2 target, as
a deposit, with the `L1CrossDomainMessenger` itself as the L1 sender:

- [`relayUndeliveredMessage`](#relayundeliveredmessage) passes on word that a message was not relayed, for
  [message expiry](./message-expiry.md).
- [`syncETHLiquidityPause`](#syncethliquiditypause) sends this chain's pause state to `ETHLiquidity`, for the
  [`ETHLiquidity` pause](./eth-liquidity.md#pause).

L2 trusts the `L1CrossDomainMessenger` as the sender of these calls (see
[iME-003](./message-expiry.md#ime-003-only-two-functions-send-as-the-l1crossdomainmessenger)). The rest of the
messenger is unchanged; see [Messengers](../protocol/messengers.md).

## Constants

| Constant                             | Value    |
| ------------------------------------ | -------- |
| `EXPIRE_MESSAGE_GAS_LIMIT`           | `100000` |
| `SET_ETH_LIQUIDITY_PAUSED_GAS_LIMIT` | `200000` |

## Unsafe Targets

`relayMessage` MUST refuse to relay a message whose target is the `L1CrossDomainMessenger` itself or its
`OptimismPortal`. A relayed message therefore cannot make the `L1CrossDomainMessenger` the sender of a message, and
it is the L1 sender of a message on L2 only through the two functions below.

## Function Specification

### relayUndeliveredMessage

Passes on, to this chain, word from another chain that it has not relayed a message sent from this chain.

```solidity
function relayUndeliveredMessage(bytes32 _messageHash, uint256 _undeliveredAt) external;
```

- MUST revert with `L1CrossDomainMessenger_InteropNotEnabled` unless this chain's `SystemConfig` has the `INTEROP`
  feature enabled.
- MUST revert with `L1CrossDomainMessenger_Paused` while this chain is paused, as `relayMessage` does.
- MUST revert with `L1CrossDomainMessenger_NotInteropMessenger` unless all of these hold:
  - the `SystemConfig` of the caller's portal names the caller as its `l1CrossDomainMessenger`;
  - this chain's `ETHLockbox` authorizes the caller's portal;
  - the caller's `xDomainMessageSender()` is the
    [`UndeliveredMessageExporter`](./predeploys.md#undeliveredmessageexporter).
- MUST send `L2ToL2CrossDomainMessenger.expireMessage(_messageHash, _undeliveredAt)` to this chain as a deposit, as
  itself, with a minimum gas limit of `EXPIRE_MESSAGE_GAS_LIMIT`.

It does not check which chain the message hash names as its destination. That binding comes from the exporter; see
[aME-001](./message-expiry.md#ame-001-authorized-chains-run-standard-contracts).

If `relayUndeliveredMessage` reverts, such as while this chain is paused or when it runs out of gas, it is recorded in
the calling messenger's failed messages and can be replayed.

### syncETHLiquidityPause

Sends this chain's pause state to [`ETHLiquidity`](./eth-liquidity.md#setpaused).

```solidity
function syncETHLiquidityPause() external;
```

- MUST be callable by anyone.
- MUST revert with `L1CrossDomainMessenger_InteropNotEnabled` unless this chain's `SystemConfig` has the `INTEROP`
  feature enabled.
- MUST NOT revert while this chain is paused.
- MUST send `ETHLiquidity.setPaused(paused(), nonce)` to this chain as a deposit, as itself, with a minimum gas limit
  of `SET_ETH_LIQUIDITY_PAUSED_GAS_LIMIT`, where `nonce` is the versioned nonce of that message.
