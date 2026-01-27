# L2 Contract Upgrades

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [ConditionalDeployer](#conditionaldeployer)
  - [Overview](#overview-1)
  - [Definitions](#definitions)
    - [CREATE2 Collision](#create2-collision)
    - [Deterministic Deployment Proxy](#deterministic-deployment-proxy)
  - [Assumptions](#assumptions)
    - [a01-001: Deterministic Deployment Proxy is Available and Correct](#a01-001-deterministic-deployment-proxy-is-available-and-correct)
      - [Mitigations](#mitigations)
    - [a02-002: Initcode is Well-Formed](#a02-002-initcode-is-well-formed)
      - [Mitigations](#mitigations-1)
  - [Invariants](#invariants)
    - [i01-001: Deterministic Address Derivation](#i01-001-deterministic-address-derivation)
      - [Impact](#impact)
    - [i02-002: Idempotent Deployment Operations](#i02-002-idempotent-deployment-operations)
      - [Impact](#impact-1)
    - [i03-003: Non-Reverting Collision Handling](#i03-003-non-reverting-collision-handling)
      - [Impact](#impact-2)
    - [i04-004: Collision Detection Accuracy](#i04-004-collision-detection-accuracy)
      - [Impact](#impact-3)
- [L2ProxyAdmin](#l2proxyadmin)
  - [Overview](#overview-2)
  - [Definitions](#definitions-1)
    - [Depositor Account](#depositor-account)
    - [Predeploy](#predeploy)
  - [Assumptions](#assumptions-1)
    - [a01-001: Depositor Account is Controlled by Protocol](#a01-001-depositor-account-is-controlled-by-protocol)
      - [Mitigations](#mitigations-2)
    - [a02-002: L2ContractsManager is Trusted](#a02-002-l2contractsmanager-is-trusted)
      - [Mitigations](#mitigations-3)
    - [a03-003: Predeploy Proxies Follow Expected Patterns](#a03-003-predeploy-proxies-follow-expected-patterns)
      - [Mitigations](#mitigations-4)
  - [Invariants](#invariants-1)
    - [i01-001: Exclusive Depositor Authorization for Batch Upgrades](#i01-001-exclusive-depositor-authorization-for-batch-upgrades)
      - [Impact](#impact-4)
    - [i02-002: Safe Delegation to L2ContractsManager](#i02-002-safe-delegation-to-l2contractsmanager)
      - [Impact](#impact-5)
    - [i03-003: Backwards Compatibility Maintained](#i03-003-backwards-compatibility-maintained)
      - [Impact](#impact-6)
    - [i04-004: L2ContractsManager Address Immutability](#i04-004-l2contractsmanager-address-immutability)
      - [Impact](#impact-7)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

This specification defines the mechanism for upgrading L2 predeploy contracts through deterministic, hard fork-driven
Network Upgrade Transactions (NUTs). The system enables safe, well-tested upgrades of L2 contracts with both
implementation and upgrade paths written in Solidity, ensuring determinism, verifiability, and testability across all
client implementations.

The upgrade system maintains the existing pattern of injecting Network Upgrade Transactions at specific fork block
heights while improving the development and testing process. Upgrade transactions are defined in JSON bundles that are
tracked in git, generated from Solidity scripts, and executed deterministically at fork activation.

## ConditionalDeployer

### Overview

The ConditionalDeployer contract enables deterministic deployment of contract implementations while maintaining
idempotency across upgrade transactions. It ensures that unchanged contract bytecode always deploys to the same
address, and that attempting to deploy already-deployed bytecode succeeds silently _rather than reverting_.

This component enables upgrade transactions to unconditionally deploy for all implementation contracts without
requiring developers to manually track which contracts have changed between upgrades.

### Definitions

#### CREATE2 Collision

A CREATE2 collision occurs when attempting to deploy contract bytecode to an address where a contract with identical
bytecode already exists. This happens when the same initcode and salt are used in multiple deployment attempts.

Note: when CREATE2 targets an address that already has code, the
[zero address is placed on the stack][create2-spec] (execution specs).

[create2-spec]:
https://github.com/ethereum/execution-specs/blob/4ef381a0f75c96b52da635653ab580e731d3882a/src/ethereum/forks/prague/vm/instructions/system.py#L112

#### Deterministic Deployment Proxy

The canonical deterministic deployment proxy contract at address `0x4e59b44847b379578588920cA78FbF26c0B4956C`,
originally deployed by Nick Johnson (Arachnid). This contract provides CREATE2-based deployment with a fixed deployer
address across all chains.

Note: when the deterministic deployment proxy deploys to an address that already has code, [it will revert with no data](https://github.com/Arachnid/deterministic-deployment-proxy/blob/be3c5974db5028d502537209329ff2e730ed336c/source/deterministic-deployment-proxy.yul#L13).
Otherwise the ConditionalDeployer would not be required.

### Assumptions

#### a01-001: Deterministic Deployment Proxy is Available and Correct

The [Deterministic Deployment Proxy](#deterministic-deployment-proxy) exists at the expected address and correctly
implements CREATE2 deployment semantics. The proxy must deterministically compute deployment addresses and execute
deployments as specified.

##### Mitigations

- The [Deterministic Deployment Proxy](#deterministic-deployment-proxy) is a well-established contract deployed across
  all EVM chains using the same keyless deployment transaction
- The proxy's behavior is verifiable by inspecting its bytecode and testing deployment operations
- The proxy contract is immutable and cannot be upgraded or modified

#### a02-002: Initcode is Well-Formed

Callers provide valid EVM initcode that, when executed, will either successfully deploy a contract or revert with a
clear error. Malformed initcode that produces undefined behavior is not considered.

##### Mitigations

- Initcode is generated by the Solidity compiler from verified source code
- The upgrade transaction generation process includes validation of all deployment operations
- Fork-based testing exercises all deployments before inclusion in upgrade bundles

### Invariants

#### i01-001: Deterministic Address Derivation

For any given initcode and salt combination, the ConditionalDeployer MUST always compute the same deployment address,
regardless of whether the contract has been previously deployed. The address calculation MUST match the CREATE2
address that would be computed by the [Deterministic Deployment Proxy](#deterministic-deployment-proxy).

##### Impact

**Severity: Critical**

If address derivation is non-deterministic or inconsistent with CREATE2 semantics, upgrade transactions could deploy
implementations to unexpected addresses. This would break proxy upgrade operations that expect implementations at
specific predetermined addresses, potentially causing proxies to point to non-existent or incorrect implementations.

#### i02-002: Idempotent Deployment Operations

Calling the ConditionalDeployer multiple times with identical initcode and salt MUST produce the same outcome: the
first call deploys the contract, and subsequent calls succeed without modification. No operation should revert due to
a [CREATE2 Collision](#create2-collision).

##### Impact

**Severity: Critical**

If deployments are not idempotent, upgrade transactions that attempt to deploy unchanged implementations would revert
or deploy the implementation to an unexpected address. In the latter case, the proxy would then be upgrade incorrectly,
as we must predict the implementation address in advance in order to correctly generate the NUT bundle.

#### i03-003: Non-Reverting Collision Handling

When a [CREATE2 Collision](#create2-collision) is detected (contract already deployed at the target address), the
ConditionalDeployer MUST return successfully without reverting and without modifying blockchain state.

##### Impact

**Severity: Medium**

If the collisions cause reverts, the following transactions can still proceed, however the presence of reverting
transactions in an upgrade block is likely to lead to confusion.

#### i04-004: Collision Detection Accuracy

The ConditionalDeployer MUST correctly distinguish between addresses where no contract exists (deploy needed) and
addresses where a contract already exists (collision detected). False negatives (failing to detect existing contracts)
and false positives (detecting non-existent contracts) are both prohibited.

##### Impact

**Severity: High**

False negatives would cause the ConditionalDeployer to attempt redeployment to occupied addresses, resulting in
failed deployments and breaking the upgrade process. False positives would prevent legitimate deployments from
occurring, causing proxies to reference non-existent implementation addresses.

## L2ProxyAdmin

### Overview

The L2ProxyAdmin is the administrative contract responsible for managing proxy upgrades for L2 predeploy contracts. It
is deployed as a predeploy at address `0x4200000000000000000000000000000000000018` and serves as the `admin` for all
upgradeable L2 predeploy proxies.

The upgraded L2ProxyAdmin implementation extends the existing proxy administration interface with a new
`upgradePredeploys()` function that orchestrates batch upgrades of multiple predeploys by delegating to an
[L2ContractsManager](#l2contractsmanager) contract. This design enables deterministic, testable upgrade paths written
entirely in Solidity.

### Definitions

#### Depositor Account

The special system address `0xDeaDDEaDDeAdDeAdDEAdDEaddeAddEAdDEAd0001` controlled by the L2 protocol's derivation
pipeline. This account is used to submit system transactions including L1 attributes updates and upgrade
transactions.

#### Predeploy

A contract deployed at a predetermined address in the L2 genesis state. Predeploys provide core L2 protocol
functionality and are typically deployed behind proxies to enable upgradability.

### Assumptions

#### a01-001: Depositor Account is Controlled by Protocol

The [Depositor Account](#depositor-account) is exclusively controlled by the L2 protocol's derivation and execution
pipeline. No external parties can submit transactions from this address.

##### Mitigations

- The [Depositor Account](#depositor-account) address has no known private key
- Transactions from this address can only originate from the protocol's derivation pipeline processing L1 deposit events
- The address is hardcoded in the protocol specification and client implementations

#### a02-002: L2ContractsManager is Trusted

The [L2ContractsManager](#l2contractsmanager) contract that receives the DELEGATECALL from `upgradePredeploys()`
correctly implements the upgrade logic and does not perform malicious operations when executing in the context of the
ProxyAdmin.

##### Mitigations

- The L2ContractsManager address is deterministically computed and verified during upgrade bundle generation
- The L2ContractsManager implementation is developed, reviewed, and tested alongside the upgrade bundle
- Fork-based testing validates the complete upgrade execution before production deployment
- The L2ContractsManager bytecode is verifiable against source code on a specific commit

#### a03-003: Predeploy Proxies Follow Expected Patterns

[Predeploys](#predeploy) being upgraded follow the expected proxy patterns (ERC-1967 or similar) and correctly handle
`upgradeTo()` and `upgradeToAndCall()` operations when called by the ProxyAdmin.

##### Mitigations

- All L2 predeploys use standardized proxy implementations from the contracts-bedrock package
- Proxy implementations are thoroughly tested and audited
- Fork-based testing validates upgrade operations against actual deployed proxies

### Invariants

#### i01-001: Exclusive Depositor Authorization for Batch Upgrades

The `upgradePredeploys()` function MUST only be callable by the [Depositor Account](#depositor-account). No other
address, including the current ProxyAdmin owner, can invoke this function.

##### Impact

**Severity: Critical**

If unauthorized addresses could call `upgradePredeploys()`, attackers could execute arbitrary upgrade logic by
deploying a malicious L2ContractsManager and triggering upgrades to compromised implementations. This would allow
complete takeover of all L2 predeploy contracts, enabling theft of funds, manipulation of system configuration, and
protocol-level attacks.

#### i02-002: Safe Delegation to L2ContractsManager

When `upgradePredeploys()` executes a DELEGATECALL to the [L2ContractsManager](#l2contractsmanager), the call MUST
preserve the ProxyAdmin's storage context and MUST properly handle success and failure conditions. The function MUST
revert if the DELEGATECALL fails.

##### Impact

**Severity: Critical**

If the DELEGATECALL is not properly executed, upgrades could fail silently leaving proxies in inconsistent states, or
worse, the ProxyAdmin's own storage could be corrupted. This could result in loss of admin control over predeploys or
enable exploitation of corrupted state.

#### i03-003: Backwards Compatibility Maintained

The upgraded L2ProxyAdmin implementation MUST maintain the existing interface for standard proxy administration
functions. Existing functionality for upgrading individual proxies, changing proxy admins, and querying proxy state
MUST continue to work as before.

##### Impact

**Severity: High**

If backwards compatibility is broken, existing tooling, scripts, and contracts that interact with the ProxyAdmin could
fail. This could prevent emergency responses, break operational procedures, and cause confusion during the transition
to the new upgrade system.

#### i04-004: L2ContractsManager Address Immutability

The address of the [L2ContractsManager](#l2contractsmanager) used by `upgradePredeploys()` MUST be deterministically
provided in the upgrade transaction and MUST NOT be modifiable through storage manipulation during the DELEGATECALL.

##### Impact

**Severity: Critical**

If the L2ContractsManager address could be manipulated, an attacker could redirect the DELEGATECALL to a malicious
contract, achieving the same impact as i01-001 (complete compromise of all predeploys).

