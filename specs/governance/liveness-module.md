# Governor

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
  - [Successful challenge](#successful-challenge)
  - [Unsuccessful challenge](#unsuccessful-challenge)
- [Assumptions](#assumptions)
- [Invariants](#invariants)
- [Function Specification](#function-specification)
  - [constructor](#constructor)
  - [`enableModule`](#enablemodule)
  - [`disableModule`](#disablemodule)
  - [`setLivenessChallengePeriod`](#setlivenesschallengeperiod)
  - [`setFallbackOwner`](#setfallbackowner)
  - [`livenessChallengePeriod`](#livenesschallengeperiod)
  - [`fallbackOwner`](#fallbackowner)
  - [`isChallenged`](#ischallenged)
  - [`startChallenge`](#startchallenge)
  - [`cancelChallenge`](#cancelchallenge)
  - [`changeOwnershipToFallback`](#changeownershiptofallback)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The `Governor` contract implements the core governance logic for creating, voting, and executing proposals.
This contract uses the `GovernanceToken` contract for voting power snapshots, and the `ProposalTypesConfigurator`
for proposal types.

## Definitions

### Successful challenge
A challenge with a `challenge_start_time` more than `liveness_challenge_period` in the past.

### Unsuccessful challenge
A challenge for which `cancelChallenge` was called earlier than `challenge_start_time + liveness_challenge_period`.
TODO: Make sure the two definitions are a perfect partition.

## Assumptions

## Invariants
- For an enabled `safe`, there can't be more than one concurrent challenge.

## Function Specification

### constructor
- MUST not set any values.

### `enableModule`
Enables the module by the multisig to be challenged.

- MUST set the caller as a `safe`.
- MUST take as parameters `liveness_challenge_period` and `fallback_owner` and store them as related to the `safe`.
- MUST accept an arbitrary number of independent `safe` contracts to enable the module.
TODO: Should we require the `fallback_owner` to execute a second transaction to confirm?
TODO: Should we hardcode some lower and higher bounds to `liveness_challenge_period`?

### `disableModule`
Disables the module by the multisig to be challenged.

- MUST only be executable an enabled `safe`.
- MUST revert if there is an ongoing challenge for the calling `safe`.
- MUST erase the existing `liveness_challenge_period` and `fallback_owner` data related to the calling `safe`.

### `setLivenessChallengePeriod`
Changes the `liveness_challenge_period` for a given `safe`

- MUST only be executable an enabled `safe`.
- MUST revert if there is a challenge for the calling `safe`.

### `setFallbackOwner`
Changes the `fallback_owner` for a given `safe`

- MUST only be executable an enabled `safe`.
- MUST revert if there is a challenge for the calling `safe`.

### `livenessChallengePeriod`
Returns `livenessChallengePeriod`.

- MUST never revert.

### `fallbackOwner`
Returns `fallbackOwner`.

- MUST never revert.

### `isChallenged`
Returns `challenge_start_time + liveness_challenge_period` if there is a challenge for the given `safe`, or 0 if not.

- MUST never revert.

### `startChallenge`
Challenges a enabled `safe`.

- MUST only be executable by `fallback` owner of the challenged `safe`.
- MUST revert if there is a challenge for the `safe`.
- MUST set `challenge_start_time` to the current block time.
- MUST emit the `ChallengeStarted` event.

### `cancelChallenge`

Cancels a challenge for a enabled `safe`.

- MUST only be executable by a enabled `safe`.
- MUST revert if there isn't a challenge for the calling `safe`.
- MUST revert if there is a challenge for the calling `safe` but the challenge is successful.
- MUST emit the `ChallengeCancelled` event.

### `changeOwnershipToFallback`

With a successful challenge, removes all current owners from a enabled `safe`, appoints `fallback` as its sole owner, and sets its quorum to 1.

- MUST be executable by anyone.
- MUST revert if the given `safe` hasn't enabled the module.
- MUST revert if there isn't a successful challenge for the given `safe`.
- MUST enable the module to start a new challenge.
- MUST emit the `ChallengeExecuted` event.
