# Rollback Inboxes

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Message Hash Reception](#message-hash-reception)
- [Upgradability](#upgradability)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The rollback inbox contracts are responsible for storing the hashes of messages that failed on the other domain. They are built with the purpose of allowing contracts on the same domain to have the capability of handling what actions to perform when a message failed on the other domain and was rolled-back to it's origin domain.

The `L2RollbackInbox` is a predeploy contract located at TO BE DEFINED.

```solidity
interface RollbackInbox {
    event MessageHashReceived(bytes32 indexed messageHash, uint256 indexed timestamp);

    function receiveMessageHash(bytes32 _messageHash, address _sender) external;
    function messenger() view external returns (address);
    function otherMessenger() view external returns (address);
    function messageHashes(bytes32 _messageHash) view external returns (uint256);
}
```

## Message Hash Reception

The `receiveMessageHash` function is used to receive message hashes from the other domain. It must ensure the caller is the `CrossDomainMessenger` from this domain, and that the sender is the `CrossDomainMessenger` from the other domain.

## Upgradability

Both the L1 and L2 rollback inboxes should be behind upgradable proxies.
