# L2CrossDomainMessenger

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
- [Assumptions](#assumptions)
  - [a01-001: L1CrossDomainMessenger trusted](#a01-001-l1crossdomainmessenger-trusted)
    - [Mitigations](#mitigations)
  - [a01-002: L2ToL1MessagePasser availability](#a01-002-l2tol1messagepasser-availability)
    - [Mitigations](#mitigations-1)
- [Invariants](#invariants)
  - [i01-001: Cross-chain message authentication](#i01-001-cross-chain-message-authentication)
    - [Impact](#impact)
  - [i01-002: Message replay protection](#i01-002-message-replay-protection)
    - [Impact](#impact-1)
  - [i01-003: Failed message replay capability](#i01-003-failed-message-replay-capability)
    - [Impact](#impact-2)
  - [i01-004: Message nonce monotonicity](#i01-004-message-nonce-monotonicity)
    - [Impact](#impact-3)
- [Function Specification](#function-specification)
  - [initialize](#initialize)
  - [sendMessage](#sendmessage)
  - [relayMessage](#relaymessage)
  - [xDomainMessageSender](#xdomainmessagesender)
  - [messageNonce](#messagenonce)
  - [baseGas](#basegas)
  - [l1CrossDomainMessenger](#l1crossdomainmessenger)
  - [OTHER_MESSENGER](#other_messenger)
  - [paused](#paused)
  - [successfulMessages](#successfulmessages)
  - [failedMessages](#failedmessages)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The L2CrossDomainMessenger provides a high-level interface for sending messages between L2 and L1. It enables
developers to send arbitrary cross-chain messages with replay protection and authentication, abstracting the
lower-level withdrawal mechanism.

## Definitions

N/A

## Assumptions

### a01-001: L1CrossDomainMessenger trusted

The paired L1CrossDomainMessenger contract on L1 is trusted to only relay valid messages that were legitimately
sent from L2.

#### Mitigations

- L1CrossDomainMessenger validates withdrawal proofs through OptimismPortal
- Address aliasing ensures messages can only come from the paired messenger

### a01-002: L2ToL1MessagePasser availability

The L2ToL1MessagePasser predeploy contract at address 0x4200000000000000000000000000000000000016 is available and
correctly implements the initiateWithdrawal function.

#### Mitigations

- L2ToL1MessagePasser is a system predeploy deployed at genesis
- Contract address is hardcoded and immutable

## Invariants

### i01-001: Cross-chain message authentication

Messages relayed from L1 can only be executed if they originate from the paired L1CrossDomainMessenger contract.
Messages cannot be spoofed or relayed by unauthorized parties.

#### Impact

**Severity: Critical**

If this invariant is violated, attackers could forge cross-chain messages and execute arbitrary calls on L2 with
the authority of the messenger, potentially draining funds or compromising protocol security.

### i01-002: Message replay protection

Successfully relayed messages cannot be replayed. Each unique message (identified by its versioned hash) can only
be executed once across all attempts, whether successful or failed-then-replayed.

#### Impact

**Severity: Critical**

If this invariant is violated, attackers could replay withdrawal messages multiple times, potentially draining
funds from L1 or executing the same state changes repeatedly.

### i01-003: Failed message replay capability

Messages that fail during execution can be replayed by anyone without requiring cross-chain authentication. Failed
messages remain replayable until they succeed, enabling recovery from transient failures.

#### Impact

**Severity: High**

If failed messages could not be replayed, users would permanently lose access to funds or messages sent cross-chain,
as there would be no recovery mechanism for transient failures like insufficient gas or temporary contract issues.

### i01-004: Message nonce monotonicity

Message nonces increase monotonically for each message sent. Each message has a unique nonce that cannot be reused
or skipped, ensuring messages can be uniquely identified.

#### Impact

**Severity: High**

Non-monotonic nonces could enable message reordering attacks or allow attackers to predict and front-run message
hashes, potentially breaking replay protection or causing messages to be processed out of order.

## Function Specification

### initialize

Initializes the L2CrossDomainMessenger with the address of the paired L1CrossDomainMessenger.

**Parameters:**

- `_l1CrossDomainMessenger`: Address of the L1CrossDomainMessenger contract on L1

**Behavior:**

- MUST only be callable once due to initializer modifier
- MUST set the otherMessenger to the provided L1CrossDomainMessenger address
- MUST initialize xDomainMsgSender to the default value (0x000000000000000000000000000000000000dEaD) if not already
  set
- MUST disable further initialization attempts

### sendMessage

Sends a message from L2 to L1 by initiating a withdrawal through the L2ToL1MessagePasser.

**Parameters:**

- `_target`: Target contract or wallet address on L1
- `_message`: Calldata to send to the target address
- `_minGasLimit`: Minimum gas limit for executing the message on L1

**Behavior:**

- MUST accept ETH value sent with the transaction
- MUST calculate the required base gas using baseGas function
- MUST encode the message as a call to relayMessage on the L1CrossDomainMessenger
- MUST call initiateWithdrawal on the L2ToL1MessagePasser predeploy with the encoded message
- MUST forward any ETH value to the L2ToL1MessagePasser
- MUST emit SentMessage event with target, sender, message, current nonce, and minGasLimit
- MUST emit SentMessageExtension1 event with sender and ETH value
- MUST increment the message nonce after emission

### relayMessage

Relays a message that was sent from L1 via the L1CrossDomainMessenger.

**Parameters:**

- `_nonce`: Nonce of the message being relayed
- `_sender`: Address of the user who sent the message on L1
- `_target`: Address that the message is targeted at on L2
- `_value`: ETH value to send with the message
- `_minGasLimit`: Minimum amount of gas that the message can be executed with
- `_message`: Message calldata to send to the target

**Behavior:**

- MUST revert if the contract is paused (always returns false on L2)
- MUST revert if the message version is not 0 or 1
- MUST check for legacy version 0 message replay and revert if already relayed
- MUST compute the version 1 message hash for replay protection
- MUST verify the caller is the L1CrossDomainMessenger (via address aliasing) for first-time relay
- MUST verify msg.value equals `_value` when called by the L1CrossDomainMessenger
- MUST verify msg.value is zero when replaying a failed message
- MUST verify the message is marked as failed when replaying
- MUST revert if target is an unsafe system address (this contract or L2ToL1MessagePasser)
- MUST revert if the message has already been successfully relayed
- MUST mark message as failed if insufficient gas is available or if reentrancy is detected
- MUST set xDomainMsgSender to `_sender` before executing the call
- MUST execute the call to `_target` with the provided `_value` and `_message`
- MUST reset xDomainMsgSender to default value after the call
- MUST mark message as successful and emit RelayedMessage event if the call succeeds
- MUST mark message as failed and emit FailedRelayedMessage event if the call fails
- MUST revert if called from the estimation address (0x0000000000000000000000000000000000000000) and the message
  fails

### xDomainMessageSender

Returns the address of the sender of the currently executing cross-chain message.

**Behavior:**

- MUST revert if no message is currently being executed (xDomainMsgSender equals default value)
- MUST return the address of the original sender on L1 when called during message execution

### messageNonce

Returns the nonce for the next message to be sent, with the message version encoded in the upper two bytes.

**Behavior:**

- MUST return the current msgNonce with MESSAGE_VERSION (1) encoded in the upper 16 bits
- MUST be a view function with no state changes

### baseGas

Calculates the minimum gas required to guarantee a message will be received on L1 without running out of gas.

**Parameters:**

- `_message`: Message calldata
- `_minGasLimit`: Minimum desired gas limit when message is executed on target

**Behavior:**

- MUST calculate execution gas including relay overhead, call overhead, reserved gas, and EIP-150 adjustment
- MUST calculate total message size including encoding overhead
- MUST apply EIP-7623 transaction cost formula (floored by calldata size)
- MUST return the sum of base transaction gas and the maximum of execution gas and calldata floor gas
- MUST be a pure function with no state access

### l1CrossDomainMessenger

Legacy getter for the paired L1CrossDomainMessenger address.

**Behavior:**

- MUST return the address stored in otherMessenger
- MUST be a view function with no state changes

### OTHER_MESSENGER

Legacy getter for the paired CrossDomainMessenger address.

**Behavior:**

- MUST return the address stored in otherMessenger
- MUST be a view function with no state changes

### paused

Returns whether the contract is paused.

**Behavior:**

- MUST always return false on L2 (pausing is only enforced on L1)
- MUST be a view function with no state changes

### successfulMessages

Returns whether a message hash has been successfully relayed.

**Parameters:**

- Message hash (bytes32)

**Behavior:**

- MUST return true if the message was successfully relayed, false otherwise
- MUST be a view function with no state changes

### failedMessages

Returns whether a message hash has failed at least once during relay.

**Parameters:**

- Message hash (bytes32)

**Behavior:**

- MUST return true if the message has failed at least once, false otherwise
- MUST be a view function with no state changes
