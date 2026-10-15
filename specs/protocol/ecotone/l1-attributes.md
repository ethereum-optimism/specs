# Ecotone L1 Attributes

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [L1 Attributes Predeployed Contract](#l1-attributes-predeployed-contract)
  - [Ecotone L1Block upgrade](#ecotone-l1block-upgrade)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The L1 attributes calldata is described in [Deposits](./deposits.md).

## L1 Attributes Predeployed Contract

[sys-config]: ../system-config.md

The L1 Attributes predeploy stores the following values:

- L1 block attributes:
  - `number` (`uint64`)
  - `timestamp` (`uint64`)
  - `basefee` (`uint256`)
  - `hash` (`bytes32`)
  - `blobBaseFee` (`uint256`)
- `sequenceNumber` (`uint64`): This equals the L2 block number relative to the start of the epoch,
  i.e. the L2 block distance to the L2 block height that the L1 attributes last changed,
  and reset to 0 at the start of a new epoch.
- System configurables tied to the L1 block, see [System configuration specification][sys-config]:
  - `batcherHash` (`bytes32`): A versioned commitment to the batch-submitter(s) currently operating.
  - `baseFeeScalar` (`uint32`): system configurable to scale the `basefee` in the Ecotone l1 cost computation
  - `blobBasefeeScalar` (`uint32`): system configurable to scale the `blobBaseFee` in the Ecotone l1 cost computation

The `overhead` and `scalar` values can continue to be accessed after the Ecotone activation block,
but no longer have any effect on system operation. These fields were also known as the `l1FeeOverhead`
and the `l1FeeScalar`.

After running `pnpm build` in the `packages/contracts-bedrock` directory, the bytecode to add to
the genesis file will be located in the `deployedBytecode` field of the build artifacts file at
`/packages/contracts-bedrock/forge-artifacts/L1Block.sol/L1Block.json`.

### Ecotone L1Block upgrade

The L1 Attributes Predeployed contract, `L1Block.sol`, is upgraded as part of the Ecotone upgrade.
The version is incremented to `1.2.0`, one new storage slot is introduced, and one existing slot
begins to store additional data:

- `blobBaseFee` (`uint256`): The L1 blob base fee.
- `blobBaseFeeScalar` (`uint32`): The scalar value applied to the L1 blob base fee portion of the L1 cost.
- `baseFeeScalar` (`uint32`): The scalar value applied to the L1 base fee portion of the L1 cost.

The function called by the L1 attributes transaction depends on the network upgrade:

- Before the Ecotone activation:
  - `setL1BlockValues` is called, following the pre-Ecotone L1 attributes rules.
- At the Ecotone activation block:
  - `setL1BlockValues` function MUST be called, except if activated at genesis.
    The contract is upgraded later in this block, to support `setL1BlockValuesEcotone`.
- After the Ecotone activation:
  - `setL1BlockValues` function is deprecated and MUST never be called.
  - `setL1BlockValuesEcotone` MUST be called with the new Ecotone attributes.

`setL1BlockValuesEcotone` uses a tightly packed encoding for its parameters, which is described in
[L1 Attributes Deposited Transaction Calldata](../deposits.md#l1-attributes-deposited-transaction-calldata).
