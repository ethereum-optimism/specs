<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Migrated Liquidity storage update](#migrated-liquidity-storage-update)
  - [Overview](#overview)
  - [`OptimismMintableERC20Factory` predeploy](#optimismmintableerc20factory-predeploy)
  - [Generate Hash Onion](#generate-hash-onion)
  - [`superchain-ops` task](#superchain-ops-task)
  - [Additional Notes](#additional-notes)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Migrated Liquidity storage update

**Disclaimer:** This content should be placed in the protocol upgrade folder when it becomes available.

## Overview

To fully migrate liquidity from `OptimismMintableERC20` tokens to `OptimismSuperchainERC20`,
the `OptimismMintableERC20Factory` needs to track its deployment history.

To achieve this, a [Hash Onion](https://github.com/ethereum-optimism/design-docs/blob/main/protocol/superchain-erc20/storage-upgrade.md#2-hash-onion)
solution will be used:

- The `OptimismMintableERC20Factory` predeploy will include functionality to set and store the Hash Onion,
  as well as verify and record deployment data.

- A Foundry script will be added to generate the Hash Onion from a list of local and remote tokens.

- A `superchain-ops` task will be added to set the Hash Onion from the L2 `ProxyAdmin` owner.

## `OptimismMintableERC20Factory` predeploy

Create a new `OptimismMintableERC20FactoryInterop` contract that inherits from `OptimismMintableERC20Factory`
and add the following functionality:

```solidity
bytes32 public hashOnion;

function setHashOnion(bytes32 _hashOnion) external {
    require(msg.sender == Predeploys.PROXY_ADMIN, "Unauthorized");
    require(hashOnion == 0, "Already initialized");

    hashOnion = _hashOnion;
}

function verifyAndStore(
    address[] calldata _localTokens,
    address[] calldata _remoteTokens,
    bytes32 _startingInnerLayer
)
    external
{
    require(hashOnion != keccak256(abi.encode(0)), "AlreadyDecoded");
    require(_localTokens.length == _remoteTokens.length, "TokensLengthMismatch");

    // Unpeel the hash onion and store the deployments
    bytes32 innerLayer = _startingInnerLayer;
    for (uint256 i; i < _localTokens.length; i++) {
        innerLayer = keccak256(abi.encodePacked(innerLayer, abi.encodePacked(_localTokens[i], _remoteTokens[i])));

        deployments[_localTokens[i]] = _remoteTokens[i];

        emit DeploymentStored(_localTokens[i], _remoteTokens[i]);
    }

    require(innerLayer == hashOnion, "InvalidProof");

    assembly {
        sstore(HASH_ONION_SLOT, _startingInnerLayer)
    }
}
```

## Generate Hash Onion

Create a Foundry script that generate the final onion hash based on a list of local and remote tokens.

```solidity
function generateHashOnion(
    address[] calldata localTokens,
    address[] calldata remoteTokens
) public {
    require(localTokens.length == remoteTokens.length, "Invalid arrays");

    bytes32 hashOnion = keccak256(abi.encode(0));

    for (uint256 i; i < localTokens.length; i++) {
        hashOnion = keccak256(abi.encodePacked(hashOnion, abi.encodePacked(localTokens[i], remoteTokens[i])));
    }

    return hashOnion;
}
```

## `superchain-ops` task

Each chain will need to generate its own hash onion based on its specific token list.
This onion will then be set via the setter function in the `OptimismMintableERC20Factory` predeploy.

The L2 `ProxyAdmin` owner will be responsible for performing the upgrade. On OP Mainnet,
this is the aliased L1 governance multisig.
To facilitate this, a task will be added to the [`superchain-ops` repository](https://github.com/ethereum-optimism/superchain-ops),
enabling the multisig to execute it.

## Additional Notes

- The token list should be proposed and approved through governance and made accessible for anyone to decode.

- Tokens in the innermost layers will need to prove all external layers before they can be converted.
  While Merkle trees were considered, they were discarded in favor of hash onions due to easier proof generation and verification.
  However, the dataset should be sorted so that the most popular tokens are in the outermost layers,
  allowing them to be decoded first.
