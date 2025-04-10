# Supervisor

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [RPC API](#rpc-api)
  - [Common types](#common-types)
    - [`Identifier`](#identifier)
    - [`Message`](#message)
    - [`ExecutingDescriptor`](#executingdescriptor)
    - [`HexUint64`](#hexuint64)
    - [`Int`](#int)
    - [`ChainID`](#chainid)
    - [`Hash`](#hash)
    - [`Bytes`](#bytes)
    - [`BlockID`](#blockid)
    - [`BlockRef`](#blockref)
    - [`DerivedIDPair`](#derivedidpair)
    - [`ChainRootInfo`](#chainrootinfo)
    - [`SuperRootResponse`](#superrootresponse)
    - [`SafetyLevel`](#safetylevel)
  - [Methods](#methods)
    - [`supervisor_crossDerivedToSource`](#supervisor_crossderivedtosource)
    - [`supervisor_localUnsafe`](#supervisor_localunsafe)
    - [`supervisor_crossSafe`](#supervisor_crosssafe)
    - [`supervisor_finalized`](#supervisor_finalized)
    - [`supervisor_finalizedL1`](#supervisor_finalizedl1)
    - [`supervisor_superRootAtTimestamp`](#supervisor_superrootattimestamp)
    - [`supervisor_syncStatus`](#supervisor_syncstatus)
    - [`supervisor_allSafeDerivedAt`](#supervisor_allsafederivedat)
    - [`supervisor_checkAccessList`](#supervisor_checkaccesslist)
      - [Access-list contents](#access-list-contents)
      - [Access-list execution context](#access-list-execution-context)
      - [Access-list checks](#access-list-checks)
      - [`supervisor_checkAccessList` contents](#supervisor_checkaccesslist-contents)
  - [Errors](#errors)
    - [Error Codes](#error-codes)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The supervisor is an implementation detail of OP Stack native interop and is not the only
architecture that can be used to implement it. The supervisor is responsible for indexing
data from all of the chains in a cluster so that the [safety level](./verifier.md#safety)
of executing messages can quickly be determined.

## RPC API

### Common types

#### `Identifier`

The identifier of a message.
Corresponds to an [Identifier](./messaging.md#message-identifier).

Object:
- `origin`: `Address`
- `blockNumber`: `HexUint64`
- `logIndex`: `HexUint64`
- `timestamp`: `HexUint64`
- `chainID`: `ChainID`

#### `Message`

Describes an initiating message.

Object:
- `identifier`: `Identifier` - identifier of the message
- `payloadHash`: `Hash` - `keccak256` hash of the message-payload bytes

#### `ExecutingDescriptor`

Describes the context for message verification.
Specifically, this helps apply message-expiry rules on message checks.

Object:
- `timestamp`: `HexUint64` - expected timestamp during message execution.
- `timeout`: `HexUint64` - optional, requests verification to still hold at `timestamp+timeout` (inclusive).
  The message expiry-window may invalidate messages.
  Default interpretation is a `0` timeout: what is valid at `timestamp` may not be valid at `timestamp+1`.

#### `HexUint64`

`STRING`:
Hex-encoded big-endian number, variable length up to 64 bits, prefixed with `0x`.

#### `Int`

`NUMBER`:
Regular JSON number, always integer. Assumed to always fit in 51 bits.

#### `ChainID`

`STRING`:
Hex-encoded big-endian number, variable length up to 256 bits, prefixed with `0x`.

#### `Hash`

`STRING`:
Hex-encoded, fixed-length, representing 32 bytes, prefixed with `0x`.

#### `Bytes`

`STRING`:
Hex-encoded, variable length (always full bytes, no odd number of nibbles),
representing a bytes list, prefixed with `0x`.

#### `BlockID`

Describes a block.

`OBJECT`:
- `hash`: `HASH` - block hash
- `number`: `Int` - block number

#### `BlockRef`

Describes a block.

`OBJECT`:
- `hash`: `Hash` - block hash
- `number`: `Int` - block number
- `parentHash`: `Hash` - block parent-hash
- `timestamp`: `Int` - block timestamp

#### `DerivedIDPair`

#### `ChainRootInfo`

`OBJECT`:
- `chainId`: `HexUint64` - The chain ID (Note: this is changing to `ChainID` soon)
- `canonical`: `Hash` - output root at the latest canonical block
- `pending`: `Bytes` - output root preimage

#### `SuperRootResponse`

`OBJECT`:
- `crossSafeDerivedFrom`: `BlockID` - common derived-from where all chains are cross-safe
- `timestamp`: `Int` - The timestamp of the super root
- `superRoot`: `Hash` - The root of the super root
- `version`: `Int` - The version of the response
- `chains`: `ARRAY` of `ChainRootInfo` - List of chains included in the super root

#### `SafetyLevel`

The safety level of the message.
Corresponds to a verifier [SafetyLevel](./verifier.md#safety).

`STRING`, one of:
- `invalid`
- `unsafe`: equivalent to safety of the `latest` RPC label.
- `cross-unsafe`
- `local-safe`
- `safe`: matching cross-safe, named `safe` to match the RPC label.
- `finalized`

### Methods

#### `supervisor_crossDerivedToSource`

Parameters:
- `chainID`: `ChainID`
- `derived`: `BlockID`

Returns: derivedFrom `BlockRef`

#### `supervisor_localUnsafe`

Parameters:
- `chainID`: `ChainID`

Returns: `BlockID`

#### `supervisor_crossSafe`

Parameters:
- `chainID`: `ChainID`

Returns: `DerivedIDPair`

#### `supervisor_finalized`

Parameters:
- `chainID`: `ChainID`

Returns: `BlockID`

#### `supervisor_finalizedL1`

Parameters: (none)

Returns: `BlockRef`

#### `supervisor_superRootAtTimestamp`

Retrieves the super root state at the specified timestamp,
which represents the global state across all monitored chains.

Parameters:
- `timestamp`: `HexUint64`

Returns: `SuperRootResponse`

#### `supervisor_syncStatus`

Parameters: (none)

Returns: `SupervisorSyncStatus`

#### `supervisor_allSafeDerivedAt`

Returns the last derived block for each chain, from the given L1 block.

Parameters:
- `derivedFrom`: `BlockID`

Returns: derived blocks, mapped in a `OBJECT`:
- key: `ChainID`
- value: `BlockID`

#### `supervisor_checkAccessList`

Verifies if an access-list, as defined in [EIP-2930], references only valid messages.
Message execution in the [`CrossL2Inbox`] that is statically declared in the access-list will not revert.

[EIP-2930]: https://eips.ethereum.org/EIPS/eip-2930

##### Access-list contents

Only the [`CrossL2Inbox`] subset of the access-list in the transaction is required,
storage-access by other addresses is not included.

Note that an access-list can contain multiple different storage key lists for the `CrossL2Inbox` address.
All storage keys applicable to the `CrossL2Inbox` MUST be joined together (preserving ordering),
missing storage-keys breaks inbox safety.

**ALL storage-keys in the access-list for the `CrossL2Inbox` MUST be checked.**
If there is any unrecognized or invalid key, the access-list check MUST fail.

[`CrossL2Inbox`]: ./predeploys.md#crossl2inbox

##### Access-list execution context

The provided execution-context is used to determine validity relative to the provided time constraints,
see [timestamp invariants](./derivation.md#invariants).

Since messages expire, validity is not definitive.
To reserve validity for a longer time range, a non-zero `timeout` value can be used.
See [`ExecutingDescriptor`](#executingdescriptor) documentation.

As block-builder a `timeout` of `0` should be used.

As transaction pre-verifier, a `timeout` of `86400` (1 day) should be used.
The transaction should be re-verified or dropped after this time duration,
as it can no longer be safely included in the block due to message-expiry.

##### Access-list checks

The access-list check errors are not definite state-transition blockers, the RPC based checks can be extra conservative.
I.e. a message that is uncertain to meet the requested safety level may be denied.
Specifically, no attempt may be made to verify messages that are initiated and executed within the same timestamp,
these are `invalid` by default.
Advanced block-builders may still choose to include these messages by verifying the intra-block constraints.

##### `supervisor_checkAccessList` contents

Parameters:
- `inboxEntries`: `ARRAY` of `Hash` - statically declared `CrossL2Inbox` access entries.
- `minSafety`: `SafetyLevel` - minimum required safety, one of:
  - `unsafe`: the message exists.
  - `cross-unsafe`: the message exists in a cross-unsafe block.
  - `local-safe`: the message exists in a local-safe block, not yet cross-verified.
  - `safe`: the message exists in a derived block that is cross-verified.
  - `finalized`: the message exists in a finalized block.
  - Other safety levels are invalid and result in an error.
- `executingDescriptor`: `ExecutingDescriptor` - applies as execution-context to all messages.

Returns: RPC error if the `minSafety` is not met by one or more of the access entries.

The access-list entries represent messages, and may be incomplete or malformed.
Malformed access-lists result in an RPC error.

### Errors

The Supervisor RPC API uses standard JSON-RPC error codes along with specific application error codes to provide deterministic error handling across different implementations.

#### Standard JSON-RPC Error Codes

##### -32700

Parse error  
Invalid JSON

##### -32600

Invalid request  
This can happen when your request is malformed. Additionally, some of the provides use this code to signal that a particular method is not available or requires switching to a paid tier.

##### -32601

Method not found  
This usually happens when the method is not available with a given provider. If you need to use a specific method that's not supported by the provider, try changing the provider or consider switching to a more expensive tier.

##### -32602

Invalid params  
This happens when the request parameters are invalid. To fix, double check the parameters that you pass with the request and make sure they comply with the spec.

##### -32603

Internal error  
This might happen when the node reverts during the request execution. This can also happen if the request is malformed or invalid.

##### -32000

Invalid input  
Missing or invalid parameters

##### -32001

Resource not found  
This usually happens when calling a method that's not supported. Try using a different method or switch providers.

##### -32002

Resource unavailable  
Requested resource not available

##### -32003

Transaction rejected  
Transaction creation failed

##### -32004

Method not supported  
Method is not implemented

##### -32005

Limit exceeded  
Request exceeds defined limit

##### -32006

JSON-RPC version not supported  
Version of JSON-RPC protocol is not supported

#### Protocol Specific Error Codes

##### -32100

unknown chain  
happens when a chain is unknown, not in the dependency set.

##### -32101

uninitialized chain database
Happens when a chain database is not initialized yet

##### -32102

out of scope  
Data access is not allowed because of a limited scope.

##### -32110

skipped data  
Happens when data is just not yet available.

##### -32111

data out of order  
Happens when you try to add data to the DB, but it does not actually fit onto the latest data (by being too old or new).

##### -32112

future data  
Happens when data is just not yet available.

##### -32113

missed data
Happens when we try to retrieve data that is not available (pruned)

##### -32114

conflicting data  
Happens when we know for sure that there is different canonical data

##### -32115

awaiting replacement block  
Happens when we know for sure that a replacement block is needed before progress can be made

##### -32116

ineffective data  
Happens when data is accepted as compatible, but did not change anything. This happens when a node is deriving an L2 block we already know of being derived from the given source, but without path to skip forward to newer source blocks without doing the known derivation work first.

##### -32117

data corruption  
happens when the underlying DB has some I/O issue

##### -32118

iter stop  
Happens when data is accessed, but access is not allowed, because of a limited scope. E.g. when limiting scope to L2 blocks derived from a specific subset of the L1 chain.

##### -32119

cannot get parent of first block in the database
Happens when you try to get the previous block of the first block. E.g. when calling PreviousDerivedFrom on the first L1 block in the DB.
