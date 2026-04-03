# Super Root

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Super Root Computation](#super-root-computation)
  - [SuperV1](#superv1)
- [RPC API](#rpc-api)
  - [Common Types](#common-types)
    - [`ChainID`](#chainid)
    - [`Hash`](#hash)
    - [`BlockID`](#blockid)
    - [`OutputV0`](#outputv0)
    - [`OutputWithRequiredL1`](#outputwithrequiredl1)
    - [`ChainIDAndOutput`](#chainidandoutput)
    - [`SuperV1`](#superv1-1)
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

The super root is a commitment to the combined verified state of all chains in a
[dependency set](./dependency-set.md) at a given timestamp. It is used by the
[fault proof](./fault-proof.md) to reason about the global state across chains,
and serves as the anchor for proposals in the Super Fault Dispute Game.

The super root API provides callers with the verified super root at a requested timestamp
when available, along with sync status information and per-chain optimistic output roots
that may not yet be fully verified.

## Super Root Computation

### SuperV1

The super root is the `keccak256` hash of a versioned encoding of the global state.

The `SuperV1` encoding is:

| Field       | Type                  | Size    | Description                             |
| ----------- | --------------------- | ------- | --------------------------------------- |
| `version`   | `uint8`               | 1 byte  | Always `1` for `SuperV1`                |
| `timestamp` | `uint64 (big-endian)` | 8 bytes | The L2 timestamp of the super root      |
| `chains`    | `[]ChainIDAndOutput`  | 64 bytes each | Per-chain output roots, see below |

Each `ChainIDAndOutput` entry is:

| Field        | Type      | Size     | Description                                       |
| ------------ | --------- | -------- | ------------------------------------------------- |
| `chainID`    | `bytes32` | 32 bytes | Chain ID, big-endian, zero-padded to 32 bytes     |
| `outputRoot` | `bytes32` | 32 bytes | The chain's [L2 output root][l2-output] at or before `timestamp` |

Chains MUST be sorted in ascending order by chain ID.

The minimum valid encoding contains exactly one chain (73 bytes total).

The super root hash is computed as:

```text
superRoot = keccak256(version ++ timestamp ++ chain[0].chainID ++ chain[0].outputRoot ++ ...)
```

[l2-output]: ../glossary.md#l2-output-root

## RPC API

### Common Types

#### `ChainID`

`STRING`: Hex-encoded big-endian number, variable length up to 256 bits, prefixed with `0x`.

#### `Hash`

`STRING`: Hex-encoded, fixed-length, representing 32 bytes, prefixed with `0x`.

#### `BlockID`

`OBJECT`:

- `hash`: `Hash` - block hash
- `number`: `NUMBER` - block number

A zero `BlockID` has a `hash` of `0x0000...0000` and a `number` of `0`.

#### `OutputV0`

The [L2 output root][l2-output] preimage.

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

#### `ChainIDAndOutput`

`OBJECT`:

- `chainID`: `ChainID`
- `output`: `Hash` - the output root

#### `SuperV1`

The super root preimage.

`OBJECT`:

- `timestamp`: `HexUint64`
- `chains`: `ARRAY` of `ChainIDAndOutput`

#### `SuperRootResponseData`

Verified super root data. Present only when all chains in the dependency set
have verified data at the requested timestamp.

`OBJECT`:

- `verified_required_l1`: `BlockID` - the minimum L1 block at which all chains
  can be fully verified at this timestamp
- `super`: `SuperV1` - the super root preimage
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
derived a local-safe block at the requested timestamp is included, regardless
of whether its executing messages have been verified. Chains that have not yet
derived a block at the requested timestamp are omitted from the map.

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
