# Subblocks

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Consumer guarantees](#consumer-guarantees)
- [WebSocket stream](#websocket-stream)
  - [Sequence](#sequence)
  - [Payload](#payload)
  - [Zero-valued fields](#zero-valued-fields)
- [JSON-RPC](#json-rpc)
- [Transaction inclusion](#transaction-inclusion)
- [Backwards compatibility](#backwards-compatibility)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

Subblocks are partial blocks that an OP Stack sequencer streams while it is building an L2 block. Each subblock adds
transactions to the in-progress block, giving consumers a preconfirmation before the block is sealed and propagated
through the normal OP Stack protocol.

Subblocks do not change the validity or finality rules of the OP Stack. They only expose the sequencer's in-progress
view sooner. A subblock therefore carries the same trust assumption as an unsafe block: its preconfirmations may be
revoked if the sequencer abandons or reorganizes the in-progress block.

The interval between subblocks is chain-configurable and is a target rather than a guarantee. It is typically much
shorter than the L2 block time.

## Consumer guarantees

Within one in-progress block, subblocks are append-only:

- The first subblock has index `0`; subsequent subblocks increment the index by one.
- All subblocks for the in-progress block have the same `payload_id` and block number.
- The sequencer MUST NOT publish distinct subblocks with the same `payload_id` and `index`.
- Transactions from each subblock are appended in stream order. A consumer obtains the in-progress transaction list by
  concatenating each subblock's `diff.transactions`.
- The cumulative in-progress block after each subblock MUST satisfy all applicable OP Stack execution rules.
- The first subblock contains the block's [deposited transactions](../glossary.md#deposited-transaction) and any other
  sequencer transactions that execute before mempool transactions. Later subblocks add mempool transactions.

If the sequencer abandons the in-progress block, a new in-progress block starting at index `0` supersedes it. Consumers
MUST NOT treat a subblock as safe or final chain data.

## WebSocket stream

The sequencer publishes subblocks through a WebSocket endpoint. Each WebSocket text frame contains one JSON `Subblock`
object, as defined below. Field names use `snake_case`; byte strings, addresses, hashes, transactions, and quantities
use their standard Ethereum JSON encodings unless stated otherwise below.

The JSON shape deliberately retains Flashblocks-era names and fields for wire compatibility.

### Sequence

The first `Subblock` for an in-progress block has `index` equal to `0` and includes `base`. Each subsequent `Subblock`
increments `index` by one and omits `base`. The `payload_id`, `base`, and `metadata.block_number` identify the
in-progress L2 block.

A consumer joining the stream after index `0` cannot reconstruct the complete in-progress block. It SHOULD ignore
payloads until it receives the next index `0`. A consumer SHOULD also discard its current sequence if an index is
skipped, duplicated, or paired with a different payload ID or block number.

### Payload

A subblock has the following shape. Optional fields are omitted when they do not apply.

```text
Subblock {
    payload_id: Bytes8
    index: uint64
    base: Optional[SubblockBase]
    diff: SubblockDelta
    metadata: Metadata
}

SubblockBase {
    parent_beacon_block_root: Bytes32
    parent_hash: Bytes32
    fee_recipient: Bytes20
    prev_randao: Bytes32
    block_number: uint64
    gas_limit: uint64
    timestamp: uint64
    extra_data: Bytes
    base_fee_per_gas: uint256
}

SubblockDelta {
    state_root: Bytes32
    receipts_root: Bytes32
    logs_bloom: Bytes256
    gas_used: uint64
    block_hash: Bytes32
    transactions: List[Bytes]
    withdrawals: List[WithdrawalV1]
    withdrawals_root: Bytes32
    blob_gas_used: Optional[uint64]
    post_exec_tx: Optional[Bytes]
}

Metadata {
    block_number: uint64
    new_account_balances: Map[Bytes20, uint256]
    receipts: Map[Bytes32, Receipt]
}
```

`WithdrawalV1` is the Ethereum Engine API's EIP-4895
[`WithdrawalV1`](https://github.com/ethereum/execution-apis/blob/739f9e00806003d2204adca7595f704849b9be30/src/engine/shanghai.md#withdrawalv1)
object. This field is retained for legacy wire compatibility and MUST be empty; it does not encode OP Stack L2-to-L1
withdrawals.

`Receipt` is the standard Ethereum transaction receipt described in the [glossary](../glossary.md#receipt), including
any OP Stack receipt extensions active for the block.

The fields have the following semantics:

- `payload_id` identifies one payload build and is constant throughout the sequence.
- `index` is a JSON number identifying the subblock's position in the sequence.
- `base` contains immutable block properties and is present only at index `0`.
- `diff.transactions` contains only the EIP-2718 encoded transactions added by this subblock.
- `diff.gas_used`, `diff.receipts_root`, and `diff.logs_bloom` describe the cumulative in-progress block after applying
  this subblock.
- `diff.blob_gas_used`, when present, is the cumulative [DA footprint](./jovian/exec-engine.md#da-footprint-block-limit)
  of the in-progress block, not L2 blob gas usage.
- From the [Lagoon network upgrade](./lagoon/overview.md), `diff.post_exec_tx`, when present, is the latest cumulative
  [post-execution transaction](./lagoon/post-exec.md). It is carried separately from `diff.transactions`.
- `metadata.block_number` is the L2 block number encoded as a JSON number.
- `metadata.new_account_balances` maps changed accounts to their latest balances.
- `metadata.receipts` maps transaction hashes to the receipts for transactions added by this subblock.

### Zero-valued fields

Subblock payloads set these four `diff` fields to their zero values:

| Field | Required value |
| --- | --- |
| `state_root` | `0x0000000000000000000000000000000000000000000000000000000000000000` |
| `block_hash` | `0x0000000000000000000000000000000000000000000000000000000000000000` |
| `withdrawals_root` | `0x0000000000000000000000000000000000000000000000000000000000000000` |
| `withdrawals` | `[]` |

These fields remain on the wire only for backwards compatibility. Consumers MUST treat them as unavailable and MUST
NOT use them as commitments to the in-progress block or state. In particular, a zero `state_root` or `block_hash` is
not the value of the eventual sealed block.

A consumer that needs the in-progress state may reconstruct it by executing the streamed transactions against the
parent state. The subblock stream does not indicate whether the in-progress block was sealed or abandoned. Consumers
obtain the sealed block's authoritative state root and block hash through normal L2 block propagation.

## JSON-RPC

Applications may consume subblocks via a subblock-aware RPC node instead of subscribing to the stream directly.
The node executes the streamed transactions and exposes the resulting state through standard Ethereum JSON-RPC
methods. No subblock-specific RPC method is required.

The following methods use subblock state when called with the `pending` block tag:

- `eth_call`
- `eth_estimateGas`
- `eth_getBalance`
- `eth_getBlockByNumber`
- `eth_getCode`
- `eth_getStorageAt`
- `eth_getTransactionCount`

Successive `eth_getBlockByNumber("pending", ...)` calls during the same L2 block may return an expanding transaction
list as new subblocks arrive.

Methods that identify a transaction directly, including `eth_getTransactionByHash` and
`eth_getTransactionReceipt`, may also return preconfirmed subblock transactions. Their responses
use the standard Ethereum JSON-RPC shapes, but block-derived fields are provisional until the block is sealed.

## Transaction inclusion

Subblocks divide a block's gas capacity across the block-building window. The amount of gas available for inclusion
increases as the block progresses. Consequently, a large transaction may be accepted into the transaction pool but
remain pending until a later subblock with enough remaining gas capacity. If earlier transactions consume too much of
the block gas limit, the transaction remains pending for a later block.

Applications SHOULD NOT assume that a transaction with a gas limit below the full block gas limit can be included in
the next subblock.

## Backwards compatibility

Subblocks are the backwards-compatible successor to Flashblocks. The WebSocket wire format remains compatible with the
[legacy Flashblocks wire format](https://github.com/flashbots/rollup-boost/blob/main/specs/flashblocks.md), and JSON-RPC
behavior is unchanged, so existing consumers can continue to decode the stream.

The compatibility exception is that subblocks always zero `state_root`, `block_hash`, `withdrawals_root`, and
`withdrawals` as specified above. A Flashblocks consumer that treated any of those fields as authoritative MUST be
updated before consuming subblocks. Other consumers can migrate without changing their wire decoder.
