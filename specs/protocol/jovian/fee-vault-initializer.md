# FeeVaultInitializer

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Summary](#summary)
- [Functions](#functions)
  - [`constructor`](#constructor)
- [Events](#events)
  - [`FeeVaultDeployed`](#feevaultdeployed)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Summary

A contract responsible for deploying new vault implementations while preserving the current vault configuration.
It is intended to be used in a Network Upgrade Transaction (NUT) series context to upgrade each vault to the
new implementation once deployed.

## Functions

### `constructor`

When the initializer is deployed, it will:

- Read and retrieve the current values for `recipient()`, `withdrawalNetwork()`, and `minWithdrawalAmount()`
  from each live vault (`SequencerFeeVault`, `L1FeeVault`, `BaseFeeVault`, `OperatorFeeVault`).
- Handle legacy vaults that may not have the `WITHDRAWAL_NETWORK` function by using a low-level staticcall and
  assigning the default value of `WithdrawalNetwork.L2` when the configuration cannot be read.
- Deploy a new implementation for each vault, passing the retrieved values per vault as constructor
  immutables, and passing `L2` as the `WITHDRAWAL_NETWORK` constructor immutable in case a legacy vault is
  being upgraded.
- Emit the `FeeVaultDeployed` event for each newly deployed vault.

```solidity
constructor()
```

- MUST deploy implementations whose constructor immutables match the current configuration values.
- For legacy vaults, MUST assign a default `WithdrawalNetwork.L2` value to the network configuration on the new implementation.
- For each vault, MUST emit the `FeeVaultDeployed` event.

## Events

### `FeeVaultDeployed`

Emitted when a new fee vault implementation has been deployed.

```solidity
event FeeVaultDeployed(
    string indexed vaultType,
    address indexed newImplementation,
    address recipient,
    WithdrawalNetwork network,
    uint256 minWithdrawalAmount
)
```
