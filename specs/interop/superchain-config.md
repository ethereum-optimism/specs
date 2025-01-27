# Superchain Configuration Interop

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
  - [Pausability](#pausability)
- [Storage Layout](#storage-layout)
- [Interface and properties](#interface-and-properties)
  - [`addDependency`](#adddependency)
  - [`authorizedPortals`](#authorizedportals)
  - [`dependencySet`](#dependencyset)
  - [`dependencySetSize`](#dependencysetsize)
- [Events](#events)
  - [`DependencyAdded`](#dependencyadded)
- [Invariants](#invariants)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The `SuperchainConfigInterop` contract extends `SuperchainConfig` to manage the dependency set and portal authorization
for interoperability features.

The contract is updated with a new `CLUSTER_MANAGER` role that has the ability to add chains to the dependency set.
This role is handled similar to other roles in `SuperchainConfig`. It uses a `CLUSTER_MANAGER_SLOT` to store the address.

### Pausability

When the Pause is activated, the following methods are disabled:

1. `SharedLockbox.unlockETH()`

## Storage Layout

The contract uses the following storage layout for interoperability features:

```solidity
struct SuperchainConfigDependencies {
    ISharedLockbox sharedLockbox;
    EnumerableSet.UintSet dependencySet;
    mapping(address => bool) authorizedPortals;
}
```

The `SuperchainConfigDependencies` struct contains the core state variables needed for managing interoperability
between chains in the dependency set:

- `sharedLockbox`: A reference to the `SharedLockbox` contract that manages unified ETH liquidity across the dependency set.
  This allows ETH withdrawals to be processed from any chain's portal regardless of where the ETH was originally deposited.

- `dependencySet`: An enumerable set containing the chain IDs of all chains in the dependency set.
  This set is used to track which chains are part of the interoperable cluster.
  The set is append-only - chains cannot be removed once added.

- `authorizedPortals`: A mapping that tracks which `OptimismPortal` contracts are authorized to interact
  with the `SharedLockbox`.
  When a chain is added to the dependency set, its portal is authorized to lock and unlock ETH from
  the shared liquidity pool.

## Interface and properties

### `addDependency`

Adds a new chain to the dependency set. Can only be called by an authorized portal via a withdrawal transaction
initiated by the `DependencyManager`, or by the `CLUSTER_MANAGER` role.

```solidity
function addDependency(uint256 _chainId, address _systemConfig) external;
```

### `authorizedPortals`

Returns whether a portal is authorized to interact with the SharedLockbox.

```solidity
function authorizedPortals(address _portal) public view returns (bool);
```

### `dependencySet`

Returns the list of chain IDs in the dependency set.

```solidity
function dependencySet() external view returns (uint256[] memory);
```

### `dependencySetSize`

Returns the number of chains in the dependency set.

```solidity
function dependencySetSize() external view returns (uint8);
```

## Events

### `DependencyAdded`

MUST be triggered when a new dependency is added to the set.

```solidity
event DependencyAdded(uint256 indexed chainId, address indexed systemConfig, address indexed portal);
```

## Invariants


- If the chain is added through a withdrawal transaction, the L2 sender MUST be the `DependencyManager` predeploy contract.

- If the chain is NOT added through a withdrawal transaction, the msg sender MUST be the `CLUSTER_MANAGER`.

- A chain CANNOT be added to the dependency set if:

  - `SuperchainConfig` is paused
  - It would exceed the maximum size (255 chains)
  - It is already in the set
  - The `OptimismPortal` is configured with a different address for the `SuperchainConfig` than this one.

- When a chain is added:

  - Its `OptimismPortal` MUST be authorized in the `SharedLockbox`
  - Its ETH liquidity MUST be migrated to the `SharedLockbox`
  - A `DependencyAdded` event MUST be emitted

- The `CLUSTER_MANAGER` role MUST only be modifiable during initialization
