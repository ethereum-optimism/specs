# Inbox Contract

## Motivation

The batch inbox is currently an Externally Owned Account (EOA), which has both advantages and disadvantages:

Advantages:
- Low submission gas cost due to the absence of onchain execution.
- Verification logic is moved offchain to the derivation part, protected by a fault dispute game with a correct absolute prestate.

Disadvantage:
- Onchain verification is not possible.


This specification aims to allow the batch inbox to be a contract, enabling customized batch submission conditions such as:
- Requiring the batch transaction to be signed by a quorum of sequencers in a decentralized sequencing network; or
- Mandating that the batch transaction call a BLOB storage contract (e.g., EthStorage) with a long-term storage fee, which is then distributed to data nodes that prove BLOB storage over time.

## How It Works

The integration process consists of two primary components:
1. Replacement of the [`BatchInboxAddress`](https://github.com/ethereum-optimism/optimism/blob/db107794c0b755bc38a8c62f11c49320c95c73db/op-chain-ops/genesis/config.go#L77) with an inbox contract: The existing `BatchInboxAddress`, which currently points to an Externally Owned Account (EOA), will be replaced by a smart contract. This new inbox contract will be responsible for verifying and enforcing batch submission conditions.
2. Modification of the op-node derivation process: The op-node will be updated to exclude failed batch transactions during the derivation process. This change ensures that only successfully executed batch transactions are processed and included in the derived state.

These modifications aim to enhance the security and efficiency of the batch submission and processing pipeline, allowing for more flexible and customizable conditions while maintaining the integrity of the derived state.


## Reference Implementation

1. [example inbox contract for EthStorage](https://github.com/blockchaindevsh/es-op-batchinbox/blob/main/src/BatchInbox.sol)
2. [op-node derive changes](https://github.com/ethstorage/optimism/pull/22)