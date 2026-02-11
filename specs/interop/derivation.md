# Derivation

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Invariants](#invariants)
- [Activation Block](#activation-block)
- [Replacing Invalid Blocks](#replacing-invalid-blocks)
  - [Optimistic Block Deposited Transaction](#optimistic-block-deposited-transaction)
    - [Optimistic Block Source-hash](#optimistic-block-source-hash)
- [Network Upgrade Transactions](#network-upgrade-transactions)
  - [L2ToL2CrossDomainMessenger Deployment](#l2tol2crossdomainmessenger-deployment)
  - [L2ToL2CrossDomainMessenger Proxy Update](#l2tol2crossdomainmessenger-proxy-update)
  - [L2 Gas Limit Requirements](#l2-gas-limit-requirements)
- [CrossL2InboxProxy Initialization](#crossl2inboxproxy-initialization)
  - [CrossL2Inbox Deployment](#crossl2inbox-deployment)
  - [CrossL2Inbox Proxy Update](#crossl2inbox-proxy-update)
  - [L2 Gas Limit Requirements](#l2-gas-limit-requirements-1)
- [Expiry Window](#expiry-window)
- [Security Considerations](#security-considerations)
  - [Depositing an Executing Message](#depositing-an-executing-message)
  - [Expiry Window](#expiry-window-1)
  - [Reliance on History](#reliance-on-history)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

New derivation rules are added to guarantee integrity of cross chain messages.
The fork choice rule is updated to fork out unsafe blocks that contain invalid
executing messages.

## Invariants

- An executing message MUST have a corresponding initiating message
- The initiating message referenced in an executing message MUST come from a chain in its dependency set
- A block MUST be considered invalid if it is built with any invalid executing messages
- The block number `n` is `>` the activation block number, see [Activation Block](#activation-block).
- The timestamp `t` of the identifier MUST be:
  - `t <= execution_timestamp`, where `execution_timestamp` is the timestamp of the block
    that includes the executing message.
  - `t > execution_timestamp - expiry_window`, where `expiry_window` is the expiry window in seconds.

L2 blocks that produce invalid executing messages MUST not be allowed to be considered safe.
They MAY optimistically exist as unsafe blocks for some period of time. An L2 block that is invalidated
because it includes invalid executing messages MUST be replaced by a deposits only block at the same
block height. This guarantees progression of the chain, ensuring that an infinite loop of processing
the same block in the proof system is not possible.

## New Protocol Rules

For Chains featuring interop, an L2 contract called the "<>" is available.
A transaction which invokes the contract emits an Executing Message, which make reference to Log Events which have
occured on any chain in the Dependency Set.

For any L2 block which contains these Executing Messages, the block's validity is conditional on the correctness of the Executing Messages it contains.

Put another way: blocks which contain invalid Executing Messages are, by definition, invalid.

### Safety Application

While blocks are eventually determined to be valid or invalid by protocol rules, they may be optimistically applied as unsafe or "locally safe" blocks.

However, blocks are only considered Safe once they meet all additional rules of verification,
in this case "Cross Validation".

Likewise, blocks may not be Finalized until all L1 data used to verify it is included in Finalized L1 Blocks.

## Activation Block and Timestamp

Interop Activation is represented as a shared L2 timestamp, representing
the first timestamp to be scrutinized by Interop.

For chains which create a block with timestamp _equal_ to the Activation Time, that block is the first to be subject to Interop.

For chains which do not have a block _equal_ to the Activation Time,
their state _at_ the Activation Time is the prior block. Meaning that the
block imediately preceeding the timestamp is the first block subject to Interop.

// I just deleted a bunch of constraints... I don't think we need them if
we have a superchain-timestamp to define the activation.
Need to know more about this.

## Replacing Invalid Blocks

When the [cross chain dependency resolution](./messaging.md#resolving-cross-chain-safety) determines
that a block contains an [invalid message](./messaging.md#invalid-messages), the block is replaced
using Holocene Replacement Rules, which is a block containing
only Deposit Transactions, replacing the original block.
