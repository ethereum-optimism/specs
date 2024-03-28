# Predeploys

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [GasPriceOracle](#gaspriceoracle)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## GasPriceOracle

Following the Fjord upgrade, three additional values used for L1 fee computation are:

- costIntercept
- costFastlzCoef
- costTxSizeCoef

These values are hard-coded constants in the `GasPriceOracle` contract. The
calculation follows the same formula outlined in the
[Fjord L1-Cost fee changes (FastLZ estimator)](./exec-engine.md#fjord-l1-cost-fee-changes-fastlz-estimator)
section.

A new method is introduced: `getL1FeeUpperBound(uint256)`. This method returns an upper bound for the L1 fee
for a given transaction size. It is provided for callers who wish to estimate L1 transaction costs in the
write path, and is much more gas efficient than `getL1Fee`.

The upper limit overhead is assumed to be `original/255+16`, borrowed from LZ4. According to historical data, this approach can encompass more than 99.99% of transactions.

implemented as follows:

```solidity
function getL1FeeUpperBound(uint256 unsignedTxSize) external view returns (uint256) {
    // txSize / 255 + 16 is the pratical fastlz upper-bound covers 99.99% txs.
    // Add 68 to both size values to account for unsigned tx:
    int256 flzUpperBound = int256(unsignedTxSize) + int256(unsignedTxSize) / 255 + 16 + 68;
    int256 txSize = int256(_unsignedTxSize) + 68;
    
    uint256 feeScaled = baseFeeScalar() * 16 * l1BaseFee() + blobBaseFeeScalar() * blobBaseFee();
    int256 cost = costIntercept + costFastlzCoef * flzUpperBound + costTxSizeCoef * txSize;
    if (cost < 0) {
        cost = 0;
    }
    return uint256(cost) * feeScaled / (10 ** (DECIMALS * 2));
}
```
