# AddressManager

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
- [Assumptions](#assumptions)
  - [a01-001: Owner governance constraints](#a01-001-owner-governance-constraints)
    - [Mitigations](#mitigations)
  - [a01-002: Legacy contract migration](#a01-002-legacy-contract-migration)
    - [Mitigations](#mitigations-1)
- [Dependencies](#dependencies)
- [Invariants](#invariants)
  - [i01-001: Owner-exclusive write access](#i01-001-owner-exclusive-write-access)
    - [Impact](#impact)
  - [i01-002: Unrestricted read access](#i01-002-unrestricted-read-access)
    - [Impact](#impact-1)
  - [i01-003: Name-address mapping persistence](#i01-003-name-address-mapping-persistence)
    - [Impact](#impact-2)
- [Function Specification](#function-specification)
  - [setAddress](#setaddress)
  - [getAddress](#getaddress)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The AddressManager is a legacy contract that maintains a registry mapping string names to addresses. It was used in
the pre-Bedrock version of the Optimism system for contract address resolution. The system now uses a standard proxy
pattern, but this contract remains deployed for backwards compatibility with older contracts that still reference it.

## Definitions

N/A

## Assumptions

### a01-001: Owner governance constraints

The owner operates within governance constraints and does not maliciously set incorrect addresses that would break
dependent legacy contracts.

#### Mitigations

- Owner is typically a multisig or governance contract with established processes
- Address changes emit events for transparency and monitoring
- Legacy contracts depending on this registry are being phased out

### a01-002: Legacy contract migration

Contracts that depend on AddressManager for address resolution are either deprecated, have migrated to the new proxy
system, or are aware that this contract is maintained only for backwards compatibility.

#### Mitigations

- Clear deprecation notices in documentation
- New contracts use the standard proxy pattern instead
- Contract remains deployed to support existing dependencies

## Dependencies

N/A

## Invariants

### i01-001: Owner-exclusive write access

Only the contract owner can modify the name-to-address mappings via `setAddress`.

#### Impact

**Severity: High**

If this invariant were violated, unauthorized parties could modify the address registry, potentially redirecting legacy
contracts to malicious addresses. This would be Critical if assumption [a01-001] fails and the owner is compromised,
as it could lead to complete system compromise for dependent contracts.

### i01-002: Unrestricted read access

Any address can query the registry via `getAddress` without restrictions.

#### Impact

**Severity: Low**

If this invariant were violated and read access were restricted, dependent legacy contracts would fail to resolve
addresses, breaking their functionality. However, since the contract is deprecated and being phased out, the impact
is limited to legacy system components.

### i01-003: Name-address mapping persistence

Once a name-to-address mapping is set, it persists in storage and can be queried. Mappings can be overwritten but
the storage slot remains accessible.

#### Impact

**Severity: Medium**

If this invariant were violated and mappings could be deleted or become inaccessible, legacy contracts relying on
these addresses would fail. The severity is Medium rather than High because the contract is deprecated and the number
of dependent contracts is limited and decreasing.

## Function Specification

### setAddress

Changes the address associated with a string name in the registry.

**Parameters:**
- `_name`: String name to associate with an address
- `_address`: Address to map to the given name (can be zero address)

**Behavior:**
- MUST revert if caller is not the owner
- MUST compute the name hash as `keccak256(abi.encodePacked(_name))`
- MUST store the previous address before updating
- MUST set `addresses[nameHash]` to `_address`
- MUST emit `AddressSet` event with `_name`, `_address`, and the previous address

### getAddress

Retrieves the address associated with a string name.

**Parameters:**
- `_name`: String name to query

**Behavior:**
- MUST compute the name hash as `keccak256(abi.encodePacked(_name))`
- MUST return the address stored at `addresses[nameHash]`
- MUST return the zero address if no mapping exists for the given name
- MUST NOT revert under any circumstances
