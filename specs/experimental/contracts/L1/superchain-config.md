# SuperchainConfig

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
  - [Guardian](#guardian)
  - [Pause Identifier](#pause-identifier)
  - [Pause Expiry](#pause-expiry)
- [Assumptions](#assumptions)
  - [aSUPC-001: Guardian operates within governance constraints](#asupc-001-guardian-operates-within-governance-constraints)
    - [Mitigations](#mitigations)
- [Invariants](#invariants)
  - [iSUPC-001: Guardian exclusive control over pause operations](#isupc-001-guardian-exclusive-control-over-pause-operations)
    - [Impact](#impact)
  - [iSUPC-002: Pause expiry ensures temporary nature](#isupc-002-pause-expiry-ensures-temporary-nature)
    - [Impact](#impact-1)
  - [iSUPC-003: Pause identifier cannot be re-paused without reset](#isupc-003-pause-identifier-cannot-be-re-paused-without-reset)
    - [Impact](#impact-2)
- [Function Specification](#function-specification)
  - [initialize](#initialize)
  - [guardian](#guardian)
  - [pauseExpiry](#pauseexpiry)
  - [pause](#pause)
  - [unpause](#unpause)
  - [extend](#extend)
  - [pausable](#pausable)
  - [paused](#paused)
  - [paused (legacy)](#paused-legacy)
  - [expiration](#expiration)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The SuperchainConfig contract manages global pause functionality for multiple OP Stack chains within a Superchain
network. It enables emergency response through a time-limited pause mechanism controlled by a designated Guardian role.

## Definitions

### Guardian

The privileged role authorized to execute pause operations (pause, unpause, extend). In the Superchain, this role is
held by the Optimism Security Council. See [Guardian](../../protocol/stage-1.md#guardian) for complete definition.

### Pause Identifier

An address parameter that determines the scope of pause operations. The zero address (`address(0)`) applies pauses
globally to all chains sharing the SuperchainConfig contract, while non-zero addresses target specific chains or chain
sets. See [Pause Identifier](../../protocol/stage-1.md#pause-identifier) for complete definition.

### Pause Expiry

The fixed duration of 7,884,000 seconds (approximately 3 months) after which an active pause automatically expires and
the system becomes unpaused. This ensures all pauses are temporary and cannot cause indefinite liveness failures.

## Assumptions

### aSUPC-001: Guardian operates within governance constraints

The Guardian role holder acts in accordance with established governance processes and only triggers pause operations in
response to legitimate security threats or protocol bugs.

#### Mitigations

- Guardian role is held by the Optimism Security Council, a multisig with established governance procedures
- All Guardian actions are publicly visible on-chain through emitted events
- Pause mechanism automatically expires after [Pause Expiry](#pause-expiry), limiting impact of any misuse

## Invariants

### iSUPC-001: Guardian exclusive control over pause operations

Only the [Guardian](#guardian) address can execute the `pause()`, `unpause()`, and `extend()` functions. No other
address, including the contract owner or ProxyAdmin, can trigger these operations.

#### Impact

**Severity: High**

If violated, unauthorized actors could trigger pause operations, potentially causing unintended withdrawal liveness
failures or preventing legitimate Guardian responses to security threats. This depends on assumption aSUPC-001 holding.

### iSUPC-002: Pause expiry ensures temporary nature

Every pause for a given [Pause Identifier](#pause-identifier) automatically expires after [Pause Expiry](#pause-expiry)
duration from the pause timestamp. After expiry, the system returns to unpaused state without requiring Guardian
intervention.

#### Impact

**Severity: Critical**

If violated, pauses could become permanent, causing indefinite withdrawal liveness failures and violating Stage 1
decentralization requirements. The automatic expiry mechanism is essential for ensuring the pause mechanism cannot be
used to permanently lock user funds.

### iSUPC-003: Pause identifier cannot be re-paused without reset

Once a [Pause Identifier](#pause-identifier) has a non-zero pause timestamp, the `pause()` function reverts when called
with that identifier. The pause must be explicitly reset through `unpause()`, `extend()`, or automatic expiry before
`pause()` can be called again for that identifier.

#### Impact

**Severity: Medium**

If violated, the pause timestamp could be silently updated without explicit Guardian action, potentially causing
confusion about pause status and expiry times. This protection ensures clear audit trails and prevents accidental
timestamp resets.

## Function Specification

### initialize

Initializes the contract with the [Guardian](#guardian) address. This function can only be called once per
initialization version due to the reinitializer pattern.

**Parameters:**

- `_guardian`: Address to be granted the Guardian role

**Behavior:**

- MUST revert if caller is not the ProxyAdmin or ProxyAdmin owner
- MUST revert if already initialized at the current initialization version
- MUST set the `guardian` storage variable to `_guardian`
- MUST emit `ConfigUpdate` event with `UpdateType.GUARDIAN` and the guardian address

### guardian

Returns the address of the current [Guardian](#guardian).

**Behavior:**

- MUST return the address stored in the `guardian` storage variable
- MAY be called by any address

### pauseExpiry

Returns the [Pause Expiry](#pause-expiry) duration constant.

**Behavior:**

- MUST return 7,884,000 (seconds)
- MAY be called by any address

### pause

Triggers the pause mechanism for a specific [Pause Identifier](#pause-identifier). Sets the pause timestamp to the
current block timestamp, starting the expiry countdown.

**Parameters:**

- `_identifier`: The [Pause Identifier](#pause-identifier) address to pause

**Behavior:**

- MUST revert if caller is not the [Guardian](#guardian)
- MUST revert if `pauseTimestamps[_identifier]` is non-zero (already paused)
- MUST set `pauseTimestamps[_identifier]` to `block.timestamp`
- MUST emit `Paused` event with `_identifier`

### unpause

Explicitly unpauses the system for a specific [Pause Identifier](#pause-identifier), resetting the pause timestamp to
zero. This allows the identifier to be paused again immediately.

**Parameters:**

- `_identifier`: The [Pause Identifier](#pause-identifier) address to unpause

**Behavior:**

- MUST revert if caller is not the [Guardian](#guardian)
- MUST set `pauseTimestamps[_identifier]` to 0
- MUST emit `Unpaused` event with `_identifier`
- MAY be called even if the identifier is not currently paused

### extend

Extends an active pause by resetting the pause timestamp to the current block timestamp, restarting the
[Pause Expiry](#pause-expiry) countdown from the current time.

**Parameters:**

- `_identifier`: The [Pause Identifier](#pause-identifier) address to extend

**Behavior:**

- MUST revert if caller is not the [Guardian](#guardian)
- MUST revert if `pauseTimestamps[_identifier]` is zero (not currently paused)
- MUST set `pauseTimestamps[_identifier]` to `block.timestamp`
- MUST emit `Paused` event with `_identifier`

### pausable

Checks whether a [Pause Identifier](#pause-identifier) can currently be paused. Returns true only if the identifier has
no active pause timestamp.

**Parameters:**

- `_identifier`: The [Pause Identifier](#pause-identifier) address to check

**Behavior:**

- MUST return `true` if `pauseTimestamps[_identifier]` equals 0
- MUST return `false` if `pauseTimestamps[_identifier]` is non-zero
- MAY be called by any address

### paused

Checks whether the system is currently paused for a specific [Pause Identifier](#pause-identifier), accounting for
expiry. A pause is considered active only if the pause timestamp is non-zero and the current time is before the
expiration time.

**Parameters:**

- `_identifier`: The [Pause Identifier](#pause-identifier) address to check

**Behavior:**

- MUST return `false` if `pauseTimestamps[_identifier]` equals 0
- MUST return `true` if `pauseTimestamps[_identifier]` is non-zero AND `block.timestamp` is less than
  `pauseTimestamps[_identifier] + PAUSE_EXPIRY`
- MUST return `false` if `pauseTimestamps[_identifier]` is non-zero AND `block.timestamp` is greater than or equal to
  `pauseTimestamps[_identifier] + PAUSE_EXPIRY`
- MAY be called by any address

### paused (legacy)

Legacy function providing backward compatibility for systems that check global pause status without specifying an
identifier. Equivalent to calling `paused(address(0))`.

**Behavior:**

- MUST return the result of `paused(address(0))`
- MAY be called by any address

### expiration

Returns the timestamp at which the pause for a given [Pause Identifier](#pause-identifier) will expire. Returns 0 if
the identifier is not currently paused.

**Parameters:**

- `_identifier`: The [Pause Identifier](#pause-identifier) address to check

**Behavior:**

- MUST return 0 if `pauseTimestamps[_identifier]` equals 0
- MUST return `pauseTimestamps[_identifier] + PAUSE_EXPIRY` if `pauseTimestamps[_identifier]` is non-zero
- MAY be called by any address
