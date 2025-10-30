# FaultDisputeGame

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
  - [Split Depth](#split-depth)
  - [Game Tree Position](#game-tree-position)
  - [Absolute Prestate](#absolute-prestate)
  - [Chess Clock](#chess-clock)
  - [Subgame](#subgame)
  - [Bond Distribution Mode](#bond-distribution-mode)
- [Assumptions](#assumptions)
  - [a01-001: Anchor State Registry Provides Valid Anchor States](#a01-001-anchor-state-registry-provides-valid-anchor-states)
    - [Mitigations](#mitigations)
  - [a01-002: Virtual Machine Executes State Transitions Correctly](#a01-002-virtual-machine-executes-state-transitions-correctly)
    - [Mitigations](#mitigations-1)
  - [a01-003: DelayedWETH Contract Functions Correctly](#a01-003-delayedweth-contract-functions-correctly)
    - [Mitigations](#mitigations-2)
- [Invariants](#invariants)
  - [i01-001: Game Resolution Reflects Root Claim Validity](#i01-001-game-resolution-reflects-root-claim-validity)
    - [Impact](#impact)
  - [i01-002: Claims Cannot Be Resolved Out Of Order](#i01-002-claims-cannot-be-resolved-out-of-order)
    - [Impact](#impact-1)
  - [i01-003: Successful Steps Permanently Counter Claims](#i01-003-successful-steps-permanently-counter-claims)
    - [Impact](#impact-2)
  - [i01-004: Bond Distribution Matches Game Outcome](#i01-004-bond-distribution-matches-game-outcome)
    - [Impact](#impact-3)
  - [i01-005: L2 Block Number Challenge Overrides Root Claim](#i01-005-l2-block-number-challenge-overrides-root-claim)
    - [Impact](#impact-4)
  - [i01-006: Game Finalization Requires Resolution And Time Delay](#i01-006-game-finalization-requires-resolution-and-time-delay)
    - [Impact](#impact-5)
- [Function Specification](#function-specification)
  - [initialize](#initialize)
  - [step](#step)
  - [attack](#attack)
  - [defend](#defend)
  - [move](#move)
  - [addLocalData](#addlocaldata)
  - [challengeRootL2Block](#challengerootl2block)
  - [resolve](#resolve)
  - [resolveClaim](#resolveclaim)
  - [claimCredit](#claimcredit)
  - [closeGame](#closegame)
  - [getRequiredBond](#getrequiredbond)
  - [getChallengerDuration](#getchallengerduration)
  - [getNumToResolve](#getnumtoresolve)
  - [l2BlockNumber](#l2blocknumber)
  - [l2SequenceNumber](#l2sequencenumber)
  - [startingBlockNumber](#startingblocknumber)
  - [startingRootHash](#startingroothash)
  - [gameType](#gametype)
  - [gameCreator](#gamecreator)
  - [rootClaim](#rootclaim)
  - [l1Head](#l1head)
  - [extraData](#extradata)
  - [gameData](#gamedata)
  - [claimDataLen](#claimdatalen)
  - [credit](#credit)
  - [absolutePrestate](#absoluteprestate)
  - [maxGameDepth](#maxgamedepth)
  - [splitDepth](#splitdepth)
  - [maxClockDuration](#maxclockduration)
  - [clockExtension](#clockextension)
  - [vm](#vm)
  - [weth](#weth)
  - [anchorStateRegistry](#anchorstateregistry)
  - [l2ChainId](#l2chainid)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The FaultDisputeGame contract implements a bisection-based dispute resolution mechanism for verifying L2 output root
claims through iterative narrowing of disagreement ranges until reaching single instruction steps that can be verified
on-chain via a fault proof virtual machine.

## Definitions

### Split Depth

The maximum depth in the game tree at which claims represent output roots. Below this depth, claims represent
execution trace commitments for single block state transitions.

### Game Tree Position

A location in the binary game tree represented by a generalized index where the high-order bit indicates depth and
remaining bits provide a unique identifier for each node at that depth.

### Absolute Prestate

The initial state of the fault proof virtual machine that serves as the starting point for all execution traces. This
is a constant defined by the VM implementation being used.

### Chess Clock

A timing mechanism where each claim inherits the accumulated duration from its grandparent claim, tracking total time
elapsed for each team to prevent indefinite delays in game resolution.

### Subgame

A directed acyclic graph of depth one where a root claim and its direct children form a fundamental dispute unit. A
claim is considered countered if at least one of its children remains uncountered after resolution.

### Bond Distribution Mode

The mechanism for distributing bonds after game finalization, which can be NORMAL (bonds distributed to winners) or
REFUND (bonds returned to original depositors) based on whether the game is determined to be proper by the Anchor
State Registry.

## Assumptions

### a01-001: Anchor State Registry Provides Valid Anchor States

The Anchor State Registry provides valid anchor output roots that serve as the starting point for dispute games.

#### Mitigations

- Anchor states are only updated through resolved dispute games that pass finalization requirements
- The registry maintains a history of anchor states with associated game references

### a01-002: Virtual Machine Executes State Transitions Correctly

The fault proof virtual machine (VM) correctly executes single instruction steps and produces accurate post-states when
given valid pre-states and proofs.

#### Mitigations

- VM implementations undergo extensive testing and formal verification
- Multiple VM implementations can be used for different game types

### a01-003: DelayedWETH Contract Functions Correctly

The DelayedWETH contract correctly holds bonds, enforces withdrawal delays, and processes unlock and withdrawal
operations as specified.

#### Mitigations

- DelayedWETH is a well-tested contract with delay mechanisms to prevent immediate bond extraction
- Bonds are locked until game finalization provides sufficient time for dispute resolution

## Invariants

### i01-001: Game Resolution Reflects Root Claim Validity

After resolution, the game status accurately reflects whether the root claim was successfully defended (DEFENDER_WINS)
or successfully challenged (CHALLENGER_WINS) based on the subgame resolution tree.

#### Impact

**Severity: Critical**

If this invariant is violated, invalid output roots could be accepted or valid output roots could be rejected,
compromising the integrity of the L2 state validation system and potentially enabling theft of funds through invalid
withdrawals.

### i01-002: Claims Cannot Be Resolved Out Of Order

Subgames must be resolved bottom-up in the directed acyclic graph, ensuring all child subgames are resolved before
their parent subgame can be resolved.

#### Impact

**Severity: Critical**

Violating this invariant could allow premature resolution of parent claims before their children are properly
evaluated, leading to incorrect game outcomes and improper bond distribution.

### i01-003: Successful Steps Permanently Counter Claims

Once a claim at maximum game depth is successfully countered via the step function, it remains countered and cannot be
stepped against again.

#### Impact

**Severity: High**

If claims could be stepped against multiple times, attackers could repeatedly challenge valid claims or defenders could
repeatedly defend invalid claims, preventing proper game resolution.

### i01-004: Bond Distribution Matches Game Outcome

Bonds are distributed according to the bond distribution mode (NORMAL or REFUND) determined by whether the game is
proper and finalized, with NORMAL mode distributing to winners and REFUND mode returning to original depositors.

#### Impact

**Severity: High**

Incorrect bond distribution undermines the economic incentives that ensure honest participation in the dispute game
system.

### i01-005: L2 Block Number Challenge Overrides Root Claim

When the root claim's L2 block number is successfully challenged via challengeRootL2Block, the root claim is always
considered countered regardless of other subgame outcomes.

#### Impact

**Severity: Critical**

This ensures that root claims with incorrect L2 block numbers cannot be used to finalize invalid state transitions,
preventing potential consensus failures.

### i01-006: Game Finalization Requires Resolution And Time Delay

Games can only be closed and have their bond distribution mode determined after they are resolved and the finalization
delay period has elapsed according to the Anchor State Registry.

#### Impact

**Severity: High**

Premature finalization could prevent legitimate challenges from being processed, allowing invalid claims to be accepted
before proper dispute resolution completes.

## Function Specification

### initialize

Initializes the dispute game with the root claim and establishes the anchor state from the Anchor State Registry.

**Behavior:**

- MUST revert if the game has already been initialized
- MUST revert if the Anchor State Registry returns a zero anchor root
- MUST revert if the calldata length is not exactly 122 bytes
- MUST revert if the root claim's L2 block number is less than or equal to the anchor state's block number
- MUST create the root claim at position 1 with the game creator as claimant and msg.value as bond
- MUST deposit the bond into the DelayedWETH contract
- MUST record the bond in refundModeCredit for the game creator
- MUST set createdAt to the current block timestamp
- MUST record whether the game type was respected when created

### step

Executes a single instruction step via the on-chain fault proof virtual machine to counter a claim at maximum game
depth.

**Parameters:**

- `_claimIndex`: The index of the claim being stepped against
- `_isAttack`: Whether the step is an attack or defense
- `_stateData`: The preimage of the pre-state claim
- `_proof`: Proof data for accessing the VM's merkle state tree

**Behavior:**

- MUST revert if the game status is not IN_PROGRESS
- MUST revert if the step position depth is not exactly MAX_GAME_DEPTH + 1
- MUST revert if the keccak256 hash of _stateData does not match the pre-state claim (ignoring highest order byte)
- MUST revert if the VM step execution result indicates a valid step
- MUST revert if the parent claim has already been countered
- MUST set the parent claim's counteredBy field to msg.sender

### attack

Creates an attack move against a disagreed upon claim.

**Parameters:**

- `_disputed`: The claim being attacked
- `_parentIndex`: Index of the claim to attack
- `_claim`: The claim at the relative attack position

**Behavior:**

- MUST call the move function with _isAttack set to true
- MUST include msg.value as the bond payment

### defend

Creates a defense move supporting an agreed upon claim and its parent.

**Parameters:**

- `_disputed`: The claim being defended
- `_parentIndex`: Index of the claim to defend
- `_claim`: The claim at the relative defense position

**Behavior:**

- MUST call the move function with _isAttack set to false
- MUST include msg.value as the bond payment

### move

Generic move function handling both attack and defend moves.

**Parameters:**

- `_disputed`: The disputed claim
- `_challengeIndex`: The index of the claim being moved against
- `_claim`: The claim at the next logical position
- `_isAttack`: Whether the move is an attack or defense

**Behavior:**

- MUST revert if the game status is not IN_PROGRESS
- MUST revert if the claim at `_challengeIndex` does not match `_disputed`
- MUST revert if attempting to defend the root claim or an execution trace bisection root claim
- MUST revert if the root claim has been challenged via challengeRootL2Block and `_challengeIndex` is 0
- MUST revert if the next position depth exceeds MAX_GAME_DEPTH
- MUST verify execution bisection root claims when next position depth equals SPLIT_DEPTH + 1
- MUST revert if msg.value does not exactly equal the required bond for the next position
- MUST revert if the challenger's clock duration equals MAX_CLOCK_DURATION
- MUST revert if a claim with the same value and position already exists at the challenge index
- MUST apply clock extension if the next duration would leave less than the extension time remaining
- MUST create a new claim with the provided parameters and current timestamp
- MUST add the new claim index to the parent's subgame array
- MUST deposit msg.value into DelayedWETH
- MUST record msg.value in refundModeCredit for msg.sender
- MUST emit a Move event

### addLocalData

Posts local data to the VM's PreimageOracle for use during execution trace verification.

**Parameters:**

- `_ident`: The local identifier of the data to post
- `_execLeafIdx`: The index of the leaf claim in an execution subgame requiring the data
- `_partOffset`: The offset of the data to post

**Behavior:**

- MUST revert if the game status is not IN_PROGRESS
- MUST revert if _ident is not a valid local preimage key identifier
- MUST compute the local context UUID from the starting and disputed outputs
- MUST load the appropriate data into the PreimageOracle based on _ident

### challengeRootL2Block

Challenges the root claim by proving the L2 block number in the output root does not match the claimed L2 block number.

**Parameters:**

- `_outputRootProof`: The output root proof containing state root, message passer storage root, and latest block hash
- `_headerRLP`: The RLP-encoded L2 block header

**Behavior:**

- MUST revert if the game status is not IN_PROGRESS
- MUST revert if the L2 block number has already been challenged
- MUST revert if the hash of _outputRootProof does not match the root claim
- MUST revert if the keccak256 hash of _headerRLP does not match the latest block hash in the proof
- MUST revert if the block number extracted from the header RLP is longer than 32 bytes
- MUST revert if the extracted block number matches the claimed L2 block number
- MUST set l2BlockNumberChallenger to msg.sender
- MUST set l2BlockNumberChallenged to true

### resolve

Resolves the entire game and determines the final outcome.

**Behavior:**

- MUST revert if the game status is not IN_PROGRESS
- MUST revert if the root subgame has not been resolved
- MUST set status to DEFENDER_WINS if the root claim is uncountered
- MUST set status to CHALLENGER_WINS if the root claim is countered
- MUST set resolvedAt to the current block timestamp
- MUST emit a Resolved event with the final status

### resolveClaim

Resolves a subgame rooted at a specific claim by checking its children.

**Parameters:**

- `_claimIndex`: The index of the subgame root claim to resolve
- `_numToResolve`: The number of children to check in this call

**Behavior:**

- MUST revert if the game status is not IN_PROGRESS
- MUST revert if the challenger's clock duration is less than MAX_CLOCK_DURATION
- MUST revert if the subgame has already been resolved
- MUST revert if any child subgame is not yet resolved
- MUST distribute bonds to the claimant for uncontested claims with no children
- MUST distribute bonds to the counteredBy address for claims countered via step
- MUST track the leftmost uncountered child position across resolution iterations
- MUST mark the subgame as resolved when all children have been checked
- MUST distribute bonds to the L2 block number challenger if the root claim was challenged that way
- MUST set the claim's counteredBy field based on resolution outcome

### claimCredit

Claims accumulated credit for a recipient after game finalization.

**Parameters:**

- `_recipient`: The address to claim credit for

**Behavior:**

- MUST call closeGame to ensure bond distribution mode is determined
- MUST revert if the recipient has no credit to claim after unlocking
- MUST unlock credit in DelayedWETH if the recipient has not yet unlocked
- MUST withdraw the credit amount from DelayedWETH
- MUST transfer the credit amount to the recipient
- MUST revert if the transfer fails
- MUST set both refundModeCredit and normalModeCredit to zero for the recipient

### closeGame

Determines the bond distribution mode and attempts to register the game as the anchor game.

**Behavior:**

- MUST return early if bond distribution mode is already REFUND or NORMAL
- MUST revert if bond distribution mode is not UNDECIDED
- MUST revert if the Anchor State Registry is paused
- MUST revert if the game has not been resolved
- MUST revert if the game is not finalized according to the Anchor State Registry
- MUST attempt to set the game as the anchor state in the registry
- MUST set bond distribution mode to NORMAL if the game is proper
- MUST set bond distribution mode to REFUND if the game is not proper
- MUST emit a GameClosed event with the bond distribution mode

### getRequiredBond

Calculates the required bond amount for a move at a given position.

**Parameters:**

- `_position`: The position of the bonded interaction

**Behavior:**

- MUST revert if the position depth exceeds MAX_GAME_DEPTH
- MUST calculate bond using exponential scaling based on position depth
- MUST return bond amount in wei

### getChallengerDuration

Returns the time elapsed on the potential challenger's chess clock for a claim.

**Parameters:**

- `_claimIndex`: The index of the subgame root claim

**Behavior:**

- MUST revert if the game status is not IN_PROGRESS
- MUST calculate duration from parent clock duration plus time since claim creation
- MUST cap the returned duration at MAX_CLOCK_DURATION

### getNumToResolve

Returns the number of children remaining to be checked for resolving a subgame.

**Parameters:**

- `_claimIndex`: The subgame root claim's index

**Behavior:**

- MUST return the difference between total children and the resolution checkpoint's subgame index

### l2BlockNumber

Returns the L2 block number from the extraData.

**Behavior:**

- MUST extract and return the L2 block number from the clone-with-immutable-args data at offset 84

### l2SequenceNumber

Returns the L2 sequence number which equals the L2 block number.

**Behavior:**

- MUST return the same value as l2BlockNumber

### startingBlockNumber

Returns the starting block number from the anchor state.

**Behavior:**

- MUST return the l2SequenceNumber from startingOutputRoot

### startingRootHash

Returns the starting output root hash from the anchor state.

**Behavior:**

- MUST return the root hash from startingOutputRoot

### gameType

Returns the game type identifier.

**Behavior:**

- MUST return the GAME_TYPE immutable value

### gameCreator

Returns the address that created the dispute game.

**Behavior:**

- MUST extract and return the creator address from clone-with-immutable-args data at offset 0

### rootClaim

Returns the root claim being disputed.

**Behavior:**

- MUST extract and return the root claim from clone-with-immutable-args data at offset 20

### l1Head

Returns the L1 block hash when the game was created.

**Behavior:**

- MUST extract and return the L1 head hash from clone-with-immutable-args data at offset 52

### extraData

Returns the extra data provided when creating the game.

**Behavior:**

- MUST extract and return 32 bytes of extra data from clone-with-immutable-args data at offset 84

### gameData

Returns the complete game identification data.

**Behavior:**

- MUST return the game type, root claim, and extra data as a tuple

### claimDataLen

Returns the length of the claimData array.

**Behavior:**

- MUST return the current length of the claimData array

### credit

Returns the credit balance for a recipient based on current bond distribution mode.

**Parameters:**

- `_recipient`: The address to check credit for

**Behavior:**

- MUST return refundModeCredit if bond distribution mode is REFUND
- MUST return normalModeCredit otherwise

### absolutePrestate

Returns the absolute prestate of the instruction trace.

**Behavior:**

- MUST return the ABSOLUTE_PRESTATE immutable value

### maxGameDepth

Returns the maximum game depth.

**Behavior:**

- MUST return the MAX_GAME_DEPTH immutable value

### splitDepth

Returns the split depth.

**Behavior:**

- MUST return the SPLIT_DEPTH immutable value

### maxClockDuration

Returns the maximum clock duration.

**Behavior:**

- MUST return the MAX_CLOCK_DURATION immutable value

### clockExtension

Returns the clock extension constant.

**Behavior:**

- MUST return the CLOCK_EXTENSION immutable value

### vm

Returns the address of the fault proof virtual machine.

**Behavior:**

- MUST return the VM immutable value

### weth

Returns the DelayedWETH contract address.

**Behavior:**

- MUST return the WETH immutable value

### anchorStateRegistry

Returns the Anchor State Registry contract address.

**Behavior:**

- MUST return the ANCHOR_STATE_REGISTRY immutable value

### l2ChainId

Returns the L2 chain ID this game argues about.

**Behavior:**

- MUST return the L2_CHAIN_ID immutable value
