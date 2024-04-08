# Builder API
<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Builder API](#builder-api)
  - [Overview](#overview)
  - [Sequencer Interaction](#sequencer-interaction)
    - [Requesting a Block](#requesting-a-block)
      - [Liveness Failsafe](#liveness-failsafe)
    - [Mempool Forwarding](#mempool-forwarding)
    - [Builder Configuration](#builder-configuration)
  - [Structures](#structures)
    - [`PayloadRequestV1`](#payloadrequestv1)
    - [`BuilderPayloadV1`](#builderpayloadv1)
  - [Methods](#methods)
    - [`builder_getPayloadV1`](#builder_getpayloadv1)
      - [Request](#request)
      - [Response](#response)
      - [Specification](#specification)
    - [`builder_forwardTransactionV1`](#builder_forwardtransactionv1)
      - [Request](#request-1)
      - [Response](#response-1)
      - [Specification](#specification-1)
  - [Alternative Approach for Review (!!!!Most Likely To Be Deleted but Keeping for Consideration!!!!)](#alternative-approach-for-review-most-likely-to-be-deleted-but-keeping-for-consideration)
    - [`engine_forkchoiceUpdatedV4`](#engine_forkchoiceupdatedv4)
    - [Extended `PayloadAttributesV4`](#extended-payloadattributesv4)
      - [Process](#process)
    - [Rationale](#rationale)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview
This document provides a in-depth specification for integrating a Builder API within the Optimism Protocol and Stack. The Builder API provides a standardized interface for block construction and transaction management between the Sequencer and an external network of Block Builders. The interactions are the minimum viable design needed to enable an external Builder Network enabling future protocol experimentation which can unlock sequencer decentralization. Additionally this minimum viable design includes a fallback as a training wheel to ensure liveness and network performance. This document ***does not*** outline how to safely enable a permissionless Builder Network to serve payloads or how to manage these configs on L1.

Separating Block Building from the Sequencer's Execution Engine offers chain operators a way to modify block building rules without creating a large divergence from the upstream Optimism Protocol Client, allowing different chains in the superchain to supply their own block building systems as a way to differentiate.


## Sequencer Interaction

![image](/specs/static/assets/builder_sequence_diagram.svg)

- **Fork Choice Update**: The Sequencer propagates a Fork Choice Update to the Builder, indicating an update to the chain's latest head.
- **Forward Transaction**: The Sequencer forwards a transaction it received to the Builder to be included in a block. This step is not necessary if the builder can get transactions elsewise.
- **Get Payload**: The Sequencer requests a block from the Builder for a specific head.

### Requesting a Block

The block request mechanism ***MUST*** be triggered when the Driver schedules a new Fork Choice Update on the Sequencer. The Sequencer will translate the received Payload Attributes into a Payload Request for the Builder. As specified lower, the Sequencer ***MUST*** simulate the received payload to ensure correctness until an accountability mechanism can be introdcued.

#### Liveness Failsafe
To maintain network liveness while utilizing the Builder API, the Sequencer ***MUST*** operate an auxiliary process when building blocks. This process concurrently executes a builder API request to the Buidler alongside a local block production request through its local execution engine. This two-pronged strategy for generating blocks ensures that network liveness persists, even in instances where the builder's block construction process may experience delays or is offline. This fallback mechanism should be seen as a training wheel for the Builder API.

### Mempool Forwarding

A builder network's throughput is conditional on the transactions it sees. Thus the Sequencer can forward transactions to the Builder as part of regular mempool management, ensuring that user transactions are included in the Builder's block construction process efficiently.

### Builder Configuration

A builder is defined as the tuple (`builderPubkey`, `builderUrl`). The Sequencer is responsible for managing this tuple, but it will eventually live on the L1 [`SystemConfig`](https://github.com/ethereum-optimism/specs/blob/main/specs/protocol/system_config.md) where changes are emitted as an event.  Builder's have no restriction or policies enforced on them at this time.

## Structures

### `PayloadRequestV1`
[TOOD] : We could potentially extend to `PayloadAttributesV3` to `PayloadAttributesV4` which includes our necessary Builder API fields. This seems ideal that we could simply extend `PayloadAttributesV3`, but seems like it would create more conflicts. 

This structure contains information necessary to request a block from an external network of builders.
- `blockNumber`: `uint256`
- `parentHash`:  `Hash32`
- `pubKey`: `Address`
- `gasLimit`: `uint256`
- `parentBeaconBlockRoot`: `Hash32`
    
    
### `BuilderPayloadV1`   
This structure represents the Block Builder's response to the request for payload.
- `executionPayload`: `ExecutionPayloadV2` ([spec](https://github.com/ethereum/execution-apis/blob/584905270d8ad665718058060267061ecfd79ca5/src/engine/shanghai.md#executionpayloadv2))
- `pubKey`: `Address`
- `value`: `uint256`

## Methods

### `builder_getPayloadV1`

#### Request

* **method**: `builder_getPayloadV1`
* **params**:
    1. `payload`: `PayloadRequestV1`
        - **Required**: true
        - **Description**: Details of block construction request for external Builder
    - `signature` : `Signature`
        - **Required**: true
        - **Description**: `secp256k1` signature over `payload`
* **timeout**: 200ms
* **retries**: 0
    * Timeout does not leave enough time to retry for this block, Sequencer ***SHOULD*** use local block and move on.

#### Response

* **result**: `BuilderPayloadV1`
* **error**: code and message set in case an exception happens while getting the payload.
    
#### Specification

1. Client software ***MAY*** call this method if `builderPubkey` and `builderUrl` are set.
2. Client software ***MUST*** validate that the response object `BuilderPayloadV1` contains `executionPayload` and that `pubKey` matches the registered `builderPubkey`.
3. Client software ***MUST*** follow the same specification as [`engine_newPayloadV3`](https://github.com/ethereum/execution-apis/blob/main/src/engine/cancun.md#executionpayloadv3) with the response body `executionPayload`.
4. Client software ***MUST*** simulate transactions in `executionPayload` on `parentHash` in`payload` all fields in `executionPayload` are correct as compared to local view of chain.

### `builder_forwardTransactionV1`
    
#### Request

* **method**: `builder_forwardTransactionV1`
* **params**:
    1. `transaction`: `string`
        - **Required**: true
        - **Description**: Hex Encoded RLP string of the transaction
* **timeout**: 200ms
    * Short timeout to increase chance of including high priority gas transactions in the Builder's current block
* **retries**: 5
    * Needed to ensure user transactions do not get "lost" in event of a failed post. Client ***SHOULD*** log loudly in event all 5 retries fail.

#### Response

* **result**: `status`
* **error**: code and message set in case an exception happens while storing the transaction.
    
#### Specification

1. Client software ***MAY*** call this method if `builderPubkey` and `builderUrl` are set.
2. Client software ***MUST*** retry if status is not `200`.


## Alternative Approach for Review (!!!!Most Likely To Be Deleted but Keeping for Consideration!!!!)

Out of scope of this document but:
- The base version of this idea is to use EVM bytecode to order transactions. 
- The next level version of this is to run a [paravirtualized](https://en.wikipedia.org/wiki/Paravirtualization) EVM from inside of a Modified EVM (interpreter mods only) that injects an API into the paravirtualized EVM located at specific precompiles which gives access to the hosts resources (state trie, simulation capabilities, etc). 
  

### `engine_forkchoiceUpdatedV4`

See [`engine_forkchoiceUpdatedV3`](https://github.com/ethereum-optimism/specs/blob/main/specs/protocol/exec-engine.md#engine_forkchoiceupdatedv3) for a description of the forkchoice updated method. `engine_forkchoiceUpdatedV4` must only be called with Ecotone payload.

To support rollup functionality, one backwards-compatible change is introduced to `engine_forkchoiceUpdatedV4`: the extended `PayloadAttributesV4`

### Extended `PayloadAttributesV4`
`PayloadAttributesV3` is extended to:

```js
PayloadAttributesV4: {
    //same as V3
    ...
    suggestedSequencerPolicy: DATA (20 bytes)
}
```

#### Process
1. OP-Node Sequencer sends `forkChoiceUpdateV4` to configured builder or execution engine.
2. Recipient builder/execution engine ***SHOULD*** grab the EVM byte code at `suggestedSequencerPolicy` if not already cached.
3. Builder grabs mempool transactions and passes as input to bytecode from `suggestedSequencerPolicy` expecting an ordered list of transactions back
4. Ordered list of transactions is passed to execution engine for execution.

![image](/specs/static/assets/paravirtual_evm.png)

### Rationale
- Fully solidity defined sequencing and block building logic
- Programmable sequencing and block building rules without client modification
- Mark comment: putting this inside of forkChoiceUpdate means it needs to be included in batch serialization which is annoying
