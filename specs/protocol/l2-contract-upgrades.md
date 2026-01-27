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
- [L2ContractsManager](#l2contractsmanager)
  - [Overview](#overview-3)
  - [Definitions](#definitions-2)
    - [Network-Specific Configuration](#network-specific-configuration)
    - [Feature Flag](#feature-flag)
    - [Initialization Parameters](#initialization-parameters)
  - [Assumptions](#assumptions-2)
    - [a01-001: Existing Predeploys Provide Valid Configuration](#a01-001-existing-predeploys-provide-valid-configuration)
      - [Mitigations](#mitigations-5)
    - [a02-002: Implementation Addresses Are Pre-Computed Correctly](#a02-002-implementation-addresses-are-pre-computed-correctly)
      - [Mitigations](#mitigations-6)
    - [a03-003: Predeploy Proxies Are Upgradeable](#a03-003-predeploy-proxies-are-upgradeable)
      - [Mitigations](#mitigations-7)
    - [a04-004: Feature Flags Are Correctly Configured](#a04-004-feature-flags-are-correctly-configured)
      - [Mitigations](#mitigations-8)
  - [Invariants](#invariants-2)
    - [i01-001: Deterministic Upgrade Execution](#i01-001-deterministic-upgrade-execution)
      - [Impact](#impact-8)
    - [i02-002: Configuration Preservation](#i02-002-configuration-preservation)
      - [Impact](#impact-9)
    - [i03-003: Upgrade Atomicity](#i03-003-upgrade-atomicity)
      - [Impact](#impact-10)
    - [i04-004: Correct Upgrade Method Selection](#i04-004-correct-upgrade-method-selection)
      - [Impact](#impact-11)
    - [i05-005: No Storage Corruption During DELEGATECALL](#i05-005-no-storage-corruption-during-delegatecall)
      - [Impact](#impact-12)
    - [i06-006: Complete Upgrade Coverage](#i06-006-complete-upgrade-coverage)
      - [Impact](#impact-13)
- [Network Upgrade Transaction Bundle](#network-upgrade-transaction-bundle)
  - [Overview](#overview-4)
  - [Definitions](#definitions-3)
    - [Network Upgrade Transaction (NUT)](#network-upgrade-transaction-nut)
    - [Fork Activation Block](#fork-activation-block)
    - [Bundle Generation Script](#bundle-generation-script)
    - [Transaction Nonce](#transaction-nonce)
  - [Assumptions](#assumptions-3)
    - [a01-001: Solidity Compiler is Deterministic](#a01-001-solidity-compiler-is-deterministic)
      - [Mitigations](#mitigations-9)
    - [a02-002: Bundle Generation Script is Pure](#a02-002-bundle-generation-script-is-pure)
      - [Mitigations](#mitigations-10)
    - [a03-003: Git Repository is Authoritative Source](#a03-003-git-repository-is-authoritative-source)
      - [Mitigations](#mitigations-11)
    - [a04-004: JSON Format is Correctly Parsed](#a04-004-json-format-is-correctly-parsed)
      - [Mitigations](#mitigations-12)
  - [Invariants](#invariants-3)
    - [i01-001: Deterministic Bundle Generation](#i01-001-deterministic-bundle-generation)
      - [Impact](#impact-14)
    - [i02-002: Transaction Completeness](#i02-002-transaction-completeness)
      - [Impact](#impact-15)
    - [i03-003: Transaction Ordering](#i03-003-transaction-ordering)
      - [Impact](#impact-16)
    - [i04-004: Correct Nonce Sequencing](#i04-004-correct-nonce-sequencing)
      - [Impact](#impact-17)
    - [i05-005: Verifiable Against Source Code](#i05-005-verifiable-against-source-code)
      - [Impact](#impact-18)
    - [i06-006: Valid Transaction Format](#i06-006-valid-transaction-format)
      - [Impact](#impact-19)
  - [Bundle Format](#bundle-format)
  - [Bundle Generation Process](#bundle-generation-process)
  - [Bundle Verification Process](#bundle-verification-process)

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

#### a01-001: Existing Predeploys Provide Valid Configuration

The existing [predeploy](#predeploy) contracts contain valid [network-specific configuration](#network-specific-configuration)
that can be read and used during the upgrade. Configuration values are accurate, properly formatted, and represent the
intended chain configuration.

##### Mitigations

- Configuration is read from well-established predeploys that have been operating correctly
- Fork-based testing validates configuration gathering against real chain state
- The upgrade will fail deterministically if configuration reads return unexpected values
- Configuration values are validated during the upgrade process

#### a02-002: Implementation Addresses Are Pre-Computed Correctly

The implementation addresses referenced by the L2ContractsManager are correctly pre-computed using the same CREATE2
parameters that will be used by the [ConditionalDeployer](#conditionaldeployer). Address mismatches would cause
proxies to point to incorrect or non-existent implementations.

##### Mitigations

- Implementation addresses are computed using deterministic CREATE2 formula during bundle generation
- The same address computation logic is used in both bundle generation and the L2ContractsManager
- Fork-based testing validates that all implementation addresses exist and contain expected bytecode
- Address computation is isolated in shared libraries to prevent divergence

#### a03-003: Predeploy Proxies Are Upgradeable

All [predeploy](#predeploy) proxies targeted for upgrade support the `upgradeTo()` and `upgradeToAndCall()` functions
and will accept upgrade calls from the [L2ProxyAdmin](#l2proxyadmin) executing the DELEGATECALL.

##### Mitigations

- All L2 predeploys use standardized proxy implementations with well-tested upgrade functions
- Fork-based testing exercises upgrade operations against actual deployed proxies
- Non-upgradeable predeploys are excluded from the upgrade process

#### a04-004: Feature Flags Are Correctly Configured

When [feature flags](#feature-flag) are used to customize upgrade behavior, the FeatureFlags contract is properly
configured in the test/development environment and returns consistent values throughout the upgrade execution.

##### Mitigations

- Feature flag values are set using `vm.etch()` and `vm.store()` in forge-based test environments
- Feature flag reads are idempotent and cannot be modified during upgrade execution
- Production upgrades do not rely on feature flags; flags are only used in development/test environments
- Fork tests validate feature flag behavior across different configurations

### Invariants

#### i01-001: Deterministic Upgrade Execution

The L2ContractsManager's `upgrade()` function MUST execute deterministically, producing identical state changes when
given identical pre-upgrade blockchain state. The function MUST NOT read external state that could vary between
executions (timestamps, block hashes, etc.) and MUST NOT accept runtime parameters.

##### Impact

**Severity: Critical**

If upgrade execution is non-deterministic, different L2 nodes could produce different post-upgrade states, causing
consensus failures across the network. This would halt the chain and require emergency intervention to restore consensus.

#### i02-002: Configuration Preservation

All [network-specific configuration](#network-specific-configuration) that exists before the upgrade MUST be preserved
in the upgraded predeploy implementations. Configuration values MUST be read from existing predeploys and properly
passed to new implementations during upgrade.

##### Impact

**Severity: Critical**

If configuration is not preserved, chains could lose critical settings like custom gas token addresses, operator fee
parameters, or other chain-specific values. This could break fee calculations, disable custom functionality, or cause
chains to operate incorrectly after upgrade.

#### i03-003: Upgrade Atomicity

All predeploy upgrades within a single L2ContractsManager execution MUST succeed or fail atomically. If any upgrade
operation fails, the entire DELEGATECALL MUST revert, leaving all predeploys in their pre-upgrade state.

##### Impact

**Severity: Critical**

If upgrades are not atomic, a partial failure could leave some predeploys upgraded and others not, creating an
inconsistent system state. This could break inter-contract dependencies, violate protocol assumptions, and potentially
enable exploits through inconsistent contract versions.

#### i04-004: Correct Upgrade Method Selection

For each predeploy being upgraded, the L2ContractsManager MUST correctly choose between `upgradeTo()` (for
implementations with no new initialization) and `upgradeToAndCall()` (for implementations requiring initialization).
The selection MUST match the requirements of the new implementation.

##### Impact

**Severity: Critical**

If the wrong upgrade method is used, implementations requiring initialization would not be properly initialized
(breaking functionality), or unnecessary initialization calls could trigger unintended behavior or reverts. Either
scenario could break critical system contracts.

#### i05-005: No Storage Corruption During DELEGATECALL

When executing in the [L2ProxyAdmin](#l2proxyadmin) context via DELEGATECALL, the L2ContractsManager MUST NOT corrupt
or modify the ProxyAdmin's own storage. All storage modifications must be directed to the predeploy proxies being
upgraded.

##### Impact

**Severity: Critical**

If the L2ContractsManager corrupts ProxyAdmin storage, it could change the ProxyAdmin's owner, disable future upgrade
capability, or create exploitable conditions. This would compromise the entire upgrade system and potentially require
L1-driven emergency recovery.

#### i06-006: Complete Upgrade Coverage

The L2ContractsManager MUST upgrade all predeploys intended for the upgrade. It MUST NOT skip predeploys that should
be upgraded, even if their implementations are unchanged, to maintain consistency across all chains executing the
upgrade.

##### Impact

**Severity: High**

If predeploys are skipped incorrectly, chains would have inconsistent contract versions, making it difficult to reason
about protocol state. This violates the goal of bringing all chains to a consistent version and could cause unexpected
behavior differences across chains.

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

#### a01-001: Solidity Compiler is Deterministic

The Solidity compiler produces identical bytecode when given identical source code and compiler settings. This enables
verification that bundle contents match the source code on a specific commit.

##### Mitigations

- Use pinned compiler versions specified in foundry.toml
- Compiler determinism is a core property of the Solidity toolchain
- Bundle generation includes compiler version and settings in metadata
- Verification process rebuilds contracts with identical settings and compares bytecode

#### a02-002: Bundle Generation Script is Pure

The [bundle generation script](#bundle-generation-script) does not depend on external state that could vary between
executions. All addresses are computed deterministically using CREATE2, and all transaction data is derived from
compiled bytecode.

##### Mitigations

- Bundle generation scripts are reviewed to ensure they contain no external dependencies
- Scripts use only deterministic address computation (CREATE2)
- Fork-based testing validates that generated bundles match expected outputs
- CI validates bundle regeneration produces identical output

#### a03-003: Git Repository is Authoritative Source

The git repository containing the bundle JSON files and source code serves as the authoritative source of truth for
upgrade transactions. The commit hash provides an immutable reference to the exact code that generated the bundle.

##### Mitigations

- Bundles are committed to git alongside the source code that generates them
- The generation script commit hash is included in bundle metadata
- Repository is hosted on GitHub with branch protection and audit logs
- Multiple reviewers verify bundle contents before merge

#### a04-004: JSON Format is Correctly Parsed

All L2 client implementations (Go, Rust, etc.) correctly parse the JSON bundle format and extract transaction fields
identically. Parsing inconsistencies would cause consensus failures.

##### Mitigations

- JSON schema is simple and uses standard field types
- Test vectors validate parsing across client implementations
- Fork-based testing exercises bundle execution in reference implementation
- Bundle format follows existing NUT patterns used in previous forks

### Invariants

#### i01-001: Deterministic Bundle Generation

Running the [bundle generation script](#bundle-generation-script) multiple times on the same source code commit MUST
produce byte-for-byte identical JSON output. No aspect of bundle generation may depend on timestamps, random values, or
external state.

##### Impact

**Severity: Critical**

If bundle generation is non-deterministic, it becomes impossible to verify that a given bundle corresponds to specific
source code. This breaks the trust model and makes it difficult to audit upgrade transactions, potentially allowing
unverified or malicious transactions to be included in upgrades.

#### i02-002: Transaction Completeness

The bundle MUST contain all transactions required to complete the upgrade. Missing transactions would cause the upgrade
to fail partially, leaving the system in an inconsistent state.

##### Impact

**Severity: Critical**

If the bundle is incomplete, the fork activation would fail, potentially halting the chain or leaving predeploys in
partially upgraded states. Recovery would require emergency intervention and could cause extended downtime.

#### i03-003: Transaction Ordering

Transactions in the bundle MUST be ordered such that dependencies are satisfied. For example, contract deployments MUST
occur before transactions that call those contracts.

##### Impact

**Severity: Critical**

If transactions are misordered, executions will fail when attempting to call non-existent contracts or reference
incorrect addresses. This would cause the entire upgrade to fail at fork activation, halting the chain.

#### i04-004: Correct Nonce Sequencing

Transaction nonces for the [Depositor Account](#depositor-account) MUST form a contiguous sequence with no gaps or
duplicates. Each transaction must use the next available nonce.

##### Impact

**Severity: Critical**

If nonces are incorrect, transactions will fail to execute or execute in wrong order. Gap in nonces would cause
subsequent transactions to fail. Duplicate nonces would cause only the first transaction to execute, failing the rest.

#### i05-005: Verifiable Against Source Code

Given the source code at a specific git commit, it MUST be possible to rebuild contracts, regenerate the bundle, and
verify that it matches the committed bundle byte-for-byte.

##### Impact

**Severity: High**

If bundles cannot be verified against source code, there is no way to audit what transactions will actually execute
during the upgrade. This eliminates transparency and could allow unauthorized or malicious transactions to be included.

#### i06-006: Valid Transaction Format

All transactions in the bundle MUST conform to the expected transaction format for [Network Upgrade Transactions](#network-upgrade-transaction-nut),
including correct sender ([Depositor Account](#depositor-account)), appropriate gas limits, and valid calldata encoding.

##### Impact

**Severity: Critical**

If transactions are malformed, they will fail to execute at fork activation, causing the upgrade to fail and
potentially halting the chain. Invalid gas limits could cause out-of-gas failures. Invalid calldata could cause
execution reverts.

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

