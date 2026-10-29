# Policy

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
  - [Verdict Writer](#verdict-writer)
  - [Hold Delay](#hold-delay)
- [IPolicy](#ipolicy)
- [What Every Policy May Assume](#what-every-policy-may-assume)
- [Requirements on a Policy](#requirements-on-a-policy)
- [Policy Choices](#policy-choices)
- [Ownership and Upgrades](#ownership-and-upgrades)
- [Non-goals](#non-goals)
- [Assumptions](#assumptions)
  - [aCM-002: The chain trusts the policy it sets](#acm-002-the-chain-trusts-the-policy-it-sets)
    - [Mitigations](#mitigations)
  - [aCM-003: The policy fits the user's gas budget](#acm-003-the-policy-fits-the-users-gas-budget)
    - [Mitigations](#mitigations-1)
- [Invariants](#invariants)
  - [iCM-010: A failing policy cannot consume an item](#icm-010-a-failing-policy-cannot-consume-an-item)
    - [Impact](#impact)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

> **Note:** This document is not finalized and should be considered experimental.

## Overview

A **Policy** is a contract the chain owns. It has two jobs:
- It decides whether each item may proceed, both at the time the item arrives and when its value moves.
- It is also the only address the hook accepts verdicts from, so it controls who can clear an item.

This page specifies the interface between the hook and its policy: what the hook hands a policy, when it asks, and
what it requires of the answer. It does not specify what a policy decides. See
[Non-goals](#non-goals).

## Definitions

### Verdict Writer

A **Verdict Writer** is the offchain service that checks an item's [Parties](./overview.md#parties) and records
verdicts through the policy. It sets each verdict's expiry, so how long a verdict stays valid is decided offchain.
It belongs to the chain and is outside this specification.

### Hold Delay

A **Hold Delay** is a common policy choice in which the policy rejects an uncleared withdrawal until a delay after its
[Finalizable Time](./overview.md#finalizable-time) has passed, and holds it after.

Take a policy with a two hour hold delay. A 100 USDC withdrawal becomes finalizable at 12:00. Until 14:00 the policy
rejects every attempt to finalize it, so a clearance that lands at 13:30 still pays the recipient through the normal
path. From 14:00 the policy holds it instead, and the 100 USDC moves to the hook.

## IPolicy

```solidity
interface IPolicy {
    function screen(
        Item calldata _item,
        address[] calldata _parties
    )
        external
        returns (bool pass_);

    function screenRelease(
        Item calldata _item,
        address[] calldata _parties,
        uint64 _expiresAt,
        uint256 _finalizableAt
    )
        external
        returns (bool pass_);
}
```

Both functions answer with a [Screening Outcome](./overview.md#screening-outcome): `true` to proceed, `false` to hold,
and a revert to reject.

## What Every Policy May Assume

- The item it is handed is the item that will execute, unchanged.
- It decides whether an item proceeds, never where the value goes.
- It is consulted twice on a held item, once on entry and once when value moves.
- It runs inside the user's transaction, so it shares that transaction's gas budget.

## Requirements on a Policy

- A policy MUST revert, and MUST NOT return `false`, when something it calls fails.
- A policy MUST terminate within the gas available in the calling transaction.
- A policy MUST restrict `screen` and `screenRelease` to the hook, so nobody else can drive its state.

The first requirement protects items the policy never meant to act on. Whoever finalizes a withdrawal chooses how
much gas it carries, so a policy that catches an internal failure and answers `false` is open to gas griefing. An
attacker attempts a finalization with too little gas, starves a call inside the policy, and the item is held. A hold
cannot be undone by retrying, so a fault becomes a permanent deferral of someone's value. A revert consumes nothing
and can be retried with more gas.

## Policy Choices

What a policy does with `_expiresAt` and `_finalizableAt` is up to the chain. For example, a policy may choose to:

- **[Hold Delay](#hold-delay).** Reject an uncleared withdrawal until `_finalizableAt` plus the delay, then hold it. A
  service that clears during the proof maturity window needs a short delay. One that clears only once the withdrawal
  is finalizable needs the delay to cover its own response time.
- **Expiring clearances.** Honor the `_expiresAt` the [Verdict Writer](#verdict-writer) chose, so a verdict written
  early stops counting once that time passes. An expired clearance counts as none, so a withdrawal finalized after
  it is held like any other uncleared one.
- **No wait for known flags.** Hold at the first attempt when a party is already flagged, and wait only for
  withdrawals still pending a verdict.
- **Synchronous policies.** A policy that reads only onchain state and answers immediately never holds, so it ignores
  `_finalizableAt` entirely.

## Ownership and Upgrades

A policy may be upgradeable or not. The hook can always point to a new one, and verdicts survive the change because
they live in the hook rather than in the policy.

## Non-goals

- What a policy decides. The rules and thresholds belong to the chain.
- The [Verdict Writer](#verdict-writer) behind the policy, and how verdicts reach it.

## Assumptions

### aCM-002: The chain trusts the policy it sets

The policy decides who may clear an item, so whoever controls the policy can clear any held item, and can refuse or
hold any new one.

#### Mitigations

- A policy can only delay or refuse. It can never redirect value or alter an item's terms. See
  [iCM-003](./optimism-portal.md#icm-003-a-hook-can-only-delay-or-refuse-an-item).
- Completion still checks the hook's own record before the policy is consulted, so a policy cannot complete an item
  that was never held.
- The hook's disable switch bounds how long a failing or adversarial policy can block new items.

### aCM-003: The policy fits the user's gas budget

A policy runs inside the transaction of whoever submits a deposit or finalizes a withdrawal, and that caller chose the
gas.

#### Mitigations

- A policy that runs out of gas reverts, which consumes nothing and can be retried with more gas.
- The withdrawal path's remaining gas is checked when the target call is made, so an underfunded finalization reverts
  rather than executing with too little. See
  [iCM-005](./optimism-portal.md#icm-005-a-held-withdrawal-keeps-its-minimum-gas-guarantee).

## Invariants

### iCM-010: A failing policy cannot consume an item

A policy that reverts rejects the item. The whole transaction reverts, so a deposit never happens and a withdrawal
stays finalizable and can be attempted again.

#### Impact

**Severity: High**

If violated, a policy bug could consume a user's deposit or withdrawal without delivering it, turning a recoverable
fault into a permanent loss. A failing policy is meant to block bridging, which is recoverable, rather than destroy
items, which is not.
