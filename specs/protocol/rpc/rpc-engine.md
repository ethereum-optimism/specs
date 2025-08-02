# Engine RPC

> **Moved from:** [specs/protocol/exec-engine.md](../exec-engine.md)

## Engine API

### `engine_forkchoiceUpdatedV2`

This updates which L2 blocks the engine considers to be canonical (`forkchoiceState` argument),
and optionally initiates block production (`payloadAttributes` argument).

Within the rollup, the types of forkchoice updates translate as:

- `headBlockHash`: block hash of the head of the canonical chain. Labeled `"unsafe"` in user JSON-RPC.
  Nodes may apply L2 blocks out of band ahead of time, and then reorg when L1 data conflicts.
- `safeBlockHash`: block hash of the canonical chain, derived from L1 data, unlikely to reorg.
- `finalizedBlockHash`: irreversible block hash, matches lower boundary of the dispute period.

To support rollup functionality, one backwards-compatible change is introduced
to [`engine_forkchoiceUpdatedV2`][engine_forkchoiceUpdatedV2]: the extended `PayloadAttributesV2`

#### Extended PayloadAttributesV2

[`PayloadAttributesV2`][PayloadAttributesV2] is extended to:

```js
PayloadAttributesV2: {
    timestamp: QUANTITY
    prevRandao: DATA (32 bytes)
    suggestedFeeRecipient: DATA (20 bytes)
    withdrawals: array of WithdrawalV1
    transactions: array of DATA
    noTxPool: bool
    gasLimit: QUANTITY or null
}
```

The type notation used here refers to the [HEX value encoding] used by the [Ethereum JSON-RPC API
specification][JSON-RPC-API], as this structure will need to be sent over JSON-RPC. `array` refers
to a JSON array.

Each item of the `transactions` array is a byte list encoding a transaction: `TransactionType ||
TransactionPayload` or `LegacyTransaction`, as defined in [EIP-2718][eip-2718].
This is equivalent to the `transactions` field in [`ExecutionPayloadV2`][ExecutionPayloadV2]

The `transactions` field is optional:

- If empty or missing: no changes to engine behavior. The sequencers will (if enabled) build a block
  by consuming transactions from the transaction pool.
- If present and non-empty: the payload MUST be produced starting with this exact list of transactions.
  The [rollup driver][rollup-driver] determines the transaction list based on deterministic L1 inputs.

The `noTxPool` is optional as well, and extends the `transactions` meaning:

- If `false`, the execution engine is free to pack additional transactions from external sources like the tx pool
  into the payload, after any of the `transactions`. This is the default behavior a L1 node implements.
- If `true`, the execution engine must not change anything about the given list of `transactions`.

If the `transactions` field is present, the engine must execute the transactions in order and return `STATUS_INVALID`
if there is an error processing the transactions. It must return `STATUS_VALID` if all of the transactions could
be executed without error. **Note**: The state transition rules have been modified such that deposits will never fail
so if `engine_forkchoiceUpdatedV2` returns `STATUS_INVALID` it is because a batched transaction is invalid.

The `gasLimit` is optional w.r.t. compatibility with L1, but required when used as rollup.
This field overrides the gas limit used during block-building.
If not specified as rollup, a `STATUS_INVALID` is returned.

[rollup-driver]: rollup-node.md

### `engine_forkchoiceUpdatedV3`

See [`engine_forkchoiceUpdatedV2`](#engine_forkchoiceupdatedv2) for a description of the forkchoice updated method.
`engine_forkchoiceUpdatedV3` **must only be called with Ecotone payload.**

To support rollup functionality, one backwards-compatible change is introduced
to [`engine_forkchoiceUpdatedV3`][engine_forkchoiceUpdatedV3]: the extended `PayloadAttributesV3`

#### Extended PayloadAttributesV3

[`PayloadAttributesV3`][PayloadAttributesV3] is extended to:

```js
PayloadAttributesV3: {
    timestamp: QUANTITY
    prevRandao: DATA (32 bytes)
    suggestedFeeRecipient: DATA (20 bytes)
    withdrawals: array of WithdrawalV1
    parentBeaconBlockRoot: DATA (32 bytes)
    transactions: array of DATA
    noTxPool: bool
    gasLimit: QUANTITY or null
    eip1559Params: DATA (8 bytes) or null
}
```

The requirements of this object are the same as extended [`PayloadAttributesV2`](#extended-payloadattributesv2) with
the addition of `parentBeaconBlockRoot` which is the parent beacon block root from the L1 origin block of the L2 block.

Starting at Ecotone, the `parentBeaconBlockRoot` must be set to the L1 origin `parentBeaconBlockRoot`,
or a zero `bytes32` if the Dencun functionality with `parentBeaconBlockRoot` is not active on L1.

Starting with Holocene, the `eip1559Params` field must encode the EIP1559 parameters. It must be `null` before.
See [Dynamic EIP-1559 Parameters](holocene/exec-engine.md#dynamic-eip-1559-parameters) for details.

### `engine_newPayloadV2`

No modifications to [`engine_newPayloadV2`][engine_newPayloadV2].
Applies a L2 block to the engine state.

### `engine_newPayloadV3`

[`engine_newPayloadV3`][engine_newPayloadV3] applies an Ecotone L2 block to the engine state. There are no
modifications to this API.
`engine_newPayloadV3` **must only be called with Ecotone payload.**

The additional parameters should be set as follows:

- `expectedBlobVersionedHashes` MUST be an empty array.
- `parentBeaconBlockRoot` MUST be the parent beacon block root from the L1 origin block of the L2 block.

### `engine_newPayloadV4`

[`engine_newPayloadV4`][engine_newPayloadV4] applies an Isthmus L2 block to the engine state.
The `ExecutionPayload` parameter will contain an extra field, `withdrawalsRoot`, after the Isthmus hardfork.

`engine_newPayloadV4` **must only be called with Isthmus payload.**

The additional parameters should be set as follows:

- `executionRequests` MUST be an empty array.

### `engine_getPayloadV2`

No modifications to [`engine_getPayloadV2`][engine_getPayloadV2].
Retrieves a payload by ID, prepared by `engine_forkchoiceUpdatedV2` when called with `payloadAttributes`.

### `engine_getPayloadV3`

[`engine_getPayloadV3`][engine_getPayloadV3] retrieves a payload by ID, prepared by `engine_forkchoiceUpdatedV3`
when called with `payloadAttributes`.
`engine_getPayloadV3` **must only be called with Ecotone payload.**

#### Extended Response

The [response][GetPayloadV3Response] is extended to:

```js
{
    executionPayload: ExecutionPayload
    blockValue: QUANTITY
    blobsBundle: BlobsBundle
    shouldOverrideBuilder: BOOLEAN
    parentBeaconBlockRoot: DATA (32 bytes)
}
```

[GetPayloadV3Response]: https://github.com/ethereum/execution-apis/blob/main/src/engine/cancun.md#response-2

In Ecotone it MUST be set to the parentBeaconBlockRoot from the L1 Origin block of the L2 block.

### `engine_getPayloadV4`

[`engine_getPayloadV4`][engine_getPayloadV4] retrieves a payload by ID, prepared by `engine_forkchoiceUpdatedV3`
when called with `payloadAttributes`.
`engine_getPayloadV4` **must only be called with Isthmus payload.**

### `engine_signalSuperchainV1`

Optional extension to the Engine API. Signals superchain information to the Engine:
V1 signals which protocol version is recommended and required.

Types:

```javascript
SuperchainSignal: {
  recommended: ProtocolVersion;
  required: ProtocolVersion;
}
```

`ProtocolVersion`: encoded for RPC as defined in
[Protocol Version format specification](superchain-upgrades.md#protocol-version-format).

Parameters:

- `signal`: `SuperchainSignal`, the signaled superchain information.

Returns:

- `ProtocolVersion`: the latest supported OP-Stack protocol version of the execution engine.

The execution engine SHOULD warn the user when the recommended version is newer than
the current version supported by the execution engine.

The execution engine SHOULD take safety precautions if it does not meet the required protocol version.
This may include halting the engine, with consent of the execution engine operator. 
