# Protocol Parameters

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

**Table of Contents**

- [Protocol Parameters](#protocol-parameters)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

The table below defines the protocol parameter requirements for an OP Stack chain to be considered a Standard Chain.

| Protocol Parameter                    | Requirement                                                    | Justification/Notes                                                                                                                                                                      |
| ------------------------------------- | -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Fault Proof Window / Challenge Period | 7 days                                                         | High security.                                                                                                                                                                           |
| Sequencing Window                     | TODO                                                           | High security.                                                                                                                                                                           |
| Chain ID                              | Foundation-approved, non-colliding value [^chain-id]           | Foundation will ensure chains are responsible with their chain IDs until there's a governance process in place.                                                                          |
| L2 Block Time                         | 2 seconds                                                      | High security & [interoperability](../interop/overview.md) compatibility requirement, until de-risked/solved at app layer.                                                               |
| Genesis State                         | Only standard predeploys and preinstalls, no additional state  | Homogeneity & standardization.                                                                                                                                                           |
| Output Frequency                      | TODO this won't exist post-FPAC, should we include it?         | TODO                                                                                                                                                                                     |
| Batch Submission Frequency            | Less than 50% of the sequencing window                         | Batcher needs to fully submit each batch within the sequencing window, so this leaves buffer to account for L1 network congestion and the amount of data the batcher would need to post. |
| Batch Inbox Address                   | TODO, ideally function of 32 byte chain ID                     | TODO                                                                                                                                                                                     |
| Compression Ratio                     | None                                                           | Safe to set however the entity running the batcher wishes.                                                                                                                               |
| Fee Vault Contracts                   | Standard revenue share contract deployment [^fee-vault]        | TODO                                                                                                                                                                                     |
| Resource Config                       | TODO.                                                          | High security, changes here can lead to security vulnerabilities.                                                                                                                        |
| Target Gas Rate                       | TODO, defined as a function of Resource Config?                | TODO.                                                                                                                                                                                    |
| Fee Margin                            | Between 0 and 50%                                              | [Law of Chains](https://github.com/ethereum-optimism/OPerating-manual/blob/main/Law%20of%20Chains.md).                                                                                   |
| Start Block                           | Any block less than the block where L1 contracts were deployed | Simple clear restriction.                                                                                                                                                                |
| Gas Limit                             | TODO                                                           | Must have well-tested gaslimit for uptime properties, also dangerously affects EIP1559 parameterization.                                                                                 |
| Data Availability                     | Ethereum                                                       | Alt-DA is not yet supported for the standard configuration.                                                                                                                              |
| Gas Token                             | Ether (ETH)                                                    | Custom gas tokens are not [yet](https://github.com/ethereum-optimism/specs/issues/67) supported.                                                                                         |

[^chain-id]:
The chain ID must not be present in the [superchain-registry](https://github.com/ethereum-optimism/superchain-registry)
TODO check other lists such as
[ethereum-lists/chains](https://github.com/ethereum-lists/chains) or [chains.json](https://chainid.network/chains.json).
TODO process for foundation approval?.

[^fee-vault]:
The standard revenue share contract is TODO, and the steps to deploy and configure it are TODO.
