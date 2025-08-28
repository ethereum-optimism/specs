# Optimism Portal

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Definitions](#definitions)
  - [Custom Gas Token Flag](#custom-gas-token-flag)
- [Rationale](#rationale)
- [Function Specification](#function-specification)
  - [isCustomGasToken](#iscustomgastoken)
  - [donateETH](#donateeth)
  - [depositTransaction](#deposittransaction)
- [Security Considerations](#security-considerations)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Definitions

### Custom Gas Token Flag

The **Custom Gas Token Flag** (`isCustomGasToken`) is a boolean value that indicates
whether the chain is operating in Custom Gas Token mode. This flag is set during the
`initialize` function call by directly passing the `_isCustomGasToken` boolean parameter,
which is then assigned to the contract's `isCustomGasToken` state variable.

## Rationale

The OptimismPortal's ETH-related logic must revert when Custom Gas Token mode is enabled to prevent ETH from
acting as the native asset. Since the client side does not discern native asset supply creation, allowing
ETH deposits would incorrectly imply that it can be minted in the chain.

## Function Specification

### isCustomGasToken

Returns true if the gas token is a custom gas token, false otherwise.

### donateETH

- MUST revert if `isCustomGasToken()` returns `true` and `msg.value > 0`.

### depositTransaction

- MUST revert if `isCustomGasToken()` returns `true` and `msg.value > 0`.

## Security Considerations

### Custom Gas Token Flag Immutability

Once the `isCustomGasToken` flag is set to `true` during initialization, it should not be
changed back to `false` in subsequent reinitializations. Changing from custom gas token mode
back to ETH mode could create inconsistencies in the chain's gas token handling and
potentially lead to security vulnerabilities. The flag represents a fundamental configuration
of the chain's gas token mechanism and should remain consistent throughout the chain's
lifetime.
