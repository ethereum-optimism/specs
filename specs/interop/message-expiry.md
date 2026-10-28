# Message Expiry

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Flow](#flow)
- [L1CrossDomainMessenger](#l1crossdomainmessenger)
- [Safety](#safety)
- [Activation](#activation)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

Executing messages cannot be included through deposit transactions (see
[Depositing an Executing Message](./derivation.md#depositing-an-executing-message)). A destination chain's sequencer
that refuses to relay a message can therefore keep it from ever being delivered. Once the
[expiry window](./derivation.md#expiry-window) has passed, no valid block can relay the message at all.

Message expiry lets the source chain learn that a message can never be delivered, using only withdrawals and
deposits, which a sequencer cannot censor. The source chain's `L2ToL2CrossDomainMessenger` records this per message
in `expiredMessages`, and applications can undo the send, as
[`SuperchainETHBridge.refundETH`](./superchain-eth-bridge.md#refundeth) does.

## Flow

For a message sent from a source chain to a destination chain and never relayed there:

1. On the source chain, `L2ToL2CrossDomainMessenger.sendMessage` records `sentMessageTimestamps[messageHash]`.
2. On the destination chain, anyone calls
   [`UndeliveredMessageExporter.exportUndeliveredMessage`](./predeploys.md#undeliveredmessageexporter) with the
   message's preimage and the source chain's `L1CrossDomainMessenger`. The exporter computes `messageHash` with the
   destination chain as the destination, checks that the destination chain has not relayed it, and sends
   `relayUndeliveredMessage(messageHash, undeliveredAt)` through the destination chain's `L2CrossDomainMessenger`,
   where `undeliveredAt` is the destination chain's block timestamp. This is not an executing message, so it can be
   included through a deposit if the destination chain's sequencer censors it.
3. On L1, once the withdrawal is proven and finalized, the destination chain's `L1CrossDomainMessenger` relays it to
   the source chain's [`L1CrossDomainMessenger.relayUndeliveredMessage`](#l1crossdomainmessenger), which sends
   `expireMessage(messageHash, undeliveredAt)` to the source chain as a deposit.
4. On the source chain, [`expireMessage`](./predeploys.md#expiremessage-invariants) marks the message expired if
   `undeliveredAt > sentMessageTimestamps[messageHash] + EXPIRY_PERIOD`.
5. On the source chain, applications read `expiredMessages(messageHash)` to undo the send.

```mermaid
sequenceDiagram
    participant Source as Source chain
    participant L1 as L1
    participant Dest as Destination chain
    Source->>Source: sendMessage records sentMessageTimestamps[messageHash]
    Note over Dest: the message is never relayed
    Dest->>L1: exportUndeliveredMessage withdraws relayUndeliveredMessage(messageHash, undeliveredAt)
    L1->>L1: destination's L1CrossDomainMessenger relays to source's L1CrossDomainMessenger
    L1->>Source: deposit expireMessage(messageHash, undeliveredAt)
    Source->>Source: expiredMessages[messageHash] = true if undeliveredAt > sentAt + EXPIRY_PERIOD
```

## L1CrossDomainMessenger

```solidity
function relayUndeliveredMessage(bytes32 _messageHash, uint256 _undeliveredAt) external;
```

- It MUST revert unless this chain's `SystemConfig` has the `INTEROP` feature enabled.
- It MUST revert while this chain is paused, as `relayMessage` does.
- It MUST revert unless the caller is a real `L1CrossDomainMessenger`: the `SystemConfig` of the caller's portal
  MUST name the caller as its `l1CrossDomainMessenger`.
- It MUST revert unless the caller's portal is authorized by this chain's `ETHLockbox`.
- It MUST revert unless the caller's `xDomainMessageSender()` is the
  [`UndeliveredMessageExporter`](./predeploys.md#undeliveredmessageexporter).
- It MUST send `L2ToL2CrossDomainMessenger.expireMessage(_messageHash, _undeliveredAt)` to this chain as a
  deposit, as itself, with a fixed minimum gas limit.

If `relayUndeliveredMessage` reverts, such as while this chain is paused or when it runs out of gas, it is recorded in
the calling messenger's failed messages and can be replayed.

The `L1CrossDomainMessenger` refuses to relay messages that target itself, so it can be the sender of a message on L2
only through `relayUndeliveredMessage` and [`syncETHLiquidityPause`](./eth-liquidity.md#syncethliquiditypause). Each
sends one fixed call to one fixed target.

## Safety

A refund MUST NOT be possible for a message that was or can still be relayed. This holds because:

- An executing message is invalid if its block timestamp is more than the expiry window after the timestamp of
  its initiating message (see [Message Expiry Invariant](./messaging.md#message-expiry-invariant)).
  `sentMessageTimestamps[messageHash]` is that initiating timestamp, and it is written once.
- The exporter on the destination chain attests that the message was not relayed by its block timestamp
  `undeliveredAt`. Any later block on the destination chain has a timestamp of at least `undeliveredAt`. If
  `undeliveredAt > sentMessageTimestamps[messageHash] + EXPIRY_PERIOD` and `EXPIRY_PERIOD` is at least the expiry
  window, no later block can relay the message.
- Only the destination chain can attest for the message, because the exporter hashes it with its own chain id as the
  destination.
- Only chains whose portals the source chain's `ETHLockbox` authorizes can attest. Each of them can already withdraw
  the source chain's ETH.
- The trusted L2 sender is the `UndeliveredMessageExporter`, whose proxy had no implementation before the upgrade
  that introduced it, so no withdrawal from it can predate that upgrade.

The `L2ToL2CrossDomainMessenger` MUST NOT re-emit a `SentMessage` event for a message, and every way of relaying a
message MUST set `successfulMessages`. An upgrade that breaks either rule breaks this argument.

## Activation

- Every node and the proof program MUST enforce an [expiry window](./derivation.md#expiry-window) of at most
  `EXPIRY_WINDOW` (7 days) before expiry is relied on. On production networks `EXPIRY_PERIOD` is 8 days, the
  window plus a day of margin; on any network it MUST exceed the network's expiry window.
- A production network MUST NOT change its expiry window without a coordinated upgrade of `EXPIRY_PERIOD` (see
  [Expiry Window](./derivation.md#expiry-window)).
- The network upgrade that activates interop MUST install an `L2ToL2CrossDomainMessenger` with expiry and the
  `UndeliveredMessageExporter`. A frozen upgrade bundle for that fork that was snapshotted before these contracts
  existed MUST be snapshotted again first, so that no `L2ToL2CrossDomainMessenger` without expiry, which could
  resend a message after it expired, is ever live on a chain with expiry.
- Every chain in a cluster's dependency set MUST be authorized by the cluster's `ETHLockbox` and run the
  `UndeliveredMessageExporter`. Otherwise messages sent to it cannot expire.
