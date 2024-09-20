# Token Bridging

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [`SuperchainERC20` standard](#superchainerc20-standard)
- [`InteropStandardBridge`](#interopstandardbridge)
  - [Functions](#functions)
    - [`sendERC20`](#senderc20)
    - [`relayERC20`](#relayerc20)
  - [Events](#events)
    - [`SentERC20`](#senterc20)
    - [`RelayedERC20`](#relayederc20)
- [Diagram](#diagram)
- [Implementation](#implementation)
- [Invariants](#invariants)
- [Future Considerations](#future-considerations)
  - [Cross Chain `transferFrom`](#cross-chain-transferfrom)
  - [Concatenated Action](#concatenated-action)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

Without a standardized security model, bridged assets may not be fungible with each other.
The `SuperchainERC20` standard is a set of properties allowing ERC20 to be fungible across the
Superchain using the official `InteropStandardBridge`.
The `InteropStandardBridge` is a predeploy that builds on the messaging protocol as the most trust-minimized bridging solution.

## `SuperchainERC20` standard

The standard will build on top of ERC20 and include the following properties:

1. Give `mint` and `burn` rights to the `InteropStandardBridge`.
2. Be deployed at the same address on every chain in the Superchain.

The first property will allow the `InteropStandardBridge` to have a liquidity guarantee,
which would not be possible in a model based on lock/unlock.
Liquidity availability is fundamental to achieving fungibility.

The second property removes the need for cross-chain access control lists.
Otherwise, the `InteropStandardBridge` would need a way to verify if the tokens they mint on
destination correspond to the tokens that were burned on source.
Same address abstracts away cross-chain validation.

One way to guarantee the same address across the Superchain, and also bind it to the same `init_code`
and constructor arguments is to use the
[`Create2Deployer` preinstall](../protocol/preinstalls.md#create2deployer).
There is also a [`OptimismSuperchainERC20Factory`](predeploys.md#optimismmintableerc20factory)
predeploy that facilitates this process for L1 native tokens.

Notice that ERC20s that do not implement the standard can still be fungible
using interop message passing but would need to use a custom bridge.

## `InteropStandardBridge`

The `InteropStandardBridge` is a predeploy that works as an abstraction
on top of the `L2toL2CrossDomainMessenger` for token bridging.

### Functions

#### `sendERC20`

Initializes a transfer of `_amount` amount of tokens with address `_tokenAddress` to target address `_to` in chain `_chainId`.

It SHOULD burn `_amount` tokens with address `_tokenAddress` and initialize a message to the
`L2ToL2CrossChainMessenger` to mint the `_amount` of the same token
in the target address `_to` at `_chainId` and emit the `SentERC20` event including the `msg.sender` as parameter.

```solidity
sendERC20(address _tokenAddress, address _to, uint256 _amount, uint256 _chainId)
```

#### `relayERC20`

Process incoming messages IF AND ONLY IF initiated
by the same contract (token) address on a different chain
and come from the `L2ToL2CrossChainMessenger` in the local chain.
It SHOULD mint `_amount` of tokens with address `_tokenAddress` to address `_to`, as defined in `sendERC20`
and emit an event including the `_tokenAddress`, the `_from` and chain id from the
`source` chain, where `_from` is the `msg.sender` of `sendERC20`.

```solidity
relayERC20(address _tokenAddress, address _from, address _to, uint256 _amount)
```

### Events

#### `SentERC20`

MUST trigger when a cross-chain transfer is initiated using `sendERC20`.

```solidity
event SentERC20(address indexed tokenAddress, address indexed from, address indexed to, uint256 amount, uint256 destination)
```

#### `RelayedERC20`

MUST trigger when a cross-chain transfer is finalized using `relayERC20`.

```solidity
event RelayedERC20(address indexed tokenAddress, address indexed from, address indexed to, uint256 amount, uint256 source);
```

## Diagram

The following diagram depicts a cross-chain transfer.

```mermaid
sequenceDiagram
  participant from
  participant L2SBA as L2StandardBridge (Chain A)
  participant SuperERC20_A as SuperchainERC20 (Chain A)
  participant Messenger_A as L2ToL2CrossDomainMessenger (Chain A)
  participant Inbox as CrossL2Inbox
  participant Messenger_B as L2ToL2CrossDomainMessenger (Chain B)
  participant L2SBB as L2StandardBridge (Chain B)
  participant SuperERC20_B as SuperchainERC20 (Chain B)

  from->>L2SBA: sendERC20To(tokenAddr, to, amount, chainID)
  L2SBA->>SuperERC20_A: burn(from, amount)
  L2SBA->>Messenger_A: sendMessage(chainId, message)
  L2SBA-->L2SBA: emit SentERC20(tokenAddr, from, to, amount, destination)
  Inbox->>Messenger_B: relayMessage()
  Messenger_B->>L2SBB: relayERC20(tokenAddr, from, to, amount)
  L2SBB->>SuperERC20_B: mint(to, amount)
  L2SBB-->L2SBB: emit RelayedERC20(tokenAddr, from, to, amount, source)
```

## Implementation

An example implementation that depends on deterministic deployments across chains
for security is provided.
This construction builds on top of the [L2ToL2CrossDomainMessenger][l2-to-l2]
for both replay protection and domain binding.

[l2-to-l2]: ./predeploys.md#l2tol2crossdomainmessenger

```solidity
function sendERC20(SuperchainERC20 _token, address _to, uint256 _amount, uint256 _chainId) public {
  _token.burn(msg.sender, _amount);

  bytes memory _message = abi.encodeCall(this.relayERC20, (_token, msg.sender, _to, _amount));
  L2ToL2CrossDomainMessenger.sendMessage(_chainId, address(this), _message);
  
  emit SendERC20(address(_token), msg.sender, _to, _amount, _chainId);
}

function relayERC20(SuperchainERC20 _token, address _from, address _to, uint256 _amount) external {
  require(msg.sender == address(L2ToL2CrossChainMessenger));
  require(L2ToL2CrossChainMessenger.crossDomainMessageSender() == address(this));
  
  uint256 _source = L2ToL2CrossChainMessenger.crossDomainMessageSource();

  _token.mint(_to, _amount);

  emit RelayERC20(address(_token), _from, _to, _amount, _source);
}
```

## Invariants

The bridging of `SuperchainERC20` using the `InteropStandardBridge` will require the following invariants:

- Conservation of bridged `amount`: The minted `amount` in `relayERC20()` should match the `amount`
  that was burnt in `sendERC20()`, as long as target chain has the initiating chain in the dependency set.
  - Corollary 1: Finalized cross-chain transactions will conserve the sum of `totalSupply`
    and each user's balance for each chain in the Superchain.
  - Corollary 2: Each initiated but not finalized message (included in initiating chain but not yet in target chain)
    will decrease the `totalSupply` and the initiating user balance precisely by the burnt `amount`.
  - Corollary 3: `SuperchainERC20s` should not charge a token fee or increase the balance when moving cross-chain.
  - Note: if the target chain is not in the initiating chain dependency set,
    funds will be locked, similar to sending funds to the wrong address.
    If the target chain includes it later, these could be unlocked.
- Freedom of movement: Users should be able to send and receive tokens in any target
  chain with the initiating chain in its dependency set
  using `sendERC20()` and `relayERC20()`, respectively.
- Unique Messenger: The `sendERC20()` function must exclusively use the `L2toL2CrossDomainMessenger` for messaging.
  Similarly, the `relayERC20()` function should only process messages originating from the `L2toL2CrossDomainMessenger`.
- Unique Address: The `sendERC20()` function must exclusively send a message
  to the same address on the target chain.
  Similarly, the `relayERC20()` function should only process messages originating from the same address.
  - Note: The `Create2Deployer` preinstall and the custom Factory will ensure same address deployment.
- Locally initiated: The bridging action should be initialized
  from the chain where funds are located only.
  - This is because the same address might correspond to different users cross-chain.
    For example, two SAFEs with the same address in two chains might have different owners.
    With the prospects of a smart wallet future, it is impossible to assume
    there will be a way to distinguish EOAs from smart wallets.
  - A way to allow for remotely initiated bridging is to include remote approval,
    i.e. approve a certain address in a certain chainId to spend local funds.
- Bridge Events:
  - `sendERC20()` should emit a `SentERC20` event. `
  - `relayERC20()` should emit a `RelayedERC20` event.

## Future Considerations

### Cross Chain `transferFrom`

In addition to standard locally initialized bridging,
it is possible to allow contracts to be cross-chain interoperable.
For example, a contract in chain A could send pre-approved funds
from a user in chain B to a contract in chain C.

For the moment, the standard will not include any specific functionality
to facilitate such an action and rely on the usage of `Permit2` like this:

```mermaid
sequenceDiagram
  participant from
  participant Intermediate_A as Initiator
  participant Messenger_A as L2ToL2CrossDomainMessenger (Chain A)
  participant Inbox as CrossL2Inbox
  participant Messenger_B as L2ToL2CrossDomainMessenger (Chain B)
  participant Permit2
  participant SuperERC20_B as SuperchainERC20 (Chain B)
  participant Recipient as to

  from->>Intermediate_A: remoteTransferFrom(..., token, to, chainId, msg, signature)
  Intermediate_A->>Messenger_A: permit: sendMessage(chainId, message)
  Inbox->>Messenger_B: permit: relayMessage()
  Messenger_B->>Permit2: permitTransferFrom(msg, sig)
  Permit2->>SuperERC20_B: transferFrom(from, to, amount)

```

If, at some point in the future, these actions were to be included in the standard,
a possible design could introduce a `remoteTransferFrom()` function.

### Concatenated Action

It is possible to have an additional input `bytes _data` in both `sendERC20()` and `relayERC20()` that would make an
additional call to the `_to` address.
This feature could be used for cross-chain concatenated actions,
i.e. bridge funds and then do X.

This vertical has much potential but can also be achieved outside the standard in the following way:

```mermaid
sequenceDiagram
  participant from
  participant Intermediate_A as intermediate A
  participant L2SBA as L2StandardBridge (Chain A)
  participant SuperERC20_A as SuperchainERC20 (Chain A)
  participant Messenger_A as L2ToL2CrossDomainMessenger (Chain A)
  participant Inbox as CrossL2Inbox
  participant Messenger_B as L2ToL2CrossDomainMessenger (Chain B)
  participant L2SBB as L2StandardBridge (Chain B)
  participant SuperERC20_B as SuperchainERC20 (Chain B)

  from->>Intermediate_A: sendWithData(data)
  Intermediate_A->>L2SBA: sendERC20To(tokenAddr, to, amount, chainID)
  L2SBA->>SuperERC20_A: burn(from, amount)
  L2SBA->>Messenger_A: sendMessage(chainId, message)
  L2SBA-->L2SBA: emit SentERC20(tokenAddr, from, to, amount, destination)
  Intermediate_A->>Messenger_A: sendMessage(chainId, to, data)
  Inbox->>Messenger_B: relayMessage()
  Messenger_B->>L2SBB: relayERC20(tokenAddr, from, to, amount)
  L2SBB->>SuperERC20_B: mint(to, amount)
  Inbox->>Messenger_B: relayMessage(): call
  L2SBB-->L2SBB: emit RelayedERC20(tokenAddr, from, to, amount, source)
  Messenger_B->>to: call(data)
```

Adding the call to the standard would remove the dependence on the sequencer regarding the proper tx ordering
at the sequencer level, but would also introduce more risk for cross-chain fund transferring,
as an incorrectly formatted call would burn funds in the initiating chain but would revert
in destination and could never be successfully replayed.
