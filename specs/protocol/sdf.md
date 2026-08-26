# Sequencer-Defined Fees

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Activation](#activation)
- [Version-1 Commitment](#version-1-commitment)
- [Block Production](#block-production)
- [Block Validation](#block-validation)
- [Deterministic Payload Building](#deterministic-payload-building)
- [Fee Accounting and EVM Semantics](#fee-accounting-and-evm-semantics)
- [Legacy Fee Parameters](#legacy-fee-parameters)
- [Engine API and Derivation](#engine-api-and-derivation)
- [Transaction Pool and Fee RPCs](#transaction-pool-and-fee-rpcs)
- [Security Considerations](#security-considerations)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

Sequencer-Defined Fees (SDF) allows the sequencer to select the `baseFeePerGas` of each L2 block.
The selected value is committed in the block's trailing
[post-execution transaction](./lagoon/post-exec.md) (`0x7D`). Validators recover the selected value from that
commitment and verify that it equals the block header's `baseFeePerGas`.

SDF changes only how the block base fee is selected. Transaction base-fee checks, priority-fee
accounting, the `BASEFEE` opcode, and deposits into the `BaseFeeVault` continue to use the selected
block base fee. L1 data fees and operator fees are unchanged.

## Activation

SDF activates with the [Lagoon network upgrade](./lagoon/overview.md). It uses Lagoon's per-chain
timestamp activation and has no separate feature flag or activation time. A block is at or after
Lagoon exactly when its L2 block timestamp is greater than or equal to the configured Lagoon
timestamp.

Before Lagoon, the block base fee MUST be derived from the parent according to the active EIP-1559
rules, including the Jovian DA-footprint input and minimum-base-fee clamp. A post-exec transaction
MUST NOT appear.

At and after Lagoon, every block MUST contain exactly one post-exec transaction satisfying the
[block-level structural rules](./lagoon/post-exec.md#block-level-structural-rules). The post-exec transaction
MUST be the final transaction in the block and MUST use payload schema version 1.

## Version-1 Commitment

At Lagoon, the version-1 post-exec payload is RLP-encoded as:

```text
[version, blockNumber, selectedBaseFeePerGas, gasRefundEntries]
```

| Field                       | Type                 | Description |
| --------------------------- | -------------------- | ----------- |
| `version`                   | `uint8`              | MUST be `1`. |
| `blockNumber`               | `uint64`             | MUST equal the number of the containing L2 block. |
| `selectedBaseFeePerGas`     | `uint64`             | Base fee selected for the containing block, in wei. |
| `gasRefundEntries`          | `list<SDMGasEntry>`  | Possibly empty [Sequencer-Defined Metering](./lagoon/sdm.md) refund list. |

The payload MUST be one canonical RLP list containing exactly these four elements. Integer fields
MUST use canonical minimal RLP integer encodings and values outside their declared widths MUST be
rejected.

`selectedBaseFeePerGas` MAY be zero. Its value is not constrained by the parent block's base fee,
the EIP-1559 update formula, or the configured Jovian minimum base fee. Its maximum value is the
`uint64` maximum implied by the commitment field type.

The post-exec transaction hash commits to `selectedBaseFeePerGas` because the field is part of the
RLP payload covered by the [transaction hash](./lagoon/post-exec.md#transaction-hash).

## Block Production

For a locally sequenced Lagoon block, the execution engine MUST:

1. Ask its configured producer policy to select one base fee for the payload job.
2. Resolve that value exactly once for the job.
3. Use the resolved value as the EVM block base fee while executing every transaction.
4. Append a version-1 post-exec transaction committing the same value.

Failure of the producer policy MUST abort block production. An implementation MUST NOT silently
substitute another fee after policy failure.

The policy is an operator choice and is not consensus-critical. Changing or reconfiguring the policy
after Lagoon does not require a hardfork. A conforming implementation MAY use the pre-Lagoon Jovian
EIP-1559 result as its policy for backwards-compatible behavior.

A locally sequenced payload-attributes request MUST NOT supply a post-exec transaction. Post-exec is
sequencer-generated validator data and MUST NOT be accepted from the transaction pool or public
transaction-submission RPCs.

## Block Validation

For a Lagoon block, a validator MUST:

1. Decode and validate the trailing version-1 post-exec payload.
2. Read `selectedBaseFeePerGas` before constructing the block's EVM environment.
3. Require the header's `baseFeePerGas` to be present.
4. Require `header.baseFeePerGas == selectedBaseFeePerGas`.
5. Execute all transactions using `selectedBaseFeePerGas` as the EVM block base fee.

The validator MUST NOT invoke the sequencer's producer policy and MUST NOT apply the parent-derived
EIP-1559 base-fee check. A Lagoon block with a missing post-exec transaction, a missing header base
fee, or unequal committed and header fees is invalid.

Before Lagoon, validators continue to enforce the parent-derived EIP-1559 base-fee check and reject
all post-exec transactions.

## Deterministic Payload Building

When the rollup node requests deterministic execution with `noTxPool = true`, an embedded post-exec
transaction is validator data. The execution engine MUST use its committed fee and MUST NOT invoke a
local producer policy.

If deterministic Lagoon payload attributes contain no post-exec transaction, the execution engine
MUST carry forward the parent block's base fee and synthesize the canonical version-1 post-exec
transaction with:

```text
selectedBaseFeePerGas = parent.baseFeePerGas
gasRefundEntries = []
```

The synthesized transaction participates in the transaction and receipt roots exactly like an
embedded post-exec transaction. This fallback is deterministic and therefore reproducible by fault
proof implementations.

## Fee Accounting and EVM Semantics

For every regular transaction in a Lagoon block:

- the normal validity check against the block base fee remains active;
- the effective priority fee is computed relative to the selected block base fee;
- `BASEFEE` returns the selected block base fee;
- the base-fee portion is credited to the `BaseFeeVault`; and
- receipts and fee accounting use the selected block base fee.

SDF does not alter L1 data-fee or operator-fee formulas. SDM settlement, when present, uses the same
selected block base fee as described in [sdm.md](./lagoon/sdm.md#settlement).

## Legacy Fee Parameters

Lagoon does not remove the existing `eip1559Params`, `minBaseFee`, or block-header `extraData`
encodings. Derivation and block production continue to populate them for compatibility.

At and after Lagoon these values are not consensus inputs to base-fee selection or validation. They
MAY be used as inputs to a producer policy, including a compatibility policy that selects the legacy
Jovian result.

## Engine API and Derivation

SDF does not add a field to `PayloadAttributesV3`, change an Engine API method version, or modify the
singular or span batch formats. The selected fee is transported by the existing transaction list as
the trailing post-exec transaction.

The batcher includes the post-exec transaction in L2 batch data like any other L2 transaction.
Derivation passes the encoded transaction through to deterministic payload attributes unchanged.
Unsafe/safe consolidation therefore compares payloads that include the selected-fee commitment.

## Transaction Pool and Fee RPCs

On a producer node, the policy's provisional next-block quote SHOULD be used for transaction-pool
base-fee classification, pending execution environments, gas estimation, transaction filling,
`eth_gasPrice`, base-fee suggestions, and the final next-block entry returned by `eth_feeHistory`.
The actual fee is resolved again and held immutable when a payload job starts.

A replica cannot in general reproduce a private sequencer policy before receiving a block. It SHOULD
proxy fee suggestions to the sequencer or use a documented conservative fallback, such as the latest
observed base fee.

## Security Considerations

**Commitment equality.** The selected fee is authenticated by the block because it is committed by
both the header and the transaction root. Validators require those two commitments to agree.

**Policy isolation.** Producer policy code is never a validator input. A policy failure can stop
sequencing but cannot make validators compute a different fee.

**Immutable job selection.** Resolving the selected fee once prevents a runtime policy update from
changing the EVM environment and post-exec commitment to different values within one payload job.
