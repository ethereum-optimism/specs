# Governor

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
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
  - [Scheduled Transaction](#scheduled-transaction)
  - [Scheduling Time](#scheduling-time)
  - [Delay Period](#delay-period)
  - [Rejected Transaction](#rejected-transaction)
  - [Rejecting Owners](#rejecting-owners)
  - [Cancellation Threshold](#cancellation-threshold)
- [Assumptions](#assumptions)
  - [aTG-001: Dishonest Users Don't Have Permanent Key Control Over a Quorum of Keys](#atg-001-dishonest-users-dont-have-permanent-key-control-over-a-quorum-of-keys)
    - [Severity: Critical](#severity-critical)
- [Invariants](#invariants)
  - [iTG-001: Honest Users Can Recover From Temporary Key Control Over a Quorum of Keys](#itg-001-honest-users-can-recover-from-temporary-key-control-over-a-quorum-of-keys)
    - [Severity: Critical](#severity-critical-1)
- [Requirements and Contraints](#requirements-and-contraints)
  - [Nested Cancellation](#nested-cancellation)
  - [Module Execution](#module-execution)
  - [Replayability Conflicts](#replayability-conflicts)
- [Function Specification](#function-specification)
  - [enable](#enable)
  - [disable](#disable)
  - [cancellationThreshold](#cancellationthreshold)
  - [delayPeriod](#delayperiod)
  - [scheduleTransaction](#scheduletransaction)
  - [checkTransaction](#checktransaction)
  - [checkModuleTransaction](#checkmoduletransaction)
  - [checkPendingTransactions](#checkpendingtransactions)
  - [rejectTransaction](#rejecttransaction)
  - [rejectTransactionWithSignature](#rejecttransactionwithsignature)
  - [cancelTransaction](#canceltransaction)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The `TimelockGuard` implements a mandatory delay on Gnosis Safe contracts as a Safe Guard. Safe Guards are external
contracts that Safes call into before and after the execution of a transaction to enquire if the execution fulfils
conditions implemented in the Guard, and revert if they don't. The `TimelockGuard` is a Safe Guard that implements
a mandatory delay on the execution of transactions.

## Definitions

The following list defines variables that will be used in TimelockGuard. None of the variable names are compulsory,
and if better names are found, they should be used.

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

### Scheduled Transaction

A specific transaction that has been stored in the Timelock, for execution from a given safe.

### Scheduling Time

The `scheduling_time(safe, tx)` is the time in seconds of the block in which a transaction was scheduled for execution
from a given safe.

### Delay Period

Given a scheduled transaction, the `delay_period(safe)` is the minimum time in seconds after
`scheduling_time(safe, tx)` that execution is allowed.

### Rejected Transaction

Given a transaction scheduled to execute from given safe, owners for the safe reject the transaction to signal they
think the transaction should not be executed after the `delay_period(safe)`.

### Rejecting Owners

Given a transaction scheduled to execute from given safe, the `rejecting_owners(safe, tx)` are the owners for the safe
that rejected the transaction.

### Cancellation Threshold

The `cancellation_threshold(safe)` is the number of owners that must reject a given transaction for it not to be
executed after the `delay_period(safe)`. It is equal to `blocking_threshold(safe)`.

Alternatively, the `cancellation_threshold(safe)` can start at 1 for each safe, increasing by 1 with each consecutive
cancelled by the given safe transaction up to `blocking_threshold(safe)`, resetting to 1 with each successfully
executed transaction by the given safe.

## Assumptions

### aTG-001: Dishonest Users Don't Have Permanent Key Control Over a Quorum of Keys

We assume that dishonest users have at most a temporary joint key control over a quorum of keys.

#### Severity: Critical

If this invariant is broken, honest control of the multisig is lost.

## Invariants

### iTG-001: Honest Users Can Recover From Temporary Key Control Over a Quorum of Keys

If an attacker has joint or temporary key control over a quorum of keys, honest users should always be able to recover
the account.

#### Severity: Critical

If this invariant is broken, honest control of the multisig is lost.

## Requirements and Contraints

### Nested Cancellation

A nested safe setup is a safe (parent safe) in which one or more owners are a Gnosis Safe (child safes). There can be
multiple levels of nesting. The one parent safe that is not a child of any other safe is called a root safe.

For a given transaction in a root safe within a nested safe setup, a scheduled transaction could be rejected by owners
in child safes an arbitrary number of levels away. The `cancellation_threshold(safe)` of a child safe must be
considered before registering that the child safe is rejecting the transaction.

To avoid rejection spamming, it must be verified upon rejection that the rejecting owner is an owner in the safe
scheduled to execute the transaction, or in one of its child safes.

### Module Execution

Safes implement separate Guard and ModuleGuard interfaces and a Safe enables a separate Guard and ModuleGuard. To make
the `delay_period(safe)` in TimelockGuard mandatory, the TimelockGuard:
- MUST implement both the Guard and ModuleGuard interfaces.
- `ITransactionGuard(timelockGuard).checkTransaction(...)` and
`IModuleGuard(timelockGuard).checkModuleTransaction(...)` MUST execute the same delay checking logic.

It follows that any module will need to implement an entry point function to `scheduleTransaction`.

### Replayability Conflicts

The TimelockGuard does not control replayability of transactions, which is done by either the safe or a potential
module would decide to overwrite the logic.

## Function Specification

The following list details the functions that must be included the in TimelockGuard. None of the function names are
compulsory, and if better names are found, they should be used.

### enable

Called by a Safe, enable the TimelockGuard for it and set the `delay_period`.

- MUST emit a `ModuleEnabled` event with at least `delay_period` as a parameter.

### disable

Called by a Safe, disable the TimelockGuard for it.

- MUST revert if the TimelockGuard is already disabled for the safe.
- MUST emit a `ModuleDisabled` event.

### cancellationThreshold

Returns the `cancellation_threshold` for a given safe.

- MUST return 0 if the TimelockGuard is not enabled for the safe.

### delayPeriod

Returns the `delay_period` for a given safe.

- MUST return 0 if the TimelockGuard is not enabled for the safe.

### scheduleTransaction

Called by anyone using signatures from Safe owners, registers a transaction in the TimelockGuard for execution after
the `delay_period`.

- MUST revert if the TimelockGuard is not enabled for the safe.
- MUST take the same parameters as `execTransaction`.
- MUST revert if an identical transaction has already been scheduled.
- MUST revert if an identical transaction was cancelled.
- MUST emit a `TransactionScheduled` event, with at least `safe` and relevant transaction data.

To allow for identical transactions to be scheduled more than once, but requiring different signatures for each one, a
`salt` parameter can be included in `data` with the sole purpose of differentiating otherwise identical transactions.

### checkTransaction

Called by anyone, and also by the Safe in `execTransaction`, verifies if a given transaction was scheduled and the
delay period has passed.

- MUST revert if the TimelockGuard is not enabled for the safe.
- MUST take the exact parameters from the `ITransactionGuard.checkTransaction` interface.
- MUST revert if `scheduling_time(safe, tx) + delay_period(safe) < block.timestamp`.
- MUST revert if the scheduled transaction was cancelled.

### checkModuleTransaction

Called by anyone, and also by the Safe in `preModuleExecution`, verifies if a given transaction was scheduled and the
delay period has passed.

- MUST revert if the TimelockGuard is not enabled for the safe.
- MUST take the exact parameters from the `IModuleGuard.checkModuleTransaction` interface.
- MUST execute the same internal logic as `checkTransaction`.

### checkPendingTransactions

Called by anyone, returns the list of all scheduled but not cancelled transactions for a given safe.

*Note:* If we want to exclude executed transactions from this list, the TimelockGuard would need to query into the
storage of the safe, and if a module that overrides replayability is implemented, the TimelockGuard would need to look
into its storage as well.

### rejectTransaction

Called by a Safe owner, signal the rejection of a scheduled transaction.

- MUST revert if the TimelockGuard is not enabled for the safe.
- MUST revert if not called by an owner of the safe scheduled to execute the transaction, or in one of its child safes.
- MUST be able to reference a transaction scheduled in a different safe. The transaction might not exist.
- MUST emit a `TransactionRejected` event, with at least `safe` and a transaction identifier.

### rejectTransactionWithSignature

Called by anyone, using signatures form one or more owners, signal the rejection of a scheduled transaction. Can reuse
the `rejectTransaction` function name.

- MUST revert if the TimelockGuard is not enabled for the safe.
- MUST reuse the same internal logic as `rejectTransaction`.

### cancelTransaction

Called by anyone, verify that the `cancellation_threshold` has been met for the Safe to cancel a given scheduled
transaction.

- MUST revert if the TimelockGuard is not enabled for the safe.
- MUST revert if `scheduling_time(safe, tx) + delay_period(safe) >= block.timestamp`.
- MUST revert if `sum(rejecting_owners(safe, tx)) < cancellation_threshold(safe)`.
- MUST emit a `TransactionCancelled` event, with at least `safe` and a transaction identifier.
