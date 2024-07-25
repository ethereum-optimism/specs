# Supervisor API

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Optional Supervisor Backend](#optional-supervisor-backend)
- [Methods](#methods)
  - [`interop_checkMessage`](#interop_checkmessage)
    - [Parameters](#parameters)
    - [Returns](#returns)
  - [`interop_crossUnsafe`](#interop_crossunsafe)
    - [Parameters](#parameters-1)
    - [Returns](#returns-1)
  - [`interop_nextDeriveTask`](#interop_nextderivetask)
    - [Parameters](#parameters-2)
    - [Returns](#returns-2)
  - [`interop_blockDerived`](#interop_blockderived)
    - [Parameters](#parameters-3)
    - [Returns](#returns-3)
  - [`interop_safe`](#interop_safe)
    - [Parameters](#parameters-4)
    - [Returns](#returns-4)
  - [`interop_finalized`](#interop_finalized)
    - [Parameters](#parameters-5)
    - [Returns](#returns-5)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Optional Supervisor Backend

Sequencers or verifies MAY utilise an external service to index the logs from chains in the dependency set and optimise
cross-chain validity checks. To aid compatibility between different implementations of sequencers, verifiers and
these supervisors, a standard API for such services to expose is defined here.

The API uses [JSON-RPC] and follows the same conventions as the [Ethereum JSON-RPC API].

[JSON-RPC]: https://www.jsonrpc.org/specification

[Ethereum JSON-RPC API]: https://ethereum.org/en/developers/docs/apis/json-rpc/

## Methods

### `interop_checkMessage`

Determines the safety level of an individual message. This can be used to verify initiating messages exist, for example
by the tx-pool and block-building, to verify user-input before inclusion into the chain.

#### Parameters

1. Object - The Identifier object
    - origin: DATA, 20 Bytes - Account that emits the log
    - blocknumber: QUANTITY - Block number in which the log was emitted
    - logIndex: QUANTITY - The index of the log in the array o fall logs emitted in the block
    - timestamp: QUANTITY - The timestamp that the log was emitted
    - chainid: QUANTITY - The chain id of the chain that emitted the log
2. payloadHash: DATA, 32 bytes - the keccak256 hash of the [message payload](./messaging.md#message-payload)

#### Returns

`String` - The strictest applicable `SafetyLevel` of the message

- `conflicts` - data is available for the block referenced by the identifier but does not contain a matching log
- `unknown` - data for the block referenced by the identifier is not yet available
- `finalized` - the specified log exists
- `unsafe` - the specified log exists and meets the requirements of [`unsafe` inputs]
- `cross-unsafe` - the specified log exists and meets the requirements of [`cross-unsafe` inputs]
- `safe` - the specified log exists and meets the requirements of [`safe` inputs]
- `finalized` - the specified log exists and meets the requirements of [`finalized` inputs]

### `interop_crossUnsafe`

Returns the latest `cross-unsafe` block in the canonical chain of the supervisor, up to and including the
specified `maxBlockNumber`. This can be used by sequencers or verifiers to determine when blocks on their chain have met
all cross-chain dependencies. For example, batchers may avoid posting batch data for transactions that have unsatisfied
cross-chain dependencies.

As the supervisor and caller may have different local views of the chain, e.g. because a reorg has not yet been
processed, callers MUST confirm that the returned block is canonical in their local view of the chain. Callers MAY retry
the query with a lower `maxBlockNumber` if the returned block is non-canonical.

Supervisors SHOULD consider calls where `maxBlockNumber` is ahead of their current `unsafe` head for a chain to be a
signal that additional blocks may be available to be indexed. However, supervisors MUST eventually index available
blocks even if `interop_crossUnsafe` is not called.

#### Parameters

1. chainID: QUANTITY - Chain ID of the chain to return data for
2. maxBlockNumber: QUANTITY - The maximum block number to return information for

#### Returns

`Object` - Block ID that meets the requirements of [`cross-unsafe` inputs] and `block.number <= maxBlockNumber`

- `hash`: DATA, 32 Bytes - the block hash
- `number`: QUANTITY - the block number

### `interop_nextDeriveTask`

Returns the next derivation task that the supervisor needs for it to potentially progress the cross-chain safe head.
The response allows the supervisor to

There are three possible cases:

1. The supervisor has sufficient information for this chain and is awaiting information from other
   chains (`derivationRequired: false`)
2. The supervisor is waiting for further local-safe blocks from the chain  (`depositOnly: false`)
3. The supervisor has determined that a local-safe block has invalid executing messages and must be replaced by a
   deposit-only block (`depositOnly: true`)

When `derivationRequired` is `true`:

- `l2Parent` MUST specify a L2 block that is canonical in the supervisor's view of the chain, that the next derived
  block will be a child of
- `l1` MUST specify the L1 block to be treated as the L1 chain head when deriving the next block.
  - The block MUST be the same as or higher than the L1 block used when deriving `l2Parent`
  - Higher L1 blocks MUST NOT be used, even if they are seen as canonical

#### Parameters

1. chainID: QUANTITY - Chain ID of the chain to return the next derive task for

#### Returns

`Object` - The next derivation task required to perform in an attempt to progress the safe head

- `derivationRequired`: Boolean - `true` if there is a derivation task required for this chain, otherwise `false`.
  When `false` all other fields must be omitted.
- `l2Parent`: `Object` - The L2 block to attempt to derive the next block on top of
  - `hash`: DATA, 32 Bytes - the block hash
  - `number`: QUANTITY - the block number
- `depositOnly`: Boolean - `true` if the block should be restricted to deposit transactions only, otherwise `false`
- `l1`: `Object - The most recent L1 block that may be used when attempting to derive the next block
  - `hash`: DATA, 32 Bytes - the block hash
  - `number`: QUANTITY - the block number

### `interop_blockDerived`

Provides the result of a previous derivation task returned by `interop_nextDeriveTask`. The `derived` block MUST:

- be derivable from data on the availability layer up to and including the specified `l1` block
- have `l2Parent` as its parent
- contain only deposit transactions from its origin L1 block if `depositOnly` is `true`.

Supervisors MUST NOT return an error if multiple calls to `interop_blockDerived` are made for the same derivation task.

Supervisors MAY return an error if the specified `l2Parent`, `depositOnly` and `l1` values do not match any derivation
task returned by `interop_nextDerivateTask`.

#### Parameters

1. chainID: QUANTITY - Chain ID of the chain the block was derived on
2. derived: `Object` - The block that was derived
   - `hash`: DATA, 32 Bytes - the block hash
   - `number`: QUANTITY - the block number
3. l2Parent: `Object` - The parent of the derived block. MUST be equal to the `l2Parent` from the original derive task.
   - `hash`: DATA, 32 Bytes - the block hash
   - `number`: QUANTITY - the block number
4. depositOnly: Boolean - `true` if the derived block was explicitly restricted to only include deposit transactions by
   the derive task, otherwise `false`. MUST be `false` if the original task `depositOnly` was `false`, even if the block
   only contains deposit transactions for any other reason.
5. l1: `Object` - The L1 block used as the L1 chain head when deriving. MUST be equal to the `l1` from the original
   derive task.
   - `hash`: DATA, 32 Bytes - the block hash
   - `number`: QUANTITY - the block number

#### Returns

N/A

### `interop_safe`

Returns the highest block for the specified chain that meets the [`safe` inputs] requirements using only data up to and
including the specified `l1Number` block on the data availability layer.

If the supervisor has not processed all data up to the specified `l1Number` is MUST use the latest L1 block it has fully
processed and MUST return that block as the `derivedFrom` block. Otherwise `derivedFrom` MUST be the block at
number `l1Number`.

As the supervisor and caller may have different local views of the chain, e.g. because a reorg has not yet been
processed, callers MUST confirm that the returned `derivedFrom` block is canonical in their local view. Callers MAY
retry the query with a lower `l1Number` if the returned block is non-canonical.

#### Parameters

1. chainID: QUANTITY - Chain ID to get the `cross-safe` block for
2. `l1Number`: QUANTITY - Block number of the L1 block to limit data to

#### Returns

`Object` - The `safe` block for the specified chain and the L1 block required to derive it.

- `safe`: `Object` - The highest L2 block from the specified chain that meets the [`safe` inputs] requirements after
  applying all data from the availability layer up to and including block `l1Number`
  - `hash`: DATA, 32 Bytes - the block hash
  - `number`: QUANTITY - the block number
- `derivedFrom`: `Object` - The L1 block used as the chain head of the data availability layer when deriving
  - `hash`: DATA, 32 Bytes - the block hash
  - `number`: QUANTITY - the block number.

### `interop_finalized`

Returns the highest block for the specified chain that meets the [`finalized` inputs] requirements using only data up to
and including the specified `l1Number` block on the data availability layer.

If `l1Number` is not finalized in the supervisor's view of the L1 chain, it MUST use the latest finalized block and
return it as the `derivedFrom` value.

#### Parameters

1. chainID: QUANTITY - Chain ID to get the `cross-safe` block for
2. `l1Number`: QUANTITY - Block number of the L1 block to limit data to

#### Returns

`Object` - The `finalized` block for the specified chain and the L1 block required to derive it.

- `finalized`: `Object` - The highest L2 block from the specified chain that meets the [`finalized` inputs] requirements
  after applying all data from the availability layer up to and including block `l1Number`
  - `hash`: DATA, 32 Bytes - the block hash
  - `number`: QUANTITY - the block number
- `derivedFrom`: `Object` - The finalized L1 block used as the chain head of the data availability layer when deriving
  - `hash`: DATA, 32 Bytes - the block hash
  - `number`: QUANTITY - the block number.

[`unsafe` inputs]: ./verifier.md#unsafe-inputs

[`cross-unsafe` inputs]: ./verifier.md#cross-unsafe-inputs

[`safe` inputs]: ./verifier.md#safe-inputs

[`finalized` inputs]: ./verifier.md#finalized-inputs
