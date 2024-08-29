# Configurability

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Constants](#constants)
  - [`ConfigType`](#configtype)
- [`SystemConfig`](#systemconfig)
  - [Interface](#interface)
    - [`setBaseFeeVaultConfig`](#setbasefeevaultconfig)
    - [`setL1FeeVaultConfig`](#setl1feevaultconfig)
    - [`setSequencerFeeVaultConfig`](#setsequencerfeevaultconfig)
- [`OptimismPortal`](#optimismportal)
  - [Interface](#interface-1)
    - [`setConfig`](#setconfig)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The `SystemConfig` and `OptimismPortal` are updated with a new flow for chain
configurability.

## Constants

### `ConfigType`

The `ConfigType` enum represents configuration that can be modified.

| Name | Value | Description |
| ---- | ----- | --- |
| `SET_GAS_PAYING_TOKEN` | `uint8(0)` | Modifies the gas paying token for the chain |
| `SET_BASE_FEE_VAULT_CONFIG` | `uint8(1)` | Sets the Fee Vault Config for the `BaseFeeVault` |
| `SET_L1_FEE_VAULT_CONFIG` | `uint8(2)` | Sets the Fee Vault Config for the `L1FeeVault` |
| `SET_SEQUENCER_FEE_VAULT_CONFIG` | `uint8(3)` | Sets the Fee Vault Config for the `SequencerFeeVault` |
| `SET_L1_CROSS_DOMAIN_MESSENGER_ADDRESS` | `uint8(4)` | Sets the `L1CrossDomainMessenger` address |
| `SET_L1_ERC_721_BRIDGE_ADDRESS` | `uint8(5)` | Sets the `L1ERC721Bridge` address |
| `SET_L1_STANDARD_BRIDGE_ADDRESS` | `uint8(6)` | Sets the `L1StandardBridge` address |
| `SET_REMOTE_CHAIN_ID` | `uint8(7)` | Sets the chain id of the base chain |

## `SystemConfig`

### Interface

Each function calls `OptimismPortal.setConfig(ConfigType,bytes)` with its corresponding `ConfigType`.

For each `FeeVault`, there is a setter for its config. The arguments to the setter include
the `RECIPIENT`, the `MIN_WITHDRAWAL_AMOUNT` and the `WithdrawalNetwork`.
Each of these functions should be `public` and only callable by the chain governor.

#### `setBaseFeeVaultConfig`

```solidity
function setBaseFeeVaultConfig(address,uint256,WithdrawalNetwork)
```

#### `setL1FeeVaultConfig`

```solidity
function setL1FeeVaultConfig(address,uint256,WithdrawalNetwork)
```

#### `setSequencerFeeVaultConfig`

```solidity
function setSequencerFeeVaultConfig(address,uint256,WithdrawalNetwork)
```

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
