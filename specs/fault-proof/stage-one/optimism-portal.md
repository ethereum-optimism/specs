# Optimism Portal

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

**Table of Contents**

- [Optimism Portal](#optimism-portal)
  - [Overview](#overview)
    - [Perspective](#perspective)
    - [Contract Dependencies](#contract-dependencies)
      - [AnchorStateRegistry](#anchorstateregistry)
      - [SuperchainConfig](#superchainconfig)
    - [Contract Dependents](#contract-dependents)
  - [Definitions](#definitions)
  - [Top-Level Invariants](#top-level-invariants)
- [Function-Level Invariants](#function-level-invariants)
  - [`initialize`](#initialize)
  - [`proveWithdrawalTransaction`](#provewithdrawaltransaction)
  - [`finalizeWithdrawalTransaction`](#finalizewithdrawaltransaction)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

### Perspective

This contract is responsible for moderating [withdrawals](../../protocol/withdrawals.md).

### Contract Dependencies

#### AnchorStateRegistry

Depends on AnchorStateRegistry to correctly report:

- Whether a game is an **invalid game**.
- Whether a game is a **valid game**.

#### SuperchainConfig

Depends on SuperchainConfig to correctly report:

- System pause status.
- Guardian address.

### Contract Dependents

TODO

## Definitions

- **Authorized input**
  - An input for which there is social consensus, i.e. coming from governance.
- **Proven withdrawal**
- **Finalized withdrawal**

## Top-Level Invariants

- A withdrawal transaction must be **proven** against a game that is not `invalid`.
- A withdrawal transaction may only be finalized against a game that is `valid`.
  - Implicit in this is that a withdrawal transaction may only be finalized after the proof maturity delay has passed.
- A withdrawal transaction may only be finalized if it has already been **proven**.
- A withdrawal transaction must be used only once to finalize a withdrawal.
- A withdrawal transaction that is finalized must attempt execution.

# Function-Level Invariants

## `initialize`

- Proof maturity delay seconds must be an **authorized input**.
- Anchor state registry must be an **authorized input**.
- Dispute game factory must be an **authorized input**.
- Superchain config must be an **authorized input**.
- System config must be an **authorized input**.

## `proveWithdrawalTransaction`

Proves a withdrawal transaction.

- Withdrawal game must not be an **invalid game**.
- Withdrawal transaction's target must not be the OptimismPortal address.
- Withdrawal game's root claim must be equal to the hashed outputRootProof input.
- Must verify that the hash of this withdrawal is stored in the L2toL1MessagePasser contract on L2.
- A withdrawal can only be proven once unless the dispute game it proved against resolves against the favor of the root
  claim.
- Must add proof submitter to the list of proof submitters for this withdrawal hash.

## `finalizeWithdrawalTransaction`

Finalizes a withdrawal transaction that has already been proven.

- Withdrawal transaction must have already been proven.
- The proof maturity delay duration must have elapsed between the time the withdrawal was proven and this call for its
  finalization.
- The time the withdrawal was proven must be greater than the time at which the withdrawal's game was created.
- Withdrawal transaction must not have been finalized before.
- The game upon which the withdrawal proof is based must be a **valid game**.
- Function must register the withdrawal as finalized.
- Function must revert when system is paused.
- TODO: withdrawal tx invariants (can't call token contract, exact balance must be transferred, estimator should revert
  for gas estimation)
- If these invariants are met, function must attempt execution of the withdrawal transaction.
