# Safe Contract Extensions V2

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Definitions](#definitions)
  - [Quorum](#quorum)
  - [Blocking Threshold](#blocking-threshold)
  - [Active Owner](#active-owner)
  - [Honest Owner](#honest-owner)
  - [Malicious Owner](#malicious-owner)
  - [Full Key Control](#full-key-control)
  - [Joint Key Control](#joint-key-control)
  - [Temporary Key Control](#temporary-key-control)
  - [Multisig Liveness Failure](#multisig-liveness-failure)
  - [Multisig Safety Failure](#multisig-safety-failure)
- [Definitions in Liveness Module](#definitions-in-liveness-module)
  - [Fallback Owner](#fallback-owner)
  - [Liveness Challenge](#liveness-challenge)
  - [Liveness Challenge Period](#liveness-challenge-period)
  - [Successful Challenge](#successful-challenge)
- [Definitions in Timelock Guard](#definitions-in-timelock-guard)
  - [Scheduled Transaction](#scheduled-transaction)
  - [Scheduling Time](#scheduling-time)
  - [Timelock Delay Period](#timelock-delay-period)
  - [Execution Time](#execution-time)
  - [Rejected Transaction](#rejected-transaction)
  - [Rejecting Owners](#rejecting-owners)
  - [Cancellation Threshold](#cancellation-threshold)
- [Assumptions](#assumptions)
  - [aSS-001: Dishonest Users Don't Have Permanent Key Control Over a Quorum of Keys](#ass-001-dishonest-users-dont-have-permanent-key-control-over-a-quorum-of-keys)
    - [Severity: Critical](#severity-critical)
  - [aSS-002: The Fallback Owner is Honest](#ass-002-the-fallback-owner-is-honest)
    - [Severity: Medium to High](#severity-medium-to-high)
  - [aSS-003: The Fallback Owner is Active](#ass-003-the-fallback-owner-is-active)
- [Invariants](#invariants)
  - [iSS-001: Honest Users Can Recover From Temporary Key Control Over a Quorum of Keys](#iss-001-honest-users-can-recover-from-temporary-key-control-over-a-quorum-of-keys)
    - [Severity: High](#severity-high)
  - [iSS-002: The `safe` Chooses The Fallback](#iss-002-the-safe-chooses-the-fallback)
    - [Severity: High](#severity-high-1)
  - [iSS-003: A Quorum Of Honest Users Retains Ownership](#iss-003-a-quorum-of-honest-users-retains-ownership)
    - [Severity: Medium](#severity-medium)
  - [iSS-004: The Liveness Challenge Period Is Greater Than The Timelock Delay](#iss-004-the-liveness-challenge-period-is-greater-than-the-timelock-delay)
    - [Severity: Medium](#severity-medium-1)
  - [iSS-005: Allowing Challenges Is Elective](#iss-005-allowing-challenges-is-elective)
    - [Severity: Medium](#severity-medium-2)
  - [iSS-006: No Challenge Spam](#iss-006-no-challenge-spam)
    - [Severity: Medium](#severity-medium-3)
  - [iSS-007: Honest Users Can Recover From Temporary Key Control Over a Quorum of Keys](#iss-007-honest-users-can-recover-from-temporary-key-control-over-a-quorum-of-keys)
    - [Severity: Critical](#severity-critical-1)
  - [iSS-008: The Execution Time Doesn't Change](#iss-008-the-execution-time-doesnt-change)
    - [Severity: Medium](#severity-medium-4)
  - [iSS-009: Owners Of Child Safes Can Signal Rejection Of Transactions](#iss-009-owners-of-child-safes-can-signal-rejection-of-transactions)
    - [Severity: Medium](#severity-medium-5)
  - [iSS-010: The Signatures For A Cancelled Transaction Can Not Be Reused](#iss-010-the-signatures-for-a-cancelled-transaction-can-not-be-reused)
    - [Severity: Medium](#severity-medium-6)
  - [iSS-011: Only Owners Can Signal Rejection Of Transactions](#iss-011-only-owners-can-signal-rejection-of-transactions)
    - [Severity: Low](#severity-low)
- [Function Specification](#function-specification)
  - [`configureLivenessModule`](#configurelivenessmodule)
  - [`clearLivenessModule`](#clearlivenessmodule)
  - [`configureTimelockGuard`](#configuretimelockguard)
  - [`clearTimelockGuard`](#cleartimelockguard)
  - [`viewLivenessModuleConfiguration`](#viewlivenessmoduleconfiguration)
  - [`viewTimelockGuardConfiguration`](#viewtimelockguardconfiguration)
  - [`getLivenessChallengePeriodEnd`](#getlivenesschallengeperiodend)
  - [`challenge`](#challenge)
  - [`respond`](#respond)
  - [`changeOwnershipToFallback`](#changeownershiptofallback)
  - [`cancellationThreshold`](#cancellationthreshold)
  - [`scheduleTransaction`](#scheduletransaction)
  - [`checkTransaction`](#checktransaction)
  - [`checkPendingTransactions`](#checkpendingtransactions)
  - [`rejectTransaction`](#rejecttransaction)
  - [`rejectTransactionWithSignature`](#rejecttransactionwithsignature)
  - [`cancelTransaction`](#canceltransaction)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->
This document describes extensions to the Security Council and Guardian Safe contracts, which
provide additional functionality and security guarantees on top of those provided by the Safe
contract.

These extensions are developed using a singleton contract that can be enabled simultaneously as a
([module](https://docs.safe.global/advanced/smart-account-modules) and a
[guard](https://docs.safe.global/advanced/smart-account-guards)) which the Safe contract has built-in support for:

1. **Guard contracts:** can execute pre- and post- transaction checks.
2. **Module contracts:** a contract which is
   authorized to execute transactions via the Safe. This means the liveness module must properly implement
   auth conditions internally.

The extension contract specificationis compatible with the 
[V1.5.0](https://github.com/safe-global/safe-contracts/releases/tag/v1.5.0) Safe contract version.

When enabled as a guard, the extension contract implements a mandatory delay on the execution of transactions. When
enabled as a module, the extension contract ensures a multisig remains operable by allowing challenges when it becomes
unresponsive. If the multisig fails to prove liveness within a set period, ownership transfers to a trusted fallback
 owner to prevent deadlock.

 As a best practice, the fallback owner should have stronger security guarantees than the safe enabling the extensions.

The extensions in this document are intended to replace the extensions in the
[Safe Contract Extensions](./safe-extensions.md) document.

For more information about the Security Council and Guardian roles, refer to the
[Stage One Roles and Requirements](./stage-1.md) document.

## Definitions

The following list defines variables that will be used in the Safe Extensions V2.

### Quorum

The number of owners required to execute a transaction.

### Blocking Threshold

The minimum number of owners not willing to execute a transaction, that by not approving the transaction guarantee
that `quorum` is not met. It is defined as `min(quorum, total_owners - quorum + 1)`.

### Active Owner

An owner that is able to approve transactions.

### Honest Owner

An owner that is never willing to execute transactions outside of governance processes.

### Malicious Owner

An owner that is willing to execute transactions outside of governance processes.

### Full Key Control

An actor has full key control of an owner if it is solely able to approve transactions as that owner.

### Joint Key Control

An actor has joint key control of an owner if it is able, along with other actors, to approve transactions as that
owner.

### Temporary Key Control

An actor has temporary key control of an owner if it is able to approve a limited set or number of transactions as
that owner.

### Multisig Liveness Failure

A multisig is considered to be in a liveness failure state if the number of active honest owners is less than the
`quorum`, or if the number of malicious active owners is equal or greater than the `blocking_threshold`.

### Multisig Safety Failure

A multisig is considered to be in a safety failure state if the number of active malicious owners is equal or greater
than `quorum`.

## Definitions in Liveness Module

The following lists definitions that will be used in LivenessModule specifically.

### Fallback Owner

The owner that is appointed to take control of a multisig in case of a liveness or safety failure.

### Liveness Challenge

A challenge to a multisig to prove that it is not in a liveness failure state.

### Liveness Challenge Period

The `liveness_challenge_period(safe)` is the minimum period of time that must pass without a response since a liveness
challenge for a liveness failure state to be assumed, which is equal to the sum of the `timelock_delay(safe)` plus the
`liveness_challenge_period(safe)`.

### Successful Challenge

A challenge is considered to be successful if `liveness_challenge_period(safe)` has passed and the multisig did not
prove that it is not in a liveness failure state.

## Definitions in Timelock Guard

The following list defines variables that will be used in TimelockGuard specifically.

### Safe

The `safe` is the Safe contract that is being extended.

### Tx Hash

The `txHash` is the hash of all the transaction data as calculated by the Safe contract.

### Scheduled Transaction

A specific transaction that has been stored in the Timelock, for execution from a given safe.

### Scheduling Time

The `scheduling_time(safe, tx)` is the time in seconds of the block in which a transaction was scheduled for execution
from a given safe.

### Timelock Delay Period

Given a scheduled transaction, the `timelock_delay(safe)` is the minimum time in seconds after
`scheduling_time(safe, tx)` that execution is allowed.

### Execution Time

The `execution_time(safe, tx)` is the sum of `scheduling_time(safe, tx)` and `timelock_delay(safe)`.

### Rejected Transaction

Given a transaction scheduled to execute from given safe, owners for the safe reject the transaction to signal they
think the transaction should not be executed after the `timelock_delay(safe)`.

### Rejecting Owners

Given a transaction scheduled to execute from given safe, the `rejecting_owners(safe, tx)` are the owners for the safe
that rejected the transaction.

### Cancellation Threshold

The `cancellation_threshold(safe)` is the number of owners that must reject a given transaction for it not to be
executed after the `timelock_delay(safe)`. It starts at 1 for each safe, increasing by 1 with each consecutive
cancelled transaction by the given safe up to the minimum of `blocking_threshold(safe)` and `quorum(safe)`, resetting
to 1 with each successfully executed transaction by the given safe.

The upper bound of the `cancellation_threshold(safe)` is `blocking_threshold(safe)` because at that point the absent
or malicious owners force the safe into a liveness failure, and the LivenessModule should be used.

The upper bound of the `cancellation_threshold(safe)` is also `quorum(safe)` because at that point the safe is in a
safety failure, and the LivenessModule should be used if there are enough honest owners left to cancel the challenge
responses. If a malicious party has control over a quorum of keys, and is capable of indefinitely respond to liveness
challenges, other security mechanisms should be used to protect the protocol or its users.

## Assumptions

### aSS-001: Dishonest Users Don't Have Permanent Key Control Over a Quorum of Keys

We assume that dishonest users have at most a temporary joint key control over a quorum of keys.

#### Severity: Critical

If this invariant is broken, honest control of the multisig is lost.

### aSS-002: The Fallback Owner is Honest

The fallback owner is chosen by the multisig which can verify that it is honest.

#### Severity: Medium to High

If this assumption is false and not known to be false, the LivenessModule is not able to recover the multisig from a
liveness failure state until a new fallback owner is chosen.

If this assumption is false but not known to be false, and a challenge is successful, the multisig would enter into a
safety failure state.

### aSS-003: The Fallback Owner is Active

The fallback owner is assumed to be active.

## Invariants

### iSS-001: Honest Users Can Recover From Temporary Key Control Over a Quorum of Keys

If an attacker has full, joint, or temporary key control over less than a quorum of keys, honest users should always
be able to recover the account by transferring ownership to the fallback owner

#### Severity: High

If this invariant is broken, an attacker with temporary key control over less than a quorum of keys could force the
multisig into a temporary safety failure state.

### iSS-002: The `safe` Chooses The Fallback

Each `safe` MUST choose its fallback address. No other account should be allowed to do this.

#### Severity: High

If this invariant is broken, control over the multisig would be lost in the case of a liveness failure.

### iSS-003: A Quorum Of Honest Users Retains Ownership

While a quorum of honest users exist, they should remain in control of the account.

#### Severity: Medium

If this invariant is broken, there would be an operational and possibly reputational impact while the ownership of the
account is reestablished to the account owners.

### iSS-004: The Liveness Challenge Period Is Greater Than The Timelock Delay

The `liveness_challenge_period(safe)` MUST be greater than the `timelock_delay(safe)`.

#### Severity: Medium

If this invariant is broken, it would not be possible to respond to challenges, and ownership could be transferred to
the fallback owner even if the multisig is not in a liveness failure state.

### iSS-005: Allowing Challenges Is Elective

A `safe` MUST choose to be open to liveness challenges at any time, and CAN choose to stop accepting liveness
challenges at any time.

#### Severity: Medium

If this invariant is broken, there would be an operational and possibly reputational impact while the ownership of the
account is reestablished to the account owners.

### iSS-006: No Challenge Spam

For an enabled `safe`, there can't be more challenges that are needed to guarantee liveness.

#### Severity: Medium

If this invariant is broken, an attacker could spam the multisig with challenges, driving it into a temporary liveness
failure state, which could be used to force ownership into the fallback address.

### iSS-007: Honest Users Can Recover From Temporary Key Control Over a Quorum of Keys

If an attacker has joint or temporary key control over a quorum of keys, honest users should always be able to recover
the account.

#### Severity: Critical

If this invariant is broken, honest control of the multisig is lost.

### iSS-008: The Execution Time Doesn't Change

For a given transaction, the `execution_time(safe, tx)` must never change.

#### Severity: Medium

If this invariant is broken, a temporary compromise of the safe could be used to skip the timelock delay.

### iSS-009: Owners Of Child Safes Can Signal Rejection Of Transactions

A nested safe setup is a safe (parent safe) in which one or more owners are a Gnosis Safe (child safes). There can be
multiple levels of nesting. The one parent safe that is not a child of any other safe is called a root safe.

For a given transaction in a root safe within a nested safe setup, a scheduled transaction could be rejected by owners
in child safes an arbitrary number of levels away. The `cancellation_threshold(safe)` of a child safe must be
considered before registering that the child safe is rejecting the transaction.

#### Severity: Medium

If this invariant is broken, the cancellation flow would be not operational for nested setups, making the timelock less
useful.

### iSS-010: The Signatures For A Cancelled Transaction Can Not Be Reused

The signatures for a cancelled transaction can not be reused.

#### Severity: Medium

If this invariant is broken, a malicious user could spam the multisig with transactions that must be cancelled,
causing an impact close to a liveness failure through operational overhead.

### iSS-011: Only Owners Can Signal Rejection Of Transactions

To avoid rejection spamming, it must be verified upon rejection that the rejecting owner is an owner in the safe
scheduled to execute the transaction, or in one of its child safes.

#### Severity: Low

If this invariant is broken, the event history of the timelock would contain useless events.

## Function Specification

### Liveness Module

The Liveness Module is the same contract as the Timelock Guard, but the function specification is in its own section
for clarity.

#### `version`

Returns the semantic contract version.

- MUST never revert.

#### `livenessSafeConfiguration`

Returns the `liveness_challenge_period` and `fallback_owner` for a given `safe`.

- MUST never revert.

#### `challengeStartTime`

Returns `challenge_start_time` if there is a challenge for the given `safe`, or 0 if not.

- MUST never revert.

#### `getLivenessChallengePeriodEnd`

Returns `challenge_start_time + liveness_challenge_period + timelock_delay` if there is a challenge for the given
`safe`, or 0 if not.

- MUST never revert.

#### `configureLivenessModule`

Configure the contract as a liveness module for a given `safe` by setting the `liveness_challenge_period` and
`fallback_owner`.

- MUST allow an arbitrary number of `safe` contracts to use the contract as a module.
- The contract MUST be enabled as a module on the `safe`.
- MUST set the caller as a `safe`.
- MUST take `liveness_challenge_period` and `fallback_owner` as parameters and store them as related to the `safe`.
- If a challenge exists, it MUST be canceled, including emitting the appropriate events.
- MUST emit a `ModuleConfigured` event with at least `liveness_challenge_period` and `fallback_owner` as parameters.

#### `clearLivenessModule`

Removes the liveness module configuration by a previously enabled `safe`.

- The contract MUST be configured for the `safe`.
- The contract MUST NOT be enabled as a module on the `safe`.
- MUST erase the existing `liveness_challenge_period` and `fallback_owner` data related to the calling `safe`.
- If a challenge exists, it MUST be cancelled, including emitting the appropriate events.
- MUST emit a `ModuleCleared` event.

#### `challenge`

Challenges an enabled `safe` to prove that it is not in a liveness failure state.

- MUST only be executable by `fallback` owner of the challenged `safe`.
- MUST revert if the `safe` hasn't enabled the contract as a module.
- MUST revert if the `safe` hasn't configured the module for the `safe`.
- MUST revert if a challenge for the `safe` exists.
- MUST set `challenge_start_time` to the current block time.
- MUST emit the `ChallengeStarted` event.

#### `respond`

Cancels a challenge for an enabled `safe`.

- MUST revert if the `safe` hasn't enabled the contract as a module.
- MUST revert if the `safe` hasn't configured the module for the `safe`.
- MUST revert if there isn't a challenge for the calling `safe`.
- MUST reset `challenge_start_time` to 0.
- MUST emit the `ChallengeCancelled` event.

#### `changeOwnershipToFallback`

With a successful challenge, removes all current owners from an enabled `safe`, appoints `fallback` as its sole owner,
and sets its quorum to 1.

- MUST only be executable by `fallback` owner of the challenged `safe`.
- MUST revert if the `safe` hasn't enabled the contract as a module.
- MUST revert if the `safe` hasn't configured the module for the `safe`.
- MUST revert if there isn't a successful challenge for the given `safe`.
- MUST reset `challenge_start_time` to 0 to enable the fallback to start a new challenge.
- MUST set the `fallback_owner` as the sole owner of the `safe`.
- MUST set the quorum of the `safe` to 1.
- MUST emit the `ChallengeExecuted` event.

### Timelock Guard

The Timelock Guard is the same contract as the Liveness Module, but the function specification is in its own section
for clarity.

#### `version`

Returns the semantic contract version.

- MUST never revert.

#### `timelockSafeConfiguration`

Returns the `timelock_delay` for a given `safe`.

- MUST never revert.

#### `cancellationThreshold`

Returns the `cancellation_threshold` for a given `safe`.

- MUST NOT revert
- MUST return 0 if the contract is not enabled as a guard for the `safe`.

#### `getScheduledTransaction`

Returns the scheduled transaction for a given `safe` and `txHash`.

- MUST NOT revert
- MUST return an empty transaction if the transaction is not scheduled.

#### `getAllScheduledTransactions`

Called by anyone, returns the list of all scheduled but not cancelled or executed transactions for a given safe.

- MUST NOT revert
- MUST return the list of all scheduled but not cancelled or executed transactions for the given `safe`.

#### `configureTimelockGuard`

Configure the contract as a timelock guard by setting the `timelock_delay`.

- MUST allow an arbitrary number of `safe` contracts to use the contract as a guard.
- MUST revert if the contract is not enabled as a guard for the `safe`.
- MUST revert if `timelock_delay` is longer than 1 year.
- MUST set the caller as a `safe`.
- MUST take `timelock_delay` as a parameter and store is as related to the `safe`.
- MUST set the `cancellation_threshold` to 1.
- MUST emit a `GuardConfigured` event with at least `timelock_delay` as a parameter.

#### `clearTimelockGuard`

Remove the timelock guard configuration by a previously enabled `safe`.

- MUST revert if the contract is enabled as a guard for the `safe`.
- MUST revert if the contract is not configured for the `safe`.
- MUST erase the existing `timelock_delay` data related to the calling `safe`.
- MUST emit a `GuardCleared` event.

#### `scheduleTransaction`

Called by anyone using signatures from Safe owners, registers a transaction in the TimelockGuard for execution after
the `timelock_delay`.

- MUST revert if the contract is not enabled as a guard for the `safe`.
- MUST revert if the contract is not configured for the `safe`.
- MUST take the same parameters as `execTransaction`.
- MUST revert if an identical transaction has already been scheduled.
- MUST revert if an identical transaction was cancelled.
- MUST set `execution_time(safe, txHash)` to `block.timestamp + timelock_delay(safe)`.
- MUST emit a `TransactionScheduled` event, with at least `safe` and relevant transaction data.

#### `cancelTransaction`

Makes a scheduled transaction not executable. To do so, it builds a no-op transaction at the same nonce as the
scheduled transaction, and verifies that the supplied signatures for such a no-op transaction are valid and amount to
`cancellation_threshold(safe)`. If successful, it increases the `cancellation_threshold(safe)` by 1.

- MUST revert if the contract is not enabled as a guard for the `safe`.
- MUST revert if the contract is not configured for the `safe`.
- MUST revert if `sum(rejecting_owners(safe, tx)) < cancellation_threshold(safe)`.
- MUST emit a `TransactionCancelled` event, with at least `safe` and a transaction identifier.

#### `checkTransaction`

Can be called by anyone. It will be called by the `safe` in `execTransaction` if the contract is enabled as a guard.
It verifies if a given transaction was scheduled and the delay period has passed, and reverts if not.

- MUST revert if the contract is not enabled as a guard for the `safe`.
- MUST revert if the contract is not configured for the `safe`.
- MUST take the exact parameters from the `ITransactionGuard.checkTransaction` interface.
- MUST revert if `execution_time(safe, tx) < block.timestamp`.
- MUST revert if the scheduled transaction was cancelled.

#### `checkAfterExecution`

Can be called by anyone. It will be called by the `safe` in `execTransaction` if the contract is enabled as a guard.
It updates state after the transaction has been executed.

- MUST take the exact parameters from the `ITransactionGuard.checkTransaction` interface.
- MUST revert if the contract is not enabled as a guard for the `safe`. // TODO: I'm not sure if we want to ever revert here
- MUST revert if the contract is not configured for the `safe`. // TODO: I'm not sure if we want to ever revert here
- MUST set `cancellation_threshold(safe)` to 1.
