# ComplianceModule

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
  - [Record](#record)
  - [Resolved Parties](#resolved-parties)
  - [Disable](#disable)
- [Assumptions](#assumptions)
  - [aCM-004: The module's upgrade authority is the custodian of all deferred value](#acm-004-the-modules-upgrade-authority-is-the-custodian-of-all-deferred-value)
    - [Mitigations](#mitigations)
  - [aCM-005: The policy is trusted](#acm-005-the-policy-is-trusted)
    - [Mitigations](#mitigations-1)
- [Dependencies](#dependencies)
- [Invariants](#invariants)
  - [iCM-011: Verdicts come only from the policy, and the hook functions only from the Portal](#icm-011-verdicts-come-only-from-the-policy-and-the-hook-functions-only-from-the-portal)
    - [Impact](#impact)
  - [iCM-012: A record is deleted before the module calls out](#icm-012-a-record-is-deleted-before-the-module-calls-out)
    - [Impact](#impact-1)
  - [iCM-013: The module holds at least what it owes](#icm-013-the-module-holds-at-least-what-it-owes)
    - [Impact](#impact-2)
- [Function Specification](#function-specification)
  - [constructor](#constructor)
  - [portal](#portal)
  - [items](#items)
  - [heldTokens](#heldtokens)
  - [policy](#policy)
  - [disabled](#disabled)
  - [paused](#paused)
  - [screenDeposit](#screendeposit)
  - [holdDeposit](#holddeposit)
  - [screenWithdrawal](#screenwithdrawal)
  - [holdWithdrawal](#holdwithdrawal)
  - [recordVerdict](#recordverdict)
  - [revokeVerdict](#revokeverdict)
  - [completeDeposit](#completedeposit)
  - [completeWithdrawal](#completewithdrawal)
  - [setPolicy](#setpolicy)
  - [disable](#disable)
  - [enable](#enable)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

> **Note:** This document is not finalized and should be considered experimental.

## Overview

The `ComplianceModule` is a reference implementation of the bridge hook an `OptimismPortal` can be pointed at. It
takes custody of the ETH and tokens of held items, owns the verdict registry, and initiates completion. It is the only
new contract that holds value.

A separate [Policy](../../compliance/policy.md) contract decides what is acceptable, and the
module consults it on every item. The feature as a whole is described in the
[Compliance Module overview](../../compliance/overview.md).

## Definitions

### Record

A **Record** is the module's entry for one item, keyed by the item's
[Identifier](../../compliance/overview.md#identifier).

```solidity
struct Record {
    uint64 heldAt;    // non-zero means the item exists and is held
    uint64 expiresAt; // non-zero means a clear verdict is recorded, and when the policy says it expires
}
```

The module doesn't store any of the item fields. They are emitted in full when the item is held, and re-supplied by
whoever attempts to move
its value. This keeps unbounded calldata out of storage, and lets anyone rebuild the set of held items from L1 alone.

The module stores whatever `expiresAt` the policy passes and hands it back when value moves, so whether an
expired verdict still counts is the policy's decision.

### Resolved Parties

The **Resolved Parties** of an item are the addresses the module passes to the policy. For a message sent through the
messengers, the module decodes the real sender and recipient from the envelope rather than passing the messengers
themselves.

This decoding is narrow by design with fixed contracts, fixed selectors, no recursion and no simulation. Anything it cannot
decode falls back to the outer addresses. Resolving this once in the module, rather than in each policy, keeps the
protocol knowledge in one place.

### Disable

**Disable** is the module's emergency switch, intended for a failing policy or a long outage of the Verdict Writer.

While it is set, every deposit proceeds without the policy being asked, and so does every withdrawal initiated at or
after the cutoff. Withdrawals initiated before the cutoff are still screened. Items already held stay held, and still
need a clear verdict and the policy's approval to complete.

The cutoff is an L2 withdrawal nonce rather than a timestamp. Nothing on L1 records when a withdrawal was initiated,
and a proof's timestamp resets whenever someone proves it again, so a timestamp cutoff could be bypassed by
re-proving.

## Assumptions

### aCM-004: The module's upgrade authority is the custodian of all deferred value

Whoever can upgrade the module can reach every item it holds. That authority is not constrained to be the chain's
`ProxyAdmin` owner, and what an upgraded module does with value already in its custody is outside the protocol's
guarantees. The value at risk is not limited to what the module holds when it is upgraded. The Portal offers it every
item, so it can hold each new deposit and withdrawal as it arrives. Since removing or replacing the hook is the only
way to stop that, the loss is bounded by how fast the chain reacts.

#### Mitigations

- The module holds only deferred value. Value on the normal path never passes through it.
- The full item is emitted when it is held, so the set of held items and their owed amounts is auditable from L1.
- The Portal's commitment binds the terms of every held item, so an item that does complete can only complete to its
  original destination under the original terms.

### aCM-005: The policy is trusted

The module takes verdicts only from the policy, and asks it before any value moves. A compromised policy can clear
any held item, or refuse and hold any new one. See
[aCM-002](../../compliance/policy.md#acm-002-the-chain-trusts-the-policy-it-sets).

#### Mitigations

- The module checks its own record before consulting the policy, so a policy cannot complete an item that was never
  held.
- A policy can only delay or refuse. See
  [iCM-003](../../compliance/optimism-portal.md#icm-003-a-hook-can-only-delay-or-refuse-an-item).
- [Disable](#disable) bounds how long a failing or malicious policy can block new items.

## Dependencies

- The `OptimismPortal`'s [Terms Commitment](../../compliance/optimism-portal.md#terms-commitment), which is what
  binds a held item to the terms it was deferred with.
- The [`IPolicy`](../../compliance/policy.md#ipolicy) interface.

## Invariants

### iCM-011: Verdicts come only from the policy, and the hook functions only from the Portal

Every write to a record's `expiresAt` requires `msg.sender` to be the policy. The four
[`IBridgeHook`](../../compliance/optimism-portal.md#ibridgehook) functions require the caller to be the Portal.

[completeDeposit](#completedeposit) and [completeWithdrawal](#completewithdrawal) are permissionless,
so a cleared user never depends on the operator to send the transaction.

#### Impact

**Severity: Critical**

If violated, anyone could clear a held item and then complete it permissionlessly, releasing value the chain's policy
never approved.

### iCM-012: A record is deleted before the module calls out

The module deletes a held item's record before it calls the policy or the Portal, so a policy that calls back cannot
move the same item twice.

#### Impact

**Severity: Critical**

If violated, a hostile or buggy policy could re-enter completion for an item whose value has already moved, draining
the module.

### iCM-013: The module holds at least what it owes

For every held item the module has custody of the ETH and tokens that item carries, and `heldTokens` matches the token
balances it actually holds.

#### Impact

**Severity: Critical**

If violated, the module is insolvent. Some held items can be completed and others cannot, decided by whichever
completion is sent first.

## Function Specification

### constructor

- MUST set the immutable `OptimismPortal` address, which is the only permitted caller of the hook entry points.

### portal

Returns the `OptimismPortal` this module is the hook for.

### items

Returns the [Record](#record) for an identifier.

- MUST return a zero record for an identifier that has never been held or cleared.

### heldTokens

Returns the amount the module holds for an L1 token and L2 token pair.

### policy

Returns the policy the module consults and accepts verdicts from.

### disabled

Returns whether [Disable](#disable) is set.

### paused

Returns the pause state that gates completion of held withdrawals.

- MUST return the result of the Portal's `paused()`.

### screenDeposit

Answers the Portal for a deposit at submission.

**Behavior:**

- MUST revert if the caller is not the Portal.
- MUST revert if the Portal's `bridgeHook()` is not this module. See
  [Why the Bridge and the Hook Are Unsafe Targets](../../compliance/optimism-portal.md#why-the-bridge-and-the-hook-are-unsafe-targets).
- MUST return `true` without consulting the policy if [Disable](#disable) is set.
- MUST otherwise resolve the [Resolved Parties](#resolved-parties) and return the result of the policy's `screen`.
- MUST hoist up any revert from the policy.

### holdDeposit

Takes custody of a held deposit.

**Behavior:**

- MUST revert if the caller is not the Portal.
- MUST revert if the Portal's `bridgeHook()` is not this module. See
  [Why the Bridge and the Hook Are Unsafe Targets](../../compliance/optimism-portal.md#why-the-bridge-and-the-hook-are-unsafe-targets).
- MUST revert if the ETH received does not match the ETH the item carries.
- MUST set the record's `heldAt` for the item's identifier.
- MUST increase `heldTokens` for the item's token pair, if the item is a token transfer whose tokens it received.
- MUST emit a `Held` event carrying the identifier and the full item.

### screenWithdrawal

Answers the Portal for a withdrawal at finalization.

**Parameters:**

- `_finalizableAt`: when the withdrawal became finalizable.

**Behavior:**

- MUST revert if the caller is not the Portal.
- MUST revert if the Portal's `bridgeHook()` is not this module. See
  [Why the Bridge and the Hook Are Unsafe Targets](../../compliance/optimism-portal.md#why-the-bridge-and-the-hook-are-unsafe-targets).
- MUST return `true` without consulting the policy if [Disable](#disable) is set AND the withdrawal's nonce is at or
  above the cutoff recorded when it was disabled.
- MUST otherwise resolve the [Resolved Parties](#resolved-parties) and return the result of the policy's
  `screenRelease`, passing the record's `expiresAt` and `_finalizableAt`.
- MUST NOT catch a revert from the policy.

### holdWithdrawal

Takes custody of a held withdrawal.

**Behavior:**

- MUST revert if the caller is not the Portal.
- MUST revert if the Portal's `bridgeHook()` is not this module. See
  [Why the Bridge and the Hook Are Unsafe Targets](../../compliance/optimism-portal.md#why-the-bridge-and-the-hook-are-unsafe-targets).
- MUST revert if the ETH received does not match the ETH the item carries.
- MUST set the record's `heldAt` for the item's identifier.
- MUST increase `heldTokens` for the item's token pair, if the item is a token transfer whose tokens it received.
- MUST emit a `Held` event carrying the identifier and the full item.

### recordVerdict

Records a clear verdict against an identifier.

**Parameters:**

- `_expiresAt`: when the verdict stops being valid. The [Verdict Writer](../../compliance/policy.md#verdict-writer)
  chooses it.

**Behavior:**

- MUST revert if the caller is not the policy.
- MUST NOT require that the item exists, so a verdict can be recorded before its item reaches the Portal.
- MUST set the record's `expiresAt` to `_expiresAt`.
- MUST emit a `VerdictRecorded` event with the identifier and the expiry.

### revokeVerdict

Removes a clear verdict.

**Behavior:**

- MUST revert if the caller is not the policy.
- MUST clear the record's `expiresAt`.
- MUST emit a `VerdictRevoked` event with the identifier.

### completeDeposit

Runs a held deposit. Permissionless.

**Parameters:**

- `_item`: the item as it was held. The module derives its identifier from this preimage.

**Behavior:**

- MUST NOT restrict the caller.
- MUST revert if the record does not exist or is not held.
- MUST revert if the record has no clear verdict.
- MUST delete the record before calling the policy or the Portal.
- MUST revert if the policy's `screenRelease` does not return `true`, passing the `expiresAt` the record held before
  the delete, and a zero `_finalizableAt`.
- MUST approve the `L1StandardBridge` for the item's amount, if the item is a token transfer whose tokens it holds.
- MUST decrease `heldTokens` for the item's token pair by that amount.
- MUST call the Portal's `completeDepositTransaction` with the ETH the item carries.
- MUST emit a `Completed` event with the identifier.

### completeWithdrawal

Runs a held withdrawal. Permissionless.

**Behavior:**

- MUST revert if [paused](#paused) returns true.
- MUST otherwise behave as [completeDeposit](#completedeposit), calling the Portal's
  `completeWithdrawalTransaction`.

### setPolicy

Points the module at a different policy.

**Behavior:**

- MUST revert if the caller is not the owner.
- MUST NOT alter any record, so held items and their verdicts survive the change.

### disable

Sets [Disable](#disable).

**Parameters:**

- `_cutoffL2Nonce`: the `L2ToL1MessagePasser` message nonce at the time of the disable.

**Behavior:**

- MUST revert if the caller is not the owner.
- MUST record `_cutoffL2Nonce` as the cutoff used by [screenWithdrawal](#screenwithdrawal).
- MUST NOT release, complete or otherwise alter any item already held.

### enable

Clears [Disable](#disable), so new items are screened again.

**Behavior:**

- MUST revert if the caller is not the owner.
