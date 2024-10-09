# Configurability

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Constants](#constants)
  - [`ConfigType`](#configtype)
- [`SystemConfig`](#systemconfig)
  - [`ConfigUpdate`](#configupdate)
  - [Initialization](#initialization)
  - [Modifying Operator Fee Parameters](#modifying-operator-fee-parameters)
  - [Interface](#interface)
    - [Operator fee parameters](#operator-fee-parameters)
      - [`operatorFeeScalar`](#operatorfeescalar)
      - [`operatorFeeConstant`](#operatorfeeconstant)
      - [`setOperatorFeeScalars`](#setoperatorfeescalars)
      - [`setOperatorFeeManager`](#setoperatorfeemanager)
    - [Fee Vault Config](#fee-vault-config)
      - [`setBaseFeeVaultConfig`](#setbasefeevaultconfig)
      - [`setL1FeeVaultConfig`](#setl1feevaultconfig)
      - [`setSequencerFeeVaultConfig`](#setsequencerfeevaultconfig)
      - [`setOperatorFeeVaultConfig`](#setoperatorfeevaultconfig)
- [`OptimismPortal`](#optimismportal)
  - [Interface](#interface-1)
    - [`setConfig`](#setconfig)
    - [`upgrade`](#upgrade)
- [Consensus Parameters](#consensus-parameters)
  - [Operator Fee Scalar](#operator-fee-scalar)
  - [Operator Fee Constant](#operator-fee-constant)
- [Service Roles](#service-roles)
  - [Operator Fee Manager](#operator-fee-manager)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The `SystemConfig` and `OptimismPortal` are updated with a new flow for chain
configurability. A new service role `OperatorFeeManager` is added to manage the operator fee collection.

## Constants

### `ConfigType`

The `ConfigType` enum represents configuration that can be modified.

| Name | Value | Description |
| ---- | ----- | --- |
| `SET_GAS_PAYING_TOKEN` | `uint8(0)` | Modifies the gas paying token for the chain |
| `SET_BASE_FEE_VAULT_CONFIG` | `uint8(1)` | Sets the Fee Vault Config for the `BaseFeeVault` |
| `SET_L1_FEE_VAULT_CONFIG` | `uint8(2)` | Sets the Fee Vault Config for the `L1FeeVault` |
| `SET_SEQUENCER_FEE_VAULT_CONFIG` | `uint8(3)` | Sets the Fee Vault Config for the `SequencerFeeVault` |
| `SET_OPERATOR_FEE_VAULT_CONFIG` | `uint8(4)` | Sets the Fee Vault Config for the `OperatorFeeVault` |
| `SET_L1_CROSS_DOMAIN_MESSENGER_ADDRESS` | `uint8(5)` | Sets the `L1CrossDomainMessenger` address |
| `SET_L1_ERC_721_BRIDGE_ADDRESS` | `uint8(6)` | Sets the `L1ERC721Bridge` address |
| `SET_L1_STANDARD_BRIDGE_ADDRESS` | `uint8(7)` | Sets the `L1StandardBridge` address |
| `SET_REMOTE_CHAIN_ID` | `uint8(8)` | Sets the chain id of the base chain |

## `SystemConfig`

### `ConfigUpdate`

The following `ConfigUpdate` event is defined where the `CONFIG_VERSION` is `uint256(0)`:

| Name | Value | Definition | Usage |
| ---- | ----- | --- | -- |
| `BATCHER` | `uint8(0)` | `abi.encode(address)` | Modifies the account that is authorized to progress the safe chain |
| `FEE_SCALARS` | `uint8(1)` | `(uint256(0x01) << 248) \| (uint256(_blobbasefeeScalar) << 32) \| _basefeeScalar` | Modifies the fee scalars |
| `GAS_LIMIT` | `uint8(2)` | `abi.encode(uint64 _gasLimit)` | Modifies the L2 gas limit |
| `UNSAFE_BLOCK_SIGNER` | `uint8(3)` | `abi.encode(address)` | Modifies the account that is authorized to progress the unsafe chain |
| `EIP_1559_PARAMS` | `uint8(4)` | `uint256(uint64(uint32(_denominator))) << 32 \| uint64(uint32(_elasticity))` | Modifies the EIP-1559 denominator and elasticity |
| `OPERATOR_FEE_PARAMS` | `uint8(5)` | `uint256(_operatorFeeScalar) << 64 \| _operatorFeeConstant` | Modifies the operator fee parameters |
| `OPERATOR_FEE_MANAGER` | `uint8(6)` | `abi.encode(address)` | Modifies the operator fee manager |

### Initialization

The following actions should happen during the initialization of the `SystemConfig`:

- `emit ConfigUpdate.BATCHER`
- `emit ConfigUpdate.FEE_SCALARS`
- `emit ConfigUpdate.GAS_LIMIT`
- `emit ConfigUpdate.UNSAFE_BLOCK_SIGNER`
- `emit ConfigUpdate.EIP_1559_PARAMS`
- `emit ConfigUpdate.OPERATOR_FEE_PARAMS`
- `emit ConfigUpdate.OPERATOR_FEE_MANAGER`
- `setConfig(SET_GAS_PAYING_TOKEN)`
- `setConfig(SET_BASE_FEE_VAULT_CONFIG)`
- `setConfig(SET_L1_FEE_VAULT_CONFIG)`
- `setConfig(SET_SEQUENCER_FEE_VAULT_CONFIG)`
- `setConfig(SET_OPERATOR_FEE_VAULT_CONFIG)`
- `setConfig(SET_L1_CROSS_DOMAIN_MESSENGER_ADDRESS)`
- `setConfig(SET_L1_ERC_721_BRIDGE_ADDRESS)`
- `setConfig(SET_L1_STANDARD_BRIDGE_ADDRESS)`
- `setConfig(SET_REMOTE_CHAIN_ID)`

These actions MAY only be triggered if there is a diff to the value.

Since the `OperatorFeeVault` is new in Isthmus, the `setConfig(SET_OPERATOR_FEE_VAULT_CONFIG)` MUST be emitted.

`ConfigUpdate.OPERATOR_FEE_PARAMS` and `ConfigUpdate.OPERATOR_FEE_MANAGER` MAY be emitted. If they are not emitted,
the `operatorFeeScalar` and `operatorFeeConstant` are set to 0 by default, and the `OperatorFeeManager`
is set to the chain governor by default.

### Modifying Operator Fee Parameters

A new `SystemConfig` `UpdateType` is introduced that enables the modification of
the `operatorFeeScalar` and `operatorFeeConstant` by the [`OperatorFeeManager`](#operator-fee-manager).

Another `UpdateType` is added to modify the [`OperatorFeeManager`].

### Interface

#### Operator fee parameters

##### `operatorFeeScalar`

This function returns the currently configured operator fee scalar.

```solidity
function operatorFeeScalar()(uint32)
```

##### `operatorFeeConstant`

This function returns the currently configured operator fee constant.

```solidity
function operatorFeeConstant()(uint64)
```

##### `setOperatorFeeScalars`

This function sets the `operatorFeeScalar` and `operatorFeeConstant`.

This function MUST only be callable by the [`OperatorFeeManager`](#operator-fee-manager).

```solidity
function setOperatorFeeScalar(uint32 _operatorFeeScalar, uint64 _operatorFeeConstant)()
```

##### `setOperatorFeeManager`

This function sets the `operatorFeeManager`.

This function MUST only be callable by the chain governor.

```solidity
function setOperatorFeeManager(address _operatorFeeManager)()
```

#### Fee Vault Config

For each `FeeVault`, there is a setter for its config. The arguments to the setter include
the `RECIPIENT`, the `MIN_WITHDRAWAL_AMOUNT` and the `WithdrawalNetwork`.
Each of these functions should be `public` and only callable by the chain governor.

Each function calls `OptimismPortal.setConfig(ConfigType,bytes)` with its corresponding `ConfigType`.

##### `setBaseFeeVaultConfig`

```solidity
function setBaseFeeVaultConfig(address,uint256,WithdrawalNetwork)
```

##### `setL1FeeVaultConfig`

```solidity
function setL1FeeVaultConfig(address,uint256,WithdrawalNetwork)
```

##### `setSequencerFeeVaultConfig`

```solidity
function setSequencerFeeVaultConfig(address,uint256,WithdrawalNetwork)
```

##### `setOperatorFeeVaultConfig`

```solidity
function setOperatorFeeVaultConfig(address,uint256,WithdrawalNetwork)
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

#### `upgrade`

The `upgrade` function MUST only be callable by the `UPGRADER` role as defined
in the [`SuperchainConfig`](./superchain-config.md).

```solidity
function upgrade(bytes memory _data) external
```

This function emits a `TransactionDeposited` event.

```solidity
event TransactionDeposited(address indexed from, address indexed to, uint256 indexed version, bytes opaqueData);
```

The following fields are included:

- `from` is the `DEPOSITOR_ACCOUNT`
- `to` is `Predeploys.ProxyAdmin`
- `version` is `uint256(0)`
- `opaqueData` is the tightly packed transaction data where `mint` is `0`, `value` is `0`, the `gasLimit`
   is `200_000`, `isCreation` is `false` and the `data` is the data passed into `upgrade`.

## Consensus Parameters

The operator fee scalar and constant are new consensus parameters, so we define standard values for them.

### [Operator Fee Scalar](exec-engine.md#operator-fees)

**Description:** Operator fee scalar -- used to calculate the operator fee<br/>
**Administrator:** [Operator Fee Manager](#operator-fee-manager)<br/>
**Requirement:** Between 0 and 0.5 * (baseFee + priorityFee) <br/>

### [Operator Fee Constant](exec-engine.md#operator-fees)

**Description:** Operator fee constant -- used to calculate the operator fee<br/>
**Administrator:** [Operator Fee Manager](#operator-fee-manager)<br/>
**Requirement:** Between 0 and 600 Gwei <br/>

## Service Roles

### Operator Fee Manager

**Description:** Account authorized to modify the operator fee scalar. <br/>
**Administrator:** [System Config Owner](../configurability.md#system-config)<br/>
**Requirement:** <br/>
**Notes:** <br/>
