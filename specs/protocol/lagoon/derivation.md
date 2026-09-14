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

## Transaction Data

This corresponds with a new encoding of the `tx_datas` list as specified in
[the Delta span batch spec](../delta/span-batches.md#span-batch-format), adding a new transaction type:

Transaction type `0x7D` ([post-exec](./post-exec.md)): `0x7D ++ rlp_encoded_payload`

where `rlp_encoded_payload` is the RLP encoding of the [post-exec payload][g-post-exec-payload] as a list, exactly
as defined by the transaction's [EIP-2718 encoding](./post-exec.md#encoding). As for every other `tx_datas`
element, the bytes following the type byte MUST be a single RLP list.

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

A decoder MUST NOT reject a batch whose bit is `0` for a post-exec transaction. It consumes the next `tx_tos` entry
as it would for any `0` bit, and discards it: a post-exec transaction has no recipient field for the address to
occupy. As with the slots below, the bit cannot change the transaction the decoder reconstructs.

### Unused signature and gas accounting slots

`y_parity_bits`, `tx_sigs`, `tx_nonces` and `tx_gases` are positional: every transaction in the span occupies one
slot in each, whether or not the corresponding field exists. A post-exec transaction has no signature, nonce or gas
limit, so:

- A batcher MUST write zero into each of these slots for a post-exec transaction, as given in the table above. This
  makes the span batch encoding of a given sequence of L2 blocks unique.
- A decoder MUST ignore the values in these slots for a post-exec transaction, and MUST NOT reject a batch because
  of the values they carry. Reconstruction discards them (see below), so a batch carrying non-zero values in them
  derives exactly the same L2 blocks as one carrying zeros. This constrains the values only: a slot that cannot be
  decoded at all — a `uvarint` too large to represent, say — still invalidates the batch, as it does for every
  other transaction type.

The asymmetry is deliberate. Requiring the encoder to zero these slots keeps the encoding canonical; requiring the
decoder to tolerate anything keeps the drop decision independent of fields that provably cannot affect the derived
blocks.

## Reconstruction

When a span batch is decoded, the full transaction reconstructed for a post-exec element is its `tx_datas` element
verbatim:

```text
0x7D ++ rlp_encoded_payload
```

A decoder MUST NOT fold `tx_nonces`, `tx_gases`, `tx_tos` or `tx_sigs` into the reconstructed transaction; there
are no fields for them to occupy. The `tx_tos` cursor is not advanced, because the transaction's
`contract_creation_bits` bit is `1`.

The reconstructed bytes are therefore identical to the transaction's encoding in the block body. This is
what makes the overlap check between a batch and an already-safe block — comparing the batch's reconstructed
transactions against the safe block's transactions — deterministic for blocks containing a post-exec transaction,
regardless of what a batcher wrote into the unused slots.

## Batch Acceptance

This section specifies only how a post-exec transaction is *encoded* within a span batch. Whether a batch is
permitted to contain one at all is a separate, batch-level question — it applies equally to singular batches, where
no transposition takes place — and is governed by the `batch.transactions` drop rules in
[Batch Queue](../derivation.md#batch-queue). Those rules drop any transaction of a future type greater than `2`,
with the type `4` exception added by [Isthmus](../isthmus/derivation.md#activation); they require a corresponding
Lagoon amendment for `0x7D`.

[EIP-2718]: https://eips.ethereum.org/EIPS/eip-2718
