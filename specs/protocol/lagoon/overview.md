# Lagoon Network Upgrade

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Execution Layer](#execution-layer)
- [Consensus Layer](#consensus-layer)
- [Smart Contracts](#smart-contracts)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

This document is not finalized and should be considered experimental.

## Execution Layer

- [Post-Execution Transactions](./post-exec.md)
- [Sequencer-Defined Fees](../sdf.md)
- [Sequencer-Defined Metering](./sdm.md)

Lagoon activates the version-1 post-exec schema. Every non-genesis Lagoon block contains exactly one post-exec
transaction as its final transaction, including blocks with an empty SDM refund list. The payload commits the block's
`baseFeePerGas` selected under SDF and carries any SDM refunds. Before Lagoon, post-exec transactions are invalid
and the parent-derived EIP-1559 base-fee rules remain active.

Lagoon uses a single per-chain activation timestamp for SDF and SDM. Neither feature has a separate activation flag
or activation time.

- Interop:
  - [Transaction Pool](../../interop/tx-pool.md)

## Consensus Layer

Lagoon does not change singular batches, span batches, or Engine API payload-attribute schemas. The batcher includes
the trailing post-exec transaction in batch data, and derivation transports its EIP-2718 encoding through the
existing transaction list.

Validators recover the selected base fee and optional SDM refunds from the post-exec payload. They do not execute a
producer fee policy. Deterministic payload building follows the fallback specified in
[Sequencer-Defined Fees](../sdf.md#deterministic-payload-building) when derived Lagoon attributes do not contain a
post-exec transaction.

- Interop:
  - [Dependency Set](../../interop/dependency-set.md)
  - [Derivation](../../interop/derivation.md)
  - [Sequencer](../../interop/sequencer.md)
  - [Verifier](../../interop/verifier.md)
  - [Super Root](../../interop/superroot.md)
  - [Fault Proof](../../interop/fault-proof.md)

## Smart Contracts

- Interop:
  - [Messaging](../../interop/messaging.md)
  - [Predeploys](../../interop/predeploys.md)
  - [Token Bridging](../../interop/token-bridging.md)
  - [ETH Liquidity](../../interop/eth-liquidity.md)
  - [Superchain ETH Bridge](../../interop/superchain-eth-bridge.md)
  - [ETH Bridging](../../interop/eth-bridging.md)
  - [OptimismPortal](../../interop/optimism-portal.md)
  - [ETH Lockbox](../../interop/eth-lockbox.md)
