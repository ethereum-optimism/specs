# Block Calldata Limit

In order to mitigate calldata spam attacks, Jovian introduces a feature that enforces a maximum estimated L1 calldata footprint per block and changes the EIP-1559 base fee calculation to compute over a multidimensional resource usage context. Noteably, this approach preserves EVM-equivalence in transaction gas accounting, such that wallets and other tooling do not need to update their gas estimation logic properly estimate gas consumption.

## Terms

- **`BlockCalldataLimit`**: Protocol constant numerically the same as the block gas limit (made possible by scaling)
- **`txCalldataFootprint`**: `sizeEstimate * calldataFootprintCost`
- **`blockCalldataFootprint`**: Sum over all txs’ calldata footprints
- **(Tx) Size Estimate**: The Fjord size estimate protocol constants, scaled back to 1
    - `minTransactionSize` is `100`
    - `intercept` is `-42_585_600`
    - `fastlzCoef` is `836_500`
- **`CalldataFootprintCost`**: Protocol constant representing cost per size estimate, set to `400`.

### Maximum Block Size

In order for a block to be valid, a block's `blockCalldataFootprint` MUST be below the `blockCalldataLimit`.

### EIP-1559 Fee Update

Upon the first block of Jovian and thereafter, we will use the following calculation to produce a block's `gasUsed` quantity, replacing the old calculation. This quantity will also be used for EIP-1559 base fee update calculations going forward.

```py
def block_gas_metered()
    tx_total_gas_used = 0
    block_da_bytes_estimate = 0
    for tx in block_txs:
        tx_total_gas_used += tx.gas_used
        block_da_bytes_estimate += max(min_transaction_size, intercept + fastlz_coef * tx.fastlz_size / 1e6)
    block_calldata_footprint = block_da_bytes_estimate * calldata_footprint_cost
    gas_metered = max(block_calldata_footprint, tx_total_gas_used)
    return gas_metered

block_gas_used = block_gas_metered
```