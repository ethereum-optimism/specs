# Jovian: System Config

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Minimum Base Fee Configuration](#minimum-base-fee-configuration)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Minimum Base Fee Configuration

Jovian adds a new configuration value to `SystemConfig` to control the minimum base fee used by the EIP-1559 fee market
on OP Stack chains. The value represents the log2 of the minimum base fee in wei.

| Name             | Type    | Default | Meaning                                                                                 |
|------------------|---------|---------|-----------------------------------------------------------------------------------------|
| `minBaseFeeLog2` | `uint8` | `0`     | Log2 of the minimum base fee in wei. `0` disables the minimum base fee entirely.        |

The configuration is updated via a new method on `SystemConfig`:

```solidity
function setMinBaseFeeLog2(uint8 minBaseFeeLog2) external onlyOwner;
```

Upon update, the contract emits a `ConfigUpdate` event with a new `UpdateType` value `MINIMUM_BASE_FEE`, enabling nodes
to derive the configuration from L1 logs.

Implementations MUST incorporate the configured value into the block header `extraData` as specified in
`./exec-engine.md`.


