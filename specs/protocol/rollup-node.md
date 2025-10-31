# Rollup Node Specification

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Driver](#driver)
  - [Derivation](#derivation)
- [L2 Output RPC method](#l2-output-rpc-method)
  - [Structures](#structures)
    - [BlockID](#blockid)
    - [L1BlockRef](#l1blockref)
    - [L2BlockRef](#l2blockref)
    - [SyncStatus](#syncstatus)
  - [Output Method API](#output-method-api)
- [Protocol Version tracking](#protocol-version-tracking)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

<!-- All glossary references in this file. -->

[g-rollup-node]: ../glossary.md#rollup-node
[g-derivation]: ../glossary.md#L2-chain-derivation
[g-payload-attr]: ../glossary.md#payload-attributes
[g-block]: ../glossary.md#block
[g-exec-engine]: ../glossary.md#execution-engine
[g-reorg]: ../glossary.md#re-organization
[g-rollup-driver]: ../glossary.md#rollup-driver
[g-receipts]: ../glossary.md#receipt

## Overview

The [rollup node][g-rollup-node] is the component responsible for [deriving the L2 chain][g-derivation] from L1 blocks
(and their associated [receipts][g-receipts]).

The part of the rollup node that derives the L2 chain is called the [rollup driver][g-rollup-driver]. This document is
currently only concerned with the specification of the rollup driver.

## Driver

The task of the [driver][g-rollup-driver] in the [rollup node][g-rollup-node]
is to manage the [derivation][g-derivation] process:

- Keep track of L1 head block
- Keep track of the L2 chain sync progress
- Iterate over the derivation steps as new inputs become available

### Derivation

This process happens in three steps:

1. Select inputs from the L1 chain, on top of the last L2 block:
   a list of blocks, with transactions and associated data and receipts.
2. Read L1 information, deposits, and sequencing batches in order to generate [payload attributes][g-payload-attr]
   (essentially [a block without output properties][g-block]).
3. Pass the payload attributes to the [execution engine][g-exec-engine], so that the L2 block (including [output block
   properties][g-block]) may be computed.

While this process is conceptually a pure function from the L1 chain to the L2 chain, it is in practice incremental. The
L2 chain is extended whenever new L1 blocks are added to the L1 chain. Similarly, the L2 chain re-organizes whenever the
L1 chain [re-organizes][g-reorg].

For a complete specification of the L2 block derivation, refer to the [L2 block derivation document](derivation.md).

## L2 Output RPC method

> **Note:** This section has been moved to [specs/protocol/rpc/rpc-optimism.md](rpc/rpc-optimism.md)

## Protocol Version tracking

The rollup-node should monitor the recommended and required protocol version by monitoring
the Protocol Version contract on L1, as specified in the [Superchain Version Signaling specifications].

[Superchain Version Signaling specifications]: superchain-upgrades.md#superchain-version-signaling

This can be implemented through polling in the [Driver](#driver) loop.
After polling the Protocol Version, the rollup node SHOULD communicate it with the execution-engine through an
[`engine_signalSuperchainV1`](exec-engine.md#enginesignalsuperchainv1) call.

The rollup node SHOULD warn the user when the recommended version is newer than
the current version supported by the rollup node.

The rollup node SHOULD take safety precautions if it does not meet the required protocol version.
This may include halting the engine, with consent of the rollup node operator.
