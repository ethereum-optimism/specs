# Super Root

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [RPC API](#rpc-api)
  - [Types](#types)
    - [`OutputV0`](#outputv0)
    - [`OutputWithRequiredL1`](#outputwithrequiredl1)
    - [`SuperRootResponseData`](#superrootresponsedata)
  - [Methods](#methods)
    - [`superroot_atTimestamp`](#superroot_attimestamp)
  - [Response Behavior](#response-behavior)
    - [Sync Status Fields](#sync-status-fields)
    - [Optimistic Data](#optimistic-data)
    - [Verified Data](#verified-data)
    - [Errors](#errors)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The [super root](../fault-proof/stage-one/optimism-portal.md#super-root) is a commitment to the
combined verified state of all chains in a [dependency set](./dependency-set.md) at a given timestamp.
Any consensus client that verifies output roots across chains with interop needs access to the
super root to confirm published roots.

This document specifies the RPC API for querying the super root and per-chain output root data.

## RPC API

The super root API provides callers with the verified super root at a requested timestamp
when available, along with sync status information and per-chain optimistic output roots
that may not yet be fully verified.

For common types (`ChainID`, `Hash`, `BlockID`, `HexUint64`) see the
existing [type definitions](../glossary.md). The `SuperV1` and `ChainIDAndOutput` structures
used in the response match the encoding defined in the
[Super Output specification](../fault-proof/stage-one/optimism-portal.md#super-output).

### Types

#### `OutputV0`

The [L2 output root](../glossary.md#l2-output-root) preimage.

`OBJECT`:

- `stateRoot`: `Hash`
- `messagePasserStorageRoot`: `Hash`
- `blockHash`: `Hash`

#### `OutputWithRequiredL1`

Per-chain optimistic output data.

`OBJECT`:

- `output`: `OutputV0` - the output root preimage
- `output_root`: `Hash` - `keccak256` hash of the marshaled output
- `required_l1`: `BlockID` - the minimum L1 block required to derive this output

#### `SuperRootResponseData`

Verified super root data. Present only when all chains in the dependency set
have verified data at the requested timestamp.

`OBJECT`:

- `verified_required_l1`: `BlockID` - the minimum L1 block at which all chains
  can be fully verified at this timestamp
- `super`: `SuperV1` - the [super root](../fault-proof/stage-one/optimism-portal.md#super-output) preimage
- `super_root`: `Hash` - the `keccak256` hash of the encoded `SuperV1`

### Methods

#### `superroot_atTimestamp`

Returns the super root state at the given timestamp, along with sync status
and per-chain optimistic output data.

Parameters:

- `timestamp`: `HexUint64` - the L2 timestamp to query

Returns:

`OBJECT`:

- `current_l1`: `BlockID` - the highest L1 block that has been fully processed
  by all chains in the dependency set. This is the minimum `currentL1` across all chains.
- `safe_timestamp`: `NUMBER` - the highest L2 timestamp that is cross-safe across
  all chains. This is the minimum per-chain cross-safe L2 head timestamp.
- `local_safe_timestamp`: `NUMBER` - the highest L2 timestamp that is local-safe
  across all chains. This is the minimum per-chain local-safe L2 head timestamp.
- `finalized_timestamp`: `NUMBER` - the highest L2 timestamp that is finalized
  across all chains. This is the minimum per-chain finalized L2 head timestamp.
- `chain_ids`: `ARRAY` of `ChainID` - the chain IDs in the dependency set,
  sorted in ascending order.
- `optimistic_at_timestamp`: `OBJECT` with `ChainID` keys and `OutputWithRequiredL1`
  values - per-chain optimistic output data at the requested timestamp.
- `data`: `SuperRootResponseData` or `null` - the verified super root data.
  `null` when verified data is not yet available for all chains.

### Response Behavior

#### Sync Status Fields

The fields `current_l1`, `safe_timestamp`, `local_safe_timestamp`,
`finalized_timestamp`, and `chain_ids` are always populated. They reflect
the aggregate sync state across all chains in the dependency set at the time of the call,
independent of the requested timestamp.

Each timestamp field is the minimum of that safety level's L2 head timestamp
across all chains, providing a conservative view of global progress.

#### Optimistic Data

The `optimistic_at_timestamp` map is populated per-chain. Each chain that has
a derived block at the requested timestamp is included, regardless of whether
its executing messages have been verified. Chains that have not yet derived a
block at the requested timestamp are omitted from the map.

If a block at the requested timestamp has been
[replaced](./derivation.md#replacing-invalid-blocks) due to invalid executing
messages, the optimistic output is the **original** (pre-replacement) block's
output — representing the chain state as if verification had succeeded and no
replacement occurred. For blocks that have not been replaced, the optimistic
output is the current local-safe block's output.

This data is useful for consumers that want to act on the most recent state
before full cross-chain verification completes.

#### Verified Data

The `data` field is non-null only when **all** chains in the dependency set have
fully verified data at the requested timestamp. "Verified" means:

- The block at the requested timestamp has been derived.
- All executing messages in the block (and its transitive dependencies) have been
  validated across the dependency set.
- Any blocks containing invalid executing messages have been replaced using
  [Holocene Replacement](../protocol/holocene/derivation.md#engine-queue).

When `data` is present:

- `data.super_root` is the canonical super root hash at the requested timestamp.
- `data.verified_required_l1` is the minimum L1 block that includes
  all batch data necessary to reproduce this verified state.
- `data.super` contains the full preimage, allowing callers to independently
  recompute the super root hash.

When `data` is null, the super root at the requested timestamp is not yet
known. Callers should retry after the node has made further sync progress.
The `safe_timestamp` field indicates the highest timestamp at which
verified data is currently available.

#### Errors

The method returns an RPC error if:

- An internal error occurs while querying chain state (e.g. database failure,
  unreachable chain node). Transient `NotFound` conditions for individual chains
  do not produce errors; they result in the chain being excluded from
  `optimistic_at_timestamp` and `data` being null.
- The dependency set is empty (no chains configured).
