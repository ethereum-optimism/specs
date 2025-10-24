# Proxy

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
  - [Admin](#admin)
  - [Implementation](#implementation)
  - [Transparent Proxy Pattern](#transparent-proxy-pattern)
- [Assumptions](#assumptions)
- [Invariants](#invariants)
  - [i01-001: Complete call delegation without interception](#i01-001-complete-call-delegation-without-interception)
    - [Impact](#impact)
  - [i01-002: Admin-only access to proxy interface](#i01-002-admin-only-access-to-proxy-interface)
    - [Impact](#impact-1)
  - [i01-003: EIP-1967 storage slot isolation](#i01-003-eip-1967-storage-slot-isolation)
    - [Impact](#impact-2)
- [Function Specification](#function-specification)
  - [constructor](#constructor)
  - [receive](#receive)
  - [fallback](#fallback)
  - [upgradeTo](#upgradeto)
  - [upgradeToAndCall](#upgradetoandcall)
  - [changeAdmin](#changeadmin)
  - [admin](#admin)
  - [implementation](#implementation)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The Proxy contract is a transparent proxy that enables upgradeability for smart contracts while maintaining a stable
address. It delegates all calls to an implementation contract, except when called by the admin, who can access the
proxy's administrative interface to upgrade the implementation or transfer ownership.

## Definitions

### Admin

The address that has exclusive access to the proxy's administrative functions. The admin can upgrade the
implementation contract and transfer admin rights to a new address. The admin address is stored at the EIP-1967 admin
storage slot to prevent collisions with the implementation contract's storage.

### Implementation

The address of the contract to which all non-admin calls are delegated. The implementation contains the actual business
logic while the proxy maintains the state and provides upgradeability. The implementation address is stored at the
EIP-1967 implementation storage slot.

### Transparent Proxy Pattern

A proxy pattern where the proxy's administrative interface is only accessible to the admin address, while all other
callers have their calls transparently delegated to the implementation. This prevents function selector collisions
between the proxy's administrative functions and the implementation's functions. Additionally, calls from `address(0)`
are treated as admin calls to enable off-chain simulations via `eth_call` without requiring low-level storage
inspection.

## Assumptions

N/A

## Invariants

### i01-001: Complete call delegation without interception

All calls from non-admin addresses MUST be delegated to the implementation contract without any interception,
modification, or validation by the proxy. The proxy MUST preserve the complete execution context including `msg.sender`,
`msg.value`, calldata, and return data. The proxy MUST NOT impose any restrictions on what functions can be called or
what data can be passed through.

#### Impact

**Severity: Critical**

If this invariant is violated, the proxy would break the fundamental trust model of transparent proxies. Users would be
unable to interact with the implementation contract as intended, potentially losing access to funds or functionality.
The proxy's purpose is to be completely transparent to non-admin users, and any interception would violate this core
property.

### i01-002: Admin-only access to proxy interface

The proxy's administrative functions (`upgradeTo`, `upgradeToAndCall`, `changeAdmin`, `admin`, `implementation`) MUST
only be accessible to the admin address or `address(0)`. All other addresses MUST have their calls delegated to the
implementation, even if they attempt to call these administrative functions. This prevents function selector collisions
where the implementation contract might have functions with the same signatures as the proxy's administrative functions.

#### Impact

**Severity: Critical**

If this invariant is violated, unauthorized addresses could upgrade the implementation to a malicious contract, steal
all funds held by the proxy, or transfer admin rights. The `address(0)` exception enables off-chain simulations without
compromising security since `address(0)` cannot be used as `msg.sender` during normal EVM execution.

### i01-003: EIP-1967 storage slot isolation

The admin and implementation addresses MUST be stored at the EIP-1967 specified storage slots
(`bytes32(uint256(keccak256('eip1967.proxy.admin')) - 1)` and
`bytes32(uint256(keccak256('eip1967.proxy.implementation')) - 1)` respectively). These slots MUST NOT be accessible or
modifiable through delegated calls to the implementation contract.

#### Impact

**Severity: Critical**

If this invariant is violated and the implementation contract could modify these storage slots, it could change its own
implementation address or admin address, leading to complete compromise of the proxy's security model. The EIP-1967
slots are specifically chosen to be in a range that is extremely unlikely to collide with normal contract storage
layouts.

## Function Specification

### constructor

Initializes the proxy with an admin address.

**Parameters:**
- `_admin`: Address that will have administrative control over the proxy

**Behavior:**
- MUST store `_admin` at the EIP-1967 admin storage slot
- MUST emit `AdminChanged` event with `previousAdmin` as `address(0)` and `newAdmin` as `_admin`

### receive

Accepts ETH transfers and delegates to the implementation.

**Behavior:**
- MUST delegate the call to the implementation contract
- MUST forward all ETH received with the call
- MUST preserve the execution context through delegatecall
- MUST return or revert based on the implementation's response

### fallback

Handles all calls that don't match other function signatures.

**Behavior:**
- MUST delegate the call to the implementation contract
- MUST forward all calldata and ETH with the call
- MUST preserve the execution context through delegatecall
- MUST return the full returndata from the implementation if the call succeeds
- MUST revert with the full returndata from the implementation if the call fails

### upgradeTo

Updates the implementation contract address.

**Parameters:**
- `_implementation`: Address of the new implementation contract

**Behavior:**
- MUST revert if called by any address other than the admin or `address(0)`
- MUST store `_implementation` at the EIP-1967 implementation storage slot
- MUST emit `Upgraded` event with the new implementation address
- MUST delegate to implementation if called by non-admin address

### upgradeToAndCall

Updates the implementation contract and executes an initialization call atomically.

**Parameters:**
- `_implementation`: Address of the new implementation contract
- `_data`: Calldata to delegatecall the new implementation with

**Behavior:**
- MUST revert if called by any address other than the admin or `address(0)`
- MUST store `_implementation` at the EIP-1967 implementation storage slot
- MUST emit `Upgraded` event with the new implementation address
- MUST perform delegatecall to `_implementation` with `_data`
- MUST revert if the delegatecall to the new implementation fails
- MUST return the returndata from the delegatecall if it succeeds
- MUST delegate to implementation if called by non-admin address

### changeAdmin

Transfers admin rights to a new address.

**Parameters:**
- `_admin`: Address of the new admin

**Behavior:**
- MUST revert if called by any address other than the admin or `address(0)`
- MUST store `_admin` at the EIP-1967 admin storage slot
- MUST emit `AdminChanged` event with the previous and new admin addresses
- MUST delegate to implementation if called by non-admin address

### admin

Returns the current admin address.

**Behavior:**
- MUST revert if called by any address other than the admin or `address(0)`
- MUST return the address stored at the EIP-1967 admin storage slot
- MUST delegate to implementation if called by non-admin address

### implementation

Returns the current implementation address.

**Behavior:**
- MUST revert if called by any address other than the admin or `address(0)`
- MUST return the address stored at the EIP-1967 implementation storage slot
- MUST delegate to implementation if called by non-admin address
