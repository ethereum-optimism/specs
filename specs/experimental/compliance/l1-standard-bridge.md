# L1StandardBridge

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [What the Bridge Receives From the Portal](#what-the-bridge-receives-from-the-portal)
- [Escrowed and Minted Tokens](#escrowed-and-minted-tokens)
- [Assumptions](#assumptions)
  - [aCM-001: The OptimismPortal is trusted](#acm-001-the-optimismportal-is-trusted)
    - [Mitigations](#mitigations)
- [Function Specification](#function-specification)
  - [holdERC20](#holderc20)
  - [restoreERC20](#restoreerc20)
- [Invariants](#invariants)
  - [iCM-006: Bridge escrow moves only when requested by the Portal](#icm-006-bridge-escrow-moves-only-when-requested-by-the-portal)
    - [Impact](#impact)
  - [iCM-007: The deposits balance always matches what the bridge still holds](#icm-007-the-deposits-balance-always-matches-what-the-bridge-still-holds)
    - [Impact](#impact-1)
  - [iCM-008: The bridge moves exactly the amount the message names](#icm-008-the-bridge-moves-exactly-the-amount-the-message-names)
    - [Impact](#impact-2)
  - [iCM-009: Escrow leaves the bridge only to the hook or to the recipient](#icm-009-escrow-leaves-the-bridge-only-to-the-hook-or-to-the-recipient)
    - [Impact](#impact-3)
- [Security Considerations](#security-considerations)
  - [A Refused Escrow Move Refuses the Hold](#a-refused-escrow-move-refuses-the-hold)
  - [The Portal Could Already Reach the Escrow](#the-portal-could-already-reach-the-escrow)
  - [Resolving the Portal](#resolving-the-portal)
  - [Tokens Native to L2 Cannot Be Recovered From a Held Item](#tokens-native-to-l2-cannot-be-recovered-from-a-held-item)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

This page specifies the `L1StandardBridge` changes to support a chain that enables a bridge hook. The model those changes
serve, and the vocabulary they use, are in the [Compliance Module overview](./overview.md). The bridge's behavior on a
default OP Stack chain is specified in its [contract specification](../contracts/L1/l1-standard-bridge.md).

The bridge gains two entry points, callable only by the `OptimismPortal`, that move the escrow of a held token
transfer to the hook and back. It does not store the hook address, it keeps no record of which items are held, and
it never calls the hook directly.

A hold is the Portal's record. The bridge is handed a message to decode and asked to move escrow for it. See
[Terms Commitment](./optimism-portal.md#terms-commitment).

## What the Bridge Receives From the Portal

The bridge only receives the inner `finalizeBridgeERC20` encoded call carried in a message between the L1 and L2
bridges, which it decodes on its own: it checks the selector, then reads the token pair and the amount from the
call's arguments.

Whether the item is a [Token Bridge Message](./overview.md#token-bridge-message) at all is the Portal's judgement, not
the bridge's. The bridge trusts the Portal on the message envelope: who sent the message, through which messenger,
and to which bridge. See [Routing and Recognition](./optimism-portal.md#routing-and-recognition).

## Escrowed and Minted Tokens

Only [Native L1 Tokens](../contracts/L1/l1-standard-bridge.md#native-l1-token) are escrowed by the bridge, and only
those have a `deposits` balance. An `OptimismMintableERC20` is burned on deposit and minted on withdrawal, so there is
no escrow to move for it.

A held item carrying an `OptimismMintableERC20` therefore moves no tokens at the bridge. Only its message is held, and
the value behind it stays in the `L2StandardBridge`'s escrow on L2 until the item completes.

## Assumptions

### aCM-001: The OptimismPortal is trusted

The `OptimismPortal` only asks for an escrow move for a message it has recognized as a token transfer between the two
canonical bridges, and only for an item whose terms it has committed to.

#### Mitigations

- Both new entry points are restricted to the `OptimismPortal`. The bridge stores no Portal address today, so how it
  resolves one is an open point. See [Resolving the Portal](#resolving-the-portal).
- The bridge decodes the inner call itself rather than trusting the Portal's reading of the token pair and amount.
- The bridge's own escrow checks still apply, so a move that would overdraw the escrow reverts.
- A faulty Portal can already drain the escrow through the `L1CrossDomainMessenger`, so these entry points add no
  additional capabilities to the Portal. See
  [The Portal Could Already Reach the Escrow](#the-portal-could-already-reach-the-escrow).

## Function Specification

### holdERC20

Moves the escrow of a held token transfer out of the bridge and to the hook.

**Parameters:**

- `_message`: the inner `finalizeBridgeERC20` call the Portal is holding.

**Behavior:**

- MUST revert if the caller is not the `OptimismPortal`.
- MUST revert if the selector of `_message` is not `finalizeBridgeERC20`.
- MUST read the local token, the remote token and the amount from `_message`.
- MUST transfer that amount of the local token to the bridge hook, if the local token is a
  [Native L1 Token](../contracts/L1/l1-standard-bridge.md#native-l1-token).
- MUST decrease the `deposits` mapping for that token pair by that amount, if the local token is a
  [Native L1 Token](../contracts/L1/l1-standard-bridge.md#native-l1-token).
- MUST revert if the `deposits` balance for that token pair is below the amount.
- MUST NOT move any tokens if the local token is an `OptimismMintableERC20`.

### restoreERC20

Takes the escrow of a held token transfer back into the bridge, so the normal path be executed.

**Parameters:**

- `_message`: the same inner `finalizeBridgeERC20` call that was passed to [holdERC20](#holderc20).

**Behavior:**

- MUST revert if the caller is not the `OptimismPortal`.
- MUST revert if the selector of `_message` is not `finalizeBridgeERC20`.
- MUST read the local token, the remote token and the amount from `_message`.
- MUST pull that amount of the local token from the bridge hook, using the allowance the hook granted, if the local
  token is a [Native L1 Token](../contracts/L1/l1-standard-bridge.md#native-l1-token).
- MUST increase the `deposits` mapping for that token pair by that amount, if the local token is a
  [Native L1 Token](../contracts/L1/l1-standard-bridge.md#native-l1-token).
- MUST NOT move any tokens if the local token is an `OptimismMintableERC20`.
- MUST NOT pay the recipient. The normal path runs after the escrow is back, so a deposit is emitted to L2 and a
  withdrawal is relayed, and it is the relay that pays the recipient from escrow.

## Invariants

### iCM-006: Bridge escrow moves only when requested by the Portal

Tokens leave the bridge's escrow for the hook, and return to it, only when the `OptimismPortal` calls. The hook never
calls the bridge, and nobody else is authorized on either entry point.

#### Impact

**Severity: Critical**

If violated, any caller could drain the bridge's escrow to any address, taking the tokens of users whether or not
they ever interacted with the hook.

### iCM-007: The deposits balance always matches what the bridge still holds

Every escrow move updates the `deposits` mapping for the token pair it moves, in both directions. The value of a held
item is accounted for at the hook, never at the bridge.

#### Impact

**Severity: Critical**

If violated, the bridge's accounting moves away from its real balance. Too low, and later legitimate withdrawals revert
for users unrelated to the hold. Too high, and the bridge releases tokens it no longer has, which is a loss paid for
by other users of the same token.

### iCM-008: The bridge moves exactly the amount the message names

Both `holdERC20` and `restoreERC20` take their amount from the inner `finalizeBridgeERC20` call they decode. A hold
and the restore that reverses it therefore move the same amount, so an item's round trip through the hook leaves the
escrow where it started.

#### Impact

**Severity: Critical**

If violated, a restore could credit more escrow than the matching hold removed, creating a balance the bridge never
received. Other users of that token pair pay for it, because their withdrawals draw on the same escrow.

### iCM-009: Escrow leaves the bridge only to the hook or to the recipient

The new entry points add no way to pay an arbitrary address. [holdERC20](#holderc20) sends escrow to the bridge hook
and nowhere else, and [restoreERC20](#restoreerc20) only pulls it back from there. The recipient named in the message
is paid by the relay on the normal path, once the escrow has returned.

This is the bridge-side counterpart to
[iCM-003](./optimism-portal.md#icm-003-a-hook-can-only-delay-or-refuse-an-item).

#### Impact

**Severity: Critical**

If violated, a hold could pay an address the item never named, which turns a mechanism for deferring value into one
for redirecting it.

## Security Considerations

### A Refused Escrow Move Refuses the Hold

The bridge's own checks still apply when the Portal asks it to move escrow. If an inner check refuses the move, the whole
hold reverts, and so does the finalization that triggered it. The withdrawal stays finalizable and can be attempted
again.

This is the correct outcome for safety, but it is a liveness risk worth monitoring. A token whose escrow move the
bridge always refuses is a token whose withdrawals can never be held, so flagged value for that token
stays in the bridge's escrow indefinitely.

A cleared withdrawal never needs the move, because it pays through the normal path which should remain unchanged.

### The Portal Could Already Reach the Escrow

These entry points do not widen what a faulty `OptimismPortal` can do to the bridge. `finalizeBridgeERC20` releases
escrow to whoever the messenger names as the cross-domain sender. The messenger takes that name from a parameter of
`relayMessage`. And only the Portal may call `relayMessage`, with an `l2Sender` it sets
itself. A compromised portal can already drain escrow through that path on a default OP Stack chain.

The existing path needs a well-formed relay through the messenger, and it
leaves a `RelayedMessage` event and a `successfulMessages` entry behind. An escrow move through
[holdERC20](#holderc20) is a single call, reachable from `depositTransaction`, which never touched the bridge
before, and it leaves no messenger record. Monitoring built on messenger events does not see it.

### Resolving the Portal

Both entry points are restricted to the `OptimismPortal`, but the bridge has no Portal address today. Its
`initialize` takes only the `L1CrossDomainMessenger` and the `SystemConfig`. Two existing routes could resolve one,
`messenger.portal()` or `systemConfig.optimismPortal()`, and the design this page is drawn from does not choose
between them.

The same question applies to the destination of a held transfer. `holdERC20` sends escrow to the bridge hook, and the
design states that the bridge does not need the hook address, which leaves the Portal to supply it. Neither point is
settled.

### Tokens Native to L2 Cannot Be Recovered From a Held Item

A held item carrying an `OptimismMintableERC20` holds only the message. The tokens were burned on deposit, or were
never minted on withdrawal, so there is nothing in the bridge for the hook to take custody of.

The consequence is that such an item can only ever complete to its original recipient or stay held. Nothing, including
upgrading the hook, can redirect the value, because the value is not in the hook's custody. On L2 it remains in the
`L2StandardBridge`'s escrow.
