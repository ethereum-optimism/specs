# Configurability

## Overview

The `SystemConfig` and `OptimismPortal` are updated with a new flow for chain
configurability. This new flow reduces the need for the `ConfigUpdate` events
emitted by the `SystemConfig`, which adds great cost to the fault proof program's
execution as it results in the program to iterate through all possible logs to
ensure that it has observed all of the events. It also enables the L1 Attributes
transaction to not post duplicate data between transactions which reduces database
size growth over time.

## Constants

### `ConfigType`

The `ConfigType` enum represents configuration that can be modified.

| Name | Value | Description |
| ---- | ----- | --- |
| `SET_GAS_LIMIT` | `uint8(0)` | Sets the L2 gas limit |
| `SET_FEE_SCALARS` | `uint8(1)` | Sets the L2 fee configuration |
| `SET_EIP_1559_PARAMS` | `uint8(2)` | Sets the EIP-1559 elasticity and denominator |
| `SET_BATCHER_HASH` | `uint8(3)` | Sets the batcher role |
| `SET_UNSAFE_BLOCK_SIGNER` | `uint8(4)` | Sets the p2p sequencer key |
| `SET_GAS_PAYING_TOKEN` | `uint8(5)` | Modifies the gas paying token for the chain |
| `SET_BATCH_INBOX` | `uint8(6)` | Sets the canonical batch inbox address |

TODO: make sure that `SET_BATCH_INBOX` doesn't break the fault proof

## `SystemConfig`

### Interface

Each listed function calls `OptimismPortal.setConfig(ConfigType)` with its corresponding
`ConfigType`.

- `setGasLimit(uint64)`
- `setFeeScalars(uint32,uint32)`
- `setEIP1559Params(uint64,uint64)`
- `setBatcherHash(bytes32)`
- `setUnsafeBlockSigner(address)`
- `setGasPayingToken(address)`
- `setBatchInbox(address)`

## `OptimismPortal`

The `OptimismPortal` is updated to emit a special system `TransactionDeposited` event.

### Interface

#### `setConfig`

The `setConfig` function MUST only be callable by the `SystemConfig`. This ensures that the `SystemConfig`
is the single source of truth for chain operator ownership.

```solidity
function setConfig(ConfigType,bytes)
```

This function emits a `TransactionDeposited` event.

```solidity
event TransactionDeposited(address indexed from, address indexed to, uint256 indexed version, bytes opaqueData);
```

The following fields are included:

- `from` is the `DEPOSITOR_ACCOUNT`
- `to` is `Predeploys.L1Block`
- `version` is `uint256(0)`
- `opaqueData` is the tightly packed transaction data where `mint` is `0`, `value` is `0`, the `gasLimit`
   is `200_000`, `isCreation` is `false` and the `data` is `abi.encodeCall(L1Block.setConfig, (_type, _value))`
