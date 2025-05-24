# Governance Proposal Validator

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Design](#design)
- [Roles](#roles)
- [Interface](#interface)
  - [Public Functions](#public-functions)
  - [Properties](#properties)
  - [Structs](#structs)
  - [Enums](#enums)
  - [Events](#events)
- [EAS Integration](#eas-integration)
  - [Why EAS?](#why-eas)
  - [Implementation Details](#implementation-details)
- [Proposal uniqueness](#proposal-uniqueness)
- [Invariants](#invariants)
- [Security Considerations](#security-considerations)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

This document specifies the `ProposalValidator` contract, designed to enable permissionless proposals in the Optimism
governance system. The contract allows proposal submissions based on predefined rules and automated checks, removing the
need for manual gate keeping.

## Design

The `ProposalValidator` manages the proposal lifecycle through three main functions:

- `submitProposal`: Records new proposals
- `approveProposal`: Handles proposal approvals
- `moveToVote`: Transitions approved proposals to voting phase

The contract also integrates with EAS (Ethereum Attestation Service) to verify authorized proposers for specific proposal
types. For detailed flows of each proposal, see [design docs](https://github.com/ethereum-optimism/design-docs/pull/260).

## Roles

The contract has a single `owner` role (Optimism Foundation) with permissions to:

- Set minimum voting power threshold for delegate approvals
- Configure voting cycle parameters
- Set maximum token distribution limits for proposals

## Interface

### Public Functions

`submitProposal`

Submits a proposal for approval and voting. Based on the `ProposalType` provided this will require different validation
checks and actions.

- MUST only be called for `ProtocolOrGovernorUpgrade`, `MaintenanceUpgradeProposals`, or `CouncilMemberElections` types
- MUST be called by an approved address
- MUST check if the proposal is a duplicate
- MUST use the correct proposal type configurator from the `_proposalTypesData`
- MUST provide a valid attestation UID
- MUST NOT transfer any tokens or change any allowances
- MUST emit `ProposalSubmitted` event
- MUST store proposal data

For `GovernanceFund` and `CouncilBudget` types:

- The user MUST use the `submitFundingProposal` that uses specific `calldata` pre-defined by the owner

Note: `MaintenanceUpgradeProposals` type can move straight to voting if all submission checks pass, unlike the rest of the
proposals where they need to collect a number of approvals by top delegates in order to move to vote. This call should be
atomic.

```solidity
function submitProposal(
    address[] memory _targets,
    uint256[] memory _values,
    bytes[] memory _calldatas,
    string memory _description,
    ProposalType _proposalType,
    bytes32 _attestationUid
) external returns (bytes32 proposalHash_);
```

`submitFundingProposal`

Submits a `GovernanceFund` or `CouncilBudget` proposal type that transfers OP tokens for approval and voting.

- MUST only be called for `GovernanceFund` or `CouncilBudget` proposal type
- CAN be called by anyone
- MUST check if the proposal is a duplicate
- MUST use the correct proposal type configurator from the `_proposalTypesData`
- MUST use the `Predeploys.GOVERNANCE_TOKEN` and `TRANSFER_SIGNATURE` to create the `calldata`
- MUST NOT request to transfer more than `distributionThreshold` tokens
- MUST emit `ProposalSubmitted` event
- MUST store proposal data

```solidity
function submitFundingProposal(
    address _to,
    uint256 _amount,
    string memory _description,
    ProposalType _proposalType,
) external returns (bytes32 proposalHash_);
```

`approveProposal`

Approves a proposal before being moved for voting, used by the top delegates.

- MUST check if proposal hash corresponds to a valid proposal
- MUST check if caller is has enough voting power to call the function and approve a proposal
- MUST check if caller has already approved the same proposal
- MUST store the approval vote
- MUST emit `ProposalApproved` when successfully called

```solidity
function approveProposal(bytes32 _proposalHash) external
```

`moveToVote`

Checks if the provided proposal is ready to move for voting. Based on the Proposal Type different checks are being
validated. If all checks pass then `OptimismGovernor.propose` is being called to forward the proposal for voting. This
function can be called by anyone.

For `ProtocolOrGovernorUpgrade`:

- MUST check if provided data produces a valid `proposalHash`
- Proposal MUST have gathered X amount of approvals by top delegates
- MUST check if proposal has already moved for voting
- MUST emit `ProposalMovedToVote` event

For `MaintenanceUpgradeProposals`:

- This type does not require any checks and is being forwarded to the Governor contracts, this should happen atomically.
- MUST emit `ProposalMovedToVote` event

For `CouncilMemberElections`, `GovernanceFund` and `CouncilBudget`:

- MUST check if provided data produce the same `proposalHash`
- Proposal MUST have gathered X amount of approvals by top delegates
- Proposal MUST be moved to vote during a valid voting cycle
- MUST check if proposal has already moved for voting
- MUST check if the total amount of tokens that can possible be distributed during this voting cycle does not go over the
  `VotingCycleData.votingCycleDistributionLimit`
- MUST emit `ProposalMovedToVote` event

```solidity
function moveToVote(
    address[] memory _targets,
    uint256[] memory _values,
    bytes[] memory _calldata,
    string memory description
)
    external
    returns (uint256 governorProposalId_)
```

`canSignOff`

Returns true if a delegate address has enough voting power to approve a proposal.

- Can be called by anyone
- MUST return TRUE if the delegates' voting power is above the `minimumVotingPower`

```solidity
function canSignOff(address _delegate) public view returns (bool canSignOff_)
```

`setMinimumVotingPower`

Sets the minimum voting power a delegate must have in order to be eligible to approve a proposal.

- MUST only be called by the owner of the contract
- MUST change the existing minimum voting power to the new
- MUST emit `MinimumVotingPowerSet` event

```solidity
function setMinimumVotingPower(uint256 _minimumVotingPower) external
```

`setVotingCycleData`

Sets the start and the duration of a voting cycle.

- MUST only be called by the owner of the contract
- MUST NOT change an existing voting cycle
- MUST emit `VotingCycleSet` event

```solidity
function setVotingCycleData(
    uint256 _cycleNumber,
    uint256 _startBlock,
    uint256 _duration,
    uint256 _distributionLimit
) external
```

`setDistributionThreshold`

Sets the maximum distribution threshold a proposal can request.

- MUST only be called by the owner of the contract
- MUST change the previous threshold to the new one
- MUST emit `DistributionThresholdSet` event

```solidity
function setDistributionThreshold(uint256 _threshold) external
```

`setProposalTypeApprovalThreshold`

Sets the number of approvals a specific proposal type should have before being able to move for voting.

- MUST only be called by the owner of the contract
- MUST change the previous value to the new one
- MUST emit `ProposalTypeApprovalThresholdSet` event

```solidity
function setProposalTypeApprovalThreshold(
    uint8 _proposalTypeId,
    uint256 _approvalThreshold
) external
```

### Properties

`ATTESTATION_SCHEMA_UID`

The EAS' schema UID that is used to verify attestation for approved addresses that can submit proposals for specific
`ProposalTypes`.

```solidity
/// Schema { approvedProposer: address, proposalType: uint8 }
bytes32 public immutable ATTESTATION_SCHEMA_UID;
```

`TRANSFER_SIGNATURE`

The 4bytes signature of ERC20.transfer, will be used for creating the calldata for funding proposals.

```solidity
bytes4 public constant TRANSFER_SIGNATURE = 0xa9059cbb;
```

`GOVERNOR`

The address of the Optimism Governor contract.

```solidity
IOptimismGovernor public immutable GOVERNOR;
```

`minimumVotingPower`

The minimum voting power a delegate must have in order to be eligible for approving a proposal.

```solidity
uint256 public minimumVotingPower;
```

`distributionThreshold`

The maximum amount of tokens a proposal can request.

```solidity
uint256 public distributionThreshold;
```

`votingCycles`

A mapping that stores the data for each voting cycle.

```solidity
mapping(uint256 => VotingCycleData) public votingCycles;
```

`_proposals`

A mapping that stores each submitted proposals' data based on its `proposalHash`. The proposal hash is produced by hashing
the ABI encoded `targets` array, the `values` array, the `calldatas` array and the `description`.

```solidity
mapping(bytes32 => ProposalSubmissionData) private _proposals;
```

`_proposalTypesData`

A mapping that stores data related to each proposal type.

```solidity
mapping(ProposalType => ProposalTypeData) private _proposalTypesData;
```

### Structs

`ProposalSubmissionData`

A struct that holds all the data for a single proposal. Consists of:

- `proposer`: The address that submitted the proposal
- `proposalType`: The type of the proposal
- `inVoting`: Returns true if the proposal has already been submitted for voting
- `delegateApprovals`: Mapping of addresses that approved the specific proposal
- `approvalsCounter`: The number of approvals the specific proposal has received

```solidity
struct ProposalSubmissionData {
    address proposer;
    ProposalType proposalType;
    bool inVoting;
    mapping(address => bool) delegateApprovals;
    uint256 approvalsCounter;
}
```

`ProposalTypeData`

A struct that holds data for each proposal type.

- `requiredApprovals`: The number of approvals each proposal type requires in order to be able to move for voting.
- `proposalTypeConfigurator`: The proposal type configurator that can be used for each proposal type. This
is set by the owner on initialize.

```solidity
struct ProposalTypeData {
    uint256 requiredApprovals;
    uint8 proposalTypeConfigurator;
}
```

`VotingCycleData`

A struct that stores the start block of a voting cycle and it's duration.

- `startingBlock`: The block number/timestamp that the voting cycle starts
- `duration`: The duration of the specific voting cycle
- `votingCycleDistributionLimit`: A more general distribution amount limit tied to the voting cycle

```solidity
struct VotingCycleData {
    uint256 startingBlock;
    uint256 duration;
    uint256 votingCycleDistributionLimit;
}
```

### Enums

`ProposalType`

Defines the different types of proposals that can be submitted. Based on each type it will be determined which validation
checks should be run when submitting and moving to vote a proposal.

The proposal types that are supported are:

- Protocol or Governor Upgrades
- Maintenance Upgrades
- Council Member Elections
- Governance Funding
- Council Budget

```solidity
enum ProposalType {
    ProtocolOrGovernorUpgrade,
    MaintenanceUpgrade,
    CouncilMemberElections,
    GovernanceFund,
    CouncilBudget
}
```

### Events

`ProposalSubmitted`

MUST be triggered when `submitProposal` is successfully called.

```solidity
event ProposalSubmitted(
    uint256 indexed proposalHash,
    address indexed proposer,
    address[] targets,
    uint256[] values,
    bytes[] calldatas,
    string description,
    ProposalType proposalType
);
```

`ProposalApproved`

MUST be triggered when `approveProposal` is successfully called.

```solidity
event ProposalApproved(uint256 indexed proposalHash, address indexed approver);
```

`ProposalMovedToVote`

MUST be triggered when `moveToVote` is successfully called.

```solidity
event ProposalMovedToVote(uint256 indexed proposalHash, address indexed executor);
```

## EAS Integration

`ProposalValidator` integrates Ethereum Attestation Service (EAS) to handle proposer authorization for specific
`ProposalType`s, removing the need for adding custom logic to the contract.

### Why EAS?

- **Decentralized trust**: Instead of custom logic, Optimism uses attestations signed by the Foundation to authorize
  proposers.
- **Low integration overhead**: `EAS` and `SchemaRegistry` are predeploys on Optimism, requiring no additional deployments
  or infrastructure.
- **Schema validation**: Ensures attestations follow strict data formats (`address approvedDelegate, uint8 proposalType`).
- **Revocability and expiration**: EAS supports expiration and revocation semantics natively, allowing dynamic control over
  authorized proposers.

### Implementation Details

- On setup, the contract registers a schema in the predeployed `SchemaRegistry`.
- The `submitProposal` function validates attestations by:
  - Ensuring the attestation UID matches the registered schema.
  - Verifying the attester is the contract owner (Optimism Foundation).
  - Decoding the attestation to check the proposer's address and proposal type.
- Only proposals of type `ProtocolOrGovernorUpgrade`, `MaintenanceUpgradeProposals`, and
`CouncilMemberElections` require
  valid EAS attestations.

**Technical implementation docs: [EAS Integration](https://www.notion.so/EAS-Integration-1de9a4c092c780478e19cc8175aa054e?pvs=21)**

## Proposal uniqueness

To prevent duplicate proposals, the contract enforces uniqueness by hashing the defining parameters of each proposal and
checking against a registry of previously submitted proposals.

A proposal is uniquely identified by a tuple:

- `targets[]`: array of addresses the proposal will call
- `values[]`: array of ETH values to send with each call
- `calldatas[]`: array of calldata payloads for each call
- `description`: a string describing the proposal

These elements are ABI-encoded and hashed:

```solidity
keccak256(abi.encode(targets, values, calldatas, description));
```

This hash serves as a unique identifier for the proposal. The contract stores submitted proposals in:

```solidity
mapping(bytes32 => ProposalSubmissionData) private _proposals;
```

When a new proposal is submitted, the contract checks that `_proposals[proposalHash]` is empty (e.g., `proposer ==
address(0)`). If data exists at that key, the proposal is rejected as a duplicate.

This mechanism guarantees that proposals with the same intent and execution logic cannot be submitted multiple times,
maintaining proposal integrity and preventing spam.

## Invariants

- It MUST allow only the `owner` to set the `minimumVotingPower`, `votingCycleData`, `distributionThreshold`, and
  `proposalTypeApprovalThreshold`
- It MUST only allow eligible addresses to approve a proposal
- It MUST only allow authorized addresses to submit proposals for types `ProtocolOrGovernorUpgrade`,
  `MaintenanceUpgradeProposals`, and `CouncilMemberElections`
- It MUST NOT transfer any tokens or ETH for `ProtocolOrGovernorUpgrade`, `MaintenanceUpgradeProposals`, and
  `CouncilMemberElections` proposal types
- It MUST emit the following events:
  - `ProposalSubmitted`
  - `ProposalApproved`
  - `ProposalMovedToVote`

## Security Considerations

- **Role-Based Restrictions:** The `owner` role should be securely managed, as it holds critical permissions such as
  setting voting power thresholds, configuring voting cycles, and distribution limits. Any compromise could significantly
  impact governance.
- **Attestation Validation:** Two key aspects need consideration:
  - The Optimism Foundation must have a secure and thorough process for validating addresses before issuing attestations
    for specific proposal types
  - The contract must properly verify attestation expiration and revocation status to prevent the use of outdated or
    invalid attestations
