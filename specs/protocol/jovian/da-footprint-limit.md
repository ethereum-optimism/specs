
# DA Footprint Limit
Starting with Jovian, the `gasUsed` field of a block may instead represent the utilization of the DA by the block, based on the calldata of the transactions included in that block.
The purpose of this feature is to take into account the throughput of the DA Layer (the L1) when creating blocks that feature a high volume of `calldata`.

# Terms 

## `da_footprint`

`da_footprint` is the estimate of how much space a given transaction is expected to consume on the DA Layer. The value of `da_footprint` is driven by the size of the transaction's `calldata`. `da_footprint` may be less than the the size of the `calldata` because the data is compressed when published to L1.

```py
da_footprint = max(min_transaction_size, intercept + fastlz_coef * tx.fastlz_size / 1e6)
```

The protocol constants `min_transaction_size`, `intercept`, `fastlz_coef` are defined in [Fjord LZ Estimation](../fjord/exec-engine#fjord-l1-cost-fee-changes-fastlz-estimator).

## `block_da_footprint`

`block_da_footprint` represents the cumulative total of `da_footprint` for all transactions included in the given block.

```py
block_da_footprint = 0
for tx in block_txs:
    block_da_footprint += tx.da_footprint
```
## `block_gas_limit`

`block_gas_limit` represents the maximum allowable gas accumulated by all transactions in a given block. Above this limit, the block is not valid by protocol rules.

## `da_footprint_gas_scalar`

`da_footprint_gas_scalar` is a multiplier which normalizes the `block_da_footprint` such that it can be compared to `block_gas_limit`.

The value of `da_footprint_gas_scalar` is 400.

```py
da_footprint_gas_scalar = 400
```

### Rationale of `da_footprint_gas_scalar` value

A `da_footprint_gas_scalar` value was selected such that under standard operation blocks are only limited by their gas usage,
while in times of calldata heavy spam, block data which is posted to the Data Layer does not exceed its throughput capabilities.
- Values which are too high would artificially restrict the size of blocks which contain standard calldata transactions.
- Values which are too low would fail to restrict calldata heavy blocks and would exceed throughput capabilities.

The value selected, `400`, represents a middle-ground value which is successful in backtesting across multiple large OP Chains.

## `da_footprint_limit`

`da_footprint_limit` represents the maximum allowable size of a block's `block_da_footprint`.
```py
da_footprint_limit = block_gas_limit / da_footprint_gas_scalar
```
In practice, this value is never computed directly, as the `block_da_footprint` is scaled up using the `da_footprint_gas_scalar` to be compared to the `block_gas_limit`.

# Calculation of `gasUsed` in a Block

Pre-Jovian, `gasUsed` always represented the cumulative total `gasUsed` of each transaction included in that block.

```py
block_gas_used= 0
for tx in block_txs:
    block_gas_used += tx.gasUsed

gasUsed = block_gas_used
```

Jovian onward, `gasUsed` may represent one of two values, the larger of either:
- The original definition, representing the cumulative total of `gasUsed` of transactions
- The `block_da_footprint`, normalized to be comparable the original `gasUsed` by multiplying it with `da_footprint_gas_scalar`

```py
block_gas_used = 0
block_da_footprint = 0
for tx in block_txs:
    block_gas_used += tx.gasUsed
    block_da_footprint = tx.da_footprint

normalized_block_da_footprint = block_da_footprint * da_footprint_gas_scalar

gasUsed = max(block_gas_used, normalized_block_da_footprint)
```

## Validation of `gasUsed` in a Block

Validation of `gasUsed` for a block is the same as the calculation above: accumulate the `da_footprint` and `gasUsed` of each
transaction in the block, scale the `block_da_footprint` by the `da_footprint_gas_scalar` and take the larger of the two.

In order to distinguish which method was used in a given block, the `gasUsed` of the block should be compared to the accumulated
`block_gas_used`. If they are equal, then the block was limited by the gas consumption of the included transactions.

If `gasUsed` does not equal the accumulated `block_gas_used`, it indicates that `block_da_footprint` was the limit imposed on the block. This can be verified by dividing `gasUsed` by `da_footprint_gas_scalar` and comparing it to the accumulated `block_da_footprint`, which should be equal.

```py
if block.gasUsed == block_gas_used:
    limit = "gas"
else if block.gasUsed / da_footprint_gas_scalar == block_da_footprint:
    limit = "da"
else:
    except("gasUsed is neither gas or da based (invalid)")
```
