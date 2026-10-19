# OptimismPortal

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
  - [Bridge Hook Address](#bridge-hook-address)
  - [Bridge Hook Feature](#bridge-hook-feature)
  - [Unsafe Target](#unsafe-target)
  - [Deposit Counter](#deposit-counter)
- [IBridgeHook](#ibridgehook)
- [Item Construction](#item-construction)
- [Routing and Recognition](#routing-and-recognition)
- [Terms Commitment](#terms-commitment)
- [Withdrawals and When They Are Held](#withdrawals-and-when-they-are-held)
- [Function Specification](#function-specification)
  - [initialize](#initialize)
  - [bridgeHook](#bridgehook)
  - [removeHook](#removehook)
  - [depositTransaction](#deposittransaction)
  - [proveWithdrawalTransaction](#provewithdrawaltransaction)
  - [finalizeWithdrawalTransactionExternalProof](#finalizewithdrawaltransactionexternalproof)
  - [completeDepositTransaction](#completedeposittransaction)
  - [completeWithdrawalTransaction](#completewithdrawaltransaction)
- [Resource Metering](#resource-metering)
- [Invariants](#invariants)
  - [iCM-001: A held item executes only on its committed terms](#icm-001-a-held-item-executes-only-on-its-committed-terms)
    - [Impact](#impact)
  - [iCM-002: A held item completes at most once](#icm-002-a-held-item-completes-at-most-once)
    - [Impact](#impact-1)
  - [iCM-003: A hook can only delay or refuse an item](#icm-003-a-hook-can-only-delay-or-refuse-an-item)
    - [Impact](#impact-2)
  - [iCM-004: A chain with no hook configured is unaffected](#icm-004-a-chain-with-no-hook-configured-is-unaffected)
    - [Impact](#impact-3)
  - [iCM-005: A held withdrawal keeps its minimum gas guarantee](#icm-005-a-held-withdrawal-keeps-its-minimum-gas-guarantee)
    - [Impact](#impact-4)
- [Security Considerations](#security-considerations)
  - [Why the Bridge and the Hook Are Unsafe Targets](#why-the-bridge-and-the-hook-are-unsafe-targets)
  - [Changing the Hook](#changing-the-hook)
  - [Gas Headroom on the Withdrawal Path](#gas-headroom-on-the-withdrawal-path)
  - [Cost When No Hook Is Set](#cost-when-no-hook-is-set)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

This page specifies what the `OptimismPortal` gains when a chain enables a bridge hook. The model those changes
serve, and the vocabulary they use, are in the [Compliance Module overview](./overview.md).

The Portal is the only contract that asks the hook. It builds every [Item](./overview.md#item), offers it to the hook,
commits the terms of every item the hook defers, and runs a deferred item later on exactly those terms. Everything the
hook can do, it does through the four functions in [`IBridgeHook`](#ibridgehook).

## Definitions

### Bridge Hook Address

The **Bridge Hook Address** is network-specific state on the Portal. It is set only through
[`initialize`](#initialize), by the ProxyAdmin or its owner, and cleared only by [`removeHook`](#removehook). While it
is `address(0)`, the Portal behaves as on a default OP Stack chain.

The `L1StandardBridge` does not hold the hook address. The Portal is the contract that moves the bridge's escrow when
an ERC-20 deposit or withdrawal is held.

Removing the hook stops screening for new items and strands every item already held. Its commitment stays in the
Portal, and its value stays with the removed hook.

### Unsafe Target

An Unsafe Target is an address a withdrawal may not call. The default set is the `OptimismPortal` itself and the
`ETHLockbox`. This page adds the `L1StandardBridge` on every chain, and the
[Bridge Hook Address](#bridge-hook-address) while it is set. See
[Why the Bridge and the Hook Are Unsafe Targets](#why-the-bridge-and-the-hook-are-unsafe-targets).

### Deposit Counter

The **Deposit Counter** is a counter the Portal assigns to a deposit when it screens it. A withdrawal carries its own
nonce, unique on L2, so it is already unique, but a deposit has no unique field of its own: two identical deposits in
the same block are otherwise indistinguishable. The counter is what makes a deposit's [Identifier](./overview.md#identifier)
name exactly one deposit, and the identifier exists only from the moment the counter is assigned.

## IBridgeHook

```solidity
interface IBridgeHook {
    function screenDeposit(Item calldata item) external returns (bool pass_);
    function holdDeposit(Item calldata item) external payable;
    function screenWithdrawal(Item calldata item, uint256 finalizableAt) external returns (bool pass_);
    function holdWithdrawal(Item calldata item) external payable;
}
```

`screenDeposit` and `screenWithdrawal` carry the [Screening Outcome](./overview.md#screening-outcome) in how they
return:

| Outcome | How the hook signals it | What the Portal does |
| --- | --- | --- |
| Proceed | returns `true` | the item takes the normal path, unchanged |
| Hold | returns `false` | the Portal commits the item's terms and moves its value to the hook |
| Reject | reverts | the whole transaction reverts and nothing is consumed |

`screenWithdrawal` also receives `finalizableAt`, the [Finalizable Time](./overview.md#finalizable-time) of the
withdrawal, so a hook can reject an uncleared withdrawal until it is ready to hold it. See
[Withdrawals and When They Are Held](#withdrawals-and-when-they-are-held).

The Portal builds its own items and commits to their terms itself. It asks the hook only what to do with them.

## Item Construction

The Portal builds an item from what it sees: the sender, target, value and call. Token transfers are items too, since
the standard bridges send their messages through the Portal. When the Portal
[recognizes](#routing-and-recognition) a token transfer between the L1 and L2 standard bridges, in either direction, it
marks the item as one. The tokens and the amount stay in the item's data, where the bridge and the hook read them. The
sender and target stay the messengers, and the hook decodes the real [Parties](./overview.md#parties) for the policy.

An item's [Identifier](./overview.md#identifier) is `keccak256(abi.encode(item))`, computed the same way by the Portal
and the hook, so both agree on which item a verdict names and the verdict covers every term. The following shape
carries the fields the identifier must bind:

```solidity
enum Direction { Deposit, Withdrawal }
enum Asset { ETH, ERC20 }

struct Item {
    Direction direction;
    Asset     asset;       // ERC20 when the Portal recognizes a transfer between the standard bridges
    address   from;        // a deposit's sender stays aliased
    bool      aliased;
    address   to;
    uint256   ethAmount;   // a deposit's msg.value, or a withdrawal's value
    uint256   l2Value;     // deposits only
    uint256   gasLimit;
    bool      isCreation;  // deposits only
    bytes     data;        // for a token transfer, carries the tokens and the amount
    uint256   nonce;       // deposit counter, or withdrawal nonce
}
```

## Routing and Recognition

The Portal recognizes one shape: a message between the two canonical bridges.

- For a deposit, the envelope's sender is the messenger, which the Portal derives from its own caller, and the
  messenger stamps the `L1StandardBridge` as the inner sender.
- For a withdrawal, the proven sender is the L2 messenger and the inner sender is the `L2StandardBridge`.
- In both, the inner call is `finalizeBridgeERC20`.

Nobody can choose these fields, so a message that matches came from the bridge. The Portal marks such an item as a
token transfer, and moves escrow only for it.

The bridge trusts the Portal on the envelope: who sent the message, through which messenger, to which bridge. It never
sees the envelope itself, only the inner `finalizeBridgeERC20` call, which it decodes on its own.

The recognition still has to be correct, because the bridge acts on it. It gives the Portal no new authority: the
messenger already accepts relays only from the Portal, with a sender the Portal supplies, so a faulty Portal can
already reach the bridge's escrow.

## Terms Commitment

```solidity
mapping(bytes32 => bool) public heldDeposits;    // keyed by the item's identifier
mapping(bytes32 => bool) public heldWithdrawals; // keyed by the withdrawal hash
```

One bit per deferred item, recording the exact terms the protocol agreed to defer, already validated on the way in.
When the hook asks to complete an item, the Portal rebuilds the key from the arguments it receives and requires the
matching bit.

A withdrawal is keyed by its own hash, which the Portal recomputes from the exact transaction it will execute, so the
key already binds every term.

The bridge keeps no commitments. It moves escrow only when the Portal calls, and only for a message the Portal has
committed to.

## Withdrawals and When They Are Held

A withdrawal is screened each time someone tries to finalize it.

- If the hook proceeds, the withdrawal pays out through the normal path. For tokens that is the messenger and the
  bridge, as on a default chain.
- If the hook rejects, the finalization reverts. The withdrawal can be finalized again later, for example once it
  clears.
- If the hook holds, the withdrawal is marked finalized and its value moves to the hook, ETH from the `ETHLockbox` and
  tokens from the bridge's escrow.

The protocol cannot force a hold, because the hook can always reject instead. How long flagged value stays in protocol
contracts is therefore the chain's commitment, not the protocol's. It is kept by finalizing flagged withdrawals once
the policy would hold them, which is an ordinary finalization that anyone can trigger through the existing
permissionless entry points.

## Function Specification

### initialize

Initializes the Portal. It is the only way to set the [Bridge Hook Address](#bridge-hook-address). Only the
`_bridgeHook` parameter is new, and the rest of the behavior is unchanged.

**Parameters:**

- `_bridgeHook`: the contract implementing [`IBridgeHook`](#ibridgehook), or `address(0)` to keep the current hook.

**Behavior:**

- MUST revert if the caller is not the ProxyAdmin or its owner.
- MUST leave `bridgeHook` unchanged if `_bridgeHook` is `address(0)`.
- MUST otherwise set `bridgeHook` to `_bridgeHook`, replacing any hook already set, and emit `BridgeHookSet`.
- MUST revert with `OptimismPortal_InvalidBridgeHookState` if, after this step, `bridgeHook` is not `address(0)` and
  the [Bridge Hook Feature](#bridge-hook-feature) is disabled.
- MUST leave `heldDeposits` and `heldWithdrawals` unchanged.

### bridgeHook

Returns the [Bridge Hook Address](#bridge-hook-address).

- MUST return `address(0)` if the chain has not configured a hook.

### removeHook

Removes the [Bridge Hook Address](#bridge-hook-address).

**Behavior:**

- MUST revert if the caller is not the ProxyAdmin owner.
- MUST revert with `OptimismPortal_InvalidBridgeHookState` if `bridgeHook` is `address(0)`.
- MUST set `bridgeHook` to `address(0)` and emit `BridgeHookRemoved` with the removed hook.

### depositTransaction

Accepts deposits of ETH and data. Behavior must remain unchanged while `bridgeHook` is `address(0)`.

**Behavior, when `bridgeHook` is not `address(0)`:**

- MUST perform every check it performs on a default OP Stack chain before consulting the hook.
- MUST assign the [Deposit Counter](#deposit-counter) and build the item from it before calling the hook, so the
  identifier the hook screens is the identifier the Portal commits to if it holds.
- MUST call `bridgeHook.screenDeposit` with that item.
- MUST take today's normal path, unchanged, when `screenDeposit` returns `true`.
- MUST revert when `screenDeposit` reverts.
- When `screenDeposit` returns `false`, it MUST hold the deposit:
  - MUST set `heldDeposits[identifier]` to `true` before moving any value.
  - MUST NOT emit a `TransactionDeposited` event.
  - MUST move any ETH the deposit carries to the hook by calling `holdDeposit` with that value.
  - MUST ask the `L1StandardBridge` to move its escrow for the item, if the item is identified as a
    [Token Bridge Message](./overview.md#token-bridge-message) by calling `holdERC20` on the `L1StandardBridge`.

### proveWithdrawalTransaction

Proves a withdrawal transaction.

**Behavior:**

- MUST revert if the withdrawal target is an [Unsafe Target](#unsafe-target).
- MUST NOT consult the hook since a withdrawal is screened when it is finalized, not when it is proven.
- MUST otherwise behave as on a default OP Stack chain while `bridgeHook` is `address(0)`.

### finalizeWithdrawalTransactionExternalProof

Finalizes a withdrawal using a proof submitted by another address.

**Behavior:**

- MUST revert if the withdrawal target is an [Unsafe Target](#unsafe-target).
- MUST otherwise behave as on a default OP Stack chain while `bridgeHook` is `address(0)`.

**Behavior, when `bridgeHook` is not `address(0)`:**

- MUST perform every check it performs on a default OP Stack chain, including `checkWithdrawal`, before consulting the
  hook.
- MUST mark the withdrawal as finalized before calling the hook.
- MUST call `bridgeHook.screenWithdrawal` with the item and the withdrawal's
  [Finalizable Time](./overview.md#finalizable-time), before forwarding the withdrawal call to the appropriate target.
- MUST take the normal path, unchanged, when `screenWithdrawal` returns `true`.
- MUST revert, consuming nothing and leaving the withdrawal finalizable, when `screenWithdrawal` reverts.
- When `screenWithdrawal` returns `false`, it MUST hold the withdrawal:
  - MUST set `heldWithdrawals[withdrawalHash]` to `true` before moving any value.
  - MUST NOT forward the withdrawal call to its target.
  - MUST move the withdrawal's ETH to the hook by calling `holdWithdrawal` with that value.
  - MUST ask the `L1StandardBridge` to move its escrow for the item, if the item is a recognized
    [Token Bridge Message](./overview.md#token-bridge-message) by calling `holdERC20` on the `L1StandardBridge`.

### completeDepositTransaction

Executes a held deposit on the terms the Portal committed to. The [Bridge Hook Address](#bridge-hook-address) calls
this function when it is ready to release the deposit.

**Parameters:**

- `_item`: the item as it was held. The Portal rebuilds its identifier from this preimage.

**Behavior:**

- MUST revert if the caller is not the [Bridge Hook Address](#bridge-hook-address).
- MUST revert if `heldDeposits[identifier]` is not `true`.
- MUST revert if the ETH sent with the call does not match the item's committed value.
- MUST delete `heldDeposits[identifier]` before moving any value.
- MUST ask the `L1StandardBridge` to take its escrow back, if the item is a recognized
  [Token Bridge Message](./overview.md#token-bridge-message) by calling `restoreERC20` on the `L1StandardBridge`.
- MUST then run the normal deposit path, emitting a `TransactionDeposited` event with the committed terms.
- MUST NOT revert if the system is paused, matching `depositTransaction` on a default OP Stack chain.

### completeWithdrawalTransaction

Runs a held withdrawal on the terms the Portal committed to. The [Bridge Hook Address](#bridge-hook-address) calls
this function when it is ready to release the withdrawal.

**Parameters:**

- `_item`: the item as it was held. The Portal rebuilds the withdrawal hash from this preimage.

**Behavior:**

- MUST revert if the caller is not the [Bridge Hook Address](#bridge-hook-address).
- MUST revert if the system is paused.
- MUST revert if the [L2 Withdrawal Sender](../../fault-proof/stage-one/optimism-portal.md#l2-withdrawal-sender) is
  not `DEFAULT_L2_SENDER`, so a completion cannot run inside another withdrawal's execution.
- MUST revert if `heldWithdrawals[withdrawalHash]` is not `true`.
- MUST revert if the ETH sent with the call does not match the item's committed value.
- MUST delete `heldWithdrawals[withdrawalHash]` before moving any value.
- MUST ask the `L1StandardBridge` to take its escrow back, if the item is a recognized
  [Token Bridge Message](./overview.md#token-bridge-message)  by calling `restoreERC20` on the `L1StandardBridge`.
- MUST set the L2 Withdrawal Sender to the item's committed sender before forwarding the call.
- MUST forward the call to the target with `SafeCall.callWithMinGas` and the item's committed `gasLimit`.
- MUST unset the L2 Withdrawal Sender after the call returns.
- MUST revert if the forwarded call fails.

## Resource Metering

A held deposit is paid for once, at submission, like any other deposit. Its gas counts against the deposit limit of
the L1 block where it completes, since that is where it reaches L2. A completion that does not fit reverts and can be
sent again in the next block.

This splits `ResourceMetering._metered` into an allocate step and a charge step, so a completion is counted against
its block's limit without being charged again.

## Invariants

### iCM-001: A held item executes only on its committed terms

A protocol contract only ever executes terms it committed to. The Portal rebuilds the commitment key from the preimage
it is handed at completion and requires the matching bit, so an item that does not match a commitment cannot be
executed.

#### Impact

**Severity: Critical**

If violated, a hook could run an item the protocol never agreed to defer, or run a deferred item on altered terms,
redirecting value or changing what the item does on L2.

### iCM-002: A held item completes at most once

The Portal deletes the commitment registered in either `heldDeposits` or `heldWithdrawals` before any value moves.

#### Impact

**Severity: Critical**

If violated, a held item could be completed repeatedly, draining the Portal, the `ETHLockbox` or the bridge's escrow.

### iCM-003: A hook can only delay or refuse an item

The Portal builds every item and commits its terms. The hook chooses which item moves and when, never where the value
goes or what the item does.

#### Impact

**Severity: Critical**

If violated, the contract at the hook address could redirect user value or decide arbitrary execution on both L1 and
L2. That is far more authority than setting a hook is meant to grant to whoever can upgrade it.

### iCM-004: A chain with no hook configured is unaffected

While `bridgeHook` is `address(0)`, every entry point behaves exactly as on a default OP Stack chain, except that the
`L1StandardBridge` is an [Unsafe Target](#unsafe-target).

#### Impact

**Severity: High**

If violated, chains that never opted in would change behavior on upgrade, which the feature exists to avoid.

### iCM-005: A held withdrawal keeps its minimum gas guarantee

A withdrawal carries a gas limit for the call it will make on L1. Holding splits that call into two transactions: the
finalization that defers it, and the completion that executes it. The gas limit has to survive this deferring.

A held withdrawal is recorded as finalized and its call does not execute. The commitment is what carries the guarantee
across. [`completeWithdrawalTransaction`](#completewithdrawaltransaction) forwards the call with
`SafeCall.callWithMinGas` and the committed `gasLimit`, and reverts if that call fails. The target receives the gas
limit the withdrawal carries, whether the withdrawal was held or not.

Without this, the withdrawal is consumed at finalization, and the gas limit set on L2 would apply to nothing.

#### Impact

**Severity: Critical**

If violated, a held withdrawal completes with less gas than its sender asked for. The target call might fail.
The commitment is already deleted and cannot be retried, leaving whichever value it carries stranded.

## Security Considerations

### Why the Bridge and the Hook Are Unsafe Targets

The Portal forwards a withdrawal's call itself, so the target sees the Portal as its caller, which is the only
check those entry points make. A withdrawal targeting the `L1StandardBridge` with a `restoreERC20` call credits
escrow the Portal never committed to, and one targeting the hook with a `holdDeposit` call writes a record for an
item the Portal never held.

The bridge is unsafe whether or not the chain sets a hook. Gating it on the hook would mean a withdrawal proven
while `bridgeHook` is `address(0)` stops being finalizable once a hook is set. Nothing legitimate targets the
bridge directly, because a token withdrawal reaches it through the `L1CrossDomainMessenger`.

The hook is an Unsafe Target only while it is set. After [`removeHook`](#removehook) or a replacement through
[`initialize`](#initialize), the former hook is an ordinary target, and a withdrawal can call it with the Portal as its
caller. A hook MUST therefore check that it is still the Portal's hook, with `bridgeHook() == address(this)`, and not
only that its caller is the Portal.

The address can also change between proving and finalizing, so the two checks can disagree. The one at finalization
is the binding one.

### Changing the Hook

Replacing or removing a hook while items are held does not move their value, which stays with the former hook.

`initialize` is the only way to set a hook, so changing it also re-applies every other `initialize` argument: the
`SystemConfig`, the `AnchorStateRegistry`, the `ETHLockbox` and the proof maturity delay. The operator must pass the
current values. A wrong proof maturity delay, for example, changes when every withdrawal already proven can be
finalized.

### Gas Headroom on the Withdrawal Path

The hook runs before `SafeCall.callWithMinGas`, so finalizing a cleared withdrawal also pays for the hook. This cannot
brick a withdrawal, because `callWithMinGas` checks the remaining gas when it makes the call, so a finalization
without enough gas reverts, consumes nothing, and can be retried with more.

It does cost headroom. A withdrawal whose gas limit is close to the most gas an L1 transaction can use may no longer
fit in one transaction. Nothing runs inside the relay, so token withdrawals do not depend on the gas the user set on
L2.

### Cost When No Hook Is Set

A chain that has not configured a hook pays one `SLOAD`, which short circuits the rest of the hook logic. Proving and
finalizing also read the `L1StandardBridge` address from `SystemConfig` for the unsafe-target check, which applies on
every chain.
