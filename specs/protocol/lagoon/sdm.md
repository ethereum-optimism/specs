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
  - [Refund Policy](#refund-policy)
  - [Block-Level Warming Policy](#block-level-warming-policy)
    - [Warmth States](#warmth-states)
    - [Surcharges](#surcharges)
    - [Refund Amount](#refund-amount)
    - [Known Limitations](#known-limitations)
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
validating the block. Consensus constrains it only through the [validity rules](#validity-rules) and
`refund(i) <= evmGasUsed(i)` (see [Canonical Gas](#canonical-gas)); it does not define, check or re-derive how the
sequencer chose it.

### Refund Policy

A refund policy is the procedure a sequencer uses to choose `gasRefundEntries` when it builds a block.

**A refund policy is not a consensus rule.** Verifiers do not run it. A block whose refunds differ from what a policy
would produce is still valid, provided it satisfies the rules above, and a sequencer can change its policy without a
network upgrade.

The rest of this section specifies the version-1 policy so that sequencer implementations agree and users can predict
their refunds. Its requirements apply to block producers only.

### Block-Level Warming Policy

This subsection specifies a [refund policy](#refund-policy). Nothing in it is a consensus rule, and verifiers do not
check that refunds follow it.

The version-1 policy is **block-level warming**. [EIP-2929] tracks warmth per transaction, so a transaction pays the
cold-access surcharge for state that an earlier transaction in the same block already accessed. Block-level warming
refunds that surcharge, so that such accesses are charged no more than if they had been warm.

[EIP-2929]: https://eips.ethereum.org/EIPS/eip-2929
[EIP-3529]: https://eips.ethereum.org/EIPS/eip-3529
[EIP-7623]: https://eips.ethereum.org/EIPS/eip-7623

#### Warmth States

Seen from the transaction at index `i`, every account or storage slot it accesses is in exactly one of three states:

| State              | Definition                                                                                      | EIP-2929 price |
| ------------------ | ----------------------------------------------------------------------------------------------- | -------------- |
| `cold`             | Not accessed by any earlier transaction in the block, and not yet by `i`.                       | cold           |
| `block-warm`       | Accessed by an earlier transaction in the block, but not yet by `i`, and not transaction-warm.  | cold           |
| `transaction-warm` | Already accessed by `i`, or warm from the start of `i` (listed below).                          | warm           |

State that is warm from the start of a transaction is its sender, its `to` address (or, for a contract creation, the
created address), the precompiles, the block's coinbase, every address and storage slot in its access list, and the
authorities of its [EIP-7702] authorization list.

[EIP-7702]: https://eips.ethereum.org/EIPS/eip-7702

The first access by `i` makes an account or slot transaction-warm for the rest of `i` and block-warm for every later
transaction in the block. Accesses by deposits make state block-warm for later transactions in the same way, and so
does a standard transaction's fee payment to the L1 fee vault, the base fee vault and (post-Isthmus) the operator fee
vault. Those fee-vault payments never earn a refund themselves, and only standard Ethereum transactions receive
refunds.

#### Surcharges

The policy assigns each block-warm access a fixed surcharge, by kind:

| Access        | Operations                                                                                  | Surcharge |
| ------------- | ------------------------------------------------------------------------------------------- | --------- |
| Account       | `BALANCE`, `EXTCODESIZE`, `EXTCODECOPY`, `EXTCODEHASH`, the `SELFDESTRUCT` beneficiary, and the code address of a `CALL`, `CALLCODE`, `DELEGATECALL` or `STATICCALL` | `2500` |
| Storage read  | `SLOAD`                                                                                     | `2000`    |
| Storage write | `SSTORE`                                                                                    | `2100`    |

These are the EIP-2929 cold surcharges (cold price minus warm price), except for a `SELFDESTRUCT` beneficiary:
EIP-2929 charges 2600 for a cold one and nothing for a warm one, and the policy assigns 2500, slightly under-refunding.

Each account and each storage slot counts at most once per transaction. A storage access does not also count as an
access to the account that holds the slot. Accesses to transaction-warm state never have a surcharge.

Let `S(i)` be the sum of the surcharges of all block-warm accesses made by transaction `i`.

#### Refund Amount

`S(i)` is what the block-warm accesses added to the gas that execution spent. It is not always what they added to
`evmGasUsed(i)`: the [EIP-3529] refund cap and the [EIP-7623] calldata floor both depend on the gas spent, so part of
the surcharge can come back through a larger refund, or be absorbed by the floor. The policy refunds only the net
saving:

```text
warmGasUsed(i) = max(spent(i) - S(i) - min(rawRefund(i), (spent(i) - S(i)) / 5), floor(i))
refund(i)      = evmGasUsed(i) - warmGasUsed(i)
```

where:

- `spent(i)` is the gas spent by execution, before any refund.
- `rawRefund(i)` is the transaction's refund counter at the end of execution, before the EIP-3529 cap.
- `floor(i)` is the transaction's EIP-7623 floor.
- `/` is integer division, and `5` is the EIP-3529 maximum refund quotient.

`warmGasUsed(i)` is the gas the transaction would have used had its block-warm accesses been priced as
transaction-warm. With this refund, `canonicalGasUsed(i) = warmGasUsed(i)`, so the policy never charges a transaction
less than that.

When neither the cap nor the floor binds, `refund(i) = S(i)`. When the cap binds both with and without the surcharges,
`refund(i) = S(i) - S(i) / 5` (up to rounding). When the floor binds both ways, `refund(i) = 0`. The sequencer includes
an entry only when `refund(i) > 0`.

#### Known Limitations

These limitations are non-normative and do not affect consensus.

- `warmGasUsed(i)` assumes the transaction would take the same execution path with the surcharges removed. Code that
  depends on the gas remaining (for example through `GAS`, or the 63/64 rule for calls) might behave differently, and
  the policy does not model this.
- An implementation MAY treat an access made inside a frame that later reverts as having happened for the rest of the
  transaction. This can only lower `S(i)`, and so the refund.

## Canonical Gas

[Canonical gas][g-canonical-gas] is the gas a standard Ethereum transaction is accounted for under SDM: the gas the EVM
reports minus the SDM refund applied to it. It is the value written to receipts and summed into the block's
`cumulativeGasUsed` and `gasUsed`, as distinct from `evmGasUsed` (the raw gas the EVM reports before any SDM
adjustment). It is unrelated to the "canonical chain" sense of _canonical_ used elsewhere in these specs.

For each standard Ethereum transaction at index `i`:

- `evmGasUsed(i)` is the gas used reported by the EVM after execution, before any SDM adjustment: the gas spent,
  minus the refund after the [EIP-3529] cap, raised to the [EIP-7623] floor if it is lower. It is the value the
  receipt would report without SDM.
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

- The sequencer executes the block, chooses the non-zero `gasRefundEntries` using its [refund policy](#refund-policy),
  and appends a post-exec transaction if and only if the entry list is non-empty.
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
allocate refunds according to arbitrary policy. The [block-level warming policy](#block-level-warming-policy) is
guidance for producers, not a rule verifiers enforce.

**Cross-block replay.** The post-exec transaction's `blockNumber` field anchors each payload to its containing
block. A payload from one block re-injected into another fails the envelope `blockNumber` check.

**Settlement underflow.** Any settlement debit underflow invalidates the block.
