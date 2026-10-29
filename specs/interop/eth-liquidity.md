# ETHLiquidity

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Constants](#constants)
- [Definitions](#definitions)
  - [ETH Liquidity](#eth-liquidity)
  - [Liquidity Minting](#liquidity-minting)
  - [Liquidity Burning](#liquidity-burning)
- [Pause](#pause)
- [Assumptions](#assumptions)
  - [aEL-001: SafeSend correctly transfers ETH to recipients](#ael-001-safesend-correctly-transfers-eth-to-recipients)
    - [Mitigations](#mitigations)
- [Invariants](#invariants)
  - [iEL-001: ETH balance is always sufficient for minting / burning](#iel-001-eth-balance-is-always-sufficient-for-minting--burning)
    - [Impact](#impact)
  - [iEL-002: Only authorized contracts can call mint and burn](#iel-002-only-authorized-contracts-can-call-mint-and-burn)
    - [Impact](#impact-1)
  - [iEL-003: Contract balance never overflows](#iel-003-contract-balance-never-overflows)
    - [Impact](#impact-2)
  - [iEL-004: Pause updates apply in L1 order](#iel-004-pause-updates-apply-in-l1-order)
    - [Impact](#impact-3)
    - [Dependencies](#dependencies)
  - [iEL-005: L1CrossDomainMessenger message nonces only increase](#iel-005-l1crossdomainmessenger-message-nonces-only-increase)
    - [Impact](#impact-4)
- [Function Specification](#function-specification)
  - [mint](#mint)
  - [burn](#burn)
  - [setPaused](#setpaused)
- [Events](#events)
  - [LiquidityMinted](#liquidityminted)
  - [LiquidityBurned](#liquidityburned)
  - [PausedSet](#pausedset)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The `ETHLiquidity` contract is a predeploy that manages native ETH liquidity for cross-chain
transfers within the Superchain interop set. It works in conjunction with the
`SuperchainETHBridge` to facilitate the movement of ETH between chains without requiring
modifications to the EVM to generate new ETH.

The contract is initialized with a very large balance (`type(uint248).max` wei) to ensure it can
handle all legitimate minting operations. This design allows the `SuperchainETHBridge` to have a
guaranteed source of ETH liquidity on each chain, which is essential for the cross-chain ETH
transfer mechanism.

The contract mirrors this chain's [pause](#pause) on L1. While it is paused, ETH can't be burned or minted, so the
`SuperchainETHBridge` can't send, relay or refund ETH.

## Constants

| Name                    | Value                                        |
| ----------------------- | -------------------------------------------- |
| `ETHLiquidity` Address  | `0x4200000000000000000000000000000000000025` |
| Initial Balance         | `type(uint248).max` wei                      |

## Definitions

### ETH Liquidity

ETH Liquidity refers to the availability of native ETH on a particular chain. The `ETHLiquidity`
contract manages this liquidity by providing a mechanism to burn and mint ETH as needed for
cross-chain transfers.

### Liquidity Minting

Liquidity Minting is the process of withdrawing ETH from the `ETHLiquidity` contract. This
operation is performed when ETH needs to be sent to a recipient on a destination chain as part of
a cross-chain transfer, or refunded to its sender on the source chain after the transfer's message
[expired](./message-expiry.md).

### Liquidity Burning

Liquidity Burning is the process of depositing ETH into the `ETHLiquidity` contract. This operation
is performed when ETH is being sent from a source chain to a destination chain as part of a
cross-chain transfer.

## Pause

The [pause mechanism](../protocol/stage-1.md#pause-mechanism) is designed to impact the liveness of the system such
that an attack on the system is unable to actually remove ETH or ERC-20 tokens from the bridge or any other contract
that stores ETH and/or tokens. The existing pause from L1 can also stop the cross-chain bridge on L2. The L1 pause
is this chain's `paused()` on its `L1CrossDomainMessenger`, which resolves through the chain's `ETHLockbox`, its
[Pause Identifier](../protocol/stage-1.md#pause-identifier), to the `SuperchainConfig`'s global pause or the pause for
that identifier, and its expiry. Chains that share an `ETHLockbox` therefore pause together. There is no separate L2
pause role.

`ETHLiquidity` holds a copy of that state. Anyone syncs it by calling
[`L1CrossDomainMessenger.syncETHLiquidityPause`](./l1-cross-domain-messenger.md#syncethliquiditypause), which
sends the current state to L2 as a deposit, also while the chain is paused. Call it again after any pause, unpause
or pause expiry; until then, L2 keeps the last state it received. Each update carries the nonce of the
`L1CrossDomainMessenger` message that sends it, and L2 ignores an update from an earlier message than the one it
applied ([iEL-004](#iel-004-pause-updates-apply-in-l1-order)). A sync that failed on L2, such as for gas, can be
replayed later without undoing a newer state.

## Assumptions

### aEL-001: SafeSend correctly transfers ETH to recipients

We assume that the `SafeSend` mechanism correctly transfers ETH to recipients without reverting
for valid addresses.

#### Mitigations

- Extensive testing of the `SafeSend` mechanism
- Audits of the ETH transfer logic

## Invariants

### iEL-001: ETH balance is always sufficient for minting / burning

The `ETHLiquidity` contract must always have enough ETH to fulfill all legitimate minting / burning
requests.

#### Impact

**Severity: Critical**

If this invariant is broken, the cross-chain ETH transfer mechanism would fail, potentially leading
to users being unable to receive their ETH on destination chains.

### iEL-002: Only authorized contracts can call mint and burn

The `mint` and `burn` functions must only be callable by authorized contracts (specifically the
`SuperchainETHBridge`).

#### Impact

**Severity: Critical**

If this invariant is broken, unauthorized parties could mint ETH without burning an equivalent
amount on a source chain, leading to inflation.

### iEL-003: Contract balance never overflows

The `ETHLiquidity` contract's balance must never overflow due to excessive burning operations.

#### Impact

**Severity: High**

If this invariant is broken, the contract could reach an invalid state, potentially disrupting the
cross-chain ETH transfer mechanism. The invariant that avoids overflow is maintained by
`SuperchainETHBridge`, but could theoretically be broken by some future contract that is allowed to
integrate with `ETHLiquidity`. Maintainers should be careful to ensure that such future contracts
do not break this invariant.

### iEL-004: Pause updates apply in L1 order

`ETHLiquidity` MUST apply pause updates in the order that this chain's `L1CrossDomainMessenger` sent them: an update
MUST NOT replace one sent after it. `paused` MUST change only through an update sent by this chain's
`L1CrossDomainMessenger`.

#### Impact

**Severity: High**

If this invariant is broken, a stale unpause could replace a newer pause and reopen the bridge during an attack, or
someone other than the chain's pause could stop or restart the bridge.

#### Dependencies

- [iEL-005](#iel-005-l1crossdomainmessenger-message-nonces-only-increase)
- [iME-003](./message-expiry.md#ime-003-only-two-functions-send-as-the-l1crossdomainmessenger)

### iEL-005: L1CrossDomainMessenger message nonces only increase

The `messageNonce()` of this chain's `L1CrossDomainMessenger` MUST only increase, so that each pause update carries
a greater nonce than every update sent before it.

#### Impact

**Severity: High**

If this invariant is broken, `ETHLiquidity` could ignore a newer pause update, or apply an older one over it.

## Function Specification

### mint

Withdraws ETH from the `ETHLiquidity` contract equal to the `_amount` and sends it to the
`msg.sender`.

```solidity
function mint(uint256 _amount) external
```

- MUST revert if called by any address other than the `SuperchainETHBridge`.
- MUST revert with `ETHLiquidity_Paused` while `paused` is `true`.
- MUST transfer the `_amount` of ETH to the `msg.sender` using `SafeSend`.
- MUST emit a `LiquidityMinted` event with the `msg.sender` and `_amount`.

### burn

Locks ETH into the `ETHLiquidity` contract.

```solidity
function burn() external payable;
```

- MUST accept ETH via `msg.value`.
- MUST revert if called by any address other than the `SuperchainETHBridge`.
- MUST revert with `ETHLiquidity_Paused` while `paused` is `true`.
- MUST emit a `LiquidityBurned` event with the `msg.sender` and `msg.value`.

### setPaused

Applies this chain's L1 pause state, as sent by
[`L1CrossDomainMessenger.syncETHLiquidityPause`](./l1-cross-domain-messenger.md#syncethliquiditypause).

```solidity
function setPaused(bool _paused, uint256 _messageNonce) external;
```

- MUST revert with `ETHLiquidity_NotL1CrossDomainMessenger` unless `msg.sender` is the `L2CrossDomainMessenger`
  and its `xDomainMessageSender()` is this chain's `L1CrossDomainMessenger`.
- MUST NOT change any state if `_messageNonce` is not greater than `pausedMessageNonce`.
- Otherwise MUST set `paused` to `_paused` and `pausedMessageNonce` to `_messageNonce`, and emit `PausedSet`.

## Events

### LiquidityMinted

MUST be triggered when `mint` is called.

```solidity
event LiquidityMinted(address indexed caller, uint256 value);
```

### LiquidityBurned

MUST be triggered when `burn` is called.

```solidity
event LiquidityBurned(address indexed caller, uint256 value);
```

### PausedSet

MUST be triggered when `setPaused` applies an update.

```solidity
event PausedSet(bool paused, uint256 messageNonce);
```
