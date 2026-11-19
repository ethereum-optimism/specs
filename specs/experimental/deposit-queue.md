# Deposit Queue

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Constants](#constants)
- [Derivation Pipeline](#derivation-pipeline)
- [ResourceMetering](#resourcemetering)
- [OptimismPortal](#optimismportal)
- [SystemConfig](#systemconfig)
- [L1Attributes](#l1attributes)
- [Security Considerations](#security-considerations)
  - [Cheaper to Transact on L2 via L1](#cheaper-to-transact-on-l2-via-l1)
  - [Size of Deposit Queue](#size-of-deposit-queue)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The launch of Bedrock came with the deposit transaction feature. A deposit
transaction is a mapping of a particular event that is emitted on L1 into a
force include transaction that executes on layer two. When operating with
force inclusion transactions, denial of service attacks must be handled to
prevent attacks on the network. The denial of service handling is done through
an EIP-1559 curve that is maintained in the L1 `ResourceMetering` contract.
This means that expensive L1 computation is used for denial of service protection
of L2 execution, that simulations of deposits may not match actual execution due
to changes in on chain EIP-1559 parameters and the large possible state space
of the on chain EIP-1559 parameters makes the contract difficult to formally
verify.

Any "force inclusion" transaction should handle denial of service attacks
through an inclusion queue.

## Constants

| Name | Value | Description |
|----------|----------|------|
| `QUEUE_CHUNK_SIZE` | `20_000_000` | Maximum amount of L2 gas that can be used by deposits in any L2 block |
| `MAX_DEPOSIT_GAS` | `QUEUE_CHUNK_SIZE` | Maximum amount of gas that a deposit transaction can consume |
| `MAX_CHUNKS` | `64` | Maximum number of pending chunks |
| `DEPOSIT_VERSION` | `1` | Version emitted in deposit event |
| `DEPOSIT_COST` | `30_000 + len(calldata)` | Standard amount of gas charged per deposit (configurable) |

## Derivation Pipeline

A queue for deposits is introduced into the derivation pipeline. This queue is broken up into `CHUNKS` that are
made up of `QUEUE_CHUNK_SIZE` amounts of L2 gas. With Bedrock, all deposits are included when the L1 origin updates,
meaning that the `sequenceNumber` is `0`. With deposit queue, each L2 block consumes a single `CHUNK` of the queue.
This means that any L2 block can contain deposits instead of just on L1 origin updates.

## ResourceMetering

The `ResourceMetering` contract is updated to track the size of the queue. As deposits are processed, the number
of `CHUNKS` are updated based on the amount of gas that the deposits consume. If a deposit overflows a `CHUNK`,
it is placed into the next `CHUNK`. Each `CHUNK` has a maximum amount of `QUEUE_CHUNK_SIZE` gas. This implies
that a single deposit cannot consume more than a single `CHUNK`.

The `ResourceMetering` contract can track the last `BLOCKNUMBER` that it was called in storage and compare that
against the current `BLOCKNUMBER` to know how many `CHUNKS` have been consumed. To prevent the queue from growing
too large, there can only ever be `MAX_CHUNKS` in the queue. Deposits MUST revert on L1 if the queue grows too large.

Instead of charging variable amounts based on an EIP-1559 curve like in the Bedrock release, a standard
`DEPOSIT_COST` amount of gas is burnt per deposit. In the future, it should be possible to instead pay
in `ether` instead of burning gas.

The `DEPOSIT_COST` is defined as the sum of a flat cost and the amount of calldata. This incentivizes smaller
amounts of calldata being sent to L2.

## OptimismPortal

The `DEPOSIT_VERSION` is updated to signal usage of the deposit queue.

## SystemConfig

The `SystemConfig` contract is updated to hold the flat portion of the `DEPOSIT_COST`. This allows for
configuration in the case of the system consistently undercharging for L2 gas via deposit transactions.

## L1Attributes

To allow for statelessness of the `op-node`, the L1Attributes transaction is updated to include a pointer
to the last deposit that was ingested. This pointer can be a `logIndex`. Combined with the L1 block number
that is already included in the L1Attributes transaction, these 2 fields together can be used to uniquely
identify the last ingested deposit so that the queue can be rebuilt statelessly by doing reads from the
`L1Block` predeploy contract.

## Security Considerations

### Cheaper to Transact on L2 via L1

One design goal of deposit queue is to have a consistent amount of gas used for deposits no matter when the
deposit transaction is included. Since L1 has no concept of the L2 `BASEFEE`, it may become possible that
it is cheaper to transact on L2 via L1. This would in theory cause users to start depositing via L1 to L2
until the L1 `BASEFEE` rises to a point where it is cheaper to instead transact by sending transactions
directly to the sequencer. If users are consistently paying less than what they should be for L2 gas via
deposits, then the `DEPOSIT_COST` can be made configurable via the `SystemConfig` L1 smart contract.

### Size of Deposit Queue

The deposit queue can only grow to being `MAX_CHUNKS` size. Keeping all of that data in memory should not
impact the performance of the derivation pipeline. Therefore additional cost is paid based on the size of
the calldata being sent to L2.
