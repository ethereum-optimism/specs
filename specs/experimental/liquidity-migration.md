<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [`OptimismMintableERC20Factory` Updates](#optimismmintableerc20factory-updates)
  - [Functions](#functions)
    - [`createOptimismMintableERC20WithDecimals`](#createoptimismmintableerc20withdecimals)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# `OptimismMintableERC20Factory` Updates

The `OptimismMintableERC20Factory` is updated to include a `deployments` mapping
that stores the `remoteToken` address for each deployed `OptimismMintableERC20`.
This is essential for the liquidity migration process defined in the liquidity migration spec.

## Functions

### `createOptimismMintableERC20WithDecimals`

**Invariants**

- The function MUST store the `_remoteToken` address for each deployed `OptimismMintableERC20` in a `deployments` mapping.
