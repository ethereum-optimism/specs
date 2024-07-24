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
processed,
callers MUST confirm that the returned block is canonical in their local view of the chain. Callers MAY retry the query
with a lower `maxBlockNumber` if the returned block is non-canonical.

Supervisors SHOULD consider calls where `maxBlockNumber` is ahead of their current `unsafe` head for a chain to be a
signal that additional blocks may be available to be indexed. However, supervisors MUST eventually index available
blocks even if `interop_crossUnsafe` is not called.

#### Parameters

1. chainID: QUANTITY - Chain ID of the chain to return data for
2. maxBlockNumber: QUANTITY - The maximum block number to return information for

#### Returns

`Object` - Block ID that meets the requirements of [`cross-unsafe` inputs] and `block.number <= maxBlockNumber`

- `hash` - the hash of the block
- `number` the number of the block

[`unsafe` inputs]: ./verifier.md#unsafe-inputs

[`cross-unsafe` inputs]: ./verifier.md#cross-unsafe-inputs

[`safe` inputs]: ./verifier.md#safe-inputs

[`finalized` inputs]: ./verifier.md#finalized-inputs
