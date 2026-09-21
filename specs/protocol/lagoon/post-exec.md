# Post-Execution Transactions

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [The Post-Execution Transaction Type](#the-post-execution-transaction-type)
  - [Encoding](#encoding)
  - [Transaction Hash](#transaction-hash)
  - [Generic Transaction Interface Representation](#generic-transaction-interface-representation)
  - [Signer and Signature](#signer-and-signature)
  - [Mempool and Propagation](#mempool-and-propagation)
- [Post-Exec Payload Envelope](#post-exec-payload-envelope)
  - [Schema Version](#schema-version)
  - [Block Number](#block-number)
  - [Defined Schema Versions](#defined-schema-versions)
- [Block-Level Structural Rules](#block-level-structural-rules)
- [DA Footprint](#da-footprint)
- [Receipt](#receipt)
- [Derivation](#derivation)
- [Subblocks](#subblocks)
  - [The post-exec transaction is carried in `diff`](#the-post-exec-transaction-is-carried-in-diff)
  - [The post-exec transaction never appears in `transactions`](#the-post-exec-transaction-never-appears-in-transactions)
  - [Only the last subblock's post-exec transaction is canonical](#only-the-last-subblocks-post-exec-transaction-is-canonical)
  - [A subblock's `transactions` may be empty](#a-subblocks-transactions-may-be-empty)
  - [No receipt is streamed for the post-exec transaction](#no-receipt-is-streamed-for-the-post-exec-transaction)
- [Rationale](#rationale)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

<!-- All glossary references in this file. -->

[g-transaction-type]: ../../glossary.md#transaction-type
[g-sequencer]: ../../glossary.md#sequencer
[g-deposited]: ../../glossary.md#deposited-transaction
[g-post-exec-payload]: ../../glossary.md#post-exec-payload
[g-post-exec-schema-version]: ../../glossary.md#post-exec-payload-schema-version
[g-sdm]: ../../glossary.md#sequencer-defined-metering

## Overview

Post-execution transactions are an [EIP-2718] [transaction type][g-transaction-type] that lets a block carry
sequencer-provided consensus data. Unlike user-submitted or [deposited transactions][g-deposited], a post-exec
transaction is created by the [sequencer][g-sequencer] and appended to the block as its final transaction. A
verifier applies its data as part of the block's state transition.

The post-exec transaction type is introduced by the [Lagoon network upgrade](./overview.md), together with its
first payload schema. Before the Lagoon activation timestamp a block MUST NOT contain a `0x7D` transaction.

The post-exec transaction is a generic envelope: it carries a versioned [post-exec payload][g-post-exec-payload]
whose interpretation is defined by separate policy specifications. Today only one schema is defined,
[Sequencer-Defined Metering][g-sdm] (`version = 1`), specified in [sdm.md](./sdm.md). Future policies extend
this document by defining additional [schema versions][g-post-exec-schema-version].

This document specifies the envelope: the transaction type, the encoding, and the structural invariants that hold
regardless of the active schema. It does **not** specify what the payload fields mean — that is the responsibility
of the active schema's specification.

[EIP-2718]: https://eips.ethereum.org/EIPS/eip-2718

## The Post-Execution Transaction Type

[post-exec-tx-type]: #the-post-execution-transaction-type

A post-execution transaction is an [EIP-2718] typed transaction with type byte `0x7D` (decimal 125).

Type byte `0x7D` was selected because EIP-2718 transaction type identifiers may use values up to `0x7F`; choosing a
high identifier minimizes the chance of collision with future Ethereum L1 transaction types. `0x7E` is reserved for
[deposited transactions](../deposits.md#the-deposited-transaction-type), and `0x7F` is left unused in case it is
later assigned to a variable-length encoding scheme.

### Encoding

The EIP-2718 encoding of a post-exec transaction is:

```text
0x7D || rlp_encoded_payload
```

where `rlp_encoded_payload` is the RLP encoding of the [post-exec payload][post-exec-payload-envelope] as a list,
and `||` denotes byte concatenation. The type byte is immediately followed by the payload's own RLP list; the
payload is not wrapped in an additional outer RLP list.

### Transaction Hash

The transaction hash of a post-exec transaction is:

```text
keccak256(0x7D || rlp_encoded_payload)
```

The hash is computed over the full EIP-2718 encoding, so the type byte is included in the hash preimage. Because
the hash is a function of the payload alone, the payload's [block number](#block-number) is what distinguishes
payloads anchored to different block numbers. (Two blocks at the same height on competing forks that carry an
identical payload share the same post-exec transaction hash, exactly as a regular transaction would.)

### Generic Transaction Interface Representation

A post-exec transaction carries only a versioned [post-exec payload][post-exec-payload-envelope]; it has none of
the fields a user transaction carries (nonce, gas price, recipient, signature, …). When surfaced through a generic
transaction interface (e.g. `eth_getTransactionByHash`), it is represented by a minimal object containing only:

| Field   | Value                                                       |
| ------- | ----------------------------------------------------------- |
| `type`  | `0x7D`                                                      |
| `hash`  | the [transaction hash](#transaction-hash)                   |
| `from`  | `0x0000000000000000000000000000000000000000` (zero address) |
| `gas`   | `0`                                                         |
| `value` | `0`                                                         |
| `input` | the RLP-encoded payload bytes                               |

Standard transaction fields that do not apply — including `nonce`, `chainId`, `gasPrice`, `maxFeePerGas`,
`maxPriorityFeePerGas`, `to`, `accessList`, and the signature fields — are omitted, not reported with placeholder
values. Block-context fields (`blockHash`, `blockNumber`, `transactionIndex`) are populated as for any other
included transaction.

A post-exec transaction never charges fees, never debits or credits an account simply by being included, and
consumes no gas from the block gas pool. Any side effects on account balances are defined by the active schema,
not by this envelope.

### Signer and Signature

A post-exec transaction has no signer and no signature: there is no `(v, r, s)` triple in its EIP-2718 encoding or
in the transaction-hash preimage. Rather than a per-transaction signature, it is trusted because the block that
contains it is — unsafe blocks are gossiped in payloads signed by the sequencer, and safe blocks are derived from
the (signed) batcher transaction. The sequencer places it at a position that satisfies the
[block-level structural rules](#block-level-structural-rules).

Its recovered sender is the zero address `0x0000000000000000000000000000000000000000`, surfaced as the transaction
object's `from` field. The signature fields are omitted from transaction responses rather than reported as zero.

### Mempool and Propagation

A post-exec transaction is constructed by the sequencer as part of block production. Nodes MUST NOT accept
post-exec transactions through public transaction-pool interfaces (e.g. `eth_sendRawTransaction`) and MUST NOT
propagate them through transaction-gossip protocols. A post-exec transaction reaches verifiers only by being
included in a block.

## Post-Exec Payload Envelope

[post-exec-payload-envelope]: #post-exec-payload-envelope

The post-exec payload is RLP-encoded as a list whose first two fields are fixed:

```text
[version, blockNumber, ...schema-defined fields...]
```

| Field         | Type     | Description                                                                    |
| ------------- | -------- | ------------------------------------------------------------------------------ |
| `version`     | `uint8`  | [Schema version](#schema-version) selecting the layout of the trailing fields. |
| `blockNumber` | `uint64` | The L2 block number this payload is anchored to.                               |
| _trailing_    | _varies_ | Defined by the active [schema version](#defined-schema-versions).              |

The leading two fields define the envelope; all remaining fields belong to the schema selected by `version`.

### Schema Version

`version` is the [post-exec payload schema version][g-post-exec-schema-version]. When the new payload schema calls
for additional or different fields, a new version number is assigned and the new layout is documented as a
[defined schema version](#defined-schema-versions).

### Block Number

`blockNumber` anchors the payload to the L2 block number of the containing block. The anchoring serves two
purposes:

1. It guarantees that otherwise identical payloads anchored to different block numbers have distinct
   [transaction hashes](#transaction-hash).
2. It detects misordered or replayed payloads at decode time, before any schema-specific validation runs.

The normative rule that `blockNumber` equals the containing block's number is stated in
[Block-Level Structural Rules](#block-level-structural-rules).

### Defined Schema Versions

| `version` | Schema                                 |
| --------- | -------------------------------------- |
| `1`       | [Sequencer-Defined Metering](./sdm.md) |

No other schema versions are currently defined. SDM (`version = 1`) is introduced by the
[Lagoon network upgrade](./overview.md); see [Overview](#overview).

## Block-Level Structural Rules

The following rules hold for every block, regardless of which schema version is active. Any violation invalidates
the block.

1. **At most one.** A block contains at most one transaction with type byte `0x7D`.
2. **Last in block.** When a `0x7D` transaction is present, it MUST be the final transaction of the block.
3. **Anchored to block.** The `blockNumber` field of the embedded payload MUST equal the L2 block number of the
   containing block.
4. **Recognized schema.** The payload's `version` MUST be a [defined schema version](#defined-schema-versions).
5. **Schema must be active.** When no schema version is active for the block's timestamp, the block MUST NOT
   contain a `0x7D` transaction.

Schema-specific validity rules (e.g. constraints on the trailing fields) are layered on top of these envelope rules
and are specified by each schema's document. Both layers MUST hold for the block to be valid.

## DA Footprint

The [Jovian DA footprint block limit](../jovian/exec-engine.md#da-footprint-block-limit) is modified to exclude
post-exec transactions. When computing a block's `daFootprint`, clients MUST treat a post-exec transaction as
having a DA footprint of zero. Clients MUST therefore skip transactions of type `0x7D` when accumulating the
block's `daFootprint`, and a post-exec transaction's receipt MUST report `blobGasUsed` as zero.

## Receipt

A post-exec transaction emits a receipt with type byte `0x7D`. The RLP-encoded consensus fields of the receipt are
identical to those of an EIP-1559 receipt:

- `postStateOrStatus` ([EIP-658])
- `cumulativeGasUsed`
- `logsBloom`
- `logs`

A post-exec transaction is constructed by the protocol; it is not executed as EVM code, emits no logs, and
consumes no gas from the block gas pool, so its own receipt records none of these:

- `postStateOrStatus` MUST encode success ([EIP-658] status `1`).
- `logs` MUST be empty.
- `logsBloom` MUST be the all-zero bloom filter.
- `cumulativeGasUsed` MUST equal the `cumulativeGasUsed` of the immediately preceding transaction's receipt. (In
  any L2 block the post-exec transaction has at least one preceding transaction — the L1 attributes deposit — so
  there is always a previous receipt to inherit from.)

The post-exec receipt participates in the block's receipts trie like any other receipt. The transaction's payload,
however, is consensus-critical and drives state changes under the active schema — for SDM, the per-transaction fee
[settlement](./sdm.md#settlement). Those changes are applied atomically with the transactions they refund, so they
belong to those transactions' state deltas, not to a separate post-exec state transition. Schema-specific data is
likewise surfaced on those transactions' receipts, not on the post-exec receipt.

[EIP-658]: https://eips.ethereum.org/EIPS/eip-658

## Derivation

Post-exec transactions are constructed by the sequencer during block production and travel inside the L2 block
body — through both the unsafe p2p payload and the L1 batch — rather than being synthesized from L1 events the way
deposited transactions are. They are included in the block payload that is submitted to the data availability
layer alongside the user transactions and any deposited transactions.

The L1 batcher transaction format is unaffected: post-exec transactions appear inside L2 blocks, never as L1
batcher transactions. The future-tx-type decoding range described in
[derivation.md](../derivation.md#on-future-proof-transaction-log-derivation) governs L1 receipts only and is
unchanged.

Because a post-exec transaction is carried in the L2 block body, a [span batch](../delta/span-batches.md) covering
that block must transpose it into the span batch `txs` structure. A post-exec transaction has no nonce, gas limit,
recipient or signature, so most of the per-transaction slots that structure reserves have no natural value for it.
The values they take, and the reconstruction rules that follow, are specified in
[Span Batch Updates](./derivation.md#span-batch-updates).

## Subblocks

[Subblocks](../subblocks.md) stream an L2 block while the sequencer is still building it. A post-exec transaction
is a function of the block's contents, so the sequencer recomputes it every time it extends the in-progress block.
This section specifies how it is exposed on that stream. It constrains the subblock wire format only; it does not
change any rule about the sealed block.

The decisions below are normative. Each is followed by a rationale and a consumer implication. **The rationales are
non-normative and subject to change**; they are recorded so a consumer can tell why the field sits where it does
without having to ask.

### The post-exec transaction is carried in `diff`

A subblock exposes the in-progress block's post-exec transaction as `diff.post_exec_tx`, holding its
[EIP-2718 encoding](#encoding) — the `0x7D` type byte followed by the RLP-encoded payload. It is a field of
`SubblockDelta`, not a member of `diff.transactions`.

`diff.post_exec_tx` is absent when the in-progress block carries no post-exec transaction. Under SDM this is the
case whenever the sequencer has assigned no gas refunds, since a version-1 payload with an empty
`gasRefundEntries` list is [invalid](./sdm.md#validity-rules) and no post-exec transaction is appended at all.

_Rationale (non-normative, subject to change)._ A subblock is not a block. Its `transactions` are append-only and
immutable once streamed, whereas its `diff` describes the cumulative in-progress block and is restated by every
subblock. A post-exec transaction is derived from the state after everything executed so far, so its value is
recomputed as subblocks are added. That makes it mutable data, which is what `diff` is for.

_Consumer implication._ Read the post-exec transaction from `diff`, and expect its value to change from subblock to
subblock within one `payload_id`. Treat an absent `post_exec_tx` as "this block has no post-exec transaction so
far", not as an error and not as "not yet computed". Absence is not sticky either: a later subblock of the same
`payload_id` may introduce the field once a refund becomes due.

### The post-exec transaction never appears in `transactions`

`diff.transactions` MUST NOT contain a `0x7D` transaction, in any subblock, at any index.

_Rationale (non-normative, subject to change)._ Placing it in `transactions` would require the sequencer to know
which subblock is the last one for the block, which it does not know while building. Appending it to an
append-only list in a subblock that turns out not to be last would publish a transaction that a later subblock
supersedes, and a consumer concatenating `transactions` across subblocks would reconstruct a transaction list
containing several `0x7D` transactions in non-final positions — a list that violates the
[block-level structural rules](#block-level-structural-rules) the sealed block satisfies.

_Consumer implication._ Do not look for the post-exec transaction in `transactions`, and do not expect the
concatenation of `diff.transactions` across a payload's subblocks to equal the sealed block's transaction list:
it is that list minus its post-exec transaction. `transactions` continues to carry every other transaction of the
block, including the [deposited transactions](../../glossary.md#deposited-transaction) in the first subblock.

### Only the last subblock's post-exec transaction is canonical

The `diff.post_exec_tx` of the last subblock of a payload is the post-exec transaction of the sealed block. The
value carried by any earlier subblock is provisional.

_Rationale (non-normative, subject to change)._ Each subblock's value reflects the block contents at that point in
the build. Only the final contents determine the transaction that is actually included, and the payload is
[anchored to the block number](#block-number) rather than to any subblock, so intermediate values are not
independently meaningful.

_Consumer implication._ The stream carries no marker identifying the last subblock of a payload, and the number of
subblocks per block is [a target rather than a guarantee](../subblocks.md#overview) — a block may carry one fewer
or one more than usual. A consumer therefore MUST NOT treat any subblock's `post_exec_tx` as final while the block
is still being built. Determine that the block was sealed by other means, such as observing the next `payload_id`
or the canonical block arriving through normal L2 block propagation, and note that the in-progress block may be
abandoned rather than sealed, in which case no value from it was ever canonical.

### A subblock's `transactions` may be empty

A subblock MAY have `transactions: []`.

_Rationale (non-normative, subject to change)._ A subblock carries a state diff and the current `post_exec_tx`
whether or not it added transactions. Suppressing subblocks with no new transactions would withhold the updated
diff, and requiring one would make the stream's cadence depend on transaction arrival.

_Consumer implication._ Handle an empty `transactions` list as ordinary: it is neither an error nor a signal that
nothing changed. Such a subblock still restates `diff`, including the current `post_exec_tx`, and still advances
`index`.

### No receipt is streamed for the post-exec transaction

`metadata.receipts` MUST NOT contain an entry for a post-exec transaction. It covers the transactions in
`diff.transactions` only.

_Rationale (non-normative, subject to change)._ Same as the reason it is absent from `transactions`: a receipt for
a provisional post-exec transaction would be superseded, and its
[`cumulativeGasUsed`](#receipt) is inherited from the preceding transaction's receipt, so the value would shift as
later subblocks add transactions. Consumers can obtain the canonical receipt from the sealed block.

_Consumer implication._ Fetch the post-exec transaction's receipt from the sealed block rather than from the
subblock stream. Do not infer from the missing receipt that the transaction failed or was dropped.

## Rationale

**Why a versioned payload.** A `version` byte at the head of the payload lets the schema extend or replace its
trailing fields without re-spending an EIP-2718 type byte.

**Why last in block.** Placing the post-exec transaction at the end of the block gives it a unique, predictable
position and matches the natural "after everything else" semantics of the data it carries.

**Why exclude post-exec transactions from the DA footprint.** A post-exec transaction is constructed only after
the block's standard transactions have executed and its schema-defined payload is known. Including it in the DA
footprint would require block builders to reserve or recompute footprint at finalization and would add a special
late-stage accounting path for both producers and verifiers. Excluding it avoids that complexity at the cost of a
small, bounded underestimate. A block contains at most one post-exec transaction, and the
[version-1 SDM payload](./sdm.md#payload-schema-version-1) contains at most one bounded-size entry per standard
transaction, so the omitted encoded data grows at most linearly with the number of transactions in the block. The
DA footprint is an estimate rather than an exact
compressed-size calculation, and this bounded error does not materially change its purpose as a block-level limit.
