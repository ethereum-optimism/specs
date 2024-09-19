# L2 Execution Engine

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [`L2ToL1MessagePasser` Storage Root in Header](#l2tol1messagepasser-storage-root-in-header)
  - [Timestamp Activation](#timestamp-activation)
  - [Header Validity Rules](#header-validity-rules)
  - [Header Withdrawals Root](#header-withdrawals-root)
    - [Rationale](#rationale)
    - [Forwards Compatibility Considerations](#forwards-compatibility-considerations)
    - [Client Implementation Considerations](#client-implementation-considerations)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## `L2ToL1MessagePasser` Storage Root in Header

After the Holocene hardfork's activation, the L2 block header's `withdrawalsRoot` field will consist of the 32-byte
[`L2ToL1MessagePasser`][l2-to-l1-mp] account storage root _after_ the block has been executed.

### Timestamp Activation

Holocene, like other network upgrades, is activated at a timestamp.
Changes to the L2 Block execution rules are applied when the `L2 Timestamp >= activation time`.
Changes to the L2 block header are applied when it is considering data from a L1 Block whose timestamp
is greater than or equal to the activation timestamp.

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

Holocene adds 2 new components to the fee calculation: the `gas_premium_fee` and the `constant_fee`. 
New OP stack variants have different resource consumption patterns, and thus require a more 
flexible pricing model.

### Fee Vaults

In addition to the existing 3 fee vaults (The [`SequencerFeeVault`][sequencer-fee-vault]
[`BaseFeeVault`][base-fee-vault], and the [`L1FeeVault`][l1feevault]), we add two
new vaults for these new fees: the [`PremiumFeeVault`](predeploys.md#premiumfeevault) and the 
[`ConstantFeeVault`](predeploys.md#constantfeevault). 

Like the existing vaults, these are hardcoded addresses, pointing at pre-deployed proxy contracts.
The proxies are backed by vault contract deployments, based on `FeeVault`, to route vault funds to L1 securely.

| Vault Name          | Predeploy                                              |
| ------------------- | ------------------------------------------------------ |
| Premium Fee Vault    | [`PremiumFeeVault`](predeploys.md#premiumfeevault)       |
| Constant Fee Vault  | [`ConstantFeeVault`](predeploys.md#constantfeevault)   |


### Premium gas fees (Premium Fee Vault)

The premium gas fee is set as follows:

`gas_premium_fee = gas_used * gas_used_scalar`

Where: 
- `gas_used` is amount of gas used by the transaction.
- `gas_premium_scalar` is a `uint256` scalar set by the chain operator. the same way that `baseFeeScalar` and 
`blobBaseFeeScalar` are set in the [`L1Fee`](../../protocol/exec-engine.md#ecotone-l1-cost-fee-changes-eip-4844-da)
calculation.

### Constant fees (Constant Fee Vault)

The constant gas fee is set as follows: 

`constant_gas_fee = constant_scalar`

Where: 
- `constant_scalar` is a `uint256` scalar set by the chain operator.

#### Configuring scalars: 

`gas_premium_scalar` and `constant_scalar` are loaded in a similar way to the `baseFeeScalar` and 
`blobBaseFeeScalar` used in the [`L1Fee`](../../protocol/exec-engine.md#ecotone-l1-cost-fee-changes-eip-4844-da). 
calculation. In more detail, these scalars can be accessed in two interchangable ways. 

- read from the deposited L1 attributes (`gasPremiumScalar` and `constantScalar`) of the current L2 block
- read from the L1 Block Info contract (`0x4200000000000000000000000000000000000015`)
  - using the respective solidity `uint256`-getter functions (`gasPremiumScalar`, `constantScalar`)
  - using direct storage-reads:
    - Gas premium scalar as big-endian `uint256` in slot `7`
    - Constant scalar as big-endian `uint256` in slot `8`

[sequencer-fee-vault]: ../../protocol/predeploys.md#sequencerfeevault
[base-fee-vault]: ../../protocol/predeploys.md#basefeevault
[l1-fee-vault]: ../../protocol/predeploys.md#l1feevault

