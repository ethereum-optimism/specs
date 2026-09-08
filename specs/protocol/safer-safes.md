# Safer Safes

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Status](#status)
- [Overview](#overview)
- [Definitions](#definitions)
  - [Safe](#safe)
  - [Owner](#owner)
  - [Quorum](#quorum)
  - [Blocking Threshold](#blocking-threshold)
  - [Fallback Owner](#fallback-owner)
  - [Liveness Challenge](#liveness-challenge)
  - [Liveness Response Period](#liveness-response-period)
  - [Timelock Delay](#timelock-delay)
  - [Scheduled Transaction](#scheduled-transaction)
  - [Cancellation Threshold](#cancellation-threshold)
  - [Timelock Configuration Generation](#timelock-configuration-generation)
  - [Module Transaction](#module-transaction)
- [Assumptions](#assumptions)
  - [aSAFE-001: Safe contracts are correct and compatible](#asafe-001-safe-contracts-are-correct-and-compatible)
    - [Mitigations](#mitigations)
  - [aSAFE-002: Safe owners choose correct configuration](#asafe-002-safe-owners-choose-correct-configuration)
    - [Mitigations](#mitigations-1)
  - [aSAFE-003: Fallback owner is honest and live](#asafe-003-fallback-owner-is-honest-and-live)
    - [Mitigations](#mitigations-2)
  - [aSAFE-004: Ethereum provides timely inclusion and reliable timestamps](#asafe-004-ethereum-provides-timely-inclusion-and-reliable-timestamps)
    - [Mitigations](#mitigations-3)
  - [aSAFE-005: Enabled modules are constrained](#asafe-005-enabled-modules-are-constrained)
    - [Mitigations](#mitigations-4)
- [Invariants](#invariants)
  - [iSAFE-001: Safe controls its own extension configuration](#isafe-001-safe-controls-its-own-extension-configuration)
    - [Impact](#impact)
  - [iSAFE-002: Liveness recovery only succeeds after an unanswered challenge](#isafe-002-liveness-recovery-only-succeeds-after-an-unanswered-challenge)
    - [Impact](#impact-1)
  - [iSAFE-003: A live Safe can cancel a liveness challenge](#isafe-003-a-live-safe-can-cancel-a-liveness-challenge)
    - [Impact](#impact-2)
  - [iSAFE-004: Successful liveness recovery produces a recoverable Safe](#isafe-004-successful-liveness-recovery-produces-a-recoverable-safe)
    - [Impact](#impact-3)
  - [iSAFE-005: Liveness challenges cannot be spammed for the same Safe](#isafe-005-liveness-challenges-cannot-be-spammed-for-the-same-safe)
    - [Impact](#impact-4)
  - [iSAFE-006: Combined timing leaves room for liveness response](#isafe-006-combined-timing-leaves-room-for-liveness-response)
    - [Impact](#impact-5)
  - [iSAFE-007: Timelock protects owner-executed Safe transactions](#isafe-007-timelock-protects-owner-executed-safe-transactions)
    - [Impact](#impact-6)
  - [iSAFE-008: Timelock execution requires a current owner executor](#isafe-008-timelock-execution-requires-a-current-owner-executor)
    - [Impact](#impact-7)
  - [iSAFE-009: Scheduled transaction timing is stable](#isafe-009-scheduled-transaction-timing-is-stable)
    - [Impact](#impact-8)
  - [iSAFE-010: Cancellation authority comes from current Safe owners](#isafe-010-cancellation-authority-comes-from-current-safe-owners)
    - [Impact](#impact-9)
  - [iSAFE-011: Cancellation threshold remains bounded](#isafe-011-cancellation-threshold-remains-bounded)
    - [Impact](#impact-10)
  - [iSAFE-012: Timelock clearing isolates old state](#isafe-012-timelock-clearing-isolates-old-state)
    - [Impact](#impact-11)
  - [iSAFE-013: Guard removal exposes old Safe signatures](#isafe-013-guard-removal-exposes-old-safe-signatures)
    - [Impact](#impact-12)
  - [iSAFE-014: Module transactions are outside timelock scope](#isafe-014-module-transactions-are-outside-timelock-scope)
    - [Impact](#impact-13)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Status

Production

## Overview

SaferSafes is a singleton Safe extension that can be installed as both a Safe module and a Safe
guard. It is intended to replace the original [Safe Contract Extensions](./safe-extensions.md)
where adopted.

SaferSafes provides two independent capabilities:

- **Liveness recovery**: A configured fallback owner can challenge a Safe to prove that it remains
  live. If the Safe does not cancel the challenge before the response window expires, control of the
  Safe transfers to the fallback owner.
- **Transaction timelock**: Owner-executed Safe transactions must be scheduled before execution
  and cannot execute until the configured delay has elapsed. A subset of owners can cancel a
  scheduled transaction before it executes.

The liveness module and timelock guard can be enabled independently. When both are enabled and
configured for the same Safe, their configuration must leave enough time for the Safe to schedule
and execute a liveness response before fallback ownership can be claimed.

SaferSafes is designed for Safes that use Safe version 1.4.1.

## Definitions

### Safe

The Safe account that has installed SaferSafes as a module, a guard, or both.

### Owner

An address that is a current owner of a [Safe](#safe), according to the Safe's owner set.

### Quorum

The Safe threshold: the number of owner approvals required for the Safe to execute an
owner-authorized transaction.

### Blocking Threshold

The minimum number of owners that can prevent a transaction from reaching [Quorum](#quorum) by
withholding approval. It is equal to `total_owners - quorum + 1`.

### Fallback Owner

The account configured by the Safe to receive sole ownership if a liveness challenge succeeds. The
fallback owner is also the only account that can start a liveness challenge or claim ownership after
the response window expires.

### Liveness Challenge

A claim by the [Fallback Owner](#fallback-owner) that the Safe may no longer be live. A liveness
challenge starts a response window during which the Safe can demonstrate liveness by cancelling the
challenge.

### Liveness Response Period

The amount of time the Safe has to cancel a [Liveness Challenge](#liveness-challenge) before the
challenge can succeed.

### Timelock Delay

The minimum amount of time that must elapse between scheduling an owner-executed Safe transaction
and executing it.

### Scheduled Transaction

An owner-authorized Safe transaction that has been registered with SaferSafes for execution after
the [Timelock Delay](#timelock-delay).

### Cancellation Threshold

The number of owner approvals required to cancel a [Scheduled Transaction](#scheduled-transaction).
The threshold starts at one for a configured Safe, increases after cancellations, and is capped at
the lower of [Quorum](#quorum) and [Blocking Threshold](#blocking-threshold).

### Timelock Configuration Generation

The active generation of timelock state for a Safe. Clearing timelock configuration moves the Safe
to a fresh generation so previously scheduled, cancelled, or executed transactions are no longer
part of the active timelock state.

### Module Transaction

A transaction that a Safe executes through an enabled Safe module rather than through the Safe's
owner-executed transaction path.

## Assumptions

### aSAFE-001: Safe contracts are correct and compatible

SaferSafes assumes the underlying Safe contract correctly implements owner management, threshold
management, signature validation, module execution, guard execution, nonce handling, and version
reporting.

SaferSafes is designed for Safe version 1.4.1. Behavior with other Safe versions is not guaranteed.

#### Mitigations

- SaferSafes validates the Safe version during configuration.
- Safe contracts are externally audited and widely used.
- SaferSafes relies on the Safe as the source of truth for owners, threshold, signatures, modules,
  guards, and nonce state.

### aSAFE-002: Safe owners choose correct configuration

SaferSafes assumes that Safe owners choose an appropriate fallback owner, liveness response period,
and timelock delay for the Safe's operational and governance requirements.

#### Mitigations

- Configuration changes are authorized by the Safe itself.
- The fallback owner and timing parameters are visible onchain.
- When the liveness module and timelock guard are both active, SaferSafes rejects configurations
  that do not leave enough time for a liveness response through the timelock.

### aSAFE-003: Fallback owner is honest and live

SaferSafes assumes the fallback owner acts in the Safe's best interest and can act when recovery is
needed.

#### Mitigations

- The Safe chooses its own fallback owner.
- The fallback owner should have stronger security and availability guarantees than the Safe it can
  recover.
- The fallback owner should itself be a Safe or another account that can execute batches, because
  recovery may need to pair ownership transfer with nonce-bumping transactions.

### aSAFE-004: Ethereum provides timely inclusion and reliable timestamps

SaferSafes assumes Ethereum block timestamps are suitable for enforcing liveness response periods
and timelock delays, and that transactions can be included within operationally reasonable time
bounds.

#### Mitigations

- Liveness response periods and timelock delays should be configured with enough buffer for network
  congestion, coordination delays, and transaction replacement.
- The combined configuration requirement provides additional buffer when both capabilities are used
  together.

### aSAFE-005: Enabled modules are constrained

SaferSafes assumes that enabled Safe modules are independently constrained to the actions they are
intended to perform. Timelock protection applies to owner-executed Safe transactions and does not
delay module transactions.

#### Mitigations

- Modules should be reviewed under their own authorization and action-scope invariants.
- Existing OP Stack modules such as the Deputy Pause Module and liveness recovery module are
  designed for narrowly scoped actions.
- New modules must explicitly consider whether they should be delayed by a guard.

## Invariants

### iSAFE-001: Safe controls its own extension configuration

A Safe must control whether SaferSafes is configured for that Safe. No external account may choose
the Safe's fallback owner, liveness response period, timelock delay, or active timelock generation.

The fallback owner may start liveness challenges and claim ownership after a successful challenge,
but cannot configure arbitrary SaferSafes parameters for the Safe.

#### Impact

**Severity: Critical**

If violated, an attacker could configure themselves as fallback owner, disable timelock protection,
or clear timelock state without Safe authorization, leading to unauthorized control or execution.

### iSAFE-002: Liveness recovery only succeeds after an unanswered challenge

Fallback ownership transfer must only be possible when all of the following are true:

1. The Safe configured liveness recovery.
2. SaferSafes remains enabled as a module for that Safe.
3. The fallback owner started an active liveness challenge.
4. The liveness response period for that challenge has elapsed.
5. The Safe has not cancelled the challenge.

#### Impact

**Severity: Critical**

If violated, ownership could transfer to the fallback owner while a quorum of owners remains live
and able to operate the Safe.

### iSAFE-003: A live Safe can cancel a liveness challenge

A configured Safe that remains live must be able to cancel an active liveness challenge through a
Safe-authorized transaction while SaferSafes remains enabled as a module.

#### Impact

**Severity: Critical**

If violated, a live Safe could lose ownership to the fallback owner despite retaining enough owner
control to operate.

### iSAFE-004: Successful liveness recovery produces a recoverable Safe

After a successful liveness recovery, the fallback owner must be the Safe's sole owner, the Safe
threshold must be one, the active challenge must be cleared, and the Safe guard must be removed.

#### Impact

**Severity: Critical**

If violated, recovery could leave the Safe unusable, leave old owners with authority, or leave a
guard in place that prevents the fallback owner from restoring operations.

### iSAFE-005: Liveness challenges cannot be spammed for the same Safe

At most one liveness challenge may be active for a Safe at a time. Reconfiguration or clearing of
liveness recovery must clear any active challenge for that Safe.

#### Impact

**Severity: High**

If violated, repeated challenges could create unnecessary operational load or make challenge
timing ambiguous, increasing the chance of accidental fallback ownership transfer.

### iSAFE-006: Combined timing leaves room for liveness response

When both liveness recovery and timelock protection are active for the same Safe, the liveness
response period must be at least twice the timelock delay.

#### Impact

**Severity: High**

If violated, a Safe could be unable to schedule and execute a liveness response through the
timelock before the liveness response period expires.

### iSAFE-007: Timelock protects owner-executed Safe transactions

When timelock protection is configured for a Safe, owner-executed Safe transactions must not
execute unless the transaction was scheduled, the scheduled execution time has arrived, and the
transaction has not been cancelled or already executed.

#### Impact

**Severity: Critical**

If violated, an attacker with temporary access to enough owner approvals could bypass the delay and
execute malicious transactions before owners can detect and cancel them.

### iSAFE-008: Timelock execution requires a current owner executor

When timelock protection is configured for a Safe, execution of an owner-executed Safe transaction
must be initiated by a current owner of that Safe.

#### Impact

**Severity: High**

If violated, an attacker who only obtains signatures could schedule and execute a transaction
without also controlling an owner key, weakening the defense provided by the timelock.

### iSAFE-009: Scheduled transaction timing is stable

The execution time for a scheduled transaction must not change while that transaction remains in
the active timelock generation. The same transaction must not be possible to schedule again after
it has been scheduled, cancelled, or executed in that generation.

#### Impact

**Severity: High**

If violated, an attacker could shorten the delay to bypass review or extend the delay to grief Safe
operations. If cancelled transactions could be rescheduled with the same authorization, cancellation
would not reliably stop malicious signatures from being reused.

### iSAFE-010: Cancellation authority comes from current Safe owners

Cancelling a scheduled transaction must require valid owner authorization meeting the current
cancellation threshold for the Safe.

#### Impact

**Severity: High**

If violated, non-owners could cancel legitimate transactions, or insufficient owner approval could
block Safe operations.

### iSAFE-011: Cancellation threshold remains bounded

The cancellation threshold must start at one for a configured Safe, increase by one after each
successful cancellation, never exceed the lower of quorum and blocking threshold, and reset to one
after an owner-executed transaction reaches the execution path.

#### Impact

**Severity: High**

If violated, cancellation could become unavailable to honest owners, or too few owners could
repeatedly cancel legitimate transactions and create a liveness failure.

### iSAFE-012: Timelock clearing isolates old state

Clearing timelock configuration must move the Safe to a fresh timelock configuration generation so
old scheduled, cancelled, and executed transaction state is not active after the Safe reconfigures
timelock protection.

#### Impact

**Severity: High**

If violated, stale timelock state could block legitimate future transactions or unexpectedly allow
old transaction state to affect a new configuration.

### iSAFE-013: Guard removal exposes old Safe signatures

Removing the timelock guard must be treated as a security-sensitive operation. Once the guard is
removed, scheduled or cancelled transactions at or below the Safe nonce may become executable if
valid Safe signatures still exist.

#### Impact

**Severity: Critical**

If ignored operationally, fallback recovery or timelock removal could make previously delayed or
cancelled transactions executable. Recovery procedures should advance the Safe nonce past any
transaction that may have valid outstanding signatures.

### iSAFE-014: Module transactions are outside timelock scope

Timelock protection must not be assumed to delay module transactions. Any module enabled on the
Safe must be safe without relying on SaferSafes timelock checks.

#### Impact

**Severity: High**

If violated by system design, an enabled module could bypass the intended delay and execute actions
that owners expected to pass through the timelock.
