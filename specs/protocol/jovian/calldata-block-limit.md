
# Calldata Limit
Starting with Jovian, the `gasUsed` field of a block may instead represent the utilization of calldata within the block.
The purpose of this feature is to take into account the throughput of the DA Layer (the L1) when creating blocks that feature a high volume of `calldata`

# Terms 

## `calldata`
Calldata is the `data` field attached to a transaction submitted to the OP Chain. The transaction author fully controls the content and size of the calldata at the time of authoring.

## `da_bytes_estimate`
`da_bytes_estimate` is the size of the `calldata` present in a transaction with respect to how much space it is expected to consume on the DA Layer. The DA Bytes Estimate may be smaller thatn the raw Calldata because the data is compressed when published to L1.

```py
da_bytes_estimate = max(min_transaction_size, intercept + fastlz_coef * tx.fastlz_size / 1e6)
```

The protocol constants `min_transaction_size`, `intercept`, `fastlz_coef` are defined in prior Hard Forks.

## `block_da_bytes_estimate`
`block_da_bytes_estimate` represents the cumulative total of `da_bytes_estimate` for all transactions included in the given block.

```py
block_da_bytes_estimate = 0
for tx in block_txs:
    block_da_bytes_estimate += tx.da_bytes_estimate
```

## `calldata_footprint_cost`
`calldata_footprint_cost` is a coefficient value which normalizes the `block_da_bytes_estimate` such that it can be compared to the `gasLimit` of the block.
The value of `calldata_footprint_cost` is 400, which is an arbitrary coefficient selected by analysis of real chain data.

```py
calldata_footprint_cost = da_bytes_estimate * calldata_footprint_cost
```

## `block_gas_limit`
`block_gas_limit` represents the maximum allowable gas accumulated by all transactions in a given block. Above this limit, the block is not valid by protocol rules.

## `block_da_bytes_limit`
`block_da_bytes_limit` represents the maximum allowable size of a block's `block_da_bytes_estimate`.
This is equal to `(block_gas_limit / calldata_footprint_cost)`, but in practice the `block_da_bytes_estimate` is normalized to be comparable with the `block_gas_limit`, so `block_da_bytes_limit` is not used directly.

## `gasUsed`
Pre-Jovian, `gasUsed` always represented the cumulative total `gasUsed` of each transaction included in that block.

Jovian onward, `gasUsed` may represent one of two values, the larger of either:
- The original definition, representing the cumulative total of `gasUsed` of transactions
- A pseudo-value representing the `block_da_bytes_estimate`, normalized to resemble the original `gasUsed` by multiplying it with the coefficient `calldata_footprint_cost`

In order to distinguish which value is being used, the `gasUsed` of each transaction may be summed. If the total is less than the `block_gas_limit`, it implies the `gasUsed` is using calldata footprint. This can be verified by constructing the `block_da_bytes_estimate`, and multiplying it by the `calldata_footprint_cost` coefficient.