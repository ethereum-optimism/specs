<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
  - [Interface](#interface)
    - [Core Functions](#core-functions)
  - [Diagram](#diagram)
  - [Implementation](#implementation)
  - [Backwards Compatibility](#backwards-compatibility)
  - [Security Considerations](#security-considerations)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Overview

The goal of this specification is to allow interoperability between the OP mainnet and other chains that use the [`Alligator`](alligator.md) predeploy. This allows the support of the
subdelegation flow with for the [`GovernanceToken`](gov-token.md) by making a few changes to the existing interface for cross-chain message passing as it pertains to the checkpoint state.

## Interface

### Core Functions

```solidity
function afterTokenTransfer(
    address src,
    address dst,
    uint256 amount
) external
```

In addition to performing it's standard functionality this method will now use the `L2ToL2CrossDomainMessenger` to send a message to the same method on the `Alligator` contract, `afterTokenTransfer` that exists on OP mainnet. It will ensure prior to doing so that the `chainId` is not OP Mainnet i.e. 10(0xa). Moreover, it will still handle a check that both address have been migrated using the new storage field and update the voting power of the delegate.

Since the mainnet instance is the single source of truth of the voting power, before updating the state, it will check that the sender of this message is in fact another OP token with the same address, which is assumed since the goverance token is a predeploy. Given that messages are received from other tokens that exist on the other OP chains, an additional check needs to be performed that ensures we are on OP mainnet by checking the `chainId` before updating the checkpoints for the delegate voting power.

## Diagram

```mermaid
sequenceDiagram
  participant delegate
  participant AlligatorSuperChain as AlligatorArbitraryChain (Chain A)
  participant AlligatorOPMainnet as AlligatorOPMainnet (Chain B)
  participant Inbox as CrossL2Inbox
  participant Messenger_A as L2ToL2CrossDomainMessenger (Chain A)
  participant Messenger_B as L2ToL2CrossDomainMessenger (Chain B)

  delegate->>AlligatorArbitraryChain: afterTokenTransfer(src, dst, amt)
  AlligatorSuperChain->>Messenger_A: sendMessage(nativeChainId, message)
  Messenger_A->>Inbox: executeMessage()
  Inbox->>Messenger_B: relayMessage()
  Messenger_B->>AlligatorOPMainnet: afterTokenTransfer(src, dst, amount, chainId)
```

## Implementation

```solidity

function getChainId() external view returns (uint256) {
    uint256 chainId;
    assembly {
         chainId := chainid()
    }

    return chainId;
}

function afterTokenTransfer(
    address src,
    address dst,
    uint256 amount
) external {
    uint256 chainId = getChainId();

    if (chainId == uint256(10)) {
        require(msg.sender == address(L2ToL2CrossChainMessenger));
        require(L2ToL2CrossChainMessenger.crossDomainMessageSender() == address(this));

        if (src != dst && amount > 0) {
           if (src != address(0)) {
                (uint256 oldWeight, uint256 newWeight) = _writeCheckpoint(_checkpoints[src], _subtract, amount);
                emit DelegateVotesChanged(src, oldWeight, newWeight);
            }

            if (dst != address(0)) {
                (uint256 oldWeight, uint256 newWeight) = _writeCheckpoint(_checkpoints[dst], _add, amount);
                emit DelegateVotesChanged(dst, oldWeight, newWeight);
            }
        }
    }

    L2ToL2CrossDomainMessenger.sendMessage({
        _destination: nativeChainId,
        _target: address(this),
        _message: abi.encodeCall(this.afterTokenTransferInterop, (src, dst, amount))
    });
}
```

The contract may support a function to get the chainId or another modifier to prevent the Interop messaging to be sent outside of OP mainnet.

## Backwards Compatibility

Previous instances of `Alligator` will not be able to interface with the OP mainnet contract given that they do not support the cross-chain message passing. However, the existing state
of voting power on the superchain shall remained unchanged.

## Security Considerations

We must ensure that that both the `GovernanceToken` and `Alligator` use the same address across all chains.

