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

The Rollup node has its own RPC method, `optimism_outputAtBlock` which returns a 32
byte hash corresponding to the [L2 output root](proposals.md#l2-output-commitment-construction).

[SSZ]: https://github.com/ethereum/consensus-specs/blob/dev/ssz/simple-serialize.md

### Structures

These define the types used by rollup node API methods.
The types defined here are extended from the [engine API specs][engine-structures].

#### BlockID

- `hash`: `DATA`, 32 Bytes
- `number`: `QUANTITY`, 64 Bits

#### L1BlockRef

- `hash`: `DATA`, 32 Bytes
- `number`: `QUANTITY`, 64 Bits
- `parentHash`: `DATA`, 32 Bytes
- `timestamp`: `QUANTITY`, 64 Bits

#### L2BlockRef

- `hash`: `DATA`, 32 Bytes
- `number`: `QUANTITY`, 64 Bits
- `parentHash`: `DATA`, 32 Bytes
- `timestamp`: `QUANTITY`, 64 Bits
- `l1origin`: `BlockID`
- `sequenceNumber`: `QUANTITY`, 64 Bits - distance to first block of epoch

#### SyncStatus

Represents a snapshot of the rollup driver.

- `current_l1`: `Object` - instance of [`L1BlockRef`](#l1blockref).
- `current_l1_finalized`: `Object` - instance of [`L1BlockRef`](#l1blockref).
- `head_l1`: `Object` - instance of [`L1BlockRef`](#l1blockref).
- `safe_l1`: `Object` - instance of [`L1BlockRef`](#l1blockref).
- `finalized_l1`: `Object` - instance of [`L1BlockRef`](#l1blockref).
- `unsafe_l2`: `Object` - instance of [`L2BlockRef`](#l2blockref).
- `safe_l2`: `Object` - instance of [`L2BlockRef`](#l2blockref).
- `finalized_l2`: `Object` - instance of [`L2BlockRef`](#l2blockref).
- `pending_safe_l2`: `Object` - instance of [`L2BlockRef`](#l2blockref).
- `queued_unsafe_l2`: `Object` - instance of [`L2BlockRef`](#l2blockref).

### Output Method API

The input and return types here are as defined by the [engine API specs][engine-structures].

[engine-structures]: https://github.com/ethereum/execution-apis/blob/main/src/engine/paris.md#structures

- method: `optimism_outputAtBlock`
- params:
  1. `blockNumber`: `QUANTITY`, 64 bits - L2 integer block number.
- returns:
  1. `version`: `DATA`, 32 Bytes - the output root version number, beginning with 0.
  1. `outputRoot`: `DATA`, 32 Bytes - the output root.
  1. `blockRef`: `Object` - instance of [`L2BlockRef`](#l2blockref).
  1. `withdrawalStorageRoot`: 32 bytes - storage root of the `L2toL1MessagePasser` contract.
  1. `stateRoot`: `DATA`: 32 bytes - the state root.
  1. `syncStatus`: `Object` - instance of [`SyncStatus`](#syncstatus).

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
