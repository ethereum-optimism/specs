# SuperchainETHBridge

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Constants](#constants)
- [Definitions](#definitions)
  - [ETH Bridging](#eth-bridging)
  - [ETH Liquidity](#eth-liquidity)
  - [Cross-Chain Message](#cross-chain-message)
  - [Source Chain](#source-chain)
  - [Destination Chain](#destination-chain)
- [Assumptions](#assumptions)
  - [aSEB-001: L2ToL2CrossDomainMessenger properly delivers messages](#aseb-001-l2tol2crossdomainmessenger-properly-delivers-messages)
    - [Mitigations](#mitigations)
  - [aSEB-002: `ETHLiquidity` contract maintains sufficient liquidity](#aseb-002-ethliquidity-contract-maintains-sufficient-liquidity)
    - [Mitigations](#mitigations-1)
  - [aSEB-003: `SafeSend` correctly transfers ETH to recipients](#aseb-003-safesend-correctly-transfers-eth-to-recipients)
    - [Mitigations](#mitigations-2)
  - [aSEB-004: `expiredMessages` only marks messages that can never be relayed](#aseb-004-expiredmessages-only-marks-messages-that-can-never-be-relayed)
    - [Mitigations](#mitigations-3)
- [Invariants](#invariants)
  - [iSEB-001: ETH sent equals ETH received](#iseb-001-eth-sent-equals-eth-received)
    - [Impact](#impact)
    - [Dependencies](#dependencies)
  - [iSEB-002: Only authorized contracts can call `relayETH`](#iseb-002-only-authorized-contracts-can-call-relayeth)
    - [Impact](#impact-1)
    - [Dependencies](#dependencies-1)
  - [iSEB-003: ETH cannot be sent to the zero address](#iseb-003-eth-cannot-be-sent-to-the-zero-address)
    - [Impact](#impact-2)
    - [Dependencies](#dependencies-2)
  - [iSEB-004: ETH is refunded only for expired sends, at most once](#iseb-004-eth-is-refunded-only-for-expired-sends-at-most-once)
    - [Impact](#impact-3)
    - [Dependencies](#dependencies-3)
- [Function Specification](#function-specification)
  - [sendETH](#sendeth)
  - [relayETH](#relayeth)
  - [refundETH](#refundeth)
- [Events](#events)
  - [SendETH](#sendeth)
  - [RelayETH](#relayeth)
  - [RefundETH](#refundeth)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The `SuperchainETHBridge` is a predeploy contract that facilitates cross-chain ETH bridging within
the Superchain interop set. It serves as an abstraction layer on top of the
`L2toL2CrossDomainMessenger` specifically designed for native ETH transfers between chains. The
contract integrates with the `ETHLiquidity` contract to manage native ETH liquidity across chains,
ensuring seamless cross-chain transfers of native ETH.

The `SuperchainETHBridge` only handles native ETH cross-chain transfers. For interoperable ETH
withdrawals, see the [`ETHLockbox`](./eth-lockbox.md) specification.

## Constants

| Name                          | Value                                        |
| ----------------------------- | -------------------------------------------- |
| `SuperchainETHBridge` Address | `0x4200000000000000000000000000000000000024` |

## Definitions

### ETH Bridging

ETH Bridging refers to the process of transferring native ETH from one chain to another within the
Superchain interop set. This process involves burning ETH on the source chain and minting an
equivalent amount on the destination chain.

### ETH Liquidity

ETH Liquidity refers to the availability of native ETH on a particular chain. The `ETHLiquidity`
contract manages this liquidity by providing a mechanism to burn and mint ETH as needed for
cross-chain transfers.

### Cross-Chain Message

A Cross-Chain Message is a message sent from one chain to another using the
`L2ToL2CrossDomainMessenger`. In the context of the `SuperchainETHBridge`, these messages contain
instructions to relay ETH to a recipient on the destination chain.

### Source Chain

The Source Chain is the chain from which a user initiates an ETH transfer. On this chain, ETH is
burned from the user's account and a cross-chain message is sent to the destination chain.

### Destination Chain

The Destination Chain is the chain to which ETH is being transferred. On this chain, ETH is sent
to the recipient's account based on the cross-chain message received from the source chain.

## Assumptions

### aSEB-001: L2ToL2CrossDomainMessenger properly delivers messages

We assume that the `L2ToL2CrossDomainMessenger` contract properly and faithfully delivers messages
between chains, maintaining the integrity and authenticity of the message contents.

#### Mitigations

- Extensive testing of the `L2ToL2CrossDomainMessenger` contract
- Audits of the messaging protocol
- Monitoring of cross-chain message delivery

### aSEB-002: `ETHLiquidity` contract maintains sufficient liquidity

We assume that the `ETHLiquidity` contract maintains sufficient liquidity to fulfill all valid ETH
minting requests. This is ensured by initializing the contract with `type(uint248).max` wei.

#### Mitigations

- Total ETH supply is much less than the initial balance of the `ETHLiquidity` contract
- Contract is initially initialized with `type(uint248).max` wei and can hold up to
`type(uint256).max` wei to prevent balance overflow

### aSEB-003: `SafeSend` correctly transfers ETH to recipients

We assume that the `SafeSend` mechanism correctly transfers ETH to recipients without reverting
for valid addresses.

#### Mitigations

- Extensive testing of the `SafeSend` mechanism
- Audits of the ETH transfer logic

### aSEB-004: `expiredMessages` only marks messages that can never be relayed

We assume that `L2ToL2CrossDomainMessenger.expiredMessages(messageHash)` is `true` only for a message sent from
this chain that its destination chain has not relayed and can never relay, as specified in
[Message Expiry](./message-expiry.md).

#### Mitigations

- The expiry check compares the destination's timestamp with the send timestamp plus `EXPIRY_PERIOD`, which is at
  least the protocol's [expiry window](./derivation.md#expiry-window)
- Only the chain's own `L1CrossDomainMessenger` can deliver an expiry, and only on behalf of the destination chain's
  `UndeliveredMessageExporter`

## Invariants

### iSEB-001: ETH sent equals ETH received

The amount of ETH sent from the source chain must equal the amount of ETH received on the
destination chain for any given cross-chain transfer.

#### Impact

**Severity: Critical**

If this invariant is broken, users could receive more or less ETH than they sent, leading to
inflation or loss of funds.

#### Dependencies

- [aSEB-001](#aseb-001-l2tol2crossdomainmessenger-properly-delivers-messages)
- [aSEB-002](#aseb-002-ethliquidity-contract-maintains-sufficient-liquidity)

### iSEB-002: Only authorized contracts can call `relayETH`

The `relayETH` function must only be callable by the `L2ToL2CrossDomainMessenger` contract, and the
cross-domain sender must be the `SuperchainETHBridge` contract on the source chain.

#### Impact

**Severity: Critical**

If this invariant is broken, unauthorized parties could mint ETH on the destination chain without
burning an equivalent amount on the source chain, leading to inflation.

#### Dependencies

- [aSEB-001](#aseb-001-l2tol2crossdomainmessenger-properly-delivers-messages)

### iSEB-003: ETH cannot be sent to the zero address

The `sendETH` function must revert if the recipient address is the zero address.

#### Impact

**Severity: High**

If this invariant is broken, ETH could be sent to the zero address, effectively burning it without
the possibility of recovery.

#### Dependencies

None

### iSEB-004: ETH is refunded only for expired sends, at most once

`refundETH` must pay out only for a send whose message is marked expired, at most once per message, and only the
amount and recipient that the send's message committed to.

#### Impact

**Severity: Critical**

If this invariant is broken, ETH could be both delivered on the destination chain and refunded on the source chain,
leading to inflation.

#### Dependencies

- [aSEB-002](#aseb-002-ethliquidity-contract-maintains-sufficient-liquidity)
- [aSEB-004](#aseb-004-expiredmessages-only-marks-messages-that-can-never-be-relayed)

## Function Specification

### sendETH

Deposits the `msg.value` of ETH into the `ETHLiquidity` contract and sends a cross-chain message
to the specified `_chainId` to call `relayETH` with the `_to` address as the recipient and the
`msg.value` as the amount.

```solidity
function sendETH(address _to, uint256 _chainId) external payable returns (bytes32 msgHash_);
```

- MUST accept ETH via `msg.value`.
- MUST revert if the `_to` address is the zero address.
- MUST transfer `msg.value` of ETH from the `msg.sender` to the `ETHLiquidity` contract by calling
`ETHLiquidity.burn{value: msg.value}()`.
- MUST create a cross-chain message to the `SuperchainETHBridge` contract on the destination chain
with the following parameters:
  - `_chainId`: The destination chain ID.
  - `message`: An encoded call to `relayETH(msg.sender, _to, msg.value)`.
- MUST return the message hash `msgHash_` generated by the `L2ToL2CrossDomainMessenger`.
- MUST emit a `SendETH` event with the `msg.sender`, `_to`, `msg.value`, and `_chainId`.

### relayETH

Withdraws ETH from the `ETHLiquidity` contract equal to the `_amount` and sends it to the `_to` address.

```solidity
function relayETH(address _from, address _to, uint256 _amount) external;
```

- MUST revert if called by any address other than the `L2ToL2CrossDomainMessenger`.
- MUST revert if the cross-domain sender is not the `SuperchainETHBridge` contract on the source
chain.
- MUST withdraw `_amount` of ETH from the `ETHLiquidity` contract by calling
`ETHLiquidity.mint(_amount)`.
- MUST transfer the `_amount` of ETH to the `_to` address using
`new SafeSend{value: _amount}(_to)`.
- MUST emit a `RelayETH` event with the `_from` address, `_to` address, `_amount`, and source chain
ID.

### refundETH

Returns the ETH of a send whose message expired: its destination chain never relayed it, and never can.

```solidity
function refundETH(uint256 _destination, uint256 _nonce, address _from, address _to, uint256 _amount) external;
```

- MUST compute the message hash of the send from its arguments, with this chain as the source and the
  `SuperchainETHBridge` as both sender and target of a `relayETH(_from, _to, _amount)` call.
- MUST revert if `L2ToL2CrossDomainMessenger.expiredMessages(messageHash)` is `false`.
- MUST revert if the send was already refunded.
- MUST record the refund before transferring ETH.
- MUST withdraw `_amount` of ETH from the `ETHLiquidity` contract by calling `ETHLiquidity.mint(_amount)`.
- MUST transfer the `_amount` of ETH to the `_from` address using `new SafeSend{value: _amount}(_from)`.
- MUST be callable by anyone.
- MUST emit a `RefundETH` event with the `_from` address, `_amount`, and the message hash.

The refund always goes to `_from`, the `msg.sender` of `sendETH`. A contract that called `sendETH` on behalf of
someone else needs its own way to pass a refund on.

## Events

### SendETH

MUST be triggered when `sendETH` is called.

```solidity
event SendETH(address indexed from, address indexed to, uint256 amount, uint256 destination);
```

### RelayETH

MUST be triggered when `relayETH` is called.

```solidity
event RelayETH(address indexed from, address indexed to, uint256 amount, uint256 source);
```

### RefundETH

MUST be triggered when `refundETH` is called.

```solidity
event RefundETH(address indexed from, uint256 amount, bytes32 indexed messageHash);
```
