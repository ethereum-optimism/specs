# Sequencer-Defined Metering

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Activation](#activation)
- [Payload Schema (Version 1)](#payload-schema-version-1)
  - [`SDMGasEntry`](#sdmgasentry)
  - [Validity Rules](#validity-rules)
- [Transaction Classification](#transaction-classification)
- [Gas Refund Semantics](#gas-refund-semantics)
- [Canonical Gas](#canonical-gas)
- [Settlement](#settlement)
  - [Per-Recipient Deltas](#per-recipient-deltas)
  - [Application Rules](#application-rules)
- [Producer and Verifier](#producer-and-verifier)
- [Receipt Extension](#receipt-extension)
- [Backwards Compatibility](#backwards-compatibility)
- [Security Considerations](#security-considerations)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

<!-- All glossary references in this file. -->

[g-deposited]: ../../glossary.md#deposited-transaction
[g-post-exec-tx]: ../../glossary.md#post-execution-transaction
[g-post-exec-payload]: ../../glossary.md#post-exec-payload
[g-post-exec-schema-version]: ../../glossary.md#post-exec-payload-schema-version
[g-canonical-gas]: ../../glossary.md#canonical-gas

## Overview

Sequencer-Defined Metering (SDM) is the version-1 [post-exec payload schema][g-post-exec-schema-version]. It lets
the sequencer attach per-transaction gas refunds to a block. Each refund lowers the gas a transaction is charged
for and rebalances the fees it already paid.

Refund data is carried by a [post-exec transaction][g-post-exec-tx] (`0x7D`) appended to the block as its final
transaction. The post-exec envelope and structural rules are specified in [post-exec.md](./post-exec.md); this
document specifies the version-1 payload and how clients apply the included refunds.

[EIP-1559]: https://eips.ethereum.org/EIPS/eip-1559

## Activation

SDM activates with the [Lagoon network upgrade](./overview.md) and is gated by the Lagoon activation timestamp.
When SDM is active for a block, the block MAY contain a post-exec transaction; when SDM is inactive, the block MUST
NOT contain a post-exec transaction (see
[post-exec.md § Block-Level Structural Rules](./post-exec.md#block-level-structural-rules)).

Before the Lagoon activation timestamp, every block MUST be produced and validated with SDM inactive, identically
to a chain that has never specified SDM.

## Payload Schema (Version 1)

When `version = 1`, the [post-exec payload][g-post-exec-payload] is RLP-encoded as:

```text
[version, blockNumber, gasRefundEntries]
```

| Field              | Type                | Description                                                                                                   |
| ------------------ | ------------------- | ------------------------------------------------------------------------------------------------------------- |
| `version`          | `uint8`             | MUST be `1`.                                                                                                  |
| `blockNumber`      | `uint64`            | The L2 block number containing this payload (see [post-exec.md § Block Number](./post-exec.md#block-number)). |
| `gasRefundEntries` | `list<SDMGasEntry>` | Non-zero per-transaction gas refunds.                                                                         |

### `SDMGasEntry`

Each entry in `gasRefundEntries` is an RLP list of two fields:

| Field       | Type     | Description                                      |
| ----------- | -------- | ------------------------------------------------ |
| `index`     | `uint64` | Transaction index within the block (zero-based). |
| `gasRefund` | `uint64` | Gas refund for the transaction at `index`.       |

### Validity Rules

A version-1 payload is invalid if any of the following hold:

1. `gasRefundEntries` is empty.
2. Any `SDMGasEntry` has `gasRefund == 0`.
3. Entries are not ordered by strictly increasing `index`.
4. Any entry's `index` does not refer to a standard Ethereum transaction in the block.

The envelope-level rules in [post-exec.md § Block-Level Structural Rules](./post-exec.md#block-level-structural-rules)
apply in addition to the rules above. As long as SDM is the only active payload schema: if the sequencer assigns
no gas refunds, the block has no post-exec transaction.

## Transaction Classification

Every transaction in the block is classified as exactly one of:

| Kind       | Source                                                | May have refund? |
| ---------- | ----------------------------------------------------- | ---------------- |
|            | A standard Ethereum transaction.                      | Yes              |
| `Deposit`  | A [deposited transaction][g-deposited] (type `0x7E`). | No               |
| `PostExec` | The post-exec transaction (type `0x7D`).              | No               |

Deposits buy gas on L1 and have no L2-side gas-price to refund. The post-exec transaction carries SDM data only;
it charges no fees, consumes no gas and is not executed as code.

## Gas Refund Semantics

For each standard Ethereum transaction at index `i`, define `refund(i)` as:

- the `gasRefund` value in the payload entry whose `index == i`, if one exists; otherwise
- `0`.

The refund value is sequencer-defined block data. Clients use the included value directly when executing and
validating the block.

## Canonical Gas

[Canonical gas][g-canonical-gas] is the gas a standard Ethereum transaction is accounted for under SDM: the gas the EVM
reports minus the SDM refund applied to it. It is the value written to receipts and summed into the block's
`cumulativeGasUsed` and `gasUsed`, as distinct from `evmGasUsed` (the raw gas the EVM reports before any SDM
adjustment). It is unrelated to the "canonical chain" sense of _canonical_ used elsewhere in these specs.

For each standard Ethereum transaction at index `i`:

- `evmGasUsed(i)` is the gas used reported by the EVM after execution, before any SDM adjustment.
- `refund(i)` MUST be less than or equal to `evmGasUsed(i)`.
- `canonicalGasUsed(i) = evmGasUsed(i) - refund(i)`.

The receipt of transaction `i` reports `canonicalGasUsed(i)` as its gas-used field. The block's `cumulativeGasUsed`
and `gasUsed` are computed using `canonicalGasUsed` for standard Ethereum transactions and `evmGasUsed` for `Deposit`
transactions. The post-exec transaction contributes zero gas (see [post-exec.md § Receipt](./post-exec.md#receipt)).

## Settlement

Because the EVM initially charges fees using `evmGasUsed(i)`, SDM applies a balance settlement for every standard
Ethereum transaction with `refund(i) > 0`.

### Per-Recipient Deltas

Let `r = refund(i)`, `p` be the transaction's [EIP-1559] effective gas price, `b` be the block's base fee, and let
`operatorFee(g)` be the operator fee charged by the L1Block precompile for gas usage `g` at the active spec
(post-Isthmus).

| Recipient                         | Adjustment | Amount                                                              |
| --------------------------------- | ---------- | ------------------------------------------------------------------- |
| Sender (`tx.from`)                | credit     | `r * p + (operatorFee(evmGasUsed) - operatorFee(canonicalGasUsed))` |
| Block beneficiary                 | debit      | `r * (p - b)`                                                       |
| Base fee vault                    | debit      | `r * b`                                                             |
| Operator fee vault (post-Isthmus) | debit      | `operatorFee(evmGasUsed) - operatorFee(canonicalGasUsed)`           |

The sender credit equals the sum of the recipient debits: `r * (p - b) + r * b = r * p`. This identity relies on
`p >= b`, which holds for every transaction that can be included: an [EIP-1559] transaction has
`p = b + min(maxPriorityFeePerGas, maxFeePerGas - b) >= b`, and a legacy transaction must have `gasPrice >= b` to
be included. Hence `p - b >= 0`, so the beneficiary debit is never negative; at the boundary `p = b` (e.g. a legacy
transaction whose gas price equals the base fee) the priority tip — and therefore the beneficiary debit — is zero.
The L1 fee vault is not adjusted: L1 cost is independent of L2 gas usage.

### Application Rules

Settlement is applied after the transaction's EVM frame finishes and before the transaction state delta is
committed. It is atomic with the transaction and does not produce a separate receipt.

If any debit would underflow, the block is invalid. For any payload that respects `refund(i) <= evmGasUsed(i)`,
this cannot occur, because each recipient was just paid the corresponding amount by the EVM in the same
transaction; an underflow therefore indicates a malformed or adversarial payload rather than a reachable state of
honest execution.

## Producer and Verifier

Under SDM:

- The sequencer executes the block, chooses the non-zero `gasRefundEntries`, and appends a post-exec transaction if
  and only if the entry list is non-empty.
- A verifier enforces the post-exec envelope rules and the SDM [validity rules](#validity-rules), then applies the
  refunds from the payload when computing canonical gas, settlement, receipts, and block gas usage.

## Receipt Extension

The post-exec transaction's own receipt carries no SDM-specific fields (see
[post-exec.md § Receipt](./post-exec.md#receipt)).

The JSON-RPC receipts returned for standard Ethereum transactions are extended with a single additional field:

| Field         | Type                            | Description                                                                                                                     |
| ------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `opGasRefund` | `Quantity` (`uint64`) or `null` | The SDM gas refund credited to the transaction, or `null` when SDM was inactive for the block or the transaction had no refund. |

The value is sourced from the embedded post-exec payload's `gasRefundEntries` for the transaction's `index`.
`opGasRefund` is not part of the receipt's RLP encoding and is not committed to the receipts trie. Because it is
an additional JSON-RPC field outside the consensus receipt, existing receipt tooling that ignores unknown fields
(e.g. `cast receipt`) is unaffected; only consumers that opt in observe it.

## Backwards Compatibility

Before the Lagoon activation timestamp, blocks are produced and validated identically to a chain that has never
specified SDM: no post-exec transactions appear, no canonical-gas adjustment is performed, and no settlement runs.

From the Lagoon activation timestamp, two changes become observable:

- A `0x7D` transaction may appear at the end of any block produced after activation, exposed through the same
  transaction-list interfaces used today.
- The receipts of standard Ethereum transactions in such blocks gain the `opGasRefund` field; clients that ignore unknown
  fields are unaffected.

Mempool and transaction-pool interfaces are unchanged: post-exec transactions are not user-submittable and do not
propagate over the public transaction-gossip protocol.

## Security Considerations

**Sequencer-defined amounts.** Refund amounts are part of the sequencer's block data. The only consensus-defined
constraints are on their encoding, their target transaction (standard Ethereum transactions only), and the application bounds
(`refund(i) <= evmGasUsed(i)` and no settlement underflow); otherwise the sequencer has complete freedom to
allocate refunds according to arbitrary policy.

**Cross-block replay.** The post-exec transaction's `blockNumber` field anchors each payload to its containing
block. A payload from one block re-injected into another fails the envelope `blockNumber` check.

**Settlement underflow.** Any settlement debit underflow invalidates the block.
