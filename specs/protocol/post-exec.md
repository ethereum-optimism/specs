# Post-Execution Transactions

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [The Post-Execution Transaction Type](#the-post-execution-transaction-type)
  - [Encoding](#encoding)
  - [Transaction Hash](#transaction-hash)
  - [Transaction Field Projections](#transaction-field-projections)
  - [Signer and Signature](#signer-and-signature)
  - [Mempool and Propagation](#mempool-and-propagation)
- [Post-Exec Payload Envelope](#post-exec-payload-envelope)
  - [Schema Version](#schema-version)
  - [Block Number](#block-number)
  - [Defined Schema Versions](#defined-schema-versions)
- [Block-Level Structural Rules](#block-level-structural-rules)
- [Receipt](#receipt)
- [Derivation](#derivation)
- [Rationale](#rationale)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

<!-- All glossary references in this file. -->

[g-transaction-type]: ../glossary.md#transaction-type
[g-sequencer]: ../glossary.md#sequencer
[g-post-exec-payload]: ../glossary.md#post-exec-payload
[g-post-exec-schema-version]: ../glossary.md#post-exec-payload-schema-version
[g-sdm]: ../glossary.md#sequencer-defined-metering

## Overview

Post-execution transactions are an [EIP-2718] [transaction type][g-transaction-type] that allows a block to carry
sequencer-provided consensus data. Unlike user-submitted transactions, a post-exec transaction is synthesized by the
[sequencer][g-sequencer] and appended to the block as its final transaction. A verifier applies the data from the
post-execution transaction as part of the block's state transition.

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
[deposited transactions](./deposits.md#the-deposited-transaction-type), and `0x7F` is left unused in case it is
later assigned to a variable-length encoding scheme.

### Encoding

The EIP-2718 encoding of a post-exec transaction is:

```text
0x7D || rlp_encoded_payload
```

where `rlp_encoded_payload` is the RLP encoding of the [post-exec payload][post-exec-payload-envelope] as a list,
and `||` denotes byte concatenation. The transaction encoding contains no outer list around the payload.

### Transaction Hash

The transaction hash of a post-exec transaction is:

```text
keccak256(0x7D || rlp_encoded_payload)
```

The hash is computed over the full EIP-2718 encoding, so the type byte is included in the hash preimage. The
payload's [block number](#block-number) is what distinguishes otherwise identical payloads in different blocks.

### Transaction Field Projections

Many of the fields a transaction is normally expected to expose are inapplicable to a post-exec transaction. When a
post-exec transaction is observed through a generic transaction interface, its fields project as follows:

| Field                  | Value                                                       |
| ---------------------- | ----------------------------------------------------------- |
| `chainId`              | absent (`null`)                                             |
| `nonce`                | `0`                                                         |
| `gasLimit` / `gas`     | `0`                                                         |
| `gasPrice`             | `0`                                                         |
| `maxFeePerGas`         | `0`                                                         |
| `maxPriorityFeePerGas` | `0`                                                         |
| `maxFeePerBlobGas`     | absent                                                      |
| `to`                   | `0x0000000000000000000000000000000000000000` (zero address) |
| `value`                | `0`                                                         |
| `accessList`           | absent                                                      |
| `authorizationList`    | absent                                                      |
| `blobVersionedHashes`  | absent                                                      |
| `input`                | the RLP-encoded payload bytes                               |

A post-exec transaction never charges fees, never debits or credits an account by virtue of being a transaction,
and consumes no gas from the block gas pool. Any side effects on account balances are defined by the active schema,
not by this envelope.

### Signer and Signature

A post-exec transaction has no signer. It is authorized by the protocol — by virtue of being synthesized by the
sequencer at a position that satisfies the [block-level structural rules](#block-level-structural-rules) — rather
than by a signature.

For compatibility with tooling that expects an ECDSA signature on every typed transaction:

- The recovered sender address is the zero address `0x0000000000000000000000000000000000000000`.
- The signature triple `(v, r, s)` is reported as `(0, 0, 0)` in API responses.

The signature triple is not part of the EIP-2718 encoding of a post-exec transaction and is not included in the
transaction hash preimage.

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

`version` is the [post-exec payload schema version][g-post-exec-schema-version]. When the payload schema needs to
gain or change fields, a new version number is assigned and the new layout is documented as a
[defined schema version](#defined-schema-versions).

### Block Number

`blockNumber` anchors the payload to the L2 block number of the containing block. The anchoring serves two
purposes:

1. It guarantees that two otherwise identical payloads produced for different blocks have distinct
   [transaction hashes](#transaction-hash).
2. It detects misordered or replayed payloads at decode time, before any schema-specific validation runs.

The normative rule that `blockNumber` equals the containing block's number is stated in
[Block-Level Structural Rules](#block-level-structural-rules).

### Defined Schema Versions

| `version` | Schema                                 | Status       |
| --------- | -------------------------------------- | ------------ |
| `1`       | [Sequencer-Defined Metering](./sdm.md) | Experimental |

No other schema versions are currently defined.

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

## Receipt

A post-exec transaction emits a receipt with type byte `0x7D`. The RLP-encoded consensus fields of the receipt are
identical to those of an EIP-1559 receipt:

- `postStateOrStatus` ([EIP-658])
- `cumulativeGasUsed`
- `logsBloom`
- `logs`

A post-exec transaction is constructed by the protocol, executes synthetically, emits no logs, and consumes no gas
pool, so:

- `postStateOrStatus` MUST encode success ([EIP-658] status `1`).
- `logs` MUST be empty.
- `logsBloom` MUST be the all-zero bloom filter.
- `cumulativeGasUsed` MUST equal the `cumulativeGasUsed` of the immediately preceding transaction's receipt. (In
  any L2 block the post-exec transaction has at least one preceding transaction — the L1 attributes deposit — so
  there is always a previous receipt to inherit from.)

The post-exec receipt participates in the block's receipts trie like any other receipt. Schema-specific data is
not surfaced through the post-exec receipt itself; it is surfaced through extensions to the receipts of the user
transactions whose execution the schema describes, as defined by the active schema.

[EIP-658]: https://eips.ethereum.org/EIPS/eip-658

## Derivation

Post-exec transactions are L2-only and are not derived from L1. They are constructed by the sequencer during block
production and are included in the block payload that is submitted to the data availability layer alongside the
user transactions and any deposited transactions.

The L1 batcher transaction format is unaffected: post-exec transactions appear inside L2 blocks, never as L1
batcher transactions. The future-tx-type decoding range described in
[derivation.md](./derivation.md#on-future-proof-transaction-log-derivation) governs L1 receipts only and is
unchanged.

## Rationale

**Why a versioned payload.** A `version` byte at the head of the payload lets the schema extend or replace its
trailing fields without re-spending an EIP-2718 type byte.

**Why last in block.** Placing the post-exec transaction at the end of the block gives it a unique, predictable
position and matches the natural "after everything else" semantics of the data it carries.
