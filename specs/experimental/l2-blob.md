# L2 BLOB Transaction

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The Ethereum Cancun upgrade has significantly reduced Layer 2 data uploading costs by introducing BLOB transaction to Layer 1. This innovation has also enabled a variety of applications based on the BLOBs due to their low cost, such as [blob.fm](https://blob.fm/), [Ethstorage](https://ethstorage.io), and [Ethscriptions](https://ethscriptions.com/). However, while the data upload costs are now lower, the execution costs remain high compared to Layer 2. This presents challenges for state proposals on Layer 2 and for non-financial applications that rely on BLOBs, which still face relatively high costs.

The goal of this specification is to add BLOB transaction support to the OP Stack. This would allow Layer 3 solutions, which settle on Layer 2, to have an enshrined data availability (DA) layer that they can use directly, without needing to integrate third-party DA providers or deal with the security risks associated with DA bridges. Additionally, the applications mentioned above could migrate to Layer 2 with minimal costs.

Furthermore, this spec proposes adding an option to use [Alt-DA]((https://github.com/ethereum-optimism/specs/blob/main/specs/experimental/alt-da.md)) (or off-chain DA) to support BLOB transactions, while still allowing Layer 1 DA (or on-chain DA) for calldata. This would result in three possible configurations for a Layer 2:

1.	Both the calldata and BLOBs use on-chain DA.
2.	Both the calldata and BLOBs use Alt-DA.
3.	Calldata uses Layer 1 on-chain DA, while BLOBs use Alt-DA.

The third option, referred to as a “hybrid Layer 2”, combines the best features of different DA solutions. This allows users and applications to choose between on-chain and off-chain data availability for different types of transactions within the same network. Specifically, users can upload and store non-financial data at a very low cost using off-chain DA, while still conducting critical financial transactions using on-chain DA. In some cases, these two types of transactions may even occur within the same application. For example, users might use a platform like Twitter primarily for social networking, while also sending payments to other users.

The following diagram illustrates the transaction data flow for a hybrid Layer 2:
```mermaid
flowchart
    A[Users] -->|Non-financial Tx Using BLOB| B(Layer 2)
    A[Users] -->|Financial Tx Using Calldata| B(Layer 2)
    B -->|BLOB| C(Alt-DA)
    B -->|Calldata| D(L1 On-chain DA)
```

## Enable BLOB Transacion in EL
The interface and implematation should keep the same as the corresponding Layer 1 EL so that the application can be migrated seamlessly. Please note that while BLOBs are gossiping in the L1 P2P network, for an enshined BLOB DA support, the BLOBs should be sent to the sequencer directly on the layer2.

## Uploading BLOB to Alt-DA
The sequencer have the responsbility of uploading the BLOBs to a DA layer. When the CL (op-node) receives payload from EL through engine API, they should open the envelope to see if there are any `BlobsBundle` and upload them to Alt-DA. Only make sure the BLOBs are uploaded successfully, the sequencer can upload the block data to the on-chain DA. As the same as the Alt-DA, the sequecenr may want to response to any data avalibity challenage afterwards.

## DataAavaliblityChallenage Contract
Any third party including the full nodes which are actively derivating the L1 data may found they can't request the data correpsonding the data hash included in the BLOB transaction, they can initilize a data challendage, the whole workflow should most likely be the same as Alt-DA [here](https://github.com/ethstorage/specs/blob/l2-blob/specs/experimental/alt-da.md#data-availability-challenge-contract).

Note that since the data hash included in the BLOB transaction is [VersionedHash](https://github.com/ethereum/EIPs/blob/master/EIPS/eip-4844.md#helpers) instead of Keccak256 hash, we need to use it as the commitment when doing BLOB uploading/downloading and challenaging/resoling. So we need to add an CommitmentType in the DataAvailabilityChallenge contract:

```solidity
enum CommitmentType {
    Keccak256,
    VersionedHash
}
```
And also add a new resolve function in the contract:

```solidity
function resolve(
    uint256 challengedBlockNumber,
    bytes calldata challengedCommitment,
)
```
This new resolve function SHOULD use Layer 1 BLOB transaction to upload the BLOB and then use EIP-4844 blobhash() opcode to obtained the `versionedhash` of the BLOB.

## BLOB Gas Cost

## Derivation

## Fault Proof

## Safety and Finality