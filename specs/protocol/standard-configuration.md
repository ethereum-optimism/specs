# OP Stack Standard Configuration 

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Consensus Parameters](#consensus-parameters)
- [Policy Parameters](#policy-parameters)
- [Admin Roles](#admin-roles)
- [Service Roles](#service-roles)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

The Standard Configuration is the set of requirements for an OP Stack chain to be considered a Standard Chain. These requirements are currently a draft, pending governance approval.
These requirements are split into four parts:

- [**Consensus Parameters**](./configurability.md#consensus-parameters)
- [**Policy Parameters**](./configurability.md#policy-parameters)
- [**Admin Roles**](./configurability.md#admin-roles)
- [**Service Roles**](./configurability.md#service-roles)

## Consensus Parameters

| Config Property                       | Requirement                                                                                                                  | Notes                       |
|---------------------------------------|------------------------------------------------------------------------------------------------------------------------------|-------------------------------------|
| [Batch Inbox address](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/L1/SystemConfig.sol#L176)                   | Current convention is `0xff000...000{chainId}`. This doesn't work when `chainId` is `uint256`.  | Follow convention if possible. A future hardfork plans to migrate Batch Inbox Addresses to better support `uint256` sized chain IDs. |
| [Batcher Hash](./system_config.md#batcherhash-bytes32) | `bytes32(uint256(uint160(batchSubmitterAddress)))` | [Batch Submitter](../protocol/batcher.md) address padded with zeros to fit 32 bytes. |
| [Chain ID](https://github.com/ethereum-optimism/superchain-registry/blob/main/superchain/configs/chainids.json)                              | Foundation-approved, non-colliding value [^chain-id]. | Foundation will ensure chains are responsible with their chain IDs until there's a governance process in place. |
| [Challenge Period](../protocol/withdrawals.md#withdrawal-flow) | 7 days. | High security. Excessively safe upper bound that leaves enough time to consider social layer solutions to a hack if necessary. Allows enough time for other network participants to challenge the integrity of the corresponding output root. |
| [Fee Scalar](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/L1/SystemConfig.sol#L288-L294)                            | Set such that Fee Margin is between 0 and 50%.  | |
| [Gas Limit](./system_config.md#gaslimit-uint64) | 60,000,000 gas | Chain operators are driven to maintain a stable and reliable chain. When considering to change this value, careful deliberation is necessary. |
| Genesis state                         | Only standard predeploys and preinstalls, no additional state. | Homogeneity & standardization, ensures initial state is secure. |
| [L2 block time](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/L1/L2OutputOracle.sol#L105)                         | 2 seconds | High security & [interoperability](../interop/overview.md) compatibility requirement, until de-risked/solved at app layer. |
| [Resource config](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/L1/SystemConfig.sol#L338-L340)                       | See [resource config table](#resource-config) | Constraints are imposed in [code](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/L1/SystemConfig.sol#L345-L365) when setting the resource config. |
| Sequencing window                     | 12 hours. | This is an important value for constraining the sequencer's ability to re-order transactions; higher values would pose a risk to User Protections. |
| [Start block](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/L1/SystemConfig.sol#L184)                           | The block where the SystemConfig was initialized. | Simple clear restriction. |
| [Superchain target](../protocol/superchain-upgrades.md#superchain-target)   | mainnet or sepolia | A superchain target defines a set of layer 2 chains which share `SuperchainConfig` and `ProtocolVersions` contracts deployed on layer 1. |

[^chain-id]: The chain ID must be globally unique among all EVM chains. 

### Resource Config
| Config Property                       | Requirement                                                                                                                  | 
|---------------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| maxResourceLimit | 2e7 | |
| elasticityMultiplier | 10 | |
| baseFeeMaxChangeDenominator | 8 | |
| minimumBaseFee | 1e9 | |
| systemTxMaxGas | 1e6 | |
| maximumBaseFee | 2^128 - 1 | |



## Policy Parameters

| Config Property                       | Requirement                                                                                                                  | Notes                       |
|---------------------------------------|------------------------------------------------------------------------------------------------------------------------------|-------------------------------------|
| Data Availability Type        | Ethereum (Blobs, Calldata). | Alt-DA is not yet supported for the standard configuration, but the sequencer can switch at-will between blob and calldata with no restiction, since both are L1 security. |
| Batch submission frequency            | 6 hours (i.e. 50% of the Sequencing Window). | Batcher needs to fully submit each batch within the sequencing window, so this leaves buffer to account for L1 network congestion and the amount of data the batcher would need to post.  |
| [Output frequency](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/L1/L2OutputOracle.sol#L104)                      | 1800 seconds | Deprecated once fault proofs are implemented. |

## Admin Roles

The table below defines admin role requirements for an OP Stack chain to be considered a Standard Chain.

| Config Property                       | Requirement                                                                                                                  | Notes                         |
|---------------------------------------|------------------------------------------------------------------------------------------------------------------------------|-------------------------------------|
| L1 Proxy Admin                        | [ProxyAdmin.sol](https://github.com/ethereum-optimism/optimism/blob/op-contracts/v1.3.0/packages/contracts-bedrock/src/universal/ProxyAdmin.sol) from the latest tagged release of source code in [Optimism repository](https://github.com/ethereum-optimism/optimism) |  Governance-controlled, high security.
| L1 ProxyAdmin owner                   | [0x5a0Aae59D09fccBdDb6C6CcEB07B7279367C3d2A](https://etherscan.io/address/0x5a0Aae59D09fccBdDb6C6CcEB07B7279367C3d2A) [^of-sc-gnosis-safe-l1] | Governance-controlled, high security.                                
| L2 Proxy Admin | [ProxyAdmin.sol](https://github.com/ethereum-optimism/optimism/blob/op-contracts/v1.3.0/packages/contracts-bedrock/src/universal/ProxyAdmin.sol) from the latest tagged release of source code in [Optimism repository](https://github.com/ethereum-optimism/optimism). Predeploy address:  [0x4200000000000000000000000000000000000018](https://docs.optimism.io/chain/addresses#op-mainnet-l2) | Governance-controlled, high security.
| L2 ProxyAdmin owner                   | Optimism Foundation Gnosis Safe e.g. [0x7871d1187A97cbbE40710aC119AA3d412944e4Fe](https://optimistic.etherscan.io/address/0x7871d1187A97cbbE40710aC119AA3d412944e4Fe) [^of-gnosis-safe-l2] | Governance-controlled, high security.                                
| [System Config Owner](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/L1/SystemConfig.sol#L14C26-L14C44)                   | Chain Governor or Servicer | As defined in the [Law of Chains](https://github.com/ethereum-optimism/OPerating-manual/blob/main/Law%20of%20Chains.md)            

[^of-sc-gnosis-safe-l1]: 2 of 2 GnosisSafe between Optimism Foundation (OF) and the Security Council (SC) on L1: [0x5a0Aae59D09fccBdDb6C6CcEB07B7279367C3d2A](https://etherscan.io/address/0x5a0Aae59D09fccBdDb6C6CcEB07B7279367C3d2A).
[^of-gnosis-safe-l2]: 5 of 7 GnosisSafe for Optimism Foundation  on L2: [0x7871d1187A97cbbE40710aC119AA3d412944e4Fe](https://optimistic.etherscan.io/address/0x7871d1187A97cbbE40710aC119AA3d412944e4Fe).


## Service Roles

Servicer roles are related to actions taken by Chain Servicers in the
[Law of Chains](https://github.com/ethereum-optimism/OPerating-manual/blob/main/Law%20of%20Chains.md).
They are typically hot wallets, as they take active roles in chain progression and are used to
participate in day-to-day, ongoing operations.

| Config Property                       | Requirement                                                                                                                  | Notes                       |
|---------------------------------------|------------------------------------------------------------------------------------------------------------------------------|-------------------------------------|
| [Batch submitter address](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/L1/SystemConfig.sol#L265)               | No requirement |  |
| [Challenger address](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/L1/L2OutputOracle.sol#L109)                    | [0x9BA6e03D8B90dE867373Db8cF1A58d2F7F006b3A](https://etherscan.io/address/0x9BA6e03D8B90dE867373Db8cF1A58d2F7F006b3A) [^of-gnosis-safe-l1] | Optimism Foundation (OF) multisig leveraging [battle-tested software](https://github.com/safe-global/safe-smart-account). |
| [Guardian address](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/L1/SuperchainConfig.sol#L50)                      | [0x9BA6e03D8B90dE867373Db8cF1A58d2F7F006b3A](https://etherscan.io/address/0x9BA6e03D8B90dE867373Db8cF1A58d2F7F006b3A) [^of-gnosis-safe-l1] | Optimism Foundation (OF) multisig leveraging [battle-tested software](https://github.com/safe-global/safe-smart-account). |
| [Proposer address](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/L1/L2OutputOracle.sol#L108)                      | No requirement |  |
| [Sequencer P2P / Unsafe head signer](https://github.com/ethereum-optimism/optimism/blob/c927ed9e8af501fd330349607a2b09a876a9a1fb/packages/contracts-bedrock/src/L1/SystemConfig.sol#L250)    | No requirement | |

[^of-gnosis-safe-l1]: 5 of 7 GnosisSafe controlled by Optimism Foundation (OF): [0x9BA6e03D8B90dE867373Db8cF1A58d2F7F006b3A](https://etherscan.io/address/0x9BA6e03D8B90dE867373Db8cF1A58d2F7F006b3A).