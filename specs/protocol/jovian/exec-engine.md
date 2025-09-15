# Jovian: Execution Engine

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Minimum Base Fee](#minimum-base-fee)
  - [Minimum Base Fee in Block Header](#minimum-base-fee-in-block-header)
  - [Minimum Base Fee in `PayloadAttributesV3`](#minimum-base-fee-in-payloadattributesv3)
  - [Rationale](#rationale)
- [DA Footprint Limit](#da-footprint-limit)
  - [Rationale](#rationale-1)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Minimum Base Fee

Jovian introduces a
[configurable minimum base fee](https://github.com/ethereum-optimism/design-docs/blob/main/protocol/minimum-base-fee.md)
to reduce the duration of priority-fee auctions on OP Stack chains.

The minimum base fee is configured via `SystemConfig` (see `./system-config.md`) and enforced by the execution engine
via the block header `extraData` encoding and the Engine API `PayloadAttributesV3` parameters.

### Minimum Base Fee in Block Header

Like [Holocene's dynamic EIP-1559 parameters](../holocene/exec-engine.md#dynamic-eip-1559-parameters), Jovian encodes
fee parameters in the `extraData` field of each L2 block header. The format is extended to include an additional
`u64` field for the minimum base fee in wei.

| Name                | Type               | Byte Offset |
| ------------------- | ------------------ | ----------- |
| `minBaseFee`        | `u64 (big-endian)` | `[9, 17)`   |

Constraints:

- `version` MUST be `1` (incremented from Holocene's `0`).
- There MUST NOT be any data beyond these 17 bytes.

The `minBaseFee` field is an absolute minimum expressed in wei. During base fee computation, if the
computed `baseFee` is less than `minBaseFee`, it MUST be clamped to `minBaseFee`.

```javascript
if (baseFee < minBaseFee) {
  baseFee = minBaseFee
}
```

Note: `extraData` has a maximum capacity of 32 bytes (to fit the L1 beacon-chain `extraData` type) and may be
extended by future upgrades.

### Minimum Base Fee in `PayloadAttributesV3`

The Engine API [`PayloadAttributesV3`](../exec-engine.md#extended-payloadattributesv3) is extended with a new
field `minBaseFee`. The existing `eip1559Params` remains 8 bytes (Holocene format).

```text
PayloadAttributesV3: {
    timestamp: QUANTITY
    prevRandao: DATA (32 bytes)
    suggestedFeeRecipient: DATA (20 bytes)
    withdrawals: array of WithdrawalV1
    parentBeaconBlockRoot: DATA (32 bytes)
    transactions: array of DATA
    noTxPool: bool
    gasLimit: QUANTITY or null
    eip1559Params: DATA (8 bytes) or null
    minBaseFee: QUANTITY or null
}
```

The `minBaseFee` MUST be `null` prior to the Jovian fork, and MUST be non-`null` after the Jovian fork.

### Rationale

As with [Holocene's dynamic EIP-1559 parameters](../holocene/exec-engine.md#rationale), placing the
minimum base fee in the block header allows us to avoid reaching into the state during block sealing.
This retains the purity of the function that computes the next block's base fee from its parent block
header, while still allowing them to be dynamically configured. Dynamic configuration is handled
similarly to `gasLimit`, with the derivation pipeline providing the appropriate `SystemConfig`
contract values to the block builder via `PayloadAttributesV3` parameters.

## DA Footprint Limit

From Jovian, `gasUsed` is equal to a block's "DA footprint" if the footprint exceeds
the total gas used by transaction, and equal to the sum of the gas used by each transaction otherwise. As a result, blocks with high DA usage may cause the base fee to increase in
subsequent blocks.

A block's DA footprint is calculated by scaling the cumulative DA footprint of its transactions
(as calculated by the [Fjord LZ Estimation](../fjord/exec-engine.md#fjord-l1-cost-fee-changes-fastlz-estimator) by
a configurable scalar value, the `daFootprintGasScalar`.

The `daFootprintGasScalar` is loaded in a similar way to the `operatorFeeScalar` and `operatorFeeConstant`
[included](../isthmus/exec-engine.md#operator-fee) in the Isthmus fork. It can be read in two interchangable ways:

- read from the deposited L1 attributes (`daFootprintGasScalar`) of the current L2 block
- read from the L1 Block Info contract (`0x4200000000000000000000000000000000000015`)
  - using the solidity getter function `daFootprintGasScalar`
  - using a direct storage-read: big-endian `uint16` in slot `9` at offset `0`.

### Rationale

While the current L1 fee mechanism charges for DA usage based on an estimate of the DA footprint of a transaction, it does not influence future
base fee calculations. As a result, excessive DA usage is not efficiently reflected in the fee market, leading to suboptimal
resource prices.

By changing the meaning of the `gasUsed` field in times of high DA demand, the fee market can properly adjust without reverting
to priority fee auctions (an inferior experience for users).
