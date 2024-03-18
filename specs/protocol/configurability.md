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

- Protocol Parameters: Parameters and properties of the chain that may
  be set at genesis and fixed for the lifetime of the chain, or may be
  changeable through a privileged account.
- Admin Roles: These roles can upgrade contracts, change role owners,
  or update protocol parameters. These are typically cold wallets not
  used directly in day to day operations.
- Service Roles: These roles are used to manage the day-to-day
  operations of the chain, and therefore are often hot wallets.

## Protocol Parameters

| Config Property                       | Description                                                                                                                  |
|---------------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| Sequencer Inbox Address               | L1 address where calldata is posted (see [Batcher Transaction](../glossary.md#batcher-transaction)).                         |
| Batch submission frequency            | Frequency with which batches are submitted to L1                                                                             |
| ChainID                               | Unique ID of Chain used for TX signature validation                                                                          |
| Challenge period                      | "Length of time for which an output root can be removed, and for which it is not considered finalized"                       |
| Compression ratio                     | How much compression the batch submitter applies to batches before submission                                                |
| Data Availability                     | Where L2 transaction calldata is posted                                                                                      |
| Fault Proof Window / Challenge Window | Duration network participants have to challenge the integrity of an output root                                              |
| Fee Vault contracts                   | Contracts which dictate how user fees are distributed                                                                        |
| Fee margin                            | Markup on transactions compared to the raw L1 data cost                                                                      |
| Gas Limit                             | L2 block gas limit                                                                                                           |
| Gas Token                             | Native token used to pay for gas                                                                                             |
| Genesis State                         | "Initial state at chain genesis, including code and storage of predeploys (all L2 smart contracts)"                          |
| L1 Smart Contracts                    | The chain’s L1 smart contracts must be unmodified from an approved governance release                                        |
| L2 Block time                         | Frequency with which blocks are produced as a result of derivation                                                           |
| Output frequency                      | Frequency with which output roots are submitted to L1                                                                        |
| ResourceConfig                        | Config for the EIP-1559 based curve used for the deposit gas market                                                          |
| Sequencing window                     | "Maximum allowed batch submission frequency, after which L1 fallback is triggered in derivation"                             |
| Start Block                           | Block at which op-node starts searching for logs from                                                                        |


## Admin Roles

| Config Property                       | Description                                                                                                                  |
|---------------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| Batch Submitter address               | Account which authenticates new batches submitted to L1 Ethereum.                                                            |
| Guardian address                      | Account authorized to pause L1 withdrawals from contracts                                                                    |
| Challenger address                    | Account which can delete output roots before challenge period has elapsed                                                    |
| Sequencer P2P / Unsafe head signer    | Account which authenticates the unsafe/pre-submitted blocks for a chain at the P2P layer.                                    |
| Proposer address                      | Account which can propose output roots to L1                                                                                 |


## Service Roles

| Config Property                       | Description                                                                                                                  |
|---------------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| L1 Proxy Admin Owner                  | Account authorized to update the L1 Proxy Admin                                                                              |
| Mint Manager Owner                    | Account which controls the MintManager to mint OP tokens                                                                     |
| L2 Proxy Admin Owner                  | Account authorized to update the L2 Proxy Admin                                                                              |
| L1 Proxy Admin                        | Account authorized to upgrade L1 contracts                                                                                   |
| L2 Proxy Admin                        | Account authorized to upgrade L2 contracts                                                                                   |
| System Config Owner                   | Account authorized to change values in the SystemConfig contract                                                             |
