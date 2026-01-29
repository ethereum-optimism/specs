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
    - [aCD-001: Deterministic Deployment Proxy is Available and Correct](#acd-001-deterministic-deployment-proxy-is-available-and-correct)
      - [Mitigations](#mitigations)
    - [aCD-002: Initcode is Well-Formed](#acd-002-initcode-is-well-formed)
      - [Mitigations](#mitigations-1)
  - [Invariants](#invariants)
    - [iCD-001: Deterministic Address Derivation](#icd-001-deterministic-address-derivation)
      - [Impact](#impact)
    - [iCD-002: Idempotent Deployment Operations](#icd-002-idempotent-deployment-operations)
      - [Impact](#impact-1)
    - [iCD-003: Non-Reverting Collision Handling](#icd-003-non-reverting-collision-handling)
      - [Impact](#impact-2)
    - [iCD-004: Collision Detection Accuracy](#icd-004-collision-detection-accuracy)
      - [Impact](#impact-3)
- [L2ProxyAdmin](#l2proxyadmin)
  - [Overview](#overview-2)
  - [Definitions](#definitions-1)
    - [Depositor Account](#depositor-account)
    - [Predeploy](#predeploy)
  - [Assumptions](#assumptions-1)
    - [aL2PA-001: Depositor Account is Controlled by Protocol](#al2pa-001-depositor-account-is-controlled-by-protocol)
      - [Mitigations](#mitigations-2)
    - [aL2PA-002: L2ContractsManager is Trusted](#al2pa-002-l2contractsmanager-is-trusted)
      - [Mitigations](#mitigations-3)
    - [aL2PA-003: Predeploy Proxies Follow Expected Patterns](#al2pa-003-predeploy-proxies-follow-expected-patterns)
      - [Mitigations](#mitigations-4)
  - [Invariants](#invariants-1)
    - [iL2PA-001: Exclusive Depositor Authorization for Batch Upgrades](#il2pa-001-exclusive-depositor-authorization-for-batch-upgrades)
      - [Impact](#impact-4)
    - [iL2PA-002: Safe Delegation to L2ContractsManager](#il2pa-002-safe-delegation-to-l2contractsmanager)
      - [Impact](#impact-5)
    - [iL2PA-003: Backwards Compatibility Maintained](#il2pa-003-backwards-compatibility-maintained)
      - [Impact](#impact-6)
    - [iL2PA-004: L2ContractsManager Address Immutability](#il2pa-004-l2contractsmanager-address-immutability)
      - [Impact](#impact-7)
- [L2ContractsManager](#l2contractsmanager)
  - [Overview](#overview-3)
  - [Definitions](#definitions-2)
    - [Network-Specific Configuration](#network-specific-configuration)
    - [Feature Flag](#feature-flag)
    - [Initialization Parameters](#initialization-parameters)
  - [Assumptions](#assumptions-2)
    - [aL2CM-001: Existing Predeploys Provide Valid Configuration](#al2cm-001-existing-predeploys-provide-valid-configuration)
      - [Mitigations](#mitigations-5)
    - [aL2CM-002: Implementation Addresses Are Pre-Computed Correctly](#al2cm-002-implementation-addresses-are-pre-computed-correctly)
      - [Mitigations](#mitigations-6)
    - [aL2CM-003: Predeploy Proxies Are Upgradeable](#al2cm-003-predeploy-proxies-are-upgradeable)
      - [Mitigations](#mitigations-7)
    - [aL2CM-004: Feature Flags Are Correctly Configured](#al2cm-004-feature-flags-are-correctly-configured)
      - [Mitigations](#mitigations-8)
  - [Invariants](#invariants-2)
    - [iL2CM-001: Deterministic Upgrade Execution](#il2cm-001-deterministic-upgrade-execution)
      - [Impact](#impact-8)
    - [iL2CM-002: Configuration Preservation](#il2cm-002-configuration-preservation)
      - [Impact](#impact-9)
    - [iL2CM-003: Upgrade Atomicity](#il2cm-003-upgrade-atomicity)
      - [Impact](#impact-10)
    - [iL2CM-004: Correct Upgrade Method Selection](#il2cm-004-correct-upgrade-method-selection)
      - [Impact](#impact-11)
    - [iL2CM-005: No Storage Corruption During DELEGATECALL](#il2cm-005-no-storage-corruption-during-delegatecall)
      - [Impact](#impact-12)
    - [iL2CM-006: Complete Upgrade Coverage](#il2cm-006-complete-upgrade-coverage)
      - [Impact](#impact-13)
- [Network Upgrade Transaction Bundle](#network-upgrade-transaction-bundle)
  - [Overview](#overview-4)
  - [Definitions](#definitions-3)
    - [Network Upgrade Transaction (NUT)](#network-upgrade-transaction-nut)
    - [Fork Activation Block](#fork-activation-block)
    - [Bundle Generation Script](#bundle-generation-script)
    - [Transaction Nonce](#transaction-nonce)
  - [Assumptions](#assumptions-3)
    - [aNUTB-001: Solidity Compiler is Deterministic](#anutb-001-solidity-compiler-is-deterministic)
      - [Mitigations](#mitigations-9)
    - [aNUTB-002: Bundle Generation Script is Pure](#anutb-002-bundle-generation-script-is-pure)
      - [Mitigations](#mitigations-10)
    - [aNUTB-003: Git Repository is Authoritative Source](#anutb-003-git-repository-is-authoritative-source)
      - [Mitigations](#mitigations-11)
    - [aNUTB-004: JSON Format is Correctly Parsed](#anutb-004-json-format-is-correctly-parsed)
      - [Mitigations](#mitigations-12)
  - [Invariants](#invariants-3)
    - [iNUTB-001: Deterministic Bundle Generation](#inutb-001-deterministic-bundle-generation)
      - [Impact](#impact-14)
    - [iNUTB-002: Transaction Completeness](#inutb-002-transaction-completeness)
      - [Impact](#impact-15)
    - [iNUTB-003: Transaction Ordering](#inutb-003-transaction-ordering)
      - [Impact](#impact-16)
    - [iNUTB-004: Correct Nonce Sequencing](#inutb-004-correct-nonce-sequencing)
      - [Impact](#impact-17)
    - [iNUTB-005: Verifiable Against Source Code](#inutb-005-verifiable-against-source-code)
      - [Impact](#impact-18)
    - [iNUTB-006: Valid Transaction Format](#inutb-006-valid-transaction-format)
      - [Impact](#impact-19)
  - [Bundle Format](#bundle-format)
  - [Bundle Generation Process](#bundle-generation-process)
  - [Bundle Verification Process](#bundle-verification-process)
- [Custom Upgrade Block Gas Limit](#custom-upgrade-block-gas-limit)
  - [Overview](#overview-5)
  - [Definitions](#definitions-4)
    - [System Transaction Gas Limit](#system-transaction-gas-limit)
    - [Upgrade Block Gas Allocation](#upgrade-block-gas-allocation)
    - [Derivation Pipeline](#derivation-pipeline)
  - [Assumptions](#assumptions-4)
    - [aUBGL-001: Upgrade Gas Requirements Are Bounded](#aubgl-001-upgrade-gas-requirements-are-bounded)
      - [Mitigations](#mitigations-13)
    - [aUBGL-002: Derivation Pipeline Correctly Allocates Gas](#aubgl-002-derivation-pipeline-correctly-allocates-gas)
      - [Mitigations](#mitigations-14)
    - [aUBGL-003: Custom Gas Does Not Affect Consensus](#aubgl-003-custom-gas-does-not-affect-consensus)
      - [Mitigations](#mitigations-15)
  - [Invariants](#invariants-4)
    - [iUBGL-001: Sufficient Gas Availability](#iubgl-001-sufficient-gas-availability)
      - [Impact](#impact-20)
    - [iUBGL-002: Deterministic Gas Allocation](#iubgl-002-deterministic-gas-allocation)
      - [Impact](#impact-21)
    - [iUBGL-003: Gas Limit Independence from Block Gas Limit](#iubgl-003-gas-limit-independence-from-block-gas-limit)
      - [Impact](#impact-22)
    - [iUBGL-004: Gas Allocation Only for Upgrade Blocks](#iubgl-004-gas-allocation-only-for-upgrade-blocks)
      - [Impact](#impact-23)
    - [iUBGL-005: No Gas Refund Exploitation](#iubgl-005-no-gas-refund-exploitation)
      - [Impact](#impact-24)
  - [Gas Allocation Specification](#gas-allocation-specification)
- [Upgrade Process](#upgrade-process)
  - [Overview](#overview-6)
  - [Definitions](#definitions-5)
    - [Fork Activation Timestamp](#fork-activation-timestamp)
    - [Upgrade Transaction Execution Order](#upgrade-transaction-execution-order)
  - [Assumptions](#assumptions-5)
    - [aUP-001: Fork Activation Time is Coordinated](#aup-001-fork-activation-time-is-coordinated)
      - [Mitigations](#mitigations-16)
    - [aUP-002: Node Operators Update Client Software](#aup-002-node-operators-update-client-software)
      - [Mitigations](#mitigations-17)
    - [aUP-003: Testing Environments Match Production](#aup-003-testing-environments-match-production)
      - [Mitigations](#mitigations-18)
  - [Invariants](#invariants-5)
    - [iUP-001: Atomic Upgrade Execution](#iup-001-atomic-upgrade-execution)
      - [Impact](#impact-25)
    - [iUP-002: Consistent Cross-Chain Execution](#iup-002-consistent-cross-chain-execution)
      - [Impact](#impact-26)
    - [iUP-003: Upgrade Transactions Execute Before User Transactions](#iup-003-upgrade-transactions-execute-before-user-transactions)
      - [Impact](#impact-27)
    - [iUP-004: Fork Activation is Irreversible](#iup-004-fork-activation-is-irreversible)
      - [Impact](#impact-28)
    - [iUP-005: Verifiable Upgrade Execution](#iup-005-verifiable-upgrade-execution)
      - [Impact](#impact-29)
  - [Upgrade Lifecycle](#upgrade-lifecycle)
    - [Phase 1: Development](#phase-1-development)
    - [Phase 2: Bundle Generation](#phase-2-bundle-generation)
    - [Phase 3: Testing](#phase-3-testing)
    - [Phase 4: Review and Approval](#phase-4-review-and-approval)
    - [Phase 5: Preparation](#phase-5-preparation)
    - [Phase 6: Execution](#phase-6-execution)
    - [Phase 7: Verification](#phase-7-verification)
  - [Transaction Execution Sequence](#transaction-execution-sequence)

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

#### aCD-001: Deterministic Deployment Proxy is Available and Correct

The [Deterministic Deployment Proxy](#deterministic-deployment-proxy) exists at the expected address and correctly
implements CREATE2 deployment semantics. The proxy must deterministically compute deployment addresses and execute
deployments as specified.

##### Mitigations

- The [Deterministic Deployment Proxy](#deterministic-deployment-proxy) is a well-established contract deployed across
  all EVM chains using the same keyless deployment transaction
- The proxy's behavior is verifiable by inspecting its bytecode and testing deployment operations
- The proxy contract is immutable and cannot be upgraded or modified

#### aCD-002: Initcode is Well-Formed

Callers provide valid EVM initcode that, when executed, will either successfully deploy a contract or revert with a
clear error. Malformed initcode that produces undefined behavior is not considered.

##### Mitigations

- Initcode is generated by the Solidity compiler from verified source code
- The upgrade transaction generation process includes validation of all deployment operations
- Fork-based testing exercises all deployments before inclusion in upgrade bundles

### Invariants

#### iCD-001: Deterministic Address Derivation

For any given initcode and salt combination, the ConditionalDeployer MUST always compute the same deployment address,
regardless of whether the contract has been previously deployed. The address calculation MUST match the CREATE2
address that would be computed by the [Deterministic Deployment Proxy](#deterministic-deployment-proxy).

##### Impact

**Severity: Critical**

If address derivation is non-deterministic or inconsistent with CREATE2 semantics, upgrade transactions could deploy
implementations to unexpected addresses, breaking proxy upgrade operations.

#### iCD-002: Idempotent Deployment Operations

Calling the ConditionalDeployer multiple times with identical initcode and salt MUST produce the same outcome: the
first call deploys the contract, and subsequent calls succeed without modification. No operation should revert due to
a [CREATE2 Collision](#create2-collision).

##### Impact

**Severity: Critical**

If deployments are not idempotent, upgrade transactions that attempt to deploy unchanged implementations would revert
or deploy the implementation to an unexpected address, breaking the upgrade.

#### iCD-003: Non-Reverting Collision Handling

When a [CREATE2 Collision](#create2-collision) is detected (contract already deployed at the target address), the
ConditionalDeployer MUST return successfully without reverting and without modifying blockchain state.

##### Impact

**Severity: Medium**

If collisions cause reverts, the presence of reverting transactions in an upgrade block would cause confusion.

#### iCD-004: Collision Detection Accuracy

The ConditionalDeployer MUST correctly distinguish between addresses where no contract exists (deploy needed) and
addresses where a contract already exists (collision detected). False negatives (failing to detect existing contracts)
and false positives (detecting non-existent contracts) are both prohibited.

##### Impact

**Severity: High**

False negatives would cause failed deployments while false positives would prevent legitimate deployments, both
breaking the upgrade process.

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

#### aL2PA-001: Depositor Account is Controlled by Protocol

The [Depositor Account](#depositor-account) is exclusively controlled by the L2 protocol's derivation and execution
pipeline. No external parties can submit transactions from this address.

##### Mitigations

- The [Depositor Account](#depositor-account) address has no known private key
- Transactions from this address can only originate from the protocol's derivation pipeline processing L1 deposit events
- The address is hardcoded in the protocol specification and client implementations

#### aL2PA-002: L2ContractsManager is Trusted

The [L2ContractsManager](#l2contractsmanager) contract that receives the DELEGATECALL from `upgradePredeploys()`
correctly implements the upgrade logic and does not perform malicious operations when executing in the context of the
ProxyAdmin.

##### Mitigations

- The L2ContractsManager address is deterministically computed and verified during upgrade bundle generation
- The L2ContractsManager implementation is developed, reviewed, and tested alongside the upgrade bundle
- Fork-based testing validates the complete upgrade execution before production deployment
- The L2ContractsManager bytecode is verifiable against source code on a specific commit

#### aL2PA-003: Predeploy Proxies Follow Expected Patterns

[Predeploys](#predeploy) being upgraded follow the expected proxy patterns (ERC-1967 or similar) and correctly handle
`upgradeTo()` and `upgradeToAndCall()` operations when called by the ProxyAdmin.

##### Mitigations

- All L2 predeploys use standardized proxy implementations from the contracts-bedrock package
- Proxy implementations are thoroughly tested and audited
- Fork-based testing validates upgrade operations against actual deployed proxies

### Invariants

#### iL2PA-001: Exclusive Depositor Authorization for Batch Upgrades

The `upgradePredeploys()` function MUST only be callable by the [Depositor Account](#depositor-account). No other
address, including the current ProxyAdmin owner, can invoke this function.

##### Impact

**Severity: Critical**

If unauthorized addresses could call `upgradePredeploys()`, attackers could execute arbitrary upgrade logic by
deploying a malicious L2ContractsManager, enabling complete takeover of all L2 predeploy contracts.

#### iL2PA-002: Safe Delegation to L2ContractsManager

When `upgradePredeploys()` executes a DELEGATECALL to the [L2ContractsManager](#l2contractsmanager), the call MUST
preserve the ProxyAdmin's storage context and MUST properly handle success and failure conditions. The function MUST
revert if the DELEGATECALL fails.

##### Impact

**Severity: Critical**

If the DELEGATECALL is not properly executed, upgrades could fail silently or the ProxyAdmin's storage could be
corrupted, resulting in loss of admin control over predeploys.

#### iL2PA-003: Backwards Compatibility Maintained

The upgraded L2ProxyAdmin implementation MUST maintain the existing interface for standard proxy administration
functions. Existing functionality for upgrading individual proxies, changing proxy admins, and querying proxy state
MUST continue to work as before.

##### Impact

**Severity: High**

If backwards compatibility is broken, existing tooling and scripts that interact with the ProxyAdmin could fail,
preventing emergency responses and breaking operational procedures.

#### iL2PA-004: L2ContractsManager Address Immutability

The address of the [L2ContractsManager](#l2contractsmanager) used by `upgradePredeploys()` MUST be deterministically
provided in the upgrade transaction and MUST NOT be modifiable through storage manipulation during the DELEGATECALL.

##### Impact

**Severity: Critical**

If the L2ContractsManager address could be manipulated, an attacker could redirect the DELEGATECALL to a malicious
contract, achieving complete compromise of all predeploys.

## L2ContractsManager

### Overview

The L2ContractsManager is a contract deployed fresh for each upgrade that contains the upgrade logic and coordination
for a specific set of predeploy upgrades. When invoked via DELEGATECALL from the [L2ProxyAdmin](#l2proxyadmin), it
gathers network-specific configuration from existing predeploys, computes new implementation addresses, and executes
upgrade operations for all affected predeploys.

Each L2ContractsManager instance is purpose-built for a specific upgrade, deployed via the
[ConditionalDeployer](#conditionaldeployer), and referenced directly in the upgrade transaction. The contract is
stateless and contains all upgrade logic in code, ensuring determinism and verifiability.

### Definitions

#### Network-Specific Configuration

Configuration values that vary between L2 chains, such as custom gas token parameters, operator fee configurations, or
chain-specific feature flags. These values are typically stored in system predeploys like `L1Block` and must be
preserved across upgrades.

#### Feature Flag

A boolean or enumerated value that enables or disables optional protocol features. Feature flags allow different
upgrade paths for development environments (alphanets), testing environments, and production chains. Flags are read
from a dedicated FeatureFlags contract during upgrade execution.

#### Initialization Parameters

Constructor arguments or initializer function parameters required by a predeploy implementation. When a predeploy's
implementation changes and requires new or updated initialization, the L2ContractsManager must call
`upgradeToAndCall()` instead of `upgradeTo()` to pass these parameters.

### Assumptions

#### aL2CM-001: Existing Predeploys Provide Valid Configuration

The existing [predeploy](#predeploy) contracts contain valid [network-specific configuration](#network-specific-configuration)
that can be read and used during the upgrade. Configuration values are accurate, properly formatted, and represent the
intended chain configuration.

##### Mitigations

- Configuration is read from well-established predeploys that have been operating correctly
- Fork-based testing validates configuration gathering against real chain state
- The upgrade will fail deterministically if configuration reads return unexpected values
- Configuration values are validated during the upgrade process

#### aL2CM-002: Implementation Addresses Are Pre-Computed Correctly

The implementation addresses referenced by the L2ContractsManager are correctly pre-computed using the same CREATE2
parameters that will be used by the [ConditionalDeployer](#conditionaldeployer). Address mismatches would cause
proxies to point to incorrect or non-existent implementations.

##### Mitigations

- Implementation addresses are computed using deterministic CREATE2 formula during bundle generation
- The same address computation logic is used in both bundle generation and the L2ContractsManager
- Fork-based testing validates that all implementation addresses exist and contain expected bytecode
- Address computation is isolated in shared libraries to prevent divergence

#### aL2CM-003: Predeploy Proxies Are Upgradeable

All [predeploy](#predeploy) proxies targeted for upgrade support the `upgradeTo()` and `upgradeToAndCall()` functions
and will accept upgrade calls from the [L2ProxyAdmin](#l2proxyadmin) executing the DELEGATECALL.

##### Mitigations

- All L2 predeploys use standardized proxy implementations with well-tested upgrade functions
- Fork-based testing exercises upgrade operations against actual deployed proxies
- Non-upgradeable predeploys are excluded from the upgrade process

#### aL2CM-004: Feature Flags Are Correctly Configured

When [feature flags](#feature-flag) are used to customize upgrade behavior, the FeatureFlags contract is properly
configured in the test/development environment and returns consistent values throughout the upgrade execution.

##### Mitigations

- Feature flag values are set using `vm.etch()` and `vm.store()` in forge-based test environments
- Feature flag reads are idempotent and cannot be modified during upgrade execution
- Production upgrades do not rely on feature flags; flags are only used in development/test environments
- Fork tests validate feature flag behavior across different configurations

### Invariants

#### iL2CM-001: Deterministic Upgrade Execution

The L2ContractsManager's `upgrade()` function MUST execute deterministically, producing identical state changes when
given identical pre-upgrade blockchain state. The function MUST NOT read external state that could vary between
executions (timestamps, block hashes, etc.) and MUST NOT accept runtime parameters.

##### Impact

**Severity: Critical**

If upgrade execution is non-deterministic, different L2 nodes could produce different post-upgrade states, causing
consensus failures and halting the chain.

#### iL2CM-002: Configuration Preservation

All [network-specific configuration](#network-specific-configuration) that exists before the upgrade MUST be preserved
in the upgraded predeploy implementations. Configuration values MUST be read from existing predeploys and properly
passed to new implementations during upgrade.

##### Impact

**Severity: Critical**

If configuration is not preserved, chains could lose critical settings like custom gas token addresses or operator fee
parameters, breaking fee calculations and chain-specific functionality.

#### iL2CM-003: Upgrade Atomicity

All predeploy upgrades within a single L2ContractsManager execution MUST succeed or fail atomically. If any upgrade
operation fails, the entire DELEGATECALL MUST revert, leaving all predeploys in their pre-upgrade state.

##### Impact

**Severity: Critical**

If upgrades are not atomic, a partial failure could leave some predeploys upgraded and others not, creating an
inconsistent system state that breaks inter-contract dependencies.

#### iL2CM-004: Correct Upgrade Method Selection

For each predeploy being upgraded, the L2ContractsManager MUST correctly choose between `upgradeTo()` (for
implementations with no new initialization) and `upgradeToAndCall()` (for implementations requiring initialization).
The selection MUST match the requirements of the new implementation.

##### Impact

**Severity: Critical**

If the wrong upgrade method is used, implementations requiring initialization would not be properly initialized or
unnecessary initialization calls could trigger reverts, breaking critical system contracts.

#### iL2CM-005: No Storage Corruption During DELEGATECALL

When executing in the [L2ProxyAdmin](#l2proxyadmin) context via DELEGATECALL, the L2ContractsManager MUST NOT corrupt
or modify the ProxyAdmin's own storage. All storage modifications must be directed to the predeploy proxies being
upgraded.

##### Impact

**Severity: Critical**

If the L2ContractsManager corrupts ProxyAdmin storage, it could change the ProxyAdmin's owner or disable future upgrade
capability, compromising the entire upgrade system.

#### iL2CM-006: Complete Upgrade Coverage

The L2ContractsManager MUST upgrade all predeploys intended for the upgrade. It MUST NOT skip predeploys that should
be upgraded, even if their implementations are unchanged, to maintain consistency across all chains executing the
upgrade.

##### Impact

**Severity: High**

If predeploys are skipped incorrectly, chains would have inconsistent contract versions, violating the goal of bringing
all chains to a consistent version.

## Network Upgrade Transaction Bundle

### Overview

The Network Upgrade Transaction (NUT) Bundle is a JSON-formatted data structure containing the complete set of
transactions that must be executed at a specific fork activation block. The bundle is generated deterministically from
Solidity scripts, tracked in git, and executed by all L2 client implementations to upgrade predeploy contracts.

The bundle format enables verification that upgrade transactions correspond to specific source code commits, ensuring
transparency and auditability across all OP Stack chains executing the upgrade.

### Definitions

#### Network Upgrade Transaction (NUT)

A system transaction injected by the protocol at a specific fork block height, executed with the
[Depositor Account](#depositor-account) as the sender. These transactions bypass normal transaction pool processing and
are deterministically included in the fork activation block.

#### Fork Activation Block

The L2 block at which a protocol upgrade becomes active, identified by a specific L2 block timestamp. This block
contains the Network Upgrade Transactions that implement the protocol changes.

#### Bundle Generation Script

A Solidity script (typically using Forge scripting) that deterministically computes all transaction data for an
upgrade. The script deploys contracts, computes addresses, and assembles transaction calldata without relying on
execution in an EVM environment.

#### Transaction Nonce

The nonce value used for transactions sent by the [Depositor Account](#depositor-account). For upgrade transactions,
nonces must be correctly sequenced to ensure all transactions execute in the proper order within the fork activation
block.

### Assumptions

#### aNUTB-001: Solidity Compiler is Deterministic

The Solidity compiler produces identical bytecode when given identical source code and compiler settings. This enables
verification that bundle contents match the source code on a specific commit.

##### Mitigations

- Use pinned compiler versions specified in foundry.toml
- Compiler determinism is a core property of the Solidity toolchain
- Bundle generation includes compiler version and settings in metadata
- Verification process rebuilds contracts with identical settings and compares bytecode

#### aNUTB-002: Bundle Generation Script is Pure

The [bundle generation script](#bundle-generation-script) does not depend on external state that could vary between
executions. All addresses are computed deterministically using CREATE2, and all transaction data is derived from
compiled bytecode.

##### Mitigations

- Bundle generation scripts are reviewed to ensure they contain no external dependencies
- Scripts use only deterministic address computation (CREATE2)
- Fork-based testing validates that generated bundles match expected outputs
- CI validates bundle regeneration produces identical output

#### aNUTB-003: Git Repository is Authoritative Source

The git repository containing the bundle JSON files and source code serves as the authoritative source of truth for
upgrade transactions. The commit hash provides an immutable reference to the exact code that generated the bundle.

##### Mitigations

- Bundles are committed to git alongside the source code that generates them
- The generation script commit hash is included in bundle metadata
- Repository is hosted on GitHub with branch protection and audit logs
- Multiple reviewers verify bundle contents before merge

#### aNUTB-004: JSON Format is Correctly Parsed

All L2 client implementations (Go, Rust, etc.) correctly parse the JSON bundle format and extract transaction fields
identically. Parsing inconsistencies would cause consensus failures.

##### Mitigations

- JSON schema is simple and uses standard field types
- Test vectors validate parsing across client implementations
- Fork-based testing exercises bundle execution in reference implementation
- Bundle format follows existing NUT patterns used in previous forks

### Invariants

#### iNUTB-001: Deterministic Bundle Generation

Running the [bundle generation script](#bundle-generation-script) multiple times on the same source code commit MUST
produce byte-for-byte identical JSON output. No aspect of bundle generation may depend on timestamps, random values, or
external state.

##### Impact

**Severity: Critical**

If bundle generation is non-deterministic, it becomes impossible to verify that a given bundle corresponds to specific
source code, potentially allowing unverified or malicious transactions to be included.

#### iNUTB-002: Transaction Completeness

The bundle MUST contain all transactions required to complete the upgrade. Missing transactions would cause the upgrade
to fail partially, leaving the system in an inconsistent state.

##### Impact

**Severity: Critical**

If the bundle is incomplete, the fork activation would fail, potentially halting the chain or leaving predeploys in
partially upgraded states.

#### iNUTB-003: Transaction Ordering

Transactions in the bundle MUST be ordered such that dependencies are satisfied. For example, contract deployments MUST
occur before transactions that call those contracts.

##### Impact

**Severity: Critical**

If transactions are misordered, executions will fail when attempting to call non-existent contracts, causing the entire
upgrade to fail at fork activation and halt the chain.

#### iNUTB-004: Correct Nonce Sequencing

Transaction nonces for the [Depositor Account](#depositor-account) MUST form a contiguous sequence with no gaps or
duplicates. Each transaction must use the next available nonce.

##### Impact

**Severity: Critical**

If nonces are incorrect, transactions will fail to execute or execute in wrong order, causing the upgrade to fail.

#### iNUTB-005: Verifiable Against Source Code

Given the source code at a specific git commit, it MUST be possible to rebuild contracts, regenerate the bundle, and
verify that it matches the committed bundle byte-for-byte.

##### Impact

**Severity: High**

If bundles cannot be verified against source code, there is no way to audit what transactions will execute during the
upgrade, eliminating transparency.

#### iNUTB-006: Valid Transaction Format

All transactions in the bundle MUST conform to the expected transaction format for [Network Upgrade Transactions](#network-upgrade-transaction-nut),
including correct sender ([Depositor Account](#depositor-account)), appropriate gas limits, and valid calldata encoding.

##### Impact

**Severity: Critical**

If transactions are malformed, they will fail to execute at fork activation, causing the upgrade to fail and
potentially halting the chain.

### Bundle Format

The bundle is a JSON file with the following structure:

```json
{
  "metadata": {
    "version": "1.0.0",
    "fork": "ForkName",
    "generatedAt": "2024-01-15T10:30:00Z",
    "sourceCommit": "abc123def456...",
    "compiler": {
      "version": "0.8.25",
      "settings": {...}
    }
  },
  "transactions": [
    {
      "nonce": 0,
      "to": "0x1234...",
      "value": "0",
      "data": "0xabcd...",
      "gasLimit": "1000000"
    }
  ]
}
```

**Field Requirements:**

- `metadata.version`: Bundle format version for compatibility
- `metadata.fork`: Name of the fork this bundle implements
- `metadata.generatedAt`: ISO 8601 timestamp of generation (informational only, not used in determinism)
- `metadata.sourceCommit`: Git commit hash of the source code that generated this bundle
- `metadata.compiler`: Compiler version and settings used to build contracts
- `transactions`: Array of transaction objects in execution order
- `transactions[].nonce`: Nonce for the [Depositor Account](#depositor-account), starting from current nonce
- `transactions[].to`: Target address (contract being called or deployed)
- `transactions[].value`: ETH value to send (typically "0")
- `transactions[].data`: Transaction calldata as hex string
- `transactions[].gasLimit`: Gas limit for this transaction

### Bundle Generation Process

Bundle generation MUST follow this process:

1. **Compile Contracts**: Build all contracts with deterministic compiler settings
2. **Compute Addresses**: Calculate implementation addresses using CREATE2 with deterministic salts
3. **Generate Transaction Data**: Construct calldata for each transaction using computed addresses
4. **Assemble Bundle**: Create JSON structure with transactions in dependency order
5. **Write Bundle File**: Output JSON to the designated path in the repository
6. **Commit to Git**: Bundle file is committed alongside source code changes

### Bundle Verification Process

To verify a bundle matches source code:

1. **Check Out Commit**: `git checkout <sourceCommit>`
2. **Build Contracts**: Compile contracts using specified compiler version and settings
3. **Regenerate Bundle**: Run the bundle generation script
4. **Compare Output**: Verify byte-for-byte match with committed bundle

## Custom Upgrade Block Gas Limit

### Overview

The Custom Upgrade Block Gas Limit mechanism provides guaranteed gas availability for executing upgrade transactions at
fork activation, independent of the regular block gas limit and system transaction gas constraints. This ensures that
complex multi-contract upgrades can execute completely within the [fork activation block](#fork-activation-block) without
running out of gas.

Standard L2 blocks are constrained by `systemTxMaxGas` (typically 1,000,000 gas), which is insufficient for executing
the deployment and upgrade transactions in a typical predeploy upgrade. The custom gas limit bypasses this constraint
for upgrade blocks specifically.

### Definitions

#### System Transaction Gas Limit

The maximum gas available for system transactions (transactions from the [Depositor Account](#depositor-account)) in a
normal L2 block, defined by `resourceConfig.systemTxMaxGas`. This limit is typically set to 1,000,000 gas.

#### Upgrade Block Gas Allocation

The total gas available for executing upgrade transactions in a [fork activation block](#fork-activation-block). This
value is set significantly higher than the [system transaction gas limit](#system-transaction-gas-limit) to accommodate
complex upgrade operations.

#### Derivation Pipeline

The component of L2 client implementations responsible for constructing L2 blocks from L1 data and protocol rules. The
derivation pipeline determines block attributes including gas limits and inserts upgrade transactions at fork
activations.

### Assumptions

#### aUBGL-001: Upgrade Gas Requirements Are Bounded

The gas required to execute all upgrade transactions in a [bundle](#network-upgrade-transaction-bundle) is finite and
can be estimated before deployment. Upgrades do not contain unbounded loops or operations that could consume arbitrary
amounts of gas.

##### Mitigations

- Fork-based testing measures actual gas consumption of upgrade transactions
- Bundle generation process includes gas estimation for all transactions
- Upgrade complexity is bounded by the number of predeploys and deployment operations
- Gas profiling is performed during development to identify expensive operations

#### aUBGL-002: Derivation Pipeline Correctly Allocates Gas

The [derivation pipeline](#derivation-pipeline) implementation correctly provides the custom gas allocation to upgrade
blocks and does not incorrectly apply this allocation to non-upgrade blocks.

##### Mitigations

- Upgrade gas allocation is conditional on fork activation logic
- Fork activation is determined by block timestamp, which is consensus-critical
- Implementation is tested with fork activation scenarios
- Multiple client implementations must agree on gas allocation behavior

#### aUBGL-003: Custom Gas Does Not Affect Consensus

Providing additional gas for upgrade blocks does not violate consensus rules or create divergence between clients. The
gas allocation is deterministic and applied consistently across all implementations.

##### Mitigations

- Gas allocation is part of the protocol specification
- All client implementations follow the same derivation rules
- Fork-based testing validates consensus across client implementations
- Gas allocation logic is simple and deterministic

### Invariants

#### iUBGL-001: Sufficient Gas Availability

The [upgrade block gas allocation](#upgrade-block-gas-allocation) MUST be sufficient to execute all transactions in the
[Network Upgrade Transaction Bundle](#network-upgrade-transaction-bundle) without running out of gas. No upgrade
transaction should fail due to insufficient gas.

##### Impact

**Severity: Critical**

If insufficient gas is allocated, upgrade transactions will fail mid-execution, leaving predeploys in partially
upgraded states and halting the chain at fork activation.

#### iUBGL-002: Deterministic Gas Allocation

The gas allocation for upgrade blocks MUST be deterministic and identical across all L2 nodes executing the fork
activation. The allocation must depend only on consensus-critical inputs (fork identification) and not on
node-specific state or configuration.

##### Impact

**Severity: Critical**

If gas allocation is non-deterministic, different nodes could allocate different gas amounts, causing a consensus
failure and chain split.

#### iUBGL-003: Gas Limit Independence from Block Gas Limit

The [upgrade block gas allocation](#upgrade-block-gas-allocation) MUST be independent of the chain's configured block
gas limit and the [system transaction gas limit](#system-transaction-gas-limit). Upgrade transactions must execute even
if block gas limits are set to minimum values.

##### Impact

**Severity: High**

If upgrade gas depends on block gas limits, chains with different configurations could have inconsistent upgrade
execution, breaking the goal of deterministic upgrades across the Superchain.

#### iUBGL-004: Gas Allocation Only for Upgrade Blocks

The custom gas allocation MUST only apply to [fork activation blocks](#fork-activation-block) containing upgrade
transactions. Regular blocks must continue to use standard gas limits without modification.

##### Impact

**Severity: High**

If custom gas allocation applies to non-upgrade blocks, it could enable DOS attacks by allowing transactions to consume
excessive gas or bypass fee markets.

#### iUBGL-005: No Gas Refund Exploitation

The gas accounting for upgrade transactions MUST not be exploitable through gas refund mechanisms. The allocated gas is
consumed by upgrade operations and cannot be reclaimed or used for unintended purposes.

##### Impact

**Severity: Medium**

If gas refunds could be exploited, upgrade transactions might consume more gas than intended or manipulate gas
accounting to break protocol assumptions.

### Gas Allocation Specification

The custom upgrade block gas allocation is implemented in the derivation pipeline with the following behavior:

**Gas Allocation Value:**
- The upgrade block gas allocation SHOULD be set to 50,000,000 gas (50M gas)
- This value is significantly higher than typical upgrade requirements to provide safety margin
- The specific value is hardcoded in the derivation pipeline for the corresponding fork

**Allocation Conditions:**
- Custom gas allocation MUST only apply when processing the fork activation block
- Fork activation is identified by L2 block timestamp matching or exceeding the fork activation timestamp
- Allocation applies to the entire upgrade transaction bundle, not per-transaction

**Implementation Requirements:**
- Implemented in `op-node/rollup/derive/attributes.go` or equivalent derivation logic
- Gas allocation is applied when constructing the payload attributes for the fork activation block
- The allocation mechanism follows patterns similar to previous fork activations

## Upgrade Process

### Overview

The Upgrade Process defines the complete lifecycle of an L2 predeploy upgrade, from initial development through fork
activation and execution. The process ensures that upgrades are developed safely, tested thoroughly, and executed
deterministically across all OP Stack chains.

This end-to-end process integrates all components of the upgrade system: contract development, bundle generation,
testing, verification, and execution at fork activation.

### Definitions

#### Fork Activation Timestamp

The L2 block timestamp at which a fork becomes active and upgrade transactions are executed. This timestamp is
specified in the protocol configuration and used by the [derivation pipeline](#derivation-pipeline) to identify when to
inject upgrade transactions.

#### Upgrade Transaction Execution Order

The sequence in which transactions from the [Network Upgrade Transaction Bundle](#network-upgrade-transaction-bundle)
are executed within the fork activation block. The order is critical for satisfying dependencies between transactions.

### Assumptions

#### aUP-001: Fork Activation Time is Coordinated

All OP Stack chains coordinate fork activation times to enable consistent upgrade rollout. The fork activation
timestamp is communicated well in advance of activation to allow node operators to prepare.

##### Mitigations

- Fork activation timestamps are published in protocol documentation and configuration files
- Activation times are set far enough in advance to allow preparation
- Multiple channels (documentation, social media, direct communication) are used to notify operators
- Testnet activations occur before mainnet to validate timing and coordination

#### aUP-002: Node Operators Update Client Software

Node operators running L2 nodes update their client software to versions that include the fork activation logic and
upgrade transaction bundle before the fork activation time.

##### Mitigations

- Client releases include clear upgrade instructions and timeline
- Breaking changes and required updates are communicated prominently
- Testnet activations serve as final validation before mainnet
- Monitoring systems alert operators of version mismatches

#### aUP-003: Testing Environments Match Production

Fork-based testing environments accurately represent production chain state, allowing upgrade testing to catch issues
that would occur in production.

##### Mitigations

- Fork tests use actual mainnet chain state as starting point
- Testing validates against multiple chains with different configurations
- CI/CD automatically runs fork tests against latest chain state
- Manual testing on testnet chains before mainnet activation

### Invariants

#### iUP-001: Atomic Upgrade Execution

All transactions in the upgrade bundle MUST execute atomically within the [fork activation block](#fork-activation-block).
If any transaction fails, the entire upgrade must fail, leaving all predeploys in their pre-upgrade state.

##### Impact

**Severity: Critical**

If upgrades are not atomic, a partial upgrade could leave the system in an inconsistent state with some predeploys
upgraded and others not, breaking protocol assumptions.

#### iUP-002: Consistent Cross-Chain Execution

All OP Stack chains executing the upgrade MUST produce identical post-upgrade state given identical pre-upgrade state.
The upgrade must be deterministic regardless of chain-specific configuration (except for preserved network-specific
configuration).

##### Impact

**Severity: Critical**

If upgrades produce different results on different chains, it would violate the Superchain's goal of consistent L2
contract versions, making it impossible to reason about protocol behavior across chains.

#### iUP-003: Upgrade Transactions Execute Before User Transactions

All upgrade transactions MUST execute before any user-submitted transactions in the fork activation block. User
transactions must interact with the post-upgrade contract state, not the pre-upgrade state.

##### Impact

**Severity: Critical**

If user transactions could execute before or during upgrades, they could exploit race conditions to manipulate system
contracts or steal funds during the upgrade window.

#### iUP-004: Fork Activation is Irreversible

Once a fork activation block is finalized, the upgrade cannot be rolled back. The upgraded predeploy state is
permanent.

##### Impact

**Severity: High**

A flawed upgrade that reaches fork activation cannot be undone through the normal upgrade process and would require a
new fork with corrective upgrades.

#### iUP-005: Verifiable Upgrade Execution

After fork activation, it MUST be possible to verify that the executed upgrade transactions match the committed bundle
and that the resulting contract state matches expectations.

##### Impact

**Severity: High**

If upgrades cannot be verified post-execution, there is no way to audit whether the correct upgrade was performed,
breaking transparency and making troubleshooting difficult.

### Upgrade Lifecycle

#### Phase 1: Development

1. **Contract Development**: Implement changes to L2 predeploy contracts
2. **Migration Logic**: Develop L2ContractsManager with configuration preservation logic
3. **Unit Testing**: Test individual contracts and migration logic
4. **Integration Testing**: Test interactions between upgraded contracts

#### Phase 2: Bundle Generation

1. **Compile Contracts**: Build all contracts with deterministic settings
2. **Run Generation Script**: Execute [bundle generation script](#bundle-generation-script) to create JSON bundle
3. **Validate Bundle**: Verify transaction ordering, nonce sequencing, and completeness
4. **Commit Bundle**: Commit bundle JSON file alongside source code to git

#### Phase 3: Testing

1. **Fork Testing**: Execute bundle against forked mainnet state
2. **Gas Profiling**: Measure gas consumption of all transactions
3. **State Validation**: Verify post-upgrade state matches expectations
4. **Multi-Chain Testing**: Test against different chain configurations
5. **Testnet Deployment**: Execute upgrade on testnet at scheduled time

#### Phase 4: Review and Approval

1. **Code Review**: Review contract changes and migration logic
2. **Bundle Verification**: Independent verification that bundle matches source code
3. **Security Review**: Audit of upgrade logic and potential vulnerabilities
4. **Governance Approval**: Approval to proceed with upgrade (where applicable)

#### Phase 5: Preparation

1. **Client Integration**: Integrate bundle into L2 client implementations
2. **Client Release**: Release updated client software with fork activation logic
3. **Documentation**: Publish upgrade documentation and operator instructions
4. **Coordination**: Communicate fork activation time to all stakeholders

#### Phase 6: Execution

1. **Fork Activation**: At the [fork activation timestamp](#fork-activation-timestamp), the derivation pipeline:
   - Identifies fork activation block by timestamp
   - Applies [custom upgrade block gas allocation](#custom-upgrade-block-gas-limit)
   - Injects upgrade transactions from bundle at the start of the block
2. **Transaction Execution**: Transactions execute in sequence:
   - Deploy [ConditionalDeployer](#conditionaldeployer) (if not already deployed)
   - Deploy new implementation contracts via ConditionalDeployer
   - Deploy new [L2ContractsManager](#l2contractsmanager)
   - Upgrade [L2ProxyAdmin](#l2proxyadmin) to new implementation (if needed)
   - Call `L2ProxyAdmin.upgradePredeploys()` with L2ContractsManager address
   - L2ContractsManager executes via DELEGATECALL to upgrade all predeploys
3. **User Transactions**: After all upgrade transactions complete, user transactions execute in the remainder of the
   block

#### Phase 7: Verification

1. **Execution Verification**: Confirm all upgrade transactions succeeded
2. **State Verification**: Verify predeploy implementations and configuration match expectations
3. **Monitoring**: Monitor chain health and contract behavior post-upgrade
4. **Issue Response**: Address any issues discovered post-upgrade

### Transaction Execution Sequence

Within the fork activation block, transactions execute in this order:

1. **ConditionalDeployer Deployment** (if needed): Deploy the ConditionalDeployer contract
2. **Implementation Deployments**: For each predeploy being upgraded, deploy new implementation via
   ConditionalDeployer
3. **L2ContractsManager Deployment**: Deploy the L2ContractsManager for this upgrade
4. **ProxyAdmin Upgrade** (if needed): Upgrade the L2ProxyAdmin implementation
5. **Batch Upgrade Execution**: Call `L2ProxyAdmin.upgradePredeploys(l2ContractsManagerAddress)` which:
   - Executes DELEGATECALL to L2ContractsManager.upgrade()
   - L2ContractsManager gathers configuration from existing predeploys
   - For each predeploy, calls `proxy.upgradeTo()` or `proxy.upgradeToAndCall()`
   - Verifies all upgrades completed successfully

All of these transactions execute before any user-submitted transactions in the block.
