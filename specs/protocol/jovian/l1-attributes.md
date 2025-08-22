# Jovian L1 Attributes

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [L1 Attributes Predeployed Contract](#l1-attributes-predeployed-contract)
  - [Jovian L1Block upgrade](#jovian-l1block-upgrade)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

On the Jovian activation block, and if Jovian is not activated at Genesis,
the L1 Attributes Transaction includes a call to `setL1BlockValuesEcotone()`
because the L1 Attributes transaction precedes the [Jovian Upgrade Transactions][jovian-upgrade-txs],
meaning that `setL1BlockValuesJovian` is not guaranteed to exist yet.

Every subsequent L1 Attributes transaction should include a call to the `setL1BlockValuesJovian()` function.
There are two additional `uint64` fields for the consensus nonces packed into calldata.
The overall calldata layout is as follows:

[jovian-upgrade-txs]: derivation.md#network-upgrade-automation-transactions

| Input arg         | Type    | Calldata bytes | Segment |
| ----------------- | ------- |----------------| ------- |
| {0x3db6be2b}      |         | 0-3            | n/a     |
| baseFeeScalar     | uint32  | 4-7            | 1       |
| blobBaseFeeScalar | uint32  | 8-11           |         |
| sequenceNumber    | uint64  | 12-19          |         |
| l1BlockTimestamp  | uint64  | 20-27          |         |
| l1BlockNumber     | uint64  | 28-35          |         |
| basefee           | uint256 | 36-67          | 2       |
| blobBaseFee       | uint256 | 68-99          | 3       |
| l1BlockHash       | bytes32 | 100-131        | 4       |
| batcherHash       | bytes32 | 132-163        | 5       |
| depositNonce      | uint64  | 164-171        | 6       |
| configUpdateNonce | uint64  | 172-179        |         |

Total calldata length MUST be exactly 180 bytes, implying the sixth and final segment is only
partially filled. This helps to slow database growth as every L2 block includes a L1 Attributes
deposit transaction.

In the first L2 block after the Jovian activation block, the Jovian L1 attributes are first used.

The pre-Jovian values are migrated over 1:1.
Blocks after the Jovian activation block contain all pre-Jovian values 1:1,
and also set the following new attributes:

- The `depositNonce` has the default value of 0.
- The `configUpdateNonce` has the default value of 0.

## L1 Attributes Predeployed Contract

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
  - `depositNonce` (`uint64`): nonce that increments for every `TransactionDeposited` event on the l1
  - `configUpdateNonce` (`uint64`): nonce that increments for every `ConfigUpdate` event on the l1

Note that the `depositNonce` and `configUpdateNonce` will remain with 0 values until the relevant
`SystemConfig` and `OptimismPortal2` contracts are upgraded on l1 to `SystemConfigJovian` and
`OptimismPortalJovian` respectively. This MUST happen after the hardfork activation date, and
before the next hardfork.

After running `pnpm build` in the `packages/contracts-bedrock` directory, the bytecode to add to
the genesis file will be located in the `deployedBytecode` field of the build artifacts file at
`/packages/contracts-bedrock/forge-artifacts/L1Block.sol/L1Block.json`.

### Jovian L1Block upgrade

The L1 Attributes Predeployed contract, `L1Block.sol`, is upgraded as part of the Jovian upgrade.
The version is incremented to `1.6.0`, and one new storage slot is introduced:

- `depositNonce` (`uint64`): nonce that increments for every `TransactionDeposited` event on the l1
- `configUpdateNonce` (`uint64`): nonce that increments for every `ConfigUpdate` event on the l1

The function called by the L1 attributes transaction depends on the network upgrade:

- Before the Jovian activation:
  - `setL1BlockValuesEcotone` is called, following the Ecotone L1 attributes rules.
- At the Jovian activation block:
  - `setL1BlockValuesEcotone` function MUST be called, except if activated at genesis.
    The contract is upgraded later in this block, to support `setL1BlockValuesJovian`.
- After the Jovian activation:
  - `setL1BlockValuesEcotone` function is deprecated and MUST never be called.
  - `setL1BlockValuesJovian` MUST be called with the new Jovian attributes.
