# Builder API

This document provides a in-depth specification for integrating a Builder framework within the Optimism protocol and stack. It outlines necessary modifications to the Sequencer to support interactions with the Builder API and details the Builder API's structure and functionalities. It ***does not*** outline how to safely enable a builder network to serve payloads or how to manage these configs on L1.

Separating the building from FCU offers chain operators a way to modify block building rules without creating a large divergence from the upstream Optimism Protocol Client, allowing different chains in the superchain to supply their own block building systems as a way to differentiate.

[ToC]

## Sequencer Interaction


The Builder API facilitates a standardized interface for block construction and transaction management between the Sequencer and an external Builder Network. The interactions are the minimum viable design needed to enable an external Builder Network enabling future protocol experimentation which can unlock sequencer decentralization. Additionally this minimum viable design includes a fallback as a training wheel to ensure liveness and network performance.

![image](https://hackmd.io/_uploads/S1nE75egA.png)


- **Fork Choice Update**: The Sequencer propagates a Fork Choice Update to the Builder, indicating an update to the chain's latest head.
- **Forward Transaction**: The Sequencer forwards a transaction it received to the Builder to be included in a block. This step is not necessary if the builder can get transactions else-wise.
- **Get Payload**: The Sequencer requests the Builder for a block that builds on a specific head.


### Requesting a Block

The block request mechanism ***MUST*** be triggered when the Driver schedules a new Fork Choice Update on the Sequencer. The Sequencer will translate the received Payload Attributes into a Payload Request for the Builder 

#### Liveness Fallback Mechanism
To maintain network liveness while utilizing the Builder API, the Sequencer ***MUST*** operate an auxiliary process when building blocks. This process concurrently executes a builder API request to the Buidler alongside a local block production request through its local execution engine. This two-pronged strategy for generating blocks ensures that network liveness persists, even in instances where the builder's block construction process may experience delays or is offline. This fallback mechanism should be seen as a training wheel for the Builder API.

### Mempool Forwarding

A builder network's throughput is conditional on the transactions it sees. Thus the Sequencer can forward transactions to the Builder as part of regular mempool management, ensuring that user transactions are included in the Builder's block construction process efficiently.

### Builder Configuration

A builder is defined as the tuple (`builderPubkey`, `builderUrl`). The Sequencer is responsible for managing this tuple, but will eventually live on the L1 Config (TODO: What is the L1 config contract called?). Builder's have no restriction or policies enforced on them at this time.

## Structures

### `PayloadRequestV1`
[TOOD] : We could potentially extend to `PayloadAttributesV3` to `PayloadAttributesV4` which includes our necessary Builder API fields. This seems ideal that we could simply extend `PayloadAttributesV3`, but seems like it would create more conflicts. 

This structure contains information necessary to request a block from an external network of builders.
- `blockNumber`: `uint256`
- `parentHash`:  `Hash32`
- `pubKey`: `Address`
- `gasLimit`: `uint256`
- `parentBeaconBlockRoot`: [TODO]
- `seqNumber`: [TODO]
    
    
### `BuilderPayloadV1`   
This structure represents the Block Builder's response to the request for payload.
- `executionPayload`: `ExecutionPayloadV2` ([spec](https://github.com/ethereum/execution-apis/blob/584905270d8ad665718058060267061ecfd79ca5/src/engine/shanghai.md#executionpayloadv2))
- `pubKey`: `Address`
- `value`: `uint256`

## Methods

### builder_getPayloadV1

#### Request

* **method**: `builder_getPayloadV1`
* **params**:
    1. `payload`: `PayloadRequestV1`
        - **Required**: true
        - **Description**: Details of block construction request for external Builder
    - `signature` : `Signature` (TODO: Link to correct signature type)
        - **Required**: true
        - **Description**: `secp256k1` signature over `payload`
* **timeout**: 200ms
* **retries**: 0
    * Timeout does not leave enough time to retry for this block, Sequencer ***SHOULD*** use local block and move on.

#### Response

* result: `BuilderPayloadV1`
* error: code and message set in case an exception happens while getting the payload.
    
#### Specification

1. Client software ***MAY*** call this method if `builderPubkey` and `builderUrl` are set.
2. Client software ***MUST*** validate that the response object `BuilderPayloadV1` contains `executionPayload` and that `pubKey` matches the registered `builderPubkey`.
3. Client software ***MUST*** follow the same specification as [`engine_newPayloadV3`](https://github.com/ethereum/execution-apis/blob/main/src/engine/cancun.md#executionpayloadv3) with the response body`executionPayload`.
4. Client software ***MUST*** simulate transactions in `executionPayload` on `parentHash` in`payload` all fields in `executionPayload` are correct as compared to local view of chain.

### builder_forwardTransactionV1
    
#### Request

* method: `builder_forwardTransactionV1`
* params:
    1. `transaction`: `string`
        - **Required**: true
        - **Description**: Hex Encoded RLP string of the transaction
* timeout: 200ms
* retries: 5
    * Needed to ensure user transactions do not get "lost" in event of a failed post

#### Response

* result: `status`
* error: code and message set in case an exception happens while storing the transaction.
    
#### Specification

1. Client software ***MAY*** call this method if `builderPubkey` and `builderUrl` are set.
2. Client software ***MUST*** retry if status is not `200`.