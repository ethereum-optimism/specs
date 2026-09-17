# Lagoon L2 Chain Derivation Changes

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Span Batch Updates](#span-batch-updates)
  - [Transaction Data](#transaction-data)
  - [Transposed Envelope Fields](#transposed-envelope-fields)
    - [`contract_creation_bits`](#contract_creation_bits)
    - [Unused signature and gas accounting slots](#unused-signature-and-gas-accounting-slots)
  - [Reconstruction](#reconstruction)
  - [Batch Acceptance](#batch-acceptance)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

<!-- All glossary references in this file. -->

[g-sequencer]: ../../glossary.md#sequencer
[g-deposited]: ../../glossary.md#deposited-transaction
[g-post-exec-payload]: ../../glossary.md#post-exec-payload

# Span Batch Updates

[Span batches](../delta/span-batches.md) encode a span of consecutive L2 blocks for submission to the data
availability layer.

The [Lagoon network upgrade](./overview.md) introduces the [post-execution transaction](./post-exec.md), an
[EIP-2718] typed transaction with type byte `0x7D`. Unlike a [deposited transaction][g-deposited], which is
derived from L1 and is never present in batch data, a post-exec transaction is produced by the
[sequencer][g-sequencer] and travels to verifiers inside the L2 block body — through the L1 batch as well as the
unsafe p2p payload. A span batch covering a block that contains a post-exec transaction therefore has to transpose
that transaction into the span batch `txs` structure like any other.

A post-exec transaction is unlike every previously batched type: it carries only an opaque
[post-exec payload][g-post-exec-payload], with no nonce, gas limit, recipient or signature. Most of the slots the
span batch format reserves per transaction have no natural value for it. This section specifies all of them.

Nothing outside the `txs` structure changes. In particular, a post-exec transaction is an ordinary member of its
block's transaction list, so it is counted in that block's `block_tx_counts` entry and in the
`MAX_SPAN_BATCH_ELEMENT_COUNT` total, exactly like a user transaction. Because a post-exec transaction is
[the final transaction of its block](./post-exec.md#block-level-structural-rules), it occupies the last index of
that block's slice of the span.

That position is an assumption this encoding inherits, not one it enforces. The span batch format transposes and
reconstructs a transaction list and has no notion of block validity, so it can faithfully encode a block that
violates the [block-level structural rules](./post-exec.md#block-level-structural-rules) — one carrying two `0x7D`
transactions, say, or one where the `0x7D` transaction is not last. Such a batch is well formed *as a batch*; the
violation is caught where the rules are stated, when the derived block is validated, and under
[Steady Block Derivation](../holocene/derivation.md#engine-queue) the invalid payload is then replaced by a
deposit-only one and the remaining span batch and its channel are dropped. Encoders are likewise not required to
check these rules: a batcher only encodes blocks that have already been accepted.

## Transaction Data

This corresponds with a new encoding of the `tx_datas` list as specified in
[the Delta span batch spec](../delta/span-batches.md#span-batch-format), adding a new transaction type:

Transaction type `0x7D` ([post-exec](./post-exec.md)): `0x7D ++ rlp_encoded_payload`

where `rlp_encoded_payload` is the RLP encoding of the [post-exec payload][g-post-exec-payload] as a list, exactly
as defined by the transaction's [EIP-2718 encoding](./post-exec.md#encoding). As for every other `tx_datas`
element, the bytes following the type byte MUST be a single RLP list.

That framing check is where batch decoding's interest in the payload ends. A decoder MUST NOT inspect the payload's
`version` byte or validate it against a [schema](./post-exec.md#defined-schema-versions) while decoding a batch:
below the outer RLP list the element is opaque bytes, reproduced verbatim into the reconstructed transaction.
Payload validity is a [block-level](./post-exec.md#block-level-structural-rules) concern and is settled when the
derived block is validated.

For every other transaction type the `tx_datas` element is a *reduced* encoding: fields the span batch format
stores in dedicated slots (`nonce`, `gasLimit`, `to`, and the signature), along with the chain ID, which is
recovered from the rollup config rather than stored at all, are omitted from the element, and the remaining fields
are re-encoded as a shorter RLP list. A post-exec transaction has none of those fields, so nothing is omitted and
nothing is re-encoded: its `tx_datas` element is byte for byte the transaction's EIP-2718 encoding as it appears in
the block body.

## Transposed Envelope Fields

A post-exec transaction has no envelope fields to transpose. Its slots in the span batch `txs` structure take the
following values:

| Slot                     | Value for a `0x7D` transaction                       |
| ------------------------ | ---------------------------------------------------- |
| `contract_creation_bits` | `1`                                                  |
| `tx_tos`                 | no entry — the transaction consumes none             |
| `y_parity_bits`          | `0`                                                  |
| `tx_sigs`                | `r = 0`, `s = 0`                                     |
| `tx_nonces`              | `0`                                                  |
| `tx_gases`               | `0`                                                  |
| `protected_bits`         | no entry — the bitlist covers legacy transactions only |

### `contract_creation_bits`

The bit for a post-exec transaction MUST be `1`.

A post-exec transaction is not a contract creation, so this deserves a word. What the bit governs is whether the
transaction consumes an entry from `tx_tos`: a `0` bit consumes the next address, a `1` bit consumes none. For
every transaction type defined before Lagoon, "is a contract creation" and "has no `to` field" are the same
condition, which is why the [Delta definition](../delta/span-batches.md#span-batch-format) states the former. A
post-exec transaction is the first type for which they differ. The operative reading is the latter: the bit is `1`
whenever the transaction has no recipient, so that `tx_tos` stays exactly as long as the number of transactions
that have one.

A decoder MUST reject a batch in which the bit is `0` for a post-exec transaction. Such a batch is invalid and is
dropped, exactly as one whose `tx_datas` element carries an unusable transaction type is.

### Unused signature and gas accounting slots

`y_parity_bits`, `tx_sigs`, `tx_nonces` and `tx_gases` are positional: every transaction in the span occupies one
slot in each, whether or not the corresponding field exists. A post-exec transaction has no signature, nonce or gas
limit, so:

- A batcher MUST write zero into each of these slots for a post-exec transaction, as given in the table above.
- A decoder MUST verify that each of them is zero, and MUST reject the span batch if any of them is not.

The rejection is at span batch granularity: these slots are positional across the whole span, so a violation
invalidates the span batch rather than the single block whose transaction carries it. How far that invalidity
then propagates — whether the remaining channel is discarded with it — is a property of malformed span batches in
general, not something particular to post-exec transactions, and is not settled here.

Decoding is deliberately no more permissive than encoding. The values in these slots cannot reach the reconstructed
transaction, so tolerating them would cost nothing in the short term — but it would make a span batch's encoding
malleable: the same sequence of L2 blocks would have unboundedly many valid encodings, differing in bytes that a
batcher chooses freely. `tx_sigs` alone reserves 64 bytes per transaction that no post-exec transaction uses. A
strict decoder keeps the encoding canonical, denies a batcher that space as a channel for arbitrary data, and
leaves nothing that a later upgrade would have to tighten retroactively.

This strictness is available precisely because `0x7D` is new. A block before the Lagoon activation timestamp
[MUST NOT contain a `0x7D` transaction](./post-exec.md#overview), so no batch already posted carries one, and no
rule stated here reinterprets any of them.

## Reconstruction

When a span batch is decoded, the full transaction reconstructed for a post-exec element is its `tx_datas` element
verbatim:

```text
0x7D ++ rlp_encoded_payload
```

A decoder MUST NOT fold `tx_nonces`, `tx_gases`, `tx_tos` or `tx_sigs` into the reconstructed transaction; there
are no fields for them to occupy. The `tx_tos` cursor is not advanced, because the transaction's
`contract_creation_bits` bit is `1`.

The reconstructed bytes are therefore identical to the transaction's encoding in the block body. This is what makes
the overlap check between a batch and an already-safe block — comparing the batch's reconstructed transactions
against the safe block's transactions — well defined for blocks containing a post-exec transaction: the comparison
turns on the `tx_datas` element alone, and every other slot is both fixed by the rules above and discarded here.

## Batch Acceptance

This document specifies only how a post-exec transaction is *encoded* within a span batch, because that is the only
batch format for which the question arises. A [singular batch](../derivation.md#batch-format) needs no Lagoon
amendment: its `transaction_list` holds each transaction's EIP-2718 encoding verbatim, so a post-exec transaction
appears there as `0x7D ++ rlp_encoded_payload` like any other typed transaction, with nothing transposed and no
slots to fill. Only the span batch format, which splits each transaction across per-field slots, needed the rules
above.

Whether a batch is permitted to contain a post-exec transaction at all is a separate, batch-level question, and one
that applies to both batch formats. It is governed by the `batch.transactions` drop rules in
[Batch Queue](../derivation.md#batch-queue). Those rules drop any transaction of a future type greater than `2`,
with the type `4` exception added by [Isthmus](../isthmus/derivation.md#activation); they require a corresponding
Lagoon amendment for `0x7D`. Until that amendment lands, the Batch Queue rules and this document disagree: the
former forbids the transaction this one gives an encoding for.

That amendment also owes an activation granularity, as [Isthmus](../isthmus/derivation.md#activation) states for
type `4`. Both implementations already check Lagoon activation against the timestamp of each individual block
derived from the span, not against the span batch as a whole, so a span batch may legally straddle the Lagoon
activation and carry post-exec transactions only in the blocks at or after it. That rule qualifies the acceptance
rule and belongs with it rather than here.

[EIP-2718]: https://eips.ethereum.org/EIPS/eip-2718
