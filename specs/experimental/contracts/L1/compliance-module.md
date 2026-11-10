# ComplianceModule

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
  - [Record](#record)
  - [Resolved Parties](#resolved-parties)
  - [Disable Switch](#disable-switch)
- [Assumptions](#assumptions)
  - [aCM-004: The module's upgrade authority is the custodian of all deferred value](#acm-004-the-modules-upgrade-authority-is-the-custodian-of-all-deferred-value)
    - [Mitigations](#mitigations)
  - [aCM-005: The policy is trusted](#acm-005-the-policy-is-trusted)
    - [Mitigations](#mitigations-1)
  - [aCM-006: The module owner is trusted with whatever the policy can do](#acm-006-the-module-owner-is-trusted-with-whatever-the-policy-can-do)
    - [Mitigations](#mitigations-2)
  - [aCM-007: Tokens behave as the StandardBridge requires](#acm-007-tokens-behave-as-the-standardbridge-requires)
    - [Mitigations](#mitigations-3)
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
  - [initialize](#initialize)
  - [portal](#portal)
  - [owner](#owner)
  - [items](#items)
  - [parties](#parties)
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
  - [renounceOwnership](#renounceownership)

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

The module stores whatever `expiresAt` the policy passes and hands it back when value moves. The module does not
judge it; the policy does, and it treats an expired verdict as none.

### Resolved Parties

The **Resolved Parties** of an item are the two addresses the module passes to the policy: the sender, then the
recipient. For a message sent through the messengers, the module decodes the real sender and recipient from the
envelope rather than passing the messengers themselves.

This decoding is narrow by design with fixed contracts, fixed selectors, no recursion and no simulation:

- A `relayMessage` envelope to the direction's messenger whose inner call is `finalizeBridgeERC20` or
  `finalizeBridgeETH`, from the counterpart standard bridge to this side's standard bridge: `_from` and `_to`.
- Any other `relayMessage` envelope to the direction's messenger: the messenger's `_sender` and `_target`.
- Anything else: the outer addresses, with a deposit's `from` unaliased when the item's `aliased` flag is set.

Resolving this once in the module, rather than in each policy, keeps the protocol knowledge in one place.

### Disable Switch

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
- [Disable Switch](#disable-switch) bounds how long a failing or compromised policy can block new items.

### aCM-006: The module owner is trusted with whatever the policy can do

The owner points the module at a policy with [setPolicy](#setpolicy), so it inherits everything
[aCM-005](#acm-005-the-policy-is-trusted) grants the policy, and it can stop screening new items with
[disable](#disable). It is a role separate from the upgrade authority in aCM-004, which reaches held value directly.

#### Mitigations

- The owner cannot alter a record, so held items keep their verdicts across a policy change.
- A replacement policy can still only delay or refuse. See
  [iCM-003](../../compliance/optimism-portal.md#icm-003-a-hook-can-only-delay-or-refuse-an-item).
- Every change is observable on L1: `PolicySet` carries both policies, and `Disabled` carries the cutoff.

### aCM-007: Tokens behave as the StandardBridge requires

The module inherits the `StandardBridge`'s token support:

- ETH.
- [Native L1 Tokens](./l1-standard-bridge.md#native-l1-token), which the bridge escrows.
- [OptimismMintableERC20](../L2/l2-standard-bridge.md#optimismmintableerc20) tokens, which have no L1 escrow, so a
  held item carrying one holds only its message.

A token that takes a fee on transfer, rebases, or otherwise moves a balance its transfer did not name breaks
[iCM-013](#icm-013-the-module-holds-at-least-what-it-owes), because `heldTokens` records the amount the message names
while the module ends up holding a different amount.

#### Mitigations

- The bridge has the same constraint, so such a token is already unsupported before a hook is involved.
- `heldTokens` is kept per token pair, so a token that breaks it cannot reach the escrow of another pair.

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

For every held item the module has custody of the ETH and tokens that item carries, and `heldTokens` is at most the
token balance it actually holds.

#### Impact

**Severity: Critical**

If violated, the module is insolvent. Some held items can be completed and others cannot, decided by whichever
completion is sent first.

## Function Specification

### constructor

**Parameters:**

- `_portal`: the `OptimismPortal` this module is the hook for.
- `_l1CrossDomainMessenger`, `_l1StandardBridge`: the contracts the module decodes a token transfer against.

**Behavior:**

- MUST set all three addresses as immutables. The Portal is the only permitted caller of the hook entry points, and
  the other two are used to find the [Resolved Parties](#resolved-parties) and to approve the bridge on token
  completions.
- MUST revert if any of the three is the zero address.

The messenger and the bridge are arguments, so the module can be deployed before the Portal is initialized and wired
as its hook in the same deployment. They must be the addresses the chain's `SystemConfig` holds.

### initialize

Sets the module's owner and its first policy.

**Behavior:**

- MUST revert if the module has already been initialized.
- MUST revert if the owner or the policy is the zero address.
- MUST set the owner and the policy.
- MUST emit a `PolicySet` event with the zero address as the previous policy.

### portal

Returns the `OptimismPortal` this module is the hook for.

### owner

Returns the address that can call [setPolicy](#setpolicy), [disable](#disable) and [enable](#enable). It is a separate
role from the upgrade authority in
[aCM-004](#acm-004-the-modules-upgrade-authority-is-the-custodian-of-all-deferred-value).

### items

Returns the [Record](#record) for an identifier.

- MUST return a zero record for an identifier that has never been held or cleared.

### parties

Returns the [Resolved Parties](#resolved-parties) of an item.

- MUST return the same addresses, in the same order, that the module passes to the policy for that item.

### heldTokens

Returns the amount the module holds for an L1 token and L2 token pair.

### policy

Returns the policy the module consults and accepts verdicts from.

### disabled

Returns whether the [Disable Switch](#disable-switch) is set.

### paused

Returns the pause state that gates completion of held withdrawals.

- MUST return the result of the Portal's `paused()`.

### screenDeposit

Answers the Portal for a deposit at submission.

**Behavior:**

- MUST revert if the caller is not the Portal.
- MUST revert if the Portal's `bridgeHook()` is not this module. See
  [Why the Bridge and the Hook Are Unsafe Targets](../../compliance/optimism-portal.md#why-the-bridge-and-the-hook-are-unsafe-targets).
- MUST return `true` without consulting the policy if the [Disable Switch](#disable-switch) is set.
- MUST otherwise resolve the [Resolved Parties](#resolved-parties) and return the result of the policy's
  `screenDeposit`.
- MUST bubble up any revert from the policy.

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

- `_finalizableAt`: the withdrawal's [Finalizable Time](../../compliance/overview.md#finalizable-time) for the proof
  being finalized.

**Behavior:**

- MUST revert if the caller is not the Portal.
- MUST revert if the Portal's `bridgeHook()` is not this module. See
  [Why the Bridge and the Hook Are Unsafe Targets](../../compliance/optimism-portal.md#why-the-bridge-and-the-hook-are-unsafe-targets).
- MUST return `true` without consulting the policy if the [Disable Switch](#disable-switch) is set AND the
  withdrawal's nonce is at or above the cutoff recorded when it was disabled.
- MUST otherwise resolve the [Resolved Parties](#resolved-parties) and return the result of the policy's
  `screenWithdrawal`, passing the record's `expiresAt` and `_finalizableAt`.
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
- MUST revert if `_expiresAt` is zero, since a zero expiry is what [revokeVerdict](#revokeverdict) leaves behind.
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
- MUST resolve the [Resolved Parties](#resolved-parties) and revert if the policy's `screenRelease` does not return
  `true`, passing the item, those parties, and the `expiresAt` the record held before the delete.
- MUST approve the `L1StandardBridge` for the item's amount and decrease `heldTokens` for the item's token pair by
  that amount, if the item is a token transfer whose tokens it holds.
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
- MUST revert if the new policy is the zero address.
- MUST set the policy to the new policy.
- MUST NOT alter any record, so held items and their verdicts survive the change.
- MUST emit a `PolicySet` event with the previous and the new policy.

### disable

Sets the [Disable Switch](#disable-switch).

**Parameters:**

- `_cutoffL2Nonce`: the versioned message nonce, as returned by `L2ToL1MessagePasser.messageNonce()`, at the time of
  the disable. A raw counter sits below every versioned nonce and would let every withdrawal bypass screening.

**Behavior:**

- MUST revert if the caller is not the owner.
- MUST record `_cutoffL2Nonce` as the cutoff used by [screenWithdrawal](#screenwithdrawal).
- MUST set `disabled` to `true`.
- MUST NOT release, complete or otherwise alter any item already held.
- MUST emit a `Disabled` event with the cutoff.

### enable

Clears the [Disable Switch](#disable-switch) and its cutoff, so every item is screened again, including a withdrawal
was set.

**Behavior:**

- MUST revert if the caller is not the owner.
- MUST clear the cutoff.
- MUST set `disabled` to `false`.
- MUST emit an `Enabled` event.

### renounceOwnership

Refuses to give up the owner role.

**Behavior:**

- MUST revert. An ownerless module could never change its policy, disable it, or enable it again, so every item it
  holds would be left to the policy in place at the time.
