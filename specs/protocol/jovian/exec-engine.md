# Jovian: Execution Engine

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Minimum Base Fee](#minimum-base-fee)
  - [Minimum Base Fee in Block Header](#minimum-base-fee-in-block-header)
  - [Minimum Base Fee in `PayloadAttributesV3`](#minimum-base-fee-in-payloadattributesv3)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Minimum Base Fee

Jovian introduces a
[configurable minimum base fee](https://github.com/ethereum-optimism/design-docs/blob/main/protocol/minimum-base-fee.md)
to reduce the duration of priority-fee auctions on OP Stack chains.

The minimum base fee is configured via `SystemConfig` (see `./system-config.md`) and enforced by the execution engine
via the block header `extraData` encoding and the Engine API `PayloadAttributesV3` parameters.

### Minimum Base Fee in Block Header

Like [Holocene's dynamic EIP-1559 parameters](../holocene/exec-engine.md#dynamic-eip-1559-parameters), Jovian encodes
fee parameters in the `extraData` field of each L2 block header. The format is extended to include an additional byte
for the minimum base fee exponent.

| Name                | Type               | Byte Offset |
| ------------------- | ------------------ | ----------- |
| `minBaseFeeFactors` | `uint8`            | `[9, 10)`   |

Constraints:

- `version` MUST be `1` (incremented from Holocene's `0`).
- There MUST NOT be any data beyond these 10 bytes.

The `minBaseFeeFactors` field encodes minimum base fee in wei as a 4-bit significand followed by a
4-bit exponent to the power of 10. A value of `0` disables the minimum base fee entirely.

```javascript
if minBaseFeeFactors > 0 {
  significand = minBaseFeeFactors >> 4 & 0x0F
  exponent = minBaseFeeFactors & 0x0F
  minBaseFee = significand * 10**exponent
  if baseFee < minBaseFee {
    baseFee = minBaseFee
  }
}
```

Note: `extraData` has a maximum capacity of 32 bytes (to fit the L1 beacon-chain `extraData` type) and may be
extended by future upgrades.

### Minimum Base Fee in `PayloadAttributesV3`

The Engine API [`PayloadAttributesV3`](../exec-engine.md#extended-payloadattributesv3) is extended in Jovian with a new
field `minBaseFeeFactors`. The existing `eip1559Params` remains 8 bytes (Holocene format).

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
    minBaseFeeFactors: QUANTITY or null
}
```
