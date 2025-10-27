# L2CrossDomainMessenger

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
  - [Message Hash](#message-hash)
  - [Message Nonce](#message-nonce)
  - [Address Aliasing](#address-aliasing)
  - [Failed Message](#failed-message)
- [Assumptions](#assumptions)
  - [a01-001: L1CrossDomainMessenger is trusted](#a01-001-l1crossdomainmessenger-is-trusted)
    - [Mitigations](#mitigations)
  - [a01-002: L2ToL1MessagePasser correctly handles withdrawals](#a01-002-l2tol1messagepasser-correctly-handles-withdrawals)
    - [Mitigations](#mitigations-1)
- [Invariants](#invariants)
  - [i01-001: Message replay protection](#i01-001-message-replay-protection)
    - [Impact](#impact)
  - [i01-002: Failed message replay capability](#i01-002-failed-message-replay-capability)
    - [Impact](#impact-1)
  - [i01-003: Message nonce monotonicity](#i01-003-message-nonce-monotonicity)
    - [Impact](#impact-2)
  - [i01-004: Cross-chain message authentication](#i01-004-cross-chain-message-authentication)
    - [Impact](#impact-3)
- [Function Specification](#function-specification)
  - [initialize](#initialize)
  - [sendMessage](#sendmessage)
  - [relayMessage](#relaymessage)
  - [xDomainMessageSender](#xdomainmessagesender)
  - [l1CrossDomainMessenger](#l1crossdomainmessenger)
  - [OTHER_MESSENGER](#other_messenger)
  - [messageNonce](#messagenonce)
  - [baseGas](#basegas)
  - [successfulMessages](#successfulmessages)
  - [failedMessages](#failedmessages)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The L2CrossDomainMessenger provides a high-level interface for sending and receiving cross-chain messages between
L2 and L1. It is deployed as a predeploy contract and handles message authentication, replay protection, and failed
message recovery for L2-to-L1 and L1-to-L2 communication.

## Definitions

### Message Hash

A unique identifier for a cross-chain message computed from the message nonce, sender, target, value, gas limit, and
message data. Version 1 messages use `hashCrossDomainMessageV1` which commits to all parameters including value and
gas limit.

### Message Nonce

A monotonically increasing counter that uniquely identifies each message sent from the messenger. The nonce includes
a version identifier in the upper 2 bytes, allowing for different message formats.

### Address Aliasing

A transformation applied to L1 addresses when they send transactions to L2, adding a constant offset to prevent
address collisions between L1 and L2 contracts. The messenger uses `undoL1ToL2Alias` to recover the original L1
address from an aliased sender.

### Failed Message

A message that was received and attempted for execution but failed during the target contract call. Failed messages
are marked in the `failedMessages` mapping and can be replayed by anyone without requiring cross-chain
authentication.

## Assumptions

### a01-001: L1CrossDomainMessenger is trusted

The L1CrossDomainMessenger contract on L1 is trusted to correctly authenticate and relay messages according to the
protocol specification.

#### Mitigations

- The L1CrossDomainMessenger address is set during initialization and cannot be changed
- Messages are validated using address aliasing to ensure they originate from the correct L1 contract

### a01-002: L2ToL1MessagePasser correctly handles withdrawals

The L2ToL1MessagePasser predeploy contract correctly initiates withdrawals and includes them in the L2 state for
proof generation on L1.

#### Mitigations

- L2ToL1MessagePasser is a system predeploy with well-defined behavior
- The messenger only calls the `initiateWithdrawal` function with validated parameters

## Invariants

### i01-001: Message replay protection

Successfully relayed messages cannot be executed again. Once a message hash is marked as successful, any attempt to
relay the same message will revert.

#### Impact

**Severity: Critical**

Without replay protection, an attacker could re-execute messages multiple times, potentially draining funds or
causing unauthorized state changes on the target contract.

### i01-002: Failed message replay capability

Messages that fail during target execution can be replayed by anyone. The replay does not require cross-chain
authentication and can be attempted with different gas amounts until successful.

#### Impact

**Severity: High**

If failed messages could not be replayed, users would permanently lose access to funds or messages sent cross-chain,
as there would be no recovery mechanism for transient failures.

### i01-003: Message nonce monotonicity

Message nonces increase monotonically for each message sent. Each message has a unique nonce that cannot be reused
or skipped.

#### Impact

**Severity: High**

Non-monotonic nonces could enable message reordering attacks or allow attackers to predict and front-run message
hashes, potentially breaking replay protection or causing messages to be processed out of order.

### i01-004: Cross-chain message authentication

Messages relayed from L1 to L2 are authenticated by verifying the sender is the aliased L1CrossDomainMessenger
address. Messages cannot be spoofed or injected by unauthorized parties.

#### Impact

**Severity: Critical**

Without proper authentication, attackers could forge messages claiming to originate from any L1 address, bypassing
all cross-chain security and enabling arbitrary unauthorized actions on L2.

## Function Specification

### initialize

Initializes the L2CrossDomainMessenger with the address of the L1CrossDomainMessenger.

**Parameters:**

- `_l1CrossDomainMessenger`: Address of the L1CrossDomainMessenger contract on L1

**Behavior:**

- MUST only be callable once due to the `initializer` modifier
- MUST set the `otherMessenger` to the provided L1CrossDomainMessenger address
- MUST initialize the `xDomainMsgSender` to the default value (0x000000000000000000000000000000000000dEaD)
  if it has not been set

### sendMessage

Sends a message to a target address on L1.

**Parameters:**

- `_target`: Target contract or wallet address on L1
- `_message`: Calldata to send to the target
- `_minGasLimit`: Minimum gas limit for executing the message on L1

**Behavior:**

- MUST accept ETH value sent with the transaction
- MUST calculate the total gas required using `baseGas(_message, _minGasLimit)`
- MUST encode the message with `relayMessage` selector and all parameters
- MUST call `L2ToL1MessagePasser.initiateWithdrawal` with the encoded message and ETH value
- MUST emit `SentMessage` event with target, sender, message, nonce, and gas limit
- MUST emit `SentMessageExtension1` event with sender and value
- MUST increment the message nonce after sending

### relayMessage

Relays a message sent from L1 to L2 and executes it on the target contract.

**Parameters:**

- `_nonce`: Nonce of the message being relayed
- `_sender`: Address of the user who sent the message on L1
- `_target`: Address that the message is targeted at on L2
- `_value`: ETH value to send with the message
- `_minGasLimit`: Minimum amount of gas that the message can be executed with
- `_message`: Message calldata to send to the target

**Behavior:**

- MUST revert if the contract is paused (always returns false on L2)
- MUST revert if the message version is greater than 1
- MUST check for legacy version 0 message replay and revert if already relayed
- MUST compute the version 1 message hash from all parameters
- MUST verify the caller is the aliased L1CrossDomainMessenger address for initial relay attempts
- MUST verify `msg.value` equals `_value` for initial relay attempts
- MUST verify `msg.value` is zero for replay attempts
- MUST verify the message is marked as failed for replay attempts
- MUST revert if the target is an unsafe address (the messenger itself or L2ToL1MessagePasser)
- MUST revert if the message has already been successfully relayed
- MUST mark the message as failed if insufficient gas is available for execution
- MUST mark the message as failed if `xDomainMsgSender` is not the default value (reentrancy detected)
- MUST set `xDomainMsgSender` to the sender address before calling the target
- MUST call the target with the remaining gas minus `RELAY_RESERVED_GAS`, the value, and the message
- MUST reset `xDomainMsgSender` to the default value after the call
- MUST mark the message as successful and emit `RelayedMessage` if the call succeeds
- MUST mark the message as failed and emit `FailedRelayedMessage` if the call fails
- MUST revert if the transaction origin is the estimation address and the call fails

### xDomainMessageSender

Returns the address of the sender of the currently executing cross-chain message.

**Behavior:**

- MUST revert if no message is currently being executed (xDomainMsgSender is the default value)
- MUST return the sender address of the currently executing message

### l1CrossDomainMessenger

Returns the address of the L1CrossDomainMessenger contract.

**Behavior:**

- MUST return the `otherMessenger` address

### OTHER_MESSENGER

Returns the address of the paired CrossDomainMessenger contract on L1.

**Behavior:**

- MUST return the `otherMessenger` address

### messageNonce

Returns the nonce for the next message to be sent, with the message version encoded in the upper 2 bytes.

**Behavior:**

- MUST return the current `msgNonce` with the `MESSAGE_VERSION` encoded in the upper 2 bytes

### baseGas

Calculates the minimum gas required to guarantee a message will be received on L1 without running out of gas.

**Parameters:**

- `_message`: Message calldata
- `_minGasLimit`: Minimum desired gas limit when message is executed

**Behavior:**

- MUST calculate execution gas including relay overhead, call overhead, reserved gas, and EIP-150 adjustment
- MUST calculate total message size including encoding overhead
- MUST apply EIP-7623 transaction cost formula with calldata floor
- MUST return the maximum of execution cost and calldata floor cost plus base transaction gas

### successfulMessages

Returns whether a message hash has been successfully relayed.

**Parameters:**

- Message hash (bytes32)

**Behavior:**

- MUST return true if the message was successfully relayed, false otherwise

### failedMessages

Returns whether a message hash has failed at least once during relay.

**Parameters:**

- Message hash (bytes32)

**Behavior:**

- MUST return true if the message has failed at least once, false otherwise
