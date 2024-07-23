# Indexing API

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Optional Indexing Backend](#optional-indexing-backend)
- [Methods](#methods)
  - [`interop_checkMessage`](#interop_checkmessage)
    - [Parameters](#parameters)
    - [Returns](#returns)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Optional Indexing Backend

Sequencers or verifies MAY utilise an external service to index the logs from chains in the dependency set and optimise
cross-chain validity checks. To aid compatibility between different implementations of sequencers, verifiers and
backends, a standard API for indexers to expose is defined here.

The API uses [JSON-RPC] and follows the same conventions as the [Ethereum JSON-RPC API].

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
- `unsafe` - the specified log exists and meets the requirements of [`unsafe` inputs`](./verifier.md#unsafe-inputs)
- `cross-unsafe` - the specified log exists and meets the requirements
  of [`cross-unsafe` inputs`](./verifier.md#cross-unsafe-inputs)
- `safe` - the specified log exists and meets the requirements of [`safe` inputs`](./verifier.md#safe-inputs)
- `finalized` - the specified log exists and meets the requirements
  of [`finalized` inputs`](./verifier.md#finalized-inputs)

[JSON-RPC]: https://www.jsonrpc.org/specification

[Ethereum JSON-RPC API]: https://ethereum.org/en/developers/docs/apis/json-rpc/
