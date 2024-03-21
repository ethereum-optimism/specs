# OP Stack Configurability

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Consensus Parameters](#consensus-parameters)
- [Admin Roles](#admin-roles)
- [Service Roles](#service-roles)
- [Policy Parameters](#policy-parameters)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

When deploying the OP Stack software to a production environment,
certain parameters about the protocol can be configured. These
configurations can include a variety of parameters which affect the
resulting properties of the blockspace in question.

There are four categories of OP Stack configuration options:

- **Consensus Parameters**: Parameters and properties of the chain that may
  be set at genesis and fixed for the lifetime of the chain, or may be
  changeable through a privileged account.
- **Policy Parameters**: Parameters of the chain that might be changed without breaking consensus. Consensus is enforced by the protocol, while policy parameters may be changeable within constraints imposed by consensus.
- **Admin Roles**: These roles can upgrade contracts, change role owners,
  or update protocol parameters. These are typically cold/multisig wallets not
  used directly in day to day operations.
- **Service Roles**: These roles are used to manage the day-to-day
  operations of the chain, and therefore are often hot wallets.

## Consensus Parameters

| Config Property                       | Description                                                                                                                  | Administrator                       |
|---------------------------------------|------------------------------------------------------------------------------------------------------------------------------|-------------------------------------|
| [Batch Inbox address](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/L1/SystemConfig.sol#L176)                   | L1 address where calldata/blobs are posted (see [Batcher Transaction](../glossary.md#batcher-transaction)).                  | L1 Proxy Admin                      |
| [Chain ID](https://github.com/ethereum-optimism/superchain-registry/blob/main/superchain/configs/chainids.json)                              | Unique ID of Chain used for TX signature validation.                                                                         |                                     |
| [Challenge Period](https://github.com/ethereum-optimism/superchain-registry/pull/44)                      | Length of time for which an output root can be removed, and for which it is not considered finalized.                        | L1 Proxy Admin                      |
| Data Availability                     | Where L2 transaction calldata is posted.                                                                                     |                                     |
| Fault Proof Window / Challenge Window | Duration network participants have to challenge the integrity of an output root.                                             |                                     |
| [Fee margin](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/L1/SystemConfig.sol#L281-L283)                            | Markup on transactions compared to the raw L1 data cost.                                                                     | System Config Owner                 |
| Proxy Fee vault contracts             | Proxy contracts which point to implementation contracts that dictate how user fees are distributed.                          |                                     |
| [Gas limit](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/L1/SystemConfig.sol#L298-L300)                             | L2 block gas limit.                                                                                                          | System Config Owner                 |
| Gas Token                             | Native token used to pay for gas.                                                                                            |                                     |
| Genesis state                         | Initial state at chain genesis, including code and storage of predeploys (all L2 smart contracts). See [Predeploy](../glossary.md#l2-genesis-block). |             |
| L1 smart contracts                    | The chain’s L1 smart contracts.                                                                                              | L1 Proxy Admin                      |
| [L2 block time](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/L1/L2OutputOracle.sol#L105)                         | Frequency with which blocks are produced as a result of derivation.                                                          | L1 Proxy Admin                      |
| [Resource config](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/L1/SystemConfig.sol#L338-L340)                       | Config for the EIP-1559 based curve used for the deposit gas market.                                                         | System Config Owner                 |
| Sequencing window                     | Maximum allowed batch submission gap, after which L1 fallback is triggered in derivation.                                    |                                     |
| [Start block](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/L1/SystemConfig.sol#L184)                           | Block at which the system config was initialized the first time.                                                             | L1 Proxy Admin                      |
| Superchain target                     | Choice of cross-L2 configuration. May be omitted in isolated OP Stack deployments. Includes SuperchainConfig and ProtocolVersions contract addresses. |            |

## Policy Parameters

| Config Property                       | Description                                                                                                                  | Administrator                       |
|---------------------------------------|------------------------------------------------------------------------------------------------------------------------------|-------------------------------------|
| Batch submission frequency            | Frequency with which batches are submitted to L1 (see [Batcher Transaction](../glossary.md#batcher-transaction)).            |                                     |
| Compression ratio                     | How much compression the batch submitter applies to batches before submission (see [Channel](../glossary.md#channel)).       |                                     |
| Implementation Fee vault contracts    | Implementation contracts that sit behind proxies and dictate how user fees are distributed.                                  |                                     |
| [Output frequency](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/L1/L2OutputOracle.sol#L104)                      | Frequency with which output roots are submitted to L1.                                                                       | L1 Proxy Admin                      |

## Admin Roles

| Config Property                       | Description                                                                                                                  | Administrator                       |
|---------------------------------------|------------------------------------------------------------------------------------------------------------------------------|-------------------------------------|
| [L1 Proxy Admin](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/universal/ProxyAdmin.sol#L30)                        | Account authorized to upgrade L1 contracts.                                                                                  | L1 Proxy Admin Owner                |
| L1 ProxyAdmin owner                   | Account authorized to update the L1 Proxy Admin.                                                                             |                                     |
| [L2 Proxy Admin](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/universal/ProxyAdmin.sol#L30)                        | Account authorized to upgrade L2 contracts.                                                                                  | L2 Proxy Admin Owner                |
| L2 ProxyAdmin owner                   | Account authorized to update the L2 Proxy Admin.                                                                             |                                     |
| [System Config Owner](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/L1/SystemConfig.sol#L14C26-L14C44)                   | Account authorized to change values in the SystemConfig contract. All configuration is stored on L1 and picked up by L2 as part of the [derviation](./derivation.md) of the L2 chain. |                                     |

## Service Roles

| Config Property                       | Description                                                                                                                  | Administrator                       |
|---------------------------------------|------------------------------------------------------------------------------------------------------------------------------|-------------------------------------|
| [Batch submitter address](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/L1/SystemConfig.sol#L265)               | Account which authenticates new batches submitted to L1 Ethereum.                                                            | System Config Owner                 |
| [Challenger address](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/L1/L2OutputOracle.sol#L109)                    | Account which can delete output roots before challenge period has elapsed.                                                   | L1 Proxy Admin                      |
| [Guardian address](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/L1/SuperchainConfig.sol#L50)                      | Account authorized to pause L1 withdrawals from contracts.                                                                   | L1 Proxy Admin                      |
| [Proposer address](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/L1/L2OutputOracle.sol#L108)                      | Account which can propose output roots to L1.                                                                                | L1 Proxy Admin                      |
| [Sequencer P2P / Unsafe head signer](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/L1/SystemConfig.sol#L250)    | Account which authenticates the unsafe/pre-submitted blocks for a chain at the P2P layer.                                    | System Config Owner                 |

