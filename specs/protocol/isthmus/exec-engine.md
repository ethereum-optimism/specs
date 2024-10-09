# L2 Execution Engine

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Timestamp Activation](#timestamp-activation)
- [`L2ToL1MessagePasser` Storage Root in Header](#l2tol1messagepasser-storage-root-in-header)
  - [Header Validity Rules](#header-validity-rules)
  - [Header Withdrawals Root](#header-withdrawals-root)
    - [Rationale](#rationale)
    - [Forwards Compatibility Considerations](#forwards-compatibility-considerations)
    - [Client Implementation Considerations](#client-implementation-considerations)
- [Fees](#fees)
  - [Operator Fee](#operator-fee)
    - [Configuring Parameters](#configuring-parameters)
  - [Fee Vaults](#fee-vaults)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The storage root of the `L2ToL1MessagePasser` is included in the block header's
`withdrawalRoot` field.

## Timestamp Activation

Isthmus, like other network upgrades, is activated at a timestamp.
Changes to the L2 Block execution rules are applied when the `L2 Timestamp >= activation time`.

## `L2ToL1MessagePasser` Storage Root in Header

After Holocene's activation, the L2 block header's `withdrawalsRoot` field will consist of the 32-byte
[`L2ToL1MessagePasser`][l2-to-l1-mp] account storage root _after_ the block has been executed, and _after_ the
insertions and deletions have been applied to the trie. In other words, the storage root should be the same root
that is returned by `eth_getProof` at the given block number.

### Header Validity Rules

Prior to holocene activation, the L2 block header's `withdrawalsRoot` field must be:

- `nil` if Canyon has not been activated.
- `keccak256(rlp(empty_string_code))` if Canyon has been activated.

After Holocene activation, an L2 block header's `withdrawalsRoot` field is valid iff:

1. It is exactly 32 bytes in length.
1. The [`L2ToL1MessagePasser`][l2-to-l1-mp] account storage root, as committed to in the `storageRoot` within the block
   header, is equal to the header's `withdrawalsRoot` field.

### Header Withdrawals Root

| Byte offset | Description                                               |
| ----------- | --------------------------------------------------------- |
| `[0, 32)`   | [`L2ToL1MessagePasser`][l2-to-l1-mp] account storage root |

#### Rationale

Currently, to generate [L2 output roots][output-root] for historical blocks, an archival node is required. This directly
places a burden on users of the system in a post-fault-proofs world, where:

1. A proposer must have an archive node to propose an output root at the safe head.
1. A user that is proving their withdrawal must have an archive node to verify that the output root they are proving
   their withdrawal against is indeed valid and included within the safe chain.

Placing the [`L2ToL1MessagePasser`][l2-to-l1-mp] account storage root in the `withdrawalsRoot` field alleviates this burden
for users and protocol participants alike, allowing them to propose and verify other proposals with lower operating costs.

#### Forwards Compatibility Considerations

As it stands, the `withdrawalsRoot` field is unused within the OP Stack's header consensus format, and will never be
used for other reasons that are currently planned. Setting this value to the account storage root of the withdrawal
directly fits with the OP Stack, and makes use of the existing field in the L1 header consensus format.

#### Client Implementation Considerations

Varous EL clients store historical state of accounts differently. If, as a contrived case, an OP Stack chain did not have
an outbound withdrawal for a long period of time, the node may not have access to the account storage root of the
[`L2ToL1MessagePasser`][l2-to-l1-mp]. In this case, the client would be unable to keep consensus. However, most modern
clients are able to at the very least reconstruct the account storage root at a given block on the fly if it does not
directly store this information.

[l2-to-l1-mp]: ../../protocol/predeploys.md#L2ToL1MessagePasser
[output-root]: ../../glossary.md#l2-output-root

## Fees

New OP stack variants have different resource consumption patterns, and thus require a more flexible
pricing model. To enable more customizable fee structures, Isthmus adds a new component to the fee
calculation: the `operatorFee`, which is parameterized by two scalars: the `operatorFeeScalar`
and the `operatorFeeConstant`.

### Operator Fee

The operator fee, is set as follows:

`operatorFee = (gasUsed * operatorFeeScalar / 1e6) + operatorFeeConstant`

Where:

- `gasUsed` is amount of gas used by the transaction.
- `operatorFeeScalar` is a `uint32` scalar set by the chain operator, scaled by `1e6`.
- `operatorFeeConstant` is a `uint64` scalar set by the chain operator.

#### Configuring Parameters

`operatorFeeScalar` and `operatorFeeConstant` are loaded in a similar way to the `baseFeeScalar` and
`blobBaseFeeScalar` used in the [`L1Fee`](../../protocol/exec-engine.md#ecotone-l1-cost-fee-changes-eip-4844-da).
calculation. In more detail, these paramters can be accessed in two interchangable ways.

- read from the deposited L1 attributes (`operatorFeeScalar` and `operatorFeeConstant`) of the current L2 block
- read from the L1 Block Info contract (`0x4200000000000000000000000000000000000015`)
  - using the respective solidity getter functions (`operatorFeeScalar`, `operatorFeeConstant`)
  - using direct storage-reads:
    - Operator fee scalar as big-endian `uint32` in slot `8` at offset `0`.
    - Operator fee constant as big-endian `uint64` in slot `8` at offset `4`.

### Fee Vaults

These collected fees are sent to a new vault for the `operatorFee`: the [`OperatorFeeVault`](predeploys.md#operatorfeevault).

Like the existing vaults, this is a hardcoded address, pointing at a pre-deployed proxy contract.
The proxy is backed by a vault contract deployment, based on `FeeVault`, to route vault funds to L1 securely.
