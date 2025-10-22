# L1FeeVault

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
  - [Minimum Withdrawal Amount](#minimum-withdrawal-amount)
  - [Withdrawal Network](#withdrawal-network)
- [Assumptions](#assumptions)
  - [a01-001: Recipient address is valid and can receive ETH](#a01-001-recipient-address-is-valid-and-can-receive-eth)
    - [Mitigations](#mitigations)
  - [a01-002: L2ToL1MessagePasser functions correctly for L1 withdrawals](#a01-002-l2tol1messagepasser-functions-correctly-for-l1-withdrawals)
    - [Mitigations](#mitigations-1)
  - [a01-003: Protocol correctly credits L1 fees to this contract](#a01-003-protocol-correctly-credits-l1-fees-to-this-contract)
    - [Mitigations](#mitigations-2)
- [Dependencies](#dependencies)
- [Invariants](#invariants)
  - [i01-001: Accumulated fees can always be withdrawn once threshold is met](#i01-001-accumulated-fees-can-always-be-withdrawn-once-threshold-is-met)
    - [Impact](#impact)
  - [i01-002: Total processed amount never decreases](#i01-002-total-processed-amount-never-decreases)
    - [Impact](#impact-1)
  - [i01-003: Withdrawals always transfer the entire balance](#i01-003-withdrawals-always-transfer-the-entire-balance)
    - [Impact](#impact-2)
  - [i01-004: Configuration parameters are immutable after deployment](#i01-004-configuration-parameters-are-immutable-after-deployment)
    - [Impact](#impact-3)
  - [i01-005: Only authorized withdrawals succeed](#i01-005-only-authorized-withdrawals-succeed)
    - [Impact](#impact-4)
- [Function Specification](#function-specification)
  - [constructor](#constructor)
  - [receive](#receive)
  - [minWithdrawalAmount](#minwithdrawalamount)
  - [recipient](#recipient)
  - [withdrawalNetwork](#withdrawalnetwork)
  - [withdraw](#withdraw)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The L1FeeVault accumulates the L1 portion of transaction fees paid by users on the L2 network. These fees
represent the cost of posting transaction data to L1 for data availability. The contract enables permissionless
withdrawal of accumulated fees to a designated recipient address once a minimum threshold is reached.

## Definitions

### Minimum Withdrawal Amount

The minimum balance of ETH that must accumulate in the vault before a withdrawal can be triggered. This threshold
prevents excessive withdrawal transactions for small fee amounts.

### Withdrawal Network

The destination network where withdrawn fees are sent. Can be either L1 (cross-domain withdrawal via message
passing) or L2 (direct transfer on the same chain).

## Assumptions

### a01-001: Recipient address is valid and can receive ETH

The recipient address configured at deployment must be capable of receiving ETH on the specified withdrawal
network. For L1 recipients, the address must be able to receive ETH from the OptimismPortal. For L2 recipients,
the address must not be a contract that reverts on ETH receipt.

#### Mitigations

- Deployment configuration should validate recipient addresses before deployment
- Recipient addresses should be tested with small transfers before production use

### a01-002: L2ToL1MessagePasser functions correctly for L1 withdrawals

When the withdrawal network is L1, the contract depends on the L2ToL1MessagePasser predeploy to correctly
initiate cross-domain withdrawals. The message passer must properly record withdrawal commitments and the L1
OptimismPortal must honor these commitments.

#### Mitigations

- L2ToL1MessagePasser is a core protocol predeploy with extensive testing and auditing
- Withdrawal proofs are validated on L1 through the fault proof system

### a01-003: Protocol correctly credits L1 fees to this contract

The execution engine must correctly calculate L1 data availability fees and credit them to the L1FeeVault
address. Incorrect fee calculation or routing would prevent the vault from accumulating the intended fees.

#### Mitigations

- Fee calculation is part of the core protocol specification
- Fee routing is handled by the execution engine's coinbase mechanism

## Dependencies

This specification depends on:

- [L2ToL1MessagePasser](../../../protocol/predeploys.md#l2tol1messagepasser): Used for initiating withdrawals to
  L1
- [OptimismPortal](../../../fault-proof/stage-one/optimism-portal.md): Finalizes L1 withdrawals on the destination
  chain

## Invariants

### i01-001: Accumulated fees can always be withdrawn once threshold is met

Once the contract balance reaches or exceeds the [Minimum Withdrawal Amount](#minimum-withdrawal-amount), any
address can successfully trigger a withdrawal. The contract must never enter a state where fees are trapped.

#### Impact

**Severity: High**

If withdrawals become impossible, accumulated L1 fees would be permanently locked in the contract, preventing the
designated recipient from receiving funds that are rightfully theirs. This would break the fee distribution
mechanism of the protocol.

### i01-002: Total processed amount never decreases

The `totalProcessed` counter must be monotonically increasing. Each withdrawal adds the withdrawn amount to this
counter, providing an immutable record of all fees ever withdrawn from the vault.

#### Impact

**Severity: Low**

If `totalProcessed` could decrease, it would compromise the accounting integrity of the fee system, making it
impossible to accurately track historical fee withdrawals. However, this does not directly impact fund security.

### i01-003: Withdrawals always transfer the entire balance

When a withdrawal is triggered, the complete balance of the contract at that moment must be transferred to the
recipient. No fees should remain in the contract after a successful withdrawal.

#### Impact

**Severity: Medium**

If partial withdrawals were possible or fees remained after withdrawal, it could lead to accounting discrepancies
and require additional withdrawal transactions, increasing operational costs and complexity.

### i01-004: Configuration parameters are immutable after deployment

The recipient address, minimum withdrawal amount, and withdrawal network must remain constant throughout the
contract's lifetime. These parameters cannot be modified after deployment.

#### Impact

**Severity: High**

If configuration could be changed, an attacker gaining control could redirect fees to their own address or prevent
legitimate withdrawals by setting an impossibly high minimum. Immutability ensures predictable behavior.

### i01-005: Only authorized withdrawals succeed

Withdrawals to L1 must only succeed through the proper L2ToL1MessagePasser mechanism with the configured minimum
gas limit. Direct transfers or alternative withdrawal paths must not be possible.

#### Impact

**Severity: Critical**

If unauthorized withdrawal mechanisms existed, attackers could bypass the fault proof system and steal accumulated
fees without proper validation on L1. The L2ToL1MessagePasser provides the security guarantees for cross-domain
transfers.

## Function Specification

### constructor

Initializes the L1FeeVault with immutable configuration parameters.

**Parameters:**

- `_recipient`: Address that will receive withdrawn fees (on L1 or L2 depending on `_withdrawalNetwork`)
- `_minWithdrawalAmount`: Minimum balance in wei required before withdrawal can be triggered
- `_withdrawalNetwork`: Enum value indicating whether withdrawals go to L1 or L2

**Behavior:**

- MUST set `RECIPIENT` to `_recipient`
- MUST set `MIN_WITHDRAWAL_AMOUNT` to `_minWithdrawalAmount`
- MUST set `WITHDRAWAL_NETWORK` to `_withdrawalNetwork`
- MUST initialize `totalProcessed` to 0

### receive

Allows the contract to accept ETH transfers representing L1 fee payments.

**Behavior:**

- MUST accept any amount of ETH from any sender
- MUST NOT revert under any circumstances

### minWithdrawalAmount

Returns the minimum balance required before withdrawal can be triggered.

**Behavior:**

- MUST return the value of `MIN_WITHDRAWAL_AMOUNT`

### recipient

Returns the address that will receive withdrawn fees.

**Behavior:**

- MUST return the value of `RECIPIENT`

### withdrawalNetwork

Returns the network where withdrawn fees will be sent.

**Behavior:**

- MUST return the value of `WITHDRAWAL_NETWORK`

### withdraw

Triggers withdrawal of all accumulated fees to the configured recipient.

**Behavior:**

- MUST revert if `address(this).balance < MIN_WITHDRAWAL_AMOUNT`
- MUST capture the current balance in a local variable
- MUST increment `totalProcessed` by the withdrawal amount
- MUST emit `Withdrawal(value, RECIPIENT, msg.sender)` event (legacy format)
- MUST emit `Withdrawal(value, RECIPIENT, msg.sender, WITHDRAWAL_NETWORK)` event (current format)
- If `WITHDRAWAL_NETWORK == Types.WithdrawalNetwork.L2`:
  - MUST call `SafeCall.send(RECIPIENT, value)` to transfer ETH on L2
  - MUST revert if the transfer fails
- If `WITHDRAWAL_NETWORK == Types.WithdrawalNetwork.L1`:
  - MUST call `L2ToL1MessagePasser.initiateWithdrawal` with:
    - `_target`: `RECIPIENT`
    - `_gasLimit`: `WITHDRAWAL_MIN_GAS` (400,000)
    - `_data`: empty bytes (`hex""`)
    - `value`: entire contract balance
  - MUST forward the entire balance as msg.value to the message passer
