# OPContractsManager

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
  - [System](#system)
  - [Contract Release](#contract-release)
  - [OPCM Version](#opcm-version)
  - [Extra Instructions](#extra-instructions)
  - [Superchain ProxyAdmin Owner](#superchain-proxyadmin-owner)
- [Assumptions](#assumptions)
  - [a01-001: Ethereum Environment](#a01-001-ethereum-environment)
    - [Mitigations](#mitigations)
  - [a01-002: Implementation Contracts Trusted](#a01-002-implementation-contracts-trusted)
    - [Mitigations](#mitigations-1)
  - [a01-003: Code at Release Commit is Safe](#a01-003-code-at-release-commit-is-safe)
    - [Mitigations](#mitigations-2)
  - [a01-004: ProxyAdmin Owner Trusted for Upgrades](#a01-004-proxyadmin-owner-trusted-for-upgrades)
    - [Mitigations](#mitigations-3)
  - [a01-005: Superchain ProxyAdmin Owner Trusted](#a01-005-superchain-proxyadmin-owner-trusted)
    - [Mitigations](#mitigations-4)
- [Invariants](#invariants)
  - [i01-001: Code Integrity](#i01-001-code-integrity)
    - [Impact](#impact)
  - [i01-002: Atomicity](#i01-002-atomicity)
    - [Impact](#impact-1)
  - [i01-003: No Unexpected Mutations](#i01-003-no-unexpected-mutations)
    - [Impact](#impact-2)
  - [i01-004: Upgrade Ordering](#i01-004-upgrade-ordering)
    - [Impact](#impact-3)
  - [i01-005: Initialization Safety](#i01-005-initialization-safety)
    - [Impact](#impact-4)
  - [i01-006: SuperchainConfig Backwards Compatibility](#i01-006-superchainconfig-backwards-compatibility)
    - [Impact](#impact-5)
  - [i01-007: Single Operation Gas Feasibility](#i01-007-single-operation-gas-feasibility)
    - [Impact](#impact-6)
  - [i01-008: Batch Operation Gas Efficiency](#i01-008-batch-operation-gas-efficiency)
    - [Impact](#impact-7)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

OPContractsManager (OPCM) is the contract that defines network upgrades for OP Stack smart contracts.
Each OPCM instance represents a specific [Contract Release](#contract-release) and holds immutable
references to the implementation contracts for that release.

OPCM provides three core capabilities:

- **System Deployment**: Deploying all contracts for a new OP Stack [System](#system) at the
  version the OPCM represents. This capability is permissionless.
- **System Upgrade**: Upgrading an existing [System](#system) to the version the OPCM represents.
  This capability is designed to be invoked via delegatecall by the ProxyAdmin owner, as OPCM
  itself holds no special authority.
- **SuperchainConfig Upgrade**: Upgrading the SuperchainConfig contract. This capability is
  designed to be invoked via delegatecall by the
  [Superchain ProxyAdmin Owner](#superchain-proxyadmin-owner).

OPCM is fully immutable with no mutable state. Implementation addresses are set at deployment time
and cannot be changed.

## Definitions

### System

All of the smart contracts that comprise a single OP Stack chain, including but not limited to
SystemConfig, OptimismPortal, L1CrossDomainMessenger, L1StandardBridge, DisputeGameFactory, and
associated proxy contracts.

### Contract Release

The version identifier for an OP Stack smart contracts release, following the format
`op-contracts/vX.Y.Z`. Each Contract Release uses a specific [OPCM Version](#opcm-version).

### OPCM Version

The version of the OPContractsManager contract itself, which may differ from the
[Contract Release](#contract-release) version. The OPCM Version reflects the capabilities and
interface of the upgrader rather than the contracts it deploys.

### Extra Instructions

A migration mechanism used during upgrades to bootstrap new state that has no predecessor value.
When an upgrade introduces a new variable that did not exist in the previous version, Extra
Instructions allow users to provide initial values for these variables. Extra Instructions are
specific to the OPCM that defines them and must not apply to OPCMs of higher major versions.

### Superchain ProxyAdmin Owner

The ProxyAdmin owner for the SuperchainConfig contract. Since SuperchainConfig is shared across
multiple chains on a network (many-to-one relationship), it has its own governance-controlled
ProxyAdmin owner separate from individual chain ProxyAdmin owners.

## Assumptions

### a01-001: Ethereum Environment

OPCM is designed to run on Ethereum networks. Behavior on non-Ethereum EVM chains is not guaranteed.

#### Mitigations

- Documentation clearly states Ethereum as the target environment
- Testing is performed against Ethereum mainnet and official testnets

### a01-002: Implementation Contracts Trusted

The implementation contracts referenced by OPCM are trusted and correct for the release they
represent.

#### Mitigations

- Implementation contracts are deployed through audited deployment scripts
- Verification scripts confirm deployed bytecode matches the release commit
- Implementation addresses are immutable once OPCM is deployed

### a01-003: Code at Release Commit is Safe

The code at the GitHub commit that the [Contract Release](#contract-release) represents is safe
and has not been tampered with.

#### Mitigations

- Release commits undergo security audits
- Multiple reviewers approve release commits
- Cryptographic signatures verify commit integrity

### a01-004: ProxyAdmin Owner Trusted for Upgrades

The ProxyAdmin owner invoking system upgrades is trusted and operating within governance
constraints.

#### Mitigations

- System upgrade capability only functions when delegatecalled, as OPCM holds no authority itself
- ProxyAdmin ownership is typically controlled by governance multisigs
- Upgrade transactions are subject to timelock delays where applicable

### a01-005: Superchain ProxyAdmin Owner Trusted

The [Superchain ProxyAdmin Owner](#superchain-proxyadmin-owner) is trusted and operating within
governance constraints when upgrading SuperchainConfig.

#### Mitigations

- SuperchainConfig upgrade capability only functions when delegatecalled
- Superchain governance controls the Superchain ProxyAdmin Owner
- SuperchainConfig changes affect multiple chains, requiring heightened governance scrutiny

## Invariants

### i01-001: Code Integrity

OPCM must faithfully deploy or upgrade to the code at the GitHub commit that the
[Contract Release](#contract-release) was created at. OPCM must not deploy code that is not
present in that commit.

#### Impact

**Severity: Critical**

If violated, malicious or incorrect code could be deployed to production systems, potentially
resulting in loss of funds, unauthorized access, or system compromise across all affected chains.

### i01-002: Atomicity

System deployment and upgrade operations must be atomic. They either fully succeed or fully
revert with no partial state changes.

#### Impact

**Severity: Critical**

If violated, a [System](#system) could be left in an inconsistent state where some contracts are
upgraded and others are not, potentially breaking cross-contract invariants and rendering the
system unusable or insecure.

### i01-003: No Unexpected Mutations

During system deployment or upgrade, system variables must never be mutated unless one of the
following conditions is met:

1. The user explicitly supplies an input requesting that change
2. OPCM deliberately mutates the value with clear documentation explaining why the mutation is
   necessary, and the change is safe to make

Properties such as ProxyAdmin ownership must be fetched from the existing system during upgrades
and preserved without modification.

#### Impact

**Severity: High/Critical**

If violated, upgrades could silently change critical system properties like ownership, potentially
transferring control to unauthorized parties or breaking the security model of the system.

### i01-004: Upgrade Ordering

Chains must follow the correct upgrade flow. Valid upgrade paths are:

- Same major version to a higher minor version (e.g., v1.2.0 to v1.3.0)
- Current major version to the next major version (e.g., v1.x.y to v2.0.0)

Downgrades and skipping required OPCMs are not permitted.

#### Impact

**Severity: High/Critical**

If violated, chains could skip critical migration steps or security patches, potentially leaving
them in an unsupported or vulnerable state that diverges from the expected upgrade path.

### i01-005: Initialization Safety

Contracts deployed or upgraded by OPCM must never be left uninitialized or open to initialization
by unauthorized parties.

#### Impact

**Severity: High/Critical**

If violated, attackers could initialize contracts with malicious parameters, potentially taking
ownership of critical system components or corrupting system state.

### i01-006: SuperchainConfig Backwards Compatibility

SuperchainConfig must maintain backwards compatibility with all past versions of the OP Stack.

#### Impact

**Severity: High**

If violated, chains running older OP Stack versions that depend on SuperchainConfig could break,
potentially halting operations for multiple chains simultaneously.

### i01-007: Single Operation Gas Feasibility

Given valid parameters, a single system deployment or upgrade operation must always be executable
within the gas limits of an Ethereum block.

#### Impact

**Severity: High**

If violated, it would be impossible to deploy new chains or upgrade existing chains, effectively
breaking the core functionality of OPCM and blocking all future upgrades.

### i01-008: Batch Operation Gas Efficiency

Multiple upgrade operations (approximately 5) should be executable within a single transaction.

#### Impact

**Severity: Low**

If violated, upgrading multiple chains would require separate transactions, increasing operational
complexity and cost but not blocking functionality.
