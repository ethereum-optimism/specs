# Governor

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
  - [`quorum(safe)`](#quorumsafe)
  - [Scheduled Transaction](#scheduled-transaction)
  - [`scheduling_time(safe, tx)`](#scheduling_timesafe-tx)
  - [`delay_period(safe)`](#delay_periodsafe)
  - [Rejected Transaction](#rejected-transaction)
  - [`rejecting_owners(safe, tx)`](#rejecting_ownerssafe-tx)
  - [`cancellation_threshold(safe)`](#cancellation_thresholdsafe)
  - [Nested Safe Setup](#nested-safe-setup)
  - [Nested Cancellation](#nested-cancellation)
- [Assumptions](#assumptions)
- [Invariants](#invariants)
- [Function Specification](#function-specification)
  - [constructor](#constructor)
  - [enable(delay_period)](#enabledelay_period)
  - [disable](#disable)
  - [cancellationThreshold(safe)](#cancellationthresholdsafe)
  - [delayPeriod(safe)](#delayperiodsafe)
  - [setDelayPeriod(delay_period)](#setdelayperioddelay_period)
  - [scheduleTransaction](#scheduletransaction)
  - [checkTransaction](#checktransaction)
  - [rejectTransaction](#rejecttransaction)
  - [cancelTransaction](#canceltransaction)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The `TimelockGuard` implements a mandatory delay on Gnosis Safe contracts as a Safe Guard. Safe Guards are external contracts that Safes call into before and after the execution of a transaction to enquire if the execution fulfils conditions implemented in the Guard, and revert if they don't. The `TimelockGuard` 

## Definitions

### `quorum(safe)`
The number of owners in a safe that must signal aproval of a transaction for it to be executed by the safe.

### Scheduled Transaction
A specific transaction that has been stored in the Timelock, for execution from a given safe.

### `scheduling_time(safe, tx)`
The time in seconds of the block in which a transaction was scheduled.

### `delay_period(safe)`
Given a scheduled transaction, the minimum time in seconds after `scheduling_time` that execution is allowed.

### Rejected Transaction
Given a transaction scheduled to execute from given safe, owners for the safe reject the transaction to signal they think the transaction should not be executed after the `delay_period`.

### `rejecting_owners(safe, tx)`
Given a transaction scheduled to execute from given safe, the owners for the safe that rejected the transaction.

### `cancellation_threshold(safe)`
The number of owners that must reject a given transaction for it not to be executed after the `delay_period`. It is equal to `blocking_minority`, where `blocking_minority = min(quorum(safe), total_owners(safe) - quorum + 1)`.

Alternatively, the `cancellation_threshold` can start at 1 for each safe, increasing by 1 with each consecutive cancelled by the given safe transaction up to `blocking_minority`, resetting to 1 with each successfully executed transaction by the given safe.

### Nested Safe Setup
A nested safe setup is a safe (parent safe) in which one or more owners are a Gnosis Safe (child safes). There can be multiple levels of nesting. The one parent safe that is not a child of any other safe is called a root safe.

### Nested Cancellation
For a given transaction in a root safe within a nested safe setup, a scheduled transaction could be rejected by owners in child safes an arbitrary number of levels away. The `cancellation_threshold` of a child safe must be considered before registering that the child safe is rejecting the transaction.

## Assumptions

## Invariants

## Function Specification

### constructor

### enable(delay_period)
Called by a Safe, enable the TimelockGuard for it.

Takes the `delay_period` as a parameter.

- MUST revert if the TimelockGuard is already enabled for the safe.

### disable
Called by a Safe, disable the TimelockGuard for it.

- MUST revert if the TimelockGuard is already disabled for the safe.

### cancellationThreshold(safe)
Returns the `cancellation_threshold` for a given safe.

- MUST return 0 if the TimelockGuard is not enabled for the safe.

### delayPeriod(safe)
Returns the `delay_period` for a given safe.

- MUST return 0 if the TimelockGuard is not enabled for the safe.

### setDelayPeriod(delay_period)
Called by a Safe, set its `delay_period`.

- MUST revert if the TimelockGuard is not enabled for the safe.

### scheduleTransaction
Called by anyone using signatures from Safe owners, registers a transaction in the TimelockGuard for execution after the `delay_period`.

- MUST revert if the TimelockGuard is not enabled for the safe.
- MUST take the same parameters as `execTransaction`.
- MUST revert if an identical transaction has already been scheduled.
- MUST revert if an identical transaction was cancelled.

To allow for identical transactions to be scheduled more than once, but requiring different signatures for each one, a `salt` parameter can be included in `data` with the sole purpose of differentiating otherwise identical transactions.

### checkTransaction
Called by anyone, and also by the Safe in `execTransaction`, verifies if the transaction was scheduled and the delay period has passed.

- MUST revert if the TimelockGuard is not enabled for the safe.
- MUST take the exact parameters from the Safe API
- MUST revert if `scheduling_time(safe, tx) + delay_period(safe) < block.timestamp`
- MUST revert if the scheduled transaction was cancelled

### rejectTransaction
Called by a Safe owner, signal the rejection of a scheduled transaction.
TODO: Should we use signatures here?

- MUST revert if the TimelockGuard is not enabled for the safe.
- MUST revert if not called by an owner of the safe.
- MUST be able to reference a transaction scheduled in a different safe. The transaction might not exist.

### cancelTransaction
Called by anyone, verify that the `cancellation_threshold` has been met for the Safe to cancel a given scheduled transaction.

- MUST revert if the TimelockGuard is not enabled for the safe.
- MUST revert if `scheduling_time(safe, tx) + delay_period(safe) >= block.timestamp`
- MUST revert if `sum(rejecting_owners(safe, tx)) < cancellation_threshold(safe)`

