# Optimism Portal

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

  - [Overview](#overview)
    - [Perspective](#perspective)
  - [Definitions](#definitions)
    - [Authorized input](#authorized-input)
    - [Proven withdrawal](#proven-withdrawal)
    - [Finalized withdrawal](#finalized-withdrawal)
    - [Proof maturity delay](#proof-maturity-delay)
  - [Assumptions](#assumptions)
    - [aASR-001: AnchorStateRegistry correctly distinguishes maybe valid games](#aasr-001-anchorstateregistry-correctly-distinguishes-maybe-valid-games)
      - [Impact](#impact)
      - [Mitigations](#mitigations)
    - [aASR-002: AnchorStateRegistry correctly distinguishes valid games](#aasr-002-anchorstateregistry-correctly-distinguishes-valid-games)
      - [Impact](#impact-1)
      - [Mitigations](#mitigations-1)
    - [aSC-001: SuperchainConfig correctly reports system pause status](#asc-001-superchainconfig-correctly-reports-system-pause-status)
      - [Impact](#impact-2)
      - [Mitigations](#mitigations-2)
  - [Top-Level Invariants](#top-level-invariants)
- [Function-Level Invariants](#function-level-invariants)
  - [`initialize`](#initialize)
  - [`proveWithdrawalTransaction`](#provewithdrawaltransaction)
  - [`finalizeWithdrawalTransaction`](#finalizewithdrawaltransaction)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

### Perspective

The whole point of the fault proof system is to create correctly resolving games whose claims we can depend on to
finalize withdrawals (or other L2-to-L1 dependents). This contract is responsible for moderating L2-to-L1
[withdrawals](../../protocol/withdrawals.md). Because of the probabilistic validity of games as discussed in
[AnchorStateRegistry](./anchor-state-registry.md), we can't immediately finalize withdrawals. Instead, we must wait for
both a [dispute game finality delay](./anchor-state-registry.md#dispute-game-finality-delay) and a **proof maturity
delay** to pass before we can finalize a withdrawal. Meanwhile, our assumptions about the fault proof system do work
such that by the time the withdrawal is finalized, we're confident the withdrawal is correct.

## Definitions

### Authorized input

An input for which there is social consensus, i.e. coming from governance.

### Proven withdrawal

A **proven withdrawal** is a withdrawal that is maybe valid, because it's been proven using a **maybe valid game**.
However, because we don't have full confidence in the game's validity, we can't yet finalize the withdrawal.

### Finalized withdrawal

A **finalized withdrawal** is a withdrawal transaction that has been proven against a game that we now know is
**valid**, and has waited the **proof maturity delay**.

### Proof maturity delay

The **proof maturity delay** is time that must elapse between a withdrawal being proven and it being finalized.

## Assumptions

### aASR-001: AnchorStateRegistry correctly distinguishes maybe valid games

We assume that the AnchorStateRegistry correctly reports whether a game is a [**maybe valid
game**](./anchor-state-registry.md#maybe-valid-game).

#### Impact

**Severity: Medium**

If a game is reported as maybe valid when it is not, an attacker can prove a withdrawal that is invalid. If
[aASR-002](#aasr-002-anchorstateregistry-correctly-distinguishes-valid-games) holds, this may not result in severe
consequences, but would negatively impact system hygiene.

#### Mitigations

- Pending audit of `AnchorStateRegistry`
- Integration testing

### aASR-002: AnchorStateRegistry correctly distinguishes valid games

We assume that the AnchorStateRegistry correctly reports whether a game is a [**valid
game**](./anchor-state-registry.md#valid-game).

#### Impact

**Severity: Critical**

If a game is reported as valid when it is not, we may finalize a withdrawal that is invalid. This would result to a loss
of funds and a loss of confidence in the system.

#### Mitigations

- Pending audit of `AnchorStateRegistry`
- Integration testing

### aSC-001: SuperchainConfig correctly reports system pause status

We assume SuperchainConfig correctly returns system pause status.

#### Impact

**Severity: Critical**

If SuperchainConfig incorrectly reports system pause status, we may prove / finalize a withdrawal when the system is
paused. This would create bad system hygiene, and could lead to a loss of funds or a loss of confidence in the system.

#### Mitigations

- Existing audit of `SuperchainConfig`

## Top-Level Invariants

- A withdrawal transaction must be **proven** against a game that is **maybe valid**.
- A withdrawal transaction may only be **finalized** against a game that is **valid**.
  - Implicit in this is that a withdrawal transaction may only be **finalized** after the **proof maturity delay** has
    passed.
- A withdrawal transaction may only be **finalized** if it has already been **proven**.
- A withdrawal transaction must be used only once to **finalize** a withdrawal.
- A withdrawal transaction that is **finalized** must attempt execution.

# Function-Level Invariants

## `initialize`

- Proof maturity delay seconds must be an **authorized input**.
- Anchor state registry must be an **authorized input**.
- Dispute game factory must be an **authorized input**.
- Superchain config must be an **authorized input**.
- System config must be an **authorized input**.

## `proveWithdrawalTransaction`

Proves a withdrawal transaction.

- Withdrawal game must be a [**maybe valid game**](./anchor-state-registry.md#maybe-valid-game).
- Withdrawal transaction's target must not be the `OptimismPortal` address.
- Withdrawal game's root claim must be equal to the hashed `outputRootProof` input.
- Must verify that the hash of this withdrawal is stored in the `L2toL1MessagePasser` contract on L2.
- A withdrawal cannot be reproved by the same proof submitter unless both of the following are true:
  - the dispute game previously used to prove the withdrawal is now an [**invalid
    game**](./anchor-state-registry.md#invalid-game).
  - the withdrawal was never finalized.
- System must not be paused.

## `finalizeWithdrawalTransaction`

Finalizes a withdrawal transaction that has already been proven.

- Withdrawal transaction must have already been proven.
- The proof maturity delay duration must have elapsed between the time the withdrawal was proven and this call for its
  finalization.
- The time the withdrawal was proven must be greater or equal to the time at which the withdrawal's game was created.
- Withdrawal transaction must not have been finalized before.
- The game upon which the withdrawal proof is based must be a [**valid game**](./anchor-state-registry.md#valid-game).
- Function must revert when system is paused.
- If the gas-paying token is not ether:
  - Withdrawal transaction's target must not be the OP token address.
  - If the withdrawal transaction transfers value:
    - The call to `transfer` must revert on fail.
    - The input amount must equal the balance delta of this contract after transfer.
- System must not be paused.
- If these invariants are met, function must attempt execution of the withdrawal transaction.
- If the transaction wasn't successful and the `tx.origin` is the `ESTIMATION_ADDRESS`, revert with `GasEstimation()`.
