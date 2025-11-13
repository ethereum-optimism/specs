# Predeploys

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Overview](#overview)
- [L2ProxyAdmin](#l2proxyadmin)
- [Invariants](#invariants)
  - [I-01: upgradePredeploys Access Control](#i-01-upgradepredeploys-access-control)
    - [Impact](#impact)
  - [I-02: Depositor Account Execution Guarantee](#i-02-depositor-account-execution-guarantee)
    - [Impact](#impact-1)
- [Functions](#functions)
  - [`upgradePredeploys`](#upgradepredeploys)
  - [`setImplementationName`](#setimplementationname)
  - [`setUpgrading`](#setupgrading)
  - [`isUpgrading`](#isupgrading)
  - [`getProxyImplementation`](#getproxyimplementation)
  - [`getProxyAdmin`](#getproxyadmin)
  - [`changeProxyAdmin`](#changeproxyadmin)
  - [`upgrade`](#upgrade)
  - [`upgradeAndCall`](#upgradeandcall)
- [Security Considerations](#security-considerations)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

## L2ProxyAdmin

The `ProxyAdmin` predeploy at `0x4200000000000000000000000000000000000018` is upgraded with a new L2-specific implementation, `L2ProxyAdmin`, that supports predeploy upgrades during hard forks. The `L2ProxyAdmin` contract adds the `upgradePredeploys()` function, which is called during a hard fork activation block by the `DEPOSITOR_ACCOUNT` to upgrade all predeploys in a single transaction.

The `L2ProxyAdmin` implementation also removes unused logic from the universal `ProxyAdmin` contract. Previously, the L2 ProxyAdmin used the same "universal" implementation deployed on L1, which supports multiple proxy types (ERC1967, ChugSplash, and ResolvedDelegate) and includes proxy type validation logic. Since all L2 predeploys use ERC1967 proxies exclusively, `L2ProxyAdmin` overrides functions related to legacy proxy types to remove their support while keeping the same public interface for backward compatibility. Setters for configuration values regarding proxy types are overridden to result in no-ops, and getters are overridden to either return default values or values that are relevant in the ERC1967 context only.

## Invariants

### I-01: upgradePredeploys Access Control

The `upgradePredeploys` function MUST only be callable by the contract owner or the `DEPOSITOR_ACCOUNT` (`0xdeaddeaddeaddeaddeaddeaddeaddeaddead0001`).

#### Impact

Violation of this invariant would allow an attacker to trigger predeploy upgrades via `delegatecall` to arbitrary contracts.

### I-02: Depositor Account Execution Guarantee

When called by the `DEPOSITOR_ACCOUNT`, the `upgradePredeploys` function MUST NOT revert, provided that the `_l2ContractsManager` parameter is a valid contract address.

#### Impact

Violation of this invariant will allow upgrades to fail, potentially leading to network stalling.

## Functions

### `upgradePredeploys`

This is a permissioned function that performs a `delegatecall` to a previously deployed `L2ContractsManager`.

```solidity
function upgradePredeploys(address _l2ContractsManager) external;
```

- MUST revert if not called by either the `DEPOSITOR_ACCOUNT` or the owner of the `L2ProxyAdmin`
- MUST perform a single `delegatecall` to `_l2ContractsManager`
- MUST never revert

### `setImplementationName`

```solidity
function setImplementationName(address _address, string memory _name) external;
```

- MUST NOT revert
- MUST NOT modify any state

### `setUpgrading`

```solidity
function setUpgrading(bool _upgrading) external;
```

- MUST NOT revert
- MUST NOT modify any state

### `isUpgrading`

```solidity
function isUpgrading() external view returns (bool);
```

- MUST return `false`

### `getProxyImplementation`

```solidity
function getProxyImplementation(address _proxy) external view returns (address);
```

- MUST return the implementation address by calling `implementation()` on the ERC1967 proxy
- MUST NOT query proxy type configuration

### `getProxyAdmin`

```solidity
function getProxyAdmin(address payable _proxy) external view returns (address);
```

- MUST return the admin address by calling `admin()` on the ERC1967 proxy
- MUST NOT query proxy type configuration

### `changeProxyAdmin`

```solidity
function changeProxyAdmin(address payable _proxy, address _newAdmin) external;
```

- MUST revert if caller is not the owner
- MUST call `changeAdmin(_newAdmin)` on the ERC1967 proxy

### `upgrade`

```solidity
function upgrade(address payable _proxy, address _implementation) public;
```

- MUST revert if caller is not the owner
- MUST call `upgradeTo(_implementation)` on the ERC1967 proxy

### `upgradeAndCall`

```solidity
function upgradeAndCall(
    address payable _proxy,
    address _implementation,
    bytes memory _data
) external payable;
```

- MUST revert if caller is not the owner
- MUST call `upgradeToAndCall(_implementation, _data)` on the ERC1967 proxy with forwarded `msg.value`

## Security Considerations

- Performing a `delegatecall` from the `ProxyAdmin` which manages **ALL** the predeploys must be implemented with extreme caution. We must ensure that no accounts other than the owner or the `DEPOSITOR_ACCOUNT` can call the `upgradePredeploys` function.
