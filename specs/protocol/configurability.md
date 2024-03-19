# OP Stack Configurability

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

**Table of Contents**

- [Standard OP Stack Configuration](#standard-op-stack-configuration)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

When deploying the OP Stack software to a production environment,
certain parameters about the protocol can be configured. These
configurations can include a variety of parameters which affect the
resulting properties of the blockspace in question.

There are three categories of OP Stack configuration options:

- **Protocol Parameters**: Parameters and properties of the chain that may
  be set at genesis and fixed for the lifetime of the chain, or may be
  changeable through a privileged account.
- **Admin Roles**: These roles can upgrade contracts, change role owners,
  or update protocol parameters. These are typically cold/multisig wallets not
  used directly in day to day operations.
- **Service Roles**: These roles are used to manage the day-to-day
  operations of the chain, and therefore are often hot wallets.

## Protocol Parameters

| Config Property                       | Description                                                                                                                  |
|---------------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| Batch Inbox address                   | L1 address where calldata/blobs are posted (see [Batcher Transaction](../glossary.md#batcher-transaction)).                         |
| Batch submission frequency            | Frequency with which batches are submitted to L1 (see [Batcher Transaction](../glossary.md#batcher-transaction)).            |
| Chain ID                              | Unique ID of Chain used for TX signature validation.                                                                         |
| Challenge Period                      | Length of time for which an output root can be removed, and for which it is not considered finalized.                                                                                                                                                             |
| Compression ratio                     | How much compression the batch submitter applies to batches before submission (see [Channel](../glossary.md#channel)).       |
| Data Availability                     | Where L2 transaction calldata is posted.                                                                                     |
| Fault Proof Window / Challenge Window | Duration network participants have to challenge the integrity of an output root.                                             |
| Fee margin                            | Markup on transactions compared to the raw L1 data cost.                                                                     |
| Fee vault contracts                   | Contracts which dictate how user fees are distributed.                                                                       |
| Gas limit                             | L2 block gas limit.                                                                                                          |
| Gas Token                             | Native token used to pay for gas.                                                                                            |
| Genesis state                         | Initial state at chain genesis, including code and storage of predeploys (all L2 smart contracts). See [Predeploy](../glossary.md#l2-genesis-block).                                            |
| L1 smart contracts                    | The chain’s L1 smart contracts.                                                                                              |
| L2 block time                         | Frequency with which blocks are produced as a result of derivation.                                                          |
| Output frequency                      | Frequency with which output roots are submitted to L1.                                                                       |
| Resource config                       | Config for the EIP-1559 based curve used for the deposit gas market.                                                         |
| Sequencing window                     | Maximum allowed batch submission frequency, after which L1 fallback is triggered in derivation.                                                                                                                                                            |
| Start block                           | Block at which op-node starts searching for logs from.                                                                       |

## Admin Roles

| Config Property                       | Description                                                                                                                  |
|---------------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| L1 Proxy Admin                        | Account authorized to upgrade L1 contracts.                                                                                  |
| L1 ProxyAdmin owner                   | Account authorized to update the L1 Proxy Admin.                                                                             |
| L2 Proxy Admin                        | Account authorized to upgrade L2 contracts.                                                                                  |
| L2 ProxyAdmin owner                   | Account authorized to update the L2 Proxy Admin.                                                                             |
| MintManager owner                     | Account which controls the MintManager to mint OP tokens.                                                                    |
| System Config Owner                   | Account authorized to change values in the SystemConfig contract.                                                            |

## Service Roles

| Config Property                       | Description                                                                                                                  |
|---------------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| Batch submitter address               | Account which authenticates new batches submitted to L1 Ethereum.                                                            |
| Challenger address                    | Account which can delete output roots before challenge period has elapsed.                                                   |
| Guardian address                      | Account authorized to pause L1 withdrawals from contracts.                                                                   |
| Proposer address                      | Account which can propose output roots to L1.                                                                                |
| Sequencer P2P / Unsafe head signer    | Account which authenticates the unsafe/pre-submitted blocks for a chain at the P2P layer.                                    |
