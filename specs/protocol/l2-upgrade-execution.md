# L2 Upgrade Execution

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Network Upgrade Transaction Bundle](#network-upgrade-transaction-bundle)
  - [Overview](#overview-1)
  - [Definitions](#definitions)
    - [Network Upgrade Transaction (NUT)](#network-upgrade-transaction-nut)
    - [Fork Activation Block](#fork-activation-block)
    - [Bundle Generation Script](#bundle-generation-script)
    - [Transaction Nonce](#transaction-nonce)
  - [Assumptions](#assumptions)
    - [aNUTB-001: Solidity Compiler is Deterministic](#anutb-001-solidity-compiler-is-deterministic)
      - [Mitigations](#mitigations)
    - [aNUTB-002: Bundle Generation Script is Pure](#anutb-002-bundle-generation-script-is-pure)
      - [Mitigations](#mitigations-1)
    - [aNUTB-003: Git Repository is Authoritative Source](#anutb-003-git-repository-is-authoritative-source)
      - [Mitigations](#mitigations-2)
    - [aNUTB-004: JSON Format is Correctly Parsed](#anutb-004-json-format-is-correctly-parsed)
      - [Mitigations](#mitigations-3)
  - [Invariants](#invariants)
    - [iNUTB-001: Deterministic Bundle Generation](#inutb-001-deterministic-bundle-generation)
      - [Impact](#impact)
    - [iNUTB-002: Transaction Completeness](#inutb-002-transaction-completeness)
      - [Impact](#impact-1)
    - [iNUTB-003: Transaction Ordering](#inutb-003-transaction-ordering)
      - [Impact](#impact-2)
    - [iNUTB-004: Correct Nonce Sequencing](#inutb-004-correct-nonce-sequencing)
      - [Impact](#impact-3)
    - [iNUTB-005: Verifiable Against Source Code](#inutb-005-verifiable-against-source-code)
      - [Impact](#impact-4)
    - [iNUTB-006: Valid Transaction Format](#inutb-006-valid-transaction-format)
      - [Impact](#impact-5)
  - [Bundle Format](#bundle-format)
  - [Bundle Generation Process](#bundle-generation-process)
  - [Bundle Verification Process](#bundle-verification-process)
- [Custom Upgrade Block Gas Limit](#custom-upgrade-block-gas-limit)
  - [Overview](#overview-2)
  - [Definitions](#definitions-1)
    - [System Transaction Gas Limit](#system-transaction-gas-limit)
    - [Upgrade Block Gas Allocation](#upgrade-block-gas-allocation)
    - [Derivation Pipeline](#derivation-pipeline)
  - [Assumptions](#assumptions-1)
    - [aUBGL-001: Upgrade Gas Requirements Are Bounded](#aubgl-001-upgrade-gas-requirements-are-bounded)
      - [Mitigations](#mitigations-4)
    - [aUBGL-002: Derivation Pipeline Correctly Allocates Gas](#aubgl-002-derivation-pipeline-correctly-allocates-gas)
      - [Mitigations](#mitigations-5)
    - [aUBGL-003: Custom Gas Does Not Affect Consensus](#aubgl-003-custom-gas-does-not-affect-consensus)
      - [Mitigations](#mitigations-6)
  - [Invariants](#invariants-1)
    - [iUBGL-001: Sufficient Gas Availability](#iubgl-001-sufficient-gas-availability)
      - [Impact](#impact-6)
    - [iUBGL-002: Deterministic Gas Allocation](#iubgl-002-deterministic-gas-allocation)
      - [Impact](#impact-7)
    - [iUBGL-003: Gas Limit Independence from Block Gas Limit](#iubgl-003-gas-limit-independence-from-block-gas-limit)
      - [Impact](#impact-8)
    - [iUBGL-004: Gas Allocation Only for Upgrade Blocks](#iubgl-004-gas-allocation-only-for-upgrade-blocks)
      - [Impact](#impact-9)
    - [iUBGL-005: No Gas Refund Exploitation](#iubgl-005-no-gas-refund-exploitation)
      - [Impact](#impact-10)
  - [Gas Allocation Specification](#gas-allocation-specification)
- [Upgrade Process](#upgrade-process)
  - [Overview](#overview-3)
  - [Definitions](#definitions-2)
    - [Fork Activation Timestamp](#fork-activation-timestamp)
    - [Upgrade Transaction Execution Order](#upgrade-transaction-execution-order)
  - [Assumptions](#assumptions-2)
    - [aUP-001: Fork Activation Time is Coordinated](#aup-001-fork-activation-time-is-coordinated)
      - [Mitigations](#mitigations-7)
    - [aUP-002: Node Operators Update Client Software](#aup-002-node-operators-update-client-software)
      - [Mitigations](#mitigations-8)
    - [aUP-003: Testing Environments Match Production](#aup-003-testing-environments-match-production)
      - [Mitigations](#mitigations-9)
  - [Invariants](#invariants-2)
    - [iUP-001: Atomic Upgrade Execution](#iup-001-atomic-upgrade-execution)
      - [Impact](#impact-11)
    - [iUP-002: Consistent Cross-Chain Execution](#iup-002-consistent-cross-chain-execution)
      - [Impact](#impact-12)
    - [iUP-003: Upgrade Transactions Execute Before User Transactions](#iup-003-upgrade-transactions-execute-before-user-transactions)
      - [Impact](#impact-13)
    - [iUP-004: Fork Activation is Irreversible](#iup-004-fork-activation-is-irreversible)
      - [Impact](#impact-14)
    - [iUP-005: Verifiable Upgrade Execution](#iup-005-verifiable-upgrade-execution)
      - [Impact](#impact-15)
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

This specification defines the execution mechanism for L2 contract upgrades, covering the bundle format, gas
allocation, and complete upgrade lifecycle. These components work together with the
[L2 Contract Upgrades](./l2-contract-upgrades.md) specification to enable deterministic, verifiable upgrades of L2
predeploy contracts across all OP Stack chains.

The upgrade execution system ensures that upgrade transactions are properly formatted, have sufficient gas to execute,
and follow a well-defined process from development through verification.

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
[Depositor Account](./l2-contract-upgrades.md#depositor-account) as the sender. These transactions bypass normal
transaction pool processing and are deterministically included in the fork activation block.

#### Fork Activation Block

The L2 block at which a protocol upgrade becomes active, identified by a specific L2 block timestamp. This block
contains the Network Upgrade Transactions that implement the protocol changes.

#### Bundle Generation Script

A Solidity script (typically using Forge scripting) that deterministically computes all transaction data for an
upgrade. The script deploys contracts, computes addresses, and assembles transaction calldata without relying on
execution in an EVM environment.

#### Transaction Nonce

The nonce value used for transactions sent by the
[Depositor Account](./l2-contract-upgrades.md#depositor-account). For upgrade transactions, nonces must be correctly
sequenced to ensure all transactions execute in the proper order within the fork activation block.

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

Transaction nonces for the [Depositor Account](./l2-contract-upgrades.md#depositor-account) MUST form a contiguous
sequence with no gaps or duplicates. Each transaction must use the next available nonce.

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

All transactions in the bundle MUST conform to the expected transaction format for
[Network Upgrade Transactions](#network-upgrade-transaction-nut), including correct sender
([Depositor Account](./l2-contract-upgrades.md#depositor-account)), appropriate gas limits, and valid calldata
encoding.

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
- `transactions[].nonce`: Nonce for the [Depositor Account](./l2-contract-upgrades.md#depositor-account), starting
  from current nonce
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
complex multi-contract upgrades can execute completely within the [fork activation block](#fork-activation-block)
without running out of gas.

Standard L2 blocks are constrained by `systemTxMaxGas` (typically 1,000,000 gas), which is insufficient for executing
the deployment and upgrade transactions in a typical predeploy upgrade. The custom gas limit bypasses this constraint
for upgrade blocks specifically.

### Definitions

#### System Transaction Gas Limit

The maximum gas available for system transactions (transactions from the
[Depositor Account](./l2-contract-upgrades.md#depositor-account)) in a normal L2 block, defined by
`resourceConfig.systemTxMaxGas`. This limit is typically set to 1,000,000 gas.

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
   - Deploy [ConditionalDeployer](./l2-contract-upgrades.md#conditionaldeployer) (if not already deployed)
   - Deploy new implementation contracts via ConditionalDeployer
   - Deploy new [L2ContractsManager](./l2-contract-upgrades.md#l2contractsmanager)
   - Upgrade [L2ProxyAdmin](./l2-contract-upgrades.md#l2proxyadmin) to new implementation (if needed)
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
