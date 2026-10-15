# Isthmus L2 Chain Derivation Changes

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Span Batch Updates](#span-batch-updates)
  - [Activation](#activation)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

The network upgrade transactions are described in [Deposits](./deposits.md).

# Span Batch Updates

[Span batches](../delta/span-batches.md) are a span of consecutive L2 blocks than are batched submitted.

Span batches contain the L1 transactions and transaction types that are posted containing the span of L2 blocks.
Since [EIP-7702] introduces a new transaction type, the Span Batch must be updated to support the [EIP-7702]
transaction.

This corresponds with a new RLP-encoding of the `tx_datas` list as specified in
[the Delta span batch spec](../delta/span-batches.md), adding a new transaction type:

Transaction type `4` ([EIP-7702] `SetCode`):
`0x04 ++ rlp_encode(value, max_priority_fee_per_gas, max_fee_per_gas, data, access_list, authorization_list)`

The [EIP-7702] transaction extends [EIP-1559] to include a new `authorization_list` field.
`authorization_list` is an RLP-encoded list of authorization tuples.
The [EIP-7702] transaction format is as follows.

- `value`: The transaction value as a `u256`.
- `max_priority_fee_per_gas`: The maximum priority fee per gas allowed as a `u256`.
- `max_fee_per_gas`: The maximum fee per gas as a `u256`.
- `data`: The transaction data bytes.
- `access_list`: The [EIP-2930] access list.
- `authorization_list`: The [EIP-7702] signed authorization list.

## Activation

Singular batches with transactions of type `4` must only be accepted if Isthmus is active at the
timestamp of the batch. If a singular batch contains a transaction of type `4` before Isthmus is
active, this batch must be _dropped_. Note that if Holocene is active, this will also
lead to the remaining span batch, and channel that contained it, to get dropped.

Also note that this check must happen at the level of individual batches that are derived from span
batches, not to span batches as a whole. In particular, it is allowed for a span batch to span the
Isthmus activation timestamp and contain SetCode transactions in singular batches that have a
timestamp at or after the Isthmus activation time, even if the timestamp of the span batch is before
the Isthmus activation time.

[EIP-1559]: https://eips.ethereum.org/EIPS/eip-1559
[EIP-7702]: https://eips.ethereum.org/EIPS/eip-7702
[EIP-2930]: https://eips.ethereum.org/EIPS/eip-2930
