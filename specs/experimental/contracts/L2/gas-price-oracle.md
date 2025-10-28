# GasPriceOracle

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
  - [L1 Data Fee](#l1-data-fee)
  - [Fork Activation](#fork-activation)
  - [Compressed Transaction Size](#compressed-transaction-size)
- [Assumptions](#assumptions)
  - [a01-001: L1Block Provides Accurate Fee Parameters](#a01-001-l1block-provides-accurate-fee-parameters)
    - [Mitigations](#mitigations)
  - [a01-002: Depositor Account Controls Fork Activation](#a01-002-depositor-account-controls-fork-activation)
    - [Mitigations](#mitigations-1)
- [Invariants](#invariants)
  - [i01-001: Fork Activation Sequence Is Enforced](#i01-001-fork-activation-sequence-is-enforced)
    - [Impact](#impact)
  - [i01-002: Fork Activation Is Irreversible](#i01-002-fork-activation-is-irreversible)
    - [Impact](#impact-1)
- [Function Specification](#function-specification)
  - [getL1Fee](#getl1fee)
  - [getL1FeeUpperBound](#getl1feeupperbound)
  - [setEcotone](#setecotone)
  - [setFjord](#setfjord)
  - [setIsthmus](#setisthmus)
  - [setJovian](#setjovian)
  - [gasPrice](#gasprice)
  - [baseFee](#basefee)
  - [overhead](#overhead)
  - [scalar](#scalar)
  - [l1BaseFee](#l1basefee)
  - [blobBaseFee](#blobbasefee)
  - [baseFeeScalar](#basefeescalar)
  - [blobBaseFeeScalar](#blobbasefeescalar)
  - [decimals](#decimals)
  - [getL1GasUsed](#getl1gasused)
  - [getOperatorFee](#getoperatorfee)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The GasPriceOracle provides an API for estimating the L1 data availability portion of transaction fees on L2.
It proxies L1 fee parameters from the L1Block predeploy and applies fork-specific calculation formulas to compute
L1 fees for transactions.

## Definitions

### L1 Data Fee

The portion of an L2 transaction fee that covers the cost of posting transaction data to L1 for data availability.
This fee is calculated based on L1 gas prices, blob fees (post-Ecotone), and transaction size.

### Fork Activation

A one-way state transition that enables new fee calculation formulas corresponding to network upgrades
(Ecotone, Fjord, Isthmus, Jovian). Once activated, a fork cannot be deactivated.

### Compressed Transaction Size

The estimated size of a transaction after compression, used in Fjord and later upgrades to more accurately
estimate L1 data costs. Fjord uses FastLZ compression with linear regression to estimate Brotli compression ratios.

## Assumptions

### a01-001: L1Block Provides Accurate Fee Parameters

The L1Block predeploy at address 0x4200000000000000000000000000000000000015 provides accurate and up-to-date
L1 fee parameters including base fee, blob base fee, and fee scalars.

#### Mitigations

- L1Block is updated each L2 block via system transaction from the depositor account
- Values are derived from L1 block headers during derivation

### a01-002: Depositor Account Controls Fork Activation

The depositor account (0xDeaDDEaDDeAdDeAdDEAdDEaddeAddEAdDEAd0001) is trusted to activate forks at the correct
time according to the network upgrade schedule.

#### Mitigations

- Depositor account is a system address controlled by the protocol
- Fork activation is part of the network upgrade process coordinated across all nodes

## Invariants

### i01-001: Fork Activation Sequence Is Enforced

Fork activations must occur in the correct sequence: Ecotone → Fjord → Isthmus → Jovian.
Later forks cannot be activated before their prerequisites.

#### Impact

**Severity: High**

Violating the fork sequence would cause fee calculation inconsistencies and could result in incorrect fee
estimation, potentially leading to transaction failures or incorrect fee collection.

### i01-002: Fork Activation Is Irreversible

Once a fork is activated, it cannot be deactivated. The fork flags (isEcotone, isFjord, isIsthmus, isJovian)
can only transition from false to true, never from true to false.

#### Impact

**Severity: Medium**

Allowing fork deactivation would create inconsistent fee calculations across the network and break the
deterministic fee estimation that applications depend on.

## Function Specification

### getL1Fee

Computes the L1 portion of the fee for a given unsigned RLP-encoded transaction.

**Parameters:**

- `_data`: Unsigned fully RLP-encoded transaction bytes

**Behavior:**

- MUST return the result of `_getL1FeeFjord(_data)` if `isFjord` is true
- MUST return the result of `_getL1FeeEcotone(_data)` if `isEcotone` is true and `isFjord` is false
- MUST return the result of `_getL1FeeBedrock(_data)` if neither `isFjord` nor `isEcotone` is true
- MUST calculate fees based on the currently active fork

### getL1FeeUpperBound

Returns an upper bound estimate for the L1 fee based on unsigned transaction size.
Optimized for gas efficiency in write paths.

**Parameters:**

- `_unsignedTxSize`: Size of the unsigned fully RLP-encoded transaction in bytes

**Behavior:**

- MUST revert if `isFjord` is false
- MUST add 68 bytes to `_unsignedTxSize` to account for signature
- MUST calculate FastLZ upper bound as `txSize + txSize / 255 + 16`
- MUST return the result of `_fjordL1Cost(flzUpperBound)`
- MUST provide an upper bound that covers 99.99% of transactions

### setEcotone

Activates the Ecotone fork, enabling EIP-4844 blob-based fee calculations.

**Behavior:**

- MUST revert if `msg.sender` is not the depositor account (0xDeaDDEaDDeAdDeAdDEAdDEaddeAddEAdDEAd0001)
- MUST revert if `isEcotone` is already true
- MUST set `isEcotone` to true

### setFjord

Activates the Fjord fork, enabling compression-based fee calculations.

**Behavior:**

- MUST revert if `msg.sender` is not the depositor account
- MUST revert if `isEcotone` is false
- MUST revert if `isFjord` is already true
- MUST set `isFjord` to true

### setIsthmus

Activates the Isthmus fork, enabling operator fee calculations.

**Behavior:**

- MUST revert if `msg.sender` is not the depositor account
- MUST revert if `isFjord` is false
- MUST revert if `isIsthmus` is already true
- MUST set `isIsthmus` to true

### setJovian

Activates the Jovian fork, enabling updated operator fee formula.

**Behavior:**

- MUST revert if `msg.sender` is not the depositor account
- MUST revert if `isIsthmus` is false
- MUST revert if `isJovian` is already true
- MUST set `isJovian` to true

### gasPrice

Retrieves the current L2 gas price (base fee).

**Behavior:**

- MUST return `block.basefee`

### baseFee

Retrieves the current L2 base fee.

**Behavior:**

- MUST return `block.basefee`

### overhead

Retrieves the legacy fee overhead parameter (deprecated post-Ecotone).

**Behavior:**

- MUST revert if `isEcotone` is true
- MUST return the value from `IL1Block(Predeploys.L1_BLOCK_ATTRIBUTES).l1FeeOverhead()`

### scalar

Retrieves the legacy fee scalar parameter (deprecated post-Ecotone).

**Behavior:**

- MUST revert if `isEcotone` is true
- MUST return the value from `IL1Block(Predeploys.L1_BLOCK_ATTRIBUTES).l1FeeScalar()`

### l1BaseFee

Retrieves the latest known L1 base fee.

**Behavior:**

- MUST return the value from `IL1Block(Predeploys.L1_BLOCK_ATTRIBUTES).basefee()`

### blobBaseFee

Retrieves the current blob base fee.

**Behavior:**

- MUST return the value from `IL1Block(Predeploys.L1_BLOCK_ATTRIBUTES).blobBaseFee()`

### baseFeeScalar

Retrieves the current base fee scalar.

**Behavior:**

- MUST return the value from `IL1Block(Predeploys.L1_BLOCK_ATTRIBUTES).baseFeeScalar()`

### blobBaseFeeScalar

Retrieves the current blob base fee scalar.

**Behavior:**

- MUST return the value from `IL1Block(Predeploys.L1_BLOCK_ATTRIBUTES).blobBaseFeeScalar()`

### decimals

Retrieves the number of decimals used in scalar calculations.

**Behavior:**

- MUST return the constant value 6

### getL1GasUsed

Estimates the amount of L1 gas used for a transaction (deprecated for fee calculation).

**Parameters:**

- `_data`: Unsigned fully RLP-encoded transaction bytes

**Behavior:**

- MUST add 68 bytes to account for missing signature
- MUST compress data using FastLZ and apply linear regression if `isFjord` is true
- MUST calculate calldata gas (4 gas per zero byte, 16 gas per non-zero byte) if `isFjord` is false
- MUST return calldata gas without overhead if `isEcotone` is true and `isFjord` is false
- MUST add L1 fee overhead from L1Block if neither `isEcotone` nor `isFjord` is true

### getOperatorFee

Calculates the operator fee for a given gas usage amount.

**Parameters:**

- `_gasUsed`: The amount of gas used by the transaction

**Behavior:**

- MUST return 0 if `isIsthmus` is false
- MUST retrieve `operatorFeeScalar` and `operatorFeeConstant` from L1Block if `isIsthmus` is true
- MUST calculate as `_gasUsed * operatorScalar * 100 + operatorConstant` if `isJovian` is true
- MUST calculate as `saturatingAdd(saturatingMul(_gasUsed, operatorScalar) / 1e6, operatorConstant)` if
  `isIsthmus` is true but `isJovian` is false
- MUST use saturating arithmetic to prevent overflow in pre-Jovian calculations
