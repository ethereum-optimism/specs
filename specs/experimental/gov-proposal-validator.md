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
  - [Submit Proposal](#submit-proposal)
  - [Approve Proposal](#approve-proposal)
- [Proposal uniqueness](#proposal-uniqueness)
- [Invariants](#invariants)
- [Security Considerations](#security-considerations)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

This document specifies the `ProposalValidator` contract, designed to enable permissionless proposals in the Optimism
governance system. The contract allows proposal submissions based on predefined rules and automated checks, removing the
need for manual gate-keeping.

## Design

The `ProposalValidator` manages the proposal lifecycle through three main actions:

- `Submit Proposal`: Records new proposals
- `Approve Proposal`: Handles proposal approvals
- `Move to Vote`: Transitions approved proposals to the Governor for voting

The contract also integrates with EAS (Ethereum Attestation Service) to verify authorized proposers and approvals for specific
proposal types. For detailed flows of each proposal, see [design docs](https://github.com/ethereum-optimism/design-docs/pull/260).

## Roles

The contract has a single `owner` role (Optimism Foundation) with permissions to:

- Set the minimum approvals for each supported proposal type
- Configure voting cycle parameters
- Set maximum token distribution limits for proposals
- Checks the address of the attester for the submit proposal attestations with the address of the owner

## Interface

### Public Functions

`submitUpgradeProposal`

Submits a Protocol/Governor Upgrade or a Maintenance Upgrade proposal to move for voting.

`ProtocolOrGovernorUpgrade`: If all submission checks pass for this proposal type, the `ProposalValidator`
will store the submission proposal data and will be able to accept approvals by top delegates before being
able to move to the Governor for voting.

`MaintenanceUpgrade`: This proposal type can move straight to voting if all submission checks pass, unlike
the rest of the proposals where they need to collect a number of approvals by top delegates in order
to move to vote. This call should be atomic.

- MUST be called by an `owner` approved address
- MUST only be called for `ProtocolOrGovernorUpgrade` or `MaintenanceUpgrade` proposal type
- MUST check if the proposal is a duplicate
- MUST use the `Optimistic` Voting Module
- MUST provide a valid againstThreshold
- MUST provide a valid attestation UID
- MUST NOT execute any operations
- MUST emit `ProposalSubmitted` and `ProposalVotingModuleData` events
- MUST store submission proposal data which are defined by the `ProposalData` struct
- MUST call `Governor.proposeWithModule` IF `_proposalType` is `MaintenanceUpgrade`

```solidity
function submitUpgradeProposal(
    uint248 _againstThreshold,
    string memory _proposalDescription,
    bytes32 _attestationUid,
    ProposalType _proposalType,
    uint256 _votingCycle
) external returns (bytes32 proposalHash_);
```

**Optimistic Voting Module**

Both proposals use the `Optimistic` voting module.

For the `ProposalSettings` of the voting module, these are:
- `uint248 againstThreshold`: Should be provided by the caller. This value will be the percentage
that will be used to calculate the fraction of against votes relative to the votable supply that the proposal will need in
against votes in order to not pass.
- `bool isRelativeToVotableSupply`: If voting power should be relative to the votable supply. Should always be `true`.
---

`submitCouncilMemberElectionsProposal`

Submits a Council Member Elections proposal for approval and voting.

- MUST be called by an `owner` approved address
- MUST check if the proposal is a duplicate
- MUST use the `Approval` Voting Module
- MUST use "TopChoices" criteria type for the Voting Module
- MUST provide a valid attestation UID
- MUST NOT execute any operations
- MUST emit `ProposalSubmitted` and `ProposalVotingModuleData` events
- MUST store submission proposal data which are defined by the `ProposalData` struct

```solidity
function submitCouncilMemberElectionsProposal(
    uint128 _criteriaValue,
    string[] _optionDescriptions,
    string memory _proposalDescription,
    bytes32 _attestationUid,
    uint256 _votingCycle
) external returns (bytes32 proposalHash_);
```

**Approval Voting Module**

Council Member Elections proposals use the `Approval` voting module.
This requires the user who submits the proposal to provide some additional data related to the proposal.

For the `ProposalSettings` of the voting module, these are:
- `uint128 criteriaValue`: Since the passing criteria type is "TopChoices" this number represents the amount
of top choices that can pass the voting.

For the `ProposalOptions` of the voting module, these are:
- `string[] optionDescriptions`: The strings of the different options that can be voted.
---

`submitFundingProposal`

Submits a `GovernanceFund` or `CouncilBudget` proposal type, for approval and voting, that transfers OP tokens.

- MUST only be called for `GovernanceFund` or `CouncilBudget` proposal type
- CAN be called by anyone
- MUST check if the proposal is a duplicate
- MUST use the `Approval` Voting Module
- MUST use "Threshold" criteria type for the Voting Module
- MUST use the `Predeploys.GOVERNANCE_TOKEN` and `IERC20.transfer` signature to create the `calldata`
for each option
- MUST NOT request to transfer more than `proposalDistributionThreshold` tokens for each option
- MUST emit `ProposalSubmitted` and `ProposalVotingModuleData` events
- MUST store submission proposal data which are defined by the `ProposalData` struct

```solidity
function submitFundingProposal(
    uint128 _criteriaValue,
    string[] _optionsDescriptions,
    address[] _optionsRecipients,
    uint256[] _optionsAmounts,
    string memory _description,
    ProposalType _proposalType,
    uint256 _votingCycle
) external returns (bytes32 proposalHash_);
```

**Approval Voting Module**

Funding proposals use the `Approval` voting module.
This requires the user who submits the proposal to provide some additional data related to the proposal.

For the `ProposalSettings` of the voting module, these are:
- `uint128 criteriaValue`: Since the passing criteria type is always "Threshold", for this proposal type,
this value will be the absolute number of votes required for the proposal to pass.
It represents the threshold that must be met or exceeded for any option to be considered successful.
For the `ProposalOptions` of the voting module, these are:
- `string[] optionsDescriptions`: The strings of the different options that can be voted.
- `address[] optionsRecipients`: An address for each option to transfer funds to in case the option passes the voting.
- `uint256[] optionsAmounts`: The amount to transfer for each option in case the option passes the voting.
---

`approveProposal`

Approves a proposal before being moved to Governor for voting, used by the top delegates.

- MUST check if proposal hash corresponds to a valid proposal
- MUST check if the caller is one of the top100 delegates
  The top100 delegates is checked against a dynamic attestation service that updates the
top100 delegates every day.
- MUST provide a valid attestation UID
- MUST check if the attestation has been revoked
- The attestation MUST refer to non partial delegation
- MUST check if caller has already approved the same proposal
- MUST store the approval vote
- MUST emit `ProposalApproved` when successfully called

```solidity
function approveProposal(bytes32 _proposalHash, bytes32 _attestationUid) external
```

Approving a funding proposal type requires extra attention to the budget amount and options, of the
approval voting module, that were provided on the submission of the proposal. This should be handled
by the Agora's UI.

---

`moveToVoteProtocolOrGovernorUpgradeProposal`

Moves a Protocol or Governor Upgrade proposal to vote by proposing it on the Governor.
If all checks pass then `OptimismGovernor.proposeWithModule` is being called to forward the proposal.

- MUST create the `proposalHash` and check if it exists and is valid
- Proposal MUST have gathered equal or more than the `requiredApprovals` defined for that type
- MUST check if proposal has already moved for voting
- MUST check that is called by the proposer that submitted the proposal
- `_optionsRecipients` and `_optionsAmounts` MUST be empty
- MUST emit `ProposalMovedToVote` event

```solidity
function moveToVoteProtocolOrGovernorUpgradeProposal(
    uint248 _againstThreshold,
    string memory _proposalDescription
)
    external
    returns (bytes32 proposalHash_)
```

---

`moveToVoteCouncilMemberElectionsProposal`

Moves a council member elections proposal to vote by proposing it on the Governor.
If all checks pass then `OptimismGovernor.proposeWithModule` is being called to forward the proposal.

- MUST create the `proposalHash` and check if it exists and is valid
- Proposal MUST have gathered equal or more than the `requiredApprovals` defined for that type
- MUST check if proposal has already moved for voting
- MUST also check that is called by the proposer that submitted the proposal
- `_optionsRecipients` and `_optionsAmounts` MUST be empty
- Proposal MUST be moved to vote during a valid voting cycle
- MUST emit `ProposalMovedToVote` event

```solidity
function moveToVoteCouncilMemberElectionsProposal(
    uint128 _criteriaValue,
    string[] memory _optionsDescriptions,
    string memory _proposalDescription
)
    external
    returns (bytes32 proposalHash_)
```

---

`moveToVoteFundingProposal`

Moves a funding proposal to vote by proposing it on the Governor.
If all checks pass then `OptimismGovernor.proposeWithModule` is being called to forward the proposal.

- MUST create the `proposalHash` and check if it exists and is valid
- Proposal MUST have gathered equal or more than the `requiredApprovals` defined for that type
- MUST check if proposal has already moved for voting
- Proposal MUST be moved to vote during a valid voting cycle
- MUST check if the total amount of tokens that can possible be distributed during this voting cycle does not go over the
  `VotingCycleData.votingCycleDistributionLimit`

```solidity
function moveToVoteFundingProposal(
    uint128 _criteriaValue,
    string[] memory _optionsDescriptions,
    address[] memory _optionsRecipients,
    uint256[] memory _optionsAmounts,
    string memory _description,
    ProposalType _proposalType
)
    external
    returns (bytes32 proposalHash_)
```

---

`canApproveProposal`

Returns true if a delegate is part of the top100 delegates based on the dynamic attestation service.

- Can be called by anyone
- MUST return TRUE if the delegate is part of the top100 and can approve a proposal

```solidity
function canApproveProposal(bytes32 _attestationUid, address _delegate) external view returns (bool canApprove_)
```

---

`setVotingCycleData`

Sets the voting cycle data.

- MUST only be called by the owner of the contract
- MUST NOT change an existing voting cycle
- MUST emit `VotingCycleDataSet` event

```solidity
function setVotingCycleData(
    uint256 _cycleNumber,
    uint256 _startingTimestamp,
    uint256 _duration,
    uint256 _votingCycleDistributionLimit
) external
```

---

`setProposalDistributionThreshold`

Sets the maximum distribution amount a proposal can request.

- MUST only be called by the owner of the contract
- MUST change the previous amount to the new one
- MUST emit `ProposalDistributionThresholdSet` event

```solidity
function setProposalDistributionThreshold(uint256 _threshold) external
```

---

`setProposalTypeData`

Sets the data for a proposal type. The amount of approvals and the voting module id each type has.

- MUST only be called by the owner of the contract
- MUST change the previous value to the new one
- MUST emit `ProposalTypeDataSet` event

```solidity
function setProposalTypeData(
    ProposalType _proposalType,
    ProposalTypeData memory _proposalTypeData
) external
```

### Properties

`APPROVED_PROPOSER_ATTESTATION_SCHEMA_UID`

The schema UID for attestations in the Ethereum Attestation Service for checking if the caller
is an approved proposer.

```solidity
/// Schema { proposalType: uint8, date: string }
bytes32 public immutable APPROVED_PROPOSER_ATTESTATION_SCHEMA_UID;
```

`TOP_DELEGATES_ATTESTATION_SCHEMA_UID`

The schema UID for attestations in the Ethereum Attestation Service for checking if the caller
is part of the top100 delegates.

```solidity
/// Schema { rank: string, includePartialDelegation: bool, date: string }
bytes32 public immutable TOP_DELEGATES_ATTESTATION_SCHEMA_UID;
```

`GOVERNOR`

The address of the Optimism Governor contract.

```solidity
IOptimismGovernor public immutable GOVERNOR;
```

`proposalTypesConfigurator`

The proposal types configurator contract.

```solidity
IProposalTypesConfigurator public proposalTypesConfigurator;
```

`proposalDistributionThreshold`

The maximum amount of tokens a proposal can request.

```solidity
uint256 public proposalDistributionThreshold;
```

`votingCycles`

A mapping that stores the data for each voting cycle.

```solidity
mapping(uint256 => VotingCycleData) public votingCycles;
```

`proposalTypesData`

A mapping that stores data related to each proposal type.

```solidity
mapping(ProposalType => ProposalTypeData) public proposalTypesData;
```

`_proposals`

A mapping that stores each submitted proposal's data based on its `proposalHash`. The proposal hash is produced by hashing
the ABI encoded values of specific proposal params, see [Proposal uniqueness](#proposal-uniqueness).

```solidity
mapping(bytes32 => ProposalData) private _proposals;
```

### Structs

`ProposalData`

A struct that holds all the data for a single proposal. Consists of:

- `proposer`: The address that submitted the proposal
- `proposalType`: The type of the proposal
- `inVoting`: Returns true if the proposal has already been submitted for voting
- `delegateApprovals`: Mapping of addresses that approved the specific proposal
- `approvalCount`: The number of approvals the specific proposal has received
- `votingCycle`: The voting cycle number the proposal is targeted for.

```solidity
struct ProposalData {
    address proposer;
    ProposalType proposalType;
    bool movedToVote;
    mapping(address => bool) delegateApprovals;
    uint256 approvalCount;
    uint256 votingCycle;
}
```

`ProposalTypeData`

A struct that holds data for each proposal type.

- `requiredApprovals`: The number of approvals each proposal type requires in order to be able to move for voting.
- `proposalVotingModule`: The proposal type ID used to get the voting module from the configurator.
This is set by the owner on initialize.

```solidity
struct ProposalTypeData {
    uint256 requiredApprovals;
    uint8 proposalVotingModule;
}
```

`VotingCycleData`

A struct that stores data related to the voting cycle.

- `startingTimestamp`: The starting timestamp of the voting cycle.
- `duration`: The duration of the specific voting cycle
- `votingCycleDistributionLimit`: A more general distribution amount limit tied to the voting cycle
- `movedToVoteTokenCount` The total amount of tokens to possibly be distributed in the voting cycle

```solidity
struct VotingCycleData {
    uint256 startingTimestamp;
    uint256 duration;
    uint256 votingCycleDistributionLimit;
    uint256 movedToVoteTokenCount;
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

MUST be triggered when a proposal submission is successfully called.

```solidity
event ProposalSubmitted(
    bytes32 indexed proposalHash,
    address indexed proposer,
    string description,
    ProposalType proposalType
);
```

`ProposalApproved`

MUST be triggered when `approveProposal` is successfully called.

```solidity
event ProposalApproved(bytes32 indexed proposalHash, address indexed approver);
```

`ProposalMovedToVote`

MUST be triggered when `moveToVote` is successfully called.

```solidity
event ProposalMovedToVote(bytes32 indexed proposalHash, address indexed executor);
```

`ProposalVotingModuleData`

MUST be triggered with `ProposalSubmitted` event.

```solidity
event ProposalVotingModuleData(bytes32 indexed proposalHash, bytes encodedVotingModuleData);
```

## EAS Integration

`ProposalValidator` integrates Ethereum Attestation Service (EAS) to handle proposer authorization for specific
`ProposalType`s, and authentication of the top100 delegates for approving a proposal, removing the need for adding
custom logic to the contract.

## Why EAS?

- **Decentralized trust**: Instead of custom logic, Optimism uses attestations signed by the Foundation to authorize
  proposers.
- **Low integration overhead**: `EAS` and `SchemaRegistry` are predeploys on Optimism, requiring no additional deployments
  or infrastructure.
- **Schema validation**: Ensures attestations follow strict data formats (e.g. `uint8 proposalType, string date`).
- **Revocability and expiration**: EAS supports expiration and revocation semantics natively, allowing dynamic control over
  authorized proposers.

## Implementation Details

### Submit Proposal

For the submit proposals we will need to register a new schema as described at `ATTESTATION_SCHEMA_UID_APPROVED_PROPOSERS`.
The submit proposal functions validates attestations by:
- Ensuring the attestation UID matches the registered schema.
- Verifying the attester is the contract owner (Optimism Foundation).
- Decoding the attestation to check the proposer's address and proposal type.
- Only proposals of type `ProtocolOrGovernorUpgrade`, `MaintenanceUpgradeProposals`, and `CouncilMemberElections`
require valid EAS attestations.

### Approve Proposal

For the top100 delegates we will be using an existing schema that was created by the [dynamic attestation service](https://github.com/CuriaLab/dynamic_attestation_mvp).
The approve proposal function validates attestations by:
- Ensuring the attestation UID matches the registered schema.
- Verifying the attester is the contract owner (Optimism Foundation).
- Decoding the attestation to check the targets address.

**Technical implementation docs: [EAS Integration](https://www.notion.so/EAS-Integration-1de9a4c092c780478e19cc8175aa054e?pvs=21)**

## Proposal uniqueness

To prevent duplicate proposals, the contract enforces uniqueness by hashing the defining parameters of each proposal and
checking against a registry of previously submitted proposals, creating a proposalId. The proposal ID should be the same
as the one created on `Governor.hashProposalWithModule` and used by the `Voting Modules`.

A proposal is uniquely identified by a tuple:

- `governor`: The address of the Governor
- `module`: The address of the voting module the proposal uses
- `proposalVotingModuleData`: The encoded voting module data
- `descriptionHash`: The hash of the description

These elements are ABI-encoded and hashed:

```solidity
keccak256(abi.encode(governor, module, proposalVotingModuleData, descriptionHash));
```

This hash serves as a unique identifier for the proposal. The contract stores submitted proposals in:

```solidity
mapping(bytes32 => ProposalData) private _proposals;
```

When a new proposal is submitted, the contract checks that `_proposals[proposalHash]` is empty (e.g., `proposer ==
address(0)`). If data exists at that key, the proposal is rejected as a duplicate.

This mechanism guarantees that proposals with the same intent and execution logic cannot be submitted multiple times,
maintaining proposal integrity and preventing spam.

## Invariants

- It MUST allow only the `owner` to set the `votingCycleData`, `proposalDistributionThreshold`, and
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
  configuring voting cycles, and distribution limits. Any compromise could significantly impact governance.
- **Attestation Validation:** Two key aspects need consideration:
  - The Optimism Foundation must have a secure and thorough process for validating addresses before issuing attestations
    for specific proposal types
  - The contract must properly verify attestation expiration and revocation status to prevent the use of outdated or
    invalid attestations
- **Dynamic Attestation Service:** Since we rely on the dynamic attestation service for updating the top100 delegates
  we need to ensure that the service will be running and updating the attestations at least during the governance cycles.
