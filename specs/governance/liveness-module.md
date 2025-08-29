# Liveness Module

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
  - [Fallback Owner](#fallback-owner)
  - [Liveness Challenge](#liveness-challenge)
- [Assumptions](#assumptions)
  - [aLM-001: The Fallback Owner is Honest](#alm-001-the-fallback-owner-is-honest)
    - [Severity: Medium to High](#severity-medium-to-high)
  - [aLM-002: The Fallback Owner is Active](#alm-002-the-fallback-owner-is-active)
    - [Severity: High](#severity-high)
- [Invariants](#invariants)
  - [iLM-001: No Concurrent Challenges](#ilm-001-no-concurrent-challenges)
    - [Severity: Medium](#severity-medium)
  - [iLM-002: Honest Users Can Recover From Temporary Key Control Over a Quorum of Keys](#ilm-002-honest-users-can-recover-from-temporary-key-control-over-a-quorum-of-keys)
    - [Severity: High](#severity-high-1)
  - [iLM-003: A Quorum Of Honest Users Retains Ownership](#ilm-003-a-quorum-of-honest-users-retains-ownership)
    - [Severity: Medium](#severity-medium-1)
- [Function Specification](#function-specification)
  - [`enableModule`](#enablemodule)
  - [`disableModule`](#disablemodule)
  - [`viewConfiguration`](#viewconfiguration)
  - [`isChallenged`](#ischallenged)
  - [`startChallenge`](#startchallenge)
  - [`cancelChallenge`](#cancelchallenge)
  - [`changeOwnershipToFallback`](#changeownershiptofallback)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The `LivenessModule` ensures a multisig remains operable by allowing challenges when it becomes unresponsive. If the
multisig fails to prove liveness within a set period, ownership transfers to a trusted fallback owner to prevent
deadlock.  

## Definitions

The following lists definitions that will be used in LivenessModule. Where variables are defined, their names are not
compulsory.

### Quorum

The number of owners required to execute a transaction.

### Blocking Threshold

The minimum number of owners not willing to execute a transaction, that by not approving the transaction guarantee that
`quorum` is not met. It is defined as `min(quorum, total_owners - quorum + 1)`.

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

An actor has temporary key control of an owner if it is able to approve a limited set or number of transactions as that
owner.

### Multisig Liveness Failure

A multisig is considered to be in a liveness failure state if the number of active honest owners is less than the
`quorum`, or if the number of malicious active owners is equal or greater than the `blocking_threshold`.

### Multisig Safety Failure

A multisig is considered to be in a safety failure state if the number of active malicious owners is equal or greater
than `quorum`.

### Fallback Owner

The owner that is appointed to take control of a multisig in case of a liveness or safety failure.

### Liveness Challenge

A challenge to a multisig to prove that it is not in a liveness failure state.

## Assumptions

### aLM-001: The Fallback Owner is Honest

The fallback owner is chosen by the multisig which can verify that it is honest.

#### Severity: Medium to High

If this assumption is false and not known to be false, the LivenessModule is not able to recover the multisig from a
liveness failure state until a new fallback owner is chosen.

If this assumption is false but not known to be false, and a challenge is successful, the multisig would enter into a
safety failure state.

### aLM-002: The Fallback Owner is Active

The fallback owner is assumed to be active.

#### Severity: High

If this assumption is false, the LivenessModule is not operational and if the multisig would fall into a liveness
failure state it would not be able to recover.

## Invariants

### iLM-001: No Concurrent Challenges

For an enabled `safe`, there can't be more than one concurrent challenge.

#### Severity: Medium

If this invariant is broken, an attacker could spam the multisig with challenges, damaging its operational performance.

### iLM-002: Honest Users Can Recover From Temporary Key Control Over a Quorum of Keys

If an attacker has full, joint, or temporary key control over less than a quorum of keys, honest users should always
be able to recover the account by transferring ownership to the fallback owner

#### Severity: High

If this invariant is broken, an attacker with temporary key control over less than a quorum of keys could force the
multisig into a liveness failure state.

### iLM-003: A Quorum Of Honest Users Retains Ownership

While a quorum of honest users exist, they should remain in control of the account.

#### Severity: Medium

If this invariant is broken, there would be an operational and possibly reputational impact while the ownership of the
account is restablished to the account owners.

## Function Specification

### `enableModule`

Enables the module by the multisig to be challenged and sets the `liveness_challenge_period` and `fallback_owner`.

- MUST set the caller as a `safe`.
- MUST allow an arbitrary number of `safe` contracts to use the module.
- MUST take as parameters `liveness_challenge_period` and `fallback_owner` and store them as related to the `safe`.

### `disableModule`

Disables the module by an enabled `safe`.

- MUST only be executable an enabled `safe`.
- MUST erase the existing `liveness_challenge_period` and `fallback_owner` data related to the calling `safe`.

### `viewConfiguration`

Returns the `liveness_challenge_period` and `fallback_owner` for a given `safe`.

- MUST never revert.

### `isChallenged`

Returns `challenge_start_time + liveness_challenge_period` if there is a challenge for the given `safe`, or 0 if not.

- MUST never revert.

### `startChallenge`

Challenges an enabled `safe`.

- MUST only be executable by `fallback` owner of the challenged `safe`.
- MUST revert if there is a challenge for the `safe`.
- MUST set `challenge_start_time` to the current block time.
- MUST emit the `ChallengeStarted` event.

### `cancelChallenge`

Cancels a challenge for an enabled `safe`.

- MUST only be executable by an enabled `safe`.
- MUST revert if there isn't a challenge for the calling `safe`.
- MUST revert if there is a challenge for the calling `safe` but the challenge is successful.
- MUST emit the `ChallengeCancelled` event.

### `changeOwnershipToFallback`

With a successful challenge, removes all current owners from an enabled `safe`, appoints `fallback` as its sole owner,
and sets its quorum to 1.

- MUST be executable by anyone.
- MUST revert if the given `safe` hasn't enabled the module.
- MUST revert if there isn't a successful challenge for the given `safe`.
- MUST enable the module to start a new challenge.
- MUST emit the `ChallengeExecuted` event.
