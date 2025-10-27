# L2CrossDomainMessenger

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
  - [Message Hash](#message-hash)
  - [Message Nonce](#message-nonce)
  - [Cross-Domain Message Sender](#cross-domain-message-sender)
- [Assumptions](#assumptions)
  - [a01-001: L1CrossDomainMessenger Configuration](#a01-001-l1crossdomainmessenger-configuration)
    - [Mitigations](#mitigations)
  - [a01-002: L2ToL1MessagePasser Integrity](#a01-002-l2tol1messagepasser-integrity)
    - [Mitigations](#mitigations-1)
  - [a01-003: Address Aliasing Correctness](#a01-003-address-aliasing-correctness)
    - [Mitigations](#mitigations-2)
- [Invariants](#invariants)
  - [i01-001: Message Replay Prevention](#i01-001-message-replay-prevention)
    - [Impact](#impact)
  - [i01-002: Failed Message Replayability](#i01-002-failed-message-replayability)
    - [Impact](#impact-1)
  - [i01-003: Cross-Chain Message Authentication](#i01-003-cross-chain-message-authentication)
    - [Impact](#impact-2)
  - [i01-004: System Address Protection](#i01-004-system-address-protection)
    - [Impact](#impact-3)
  - [i01-005: Nonce Monotonicity](#i01-005-nonce-monotonicity)
    - [Impact](#impact-4)
- [Function Specification](#function-specification)
  - [initialize](#initialize)
  - [sendMessage](#sendmessage)
  - [relayMessage](#relaymessage)
  - [xDomainMessageSender](#xdomainmessagesender)
  - [l1CrossDomainMessenger](#l1crossdomainmessenger)
  - [OTHER_MESSENGER](#other_messenger)
  - [messageNonce](#messagenonce)
  - [baseGas](#basegas)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The L2CrossDomainMessenger provides a high-level interface for sending and receiving messages between L2 and L1.
It enables cross-chain communication by wrapping lower-level messaging primitives with replay protection and
sender authentication.

## Definitions

### Message Hash

A unique identifier for a cross-chain message, computed from the message nonce, sender, target, value, gas limit,
and message data. Used to track message execution status and prevent replay attacks.

### Message Nonce

A monotonically increasing counter that uniquely identifies each message sent from this messenger. The nonce is
versioned, with the first two bytes encoding the message version.

### Cross-Domain Message Sender

The address on the originating chain that initiated the currently executing cross-chain message. Only available
during message relay execution.

## Assumptions

### a01-001: L1CrossDomainMessenger Configuration

The paired L1CrossDomainMessenger address is correctly configured during initialization and remains unchanged.

#### Mitigations

- Initialization is protected by the initializer modifier to prevent reinitialization
- The otherMessenger address is immutable after initialization

### a01-002: L2ToL1MessagePasser Integrity

The L2ToL1MessagePasser predeploy at address 0x4200000000000000000000000000000000000016 correctly processes
withdrawal initiations.

#### Mitigations

- L2ToL1MessagePasser is a core protocol predeploy with well-defined behavior
- Address is hardcoded and cannot be changed

### a01-003: Address Aliasing Correctness

The AddressAliasHelper correctly implements the L1-to-L2 address aliasing scheme used to identify messages from
the L1CrossDomainMessenger.

#### Mitigations

- AddressAliasHelper is a standard library used across the OP Stack
- Aliasing scheme is deterministic and well-tested

## Invariants

### i01-001: Message Replay Prevention

A message that has been successfully relayed cannot be relayed again.

#### Impact

**Severity: Critical**

Violation would allow attackers to replay successful messages, potentially draining funds or executing unauthorized
actions multiple times.

### i01-002: Failed Message Replayability

A message that has failed relay execution can be replayed until it succeeds, but only if it originally came from
the other messenger.

#### Impact

**Severity: High**

Violation would either prevent legitimate message recovery (if failed messages cannot be replayed) or allow
unauthorized replay of failed messages (if replay protection is insufficient).

### i01-003: Cross-Chain Message Authentication

Messages can only be relayed if they originate from the paired L1CrossDomainMessenger (verified via address
aliasing) or are valid replays of previously failed messages.

#### Impact

**Severity: Critical**

Violation would allow arbitrary addresses to inject malicious messages, bypassing the intended cross-chain
security model.

### i01-004: System Address Protection

Messages cannot target the L2CrossDomainMessenger itself or the L2ToL1MessagePasser predeploy.

#### Impact

**Severity: High**

Violation could allow attackers to manipulate messenger state or interfere with the withdrawal mechanism,
potentially breaking message replay protection or withdrawal processing.

### i01-005: Nonce Monotonicity

The message nonce increases by exactly one for each message sent, ensuring unique message identification.

#### Impact

**Severity: High**

Violation would break message uniqueness guarantees, potentially allowing message hash collisions or replay
attacks.

## Function Specification

### initialize

Initializes the L2CrossDomainMessenger with the paired L1CrossDomainMessenger address.

**Parameters:**

- `_l1CrossDomainMessenger`: Address of the L1CrossDomainMessenger contract on L1

**Behavior:**

- MUST only be callable once due to the initializer modifier
- MUST set the otherMessenger to the provided L1CrossDomainMessenger address
- MUST initialize xDomainMsgSender to the default value (0x000000000000000000000000000000000000dEaD)
  if not already set

### sendMessage

Sends a message to a target address on L1.

**Parameters:**

- `_target`: Target contract or wallet address on L1
- `_message`: Calldata to send to the target
- `_minGasLimit`: Minimum gas limit for executing the message on L1

**Behavior:**

- MUST accept ETH value to be sent with the message
- MUST compute the total gas limit using baseGas() to ensure sufficient gas for relay
- MUST encode a call to relayMessage with the current nonce, sender, target, value, gas limit, and message
- MUST call L2ToL1MessagePasser.initiateWithdrawal with the encoded message and ETH value
- MUST emit SentMessage event with target, sender, message, nonce, and gas limit
- MUST emit SentMessageExtension1 event with sender and value
- MUST increment msgNonce by one after sending

### relayMessage

Relays a message sent from L1 to its target address on L2.

**Parameters:**

- `_nonce`: Nonce of the message being relayed
- `_sender`: Address that sent the message on L1
- `_target`: Target address on L2
- `_value`: ETH value to send with the message
- `_minGasLimit`: Minimum gas limit for executing the message
- `_message`: Calldata to send to the target

**Behavior:**

- MUST revert if the contract is paused (always false on L2)
- MUST revert if the message version (extracted from nonce) is greater than 1
- MUST check for legacy version 0 message replay and revert if already relayed
- MUST compute the version 1 message hash from all parameters
- MUST verify the caller is the L1CrossDomainMessenger (via address aliasing) for initial relay, or verify the
  message previously failed for replay attempts
- MUST revert if msg.value is non-zero for replay attempts
- MUST revert if the target is the L2CrossDomainMessenger itself or the L2ToL1MessagePasser
- MUST revert if the message has already been successfully relayed
- MUST mark the message as failed and emit FailedRelayedMessage if insufficient gas is available or if
  reentrancy is detected (xDomainMsgSender is not the default value)
- MUST revert if tx.origin is the estimation address (0x000000000000000000000000000000000000Aaaa) when
  marking as failed
- MUST set xDomainMsgSender to the sender address before the external call
- MUST call the target with the remaining gas minus RELAY_RESERVED_GAS and the provided value and message
- MUST reset xDomainMsgSender to the default value after the call
- MUST mark the message as successful and emit RelayedMessage if the call succeeds
- MUST mark the message as failed and emit FailedRelayedMessage if the call fails
- MUST revert if tx.origin is the estimation address when the call fails

### xDomainMessageSender

Returns the address that initiated the currently executing cross-chain message.

**Behavior:**

- MUST revert if no message is currently being executed (xDomainMsgSender equals the default value)
- MUST return the xDomainMsgSender address when a message is being executed

### l1CrossDomainMessenger

Returns the paired L1CrossDomainMessenger address.

**Behavior:**

- MUST return the otherMessenger address

### OTHER_MESSENGER

Returns the paired L1CrossDomainMessenger address (legacy getter).

**Behavior:**

- MUST return the otherMessenger address

### messageNonce

Returns the nonce for the next message to be sent, with the message version encoded in the upper two bytes.

**Behavior:**

- MUST return the current msgNonce with MESSAGE_VERSION (1) encoded in the upper two bytes

### baseGas

Computes the total gas required to guarantee a message can be relayed without running out of gas.

**Parameters:**

- `_message`: Message data
- `_minGasLimit`: Minimum gas limit for the target call

**Behavior:**

- MUST calculate execution gas including relay overhead, call overhead, reserved gas, gas check buffer, and the
  minimum gas limit adjusted for EIP-150 (64/63 rule)
- MUST calculate total message size including the message length and encoding overhead
- MUST return the maximum of the base transaction gas plus execution gas with calldata overhead, or the base
  transaction gas plus the calldata floor cost (per EIP-7623)
