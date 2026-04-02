# L1 Block Attributes

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

# L1 Block Attributes

**Table of Contents**

- [Overview](#overview)

## Overview

The L1 block attributes transaction is updated to include the operator fee parameters.

| Input arg | Type | Calldata bytes | Segment |
| :--- | :--- | :--- | :--- |
| {0x098999be} | | 0-3 | n/a |
| baseFeeScalar | uint32 | 4-7 | 1 |
| blobBaseFeeScalar | uint32 | 8-11 | |
| sequenceNumber | uint64 | 12-19 | |
| l1BlockTimestamp | uint64 | 20-27 | |
| l1BlockNumber | uint64 | 28-35 | |
| basefee | uint256 | 36-67 | 2 |
| blobBaseFee | uint256 | 68-99 | 3 |
| l1BlockHash | bytes32 | 100-131 | 4 |
| batcherHash | bytes32 | 132-163 | 5 |
| operatorFeeScalar | uint32 | 164-167 | 6 |
| operatorFeeConstant | uint64 | 168-175 | |

Note that the first input argument, in the same pattern as previous versions of the L1 attributes transaction, is the function selector: the first four bytes of `keccak256("setL1BlockValuesJovian()")`.

In the activation block, there are two possibilities:

- If Jovian is active at genesis, there are no transactions in the activation block and therefore no L1 Block Attributes transaction to consider.
- If Jovian activates after genesis, the [`setL1BlockValuesIsthmus()`](../isthmus/l1-attributes.md) method must be used. This is because the L1 Block contract will not yet have been upgraded.

In each subsequent L2 block, the `setL1BlockValuesJovian()` method must be used. This method ensures that the `daFootprintGasScalar` and `tokenRatio` parameters are correctly propagated alongside the existing operator fee scalars.

When using this method, the pre-Jovian values are migrated over 1:1 and the transaction also sets the following new attributes to the values from the [`SystemConfig`](./system-config.md):

- `operatorFeeScalar`
- `operatorFeeConstant`
- `daFootprintGasScalar`
- `tokenRatio`
is the function selector: the first four bytes of `keccak256("setL1BlockValuesIsthmus()")`.

In the activation block, there are two possibilities:
- If Isthmus is active at genesis, there are no transactions in the activation block
and therefore no L1 Block Attributes transaction to consider.
- If Isthmus activates after genesis [`setL1BlockValuesEcotone()`](../ecotone/l1-attributes.md)
method must be used. This is because the L1 Block contract will not yet have been upgraded.
- In each subsequent L2 block, the setL1BlockValuesJovian() method must be used. This method ensures that the daFootprintGasScalar and tokenRatio parameters are correctly propagated alongside the existing operator fee scalars.

When using this method, the pre-Isthmus values are migrated over 1:1
and the transaction also sets the following new attributes to the values
from the [`SystemConfig`](./system-config.md):

- `operatorFeeScalar`
- `operatorFeeConstant`
- `daFootprintGasScalar`
- `tokenRatio`
