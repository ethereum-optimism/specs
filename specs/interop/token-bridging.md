# Token Bridging

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [`SuperchainERC20` standard](#superchainerc20-standard)
  - [Properties](#properties)
  - [`IERC7802`](#ierc7802)
    - [`crosschainMint`](#crosschainmint)
    - [`crosschainBurn`](#crosschainburn)
    - [`CrosschainMint`](#crosschainmint)
    - [`CrosschainBurn`](#crosschainburn)
- [`SuperchainTokenBridge`](#superchaintokenbridge)
- [Diagram](#diagram)
- [Implementation](#implementation)
- [Future Considerations](#future-considerations)
  - [Cross Chain `transferFrom`](#cross-chain-transferfrom)
  - [Concatenated Action](#concatenated-action)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

Without a standardized security model, bridged assets may not be fungible with each other.
The `SuperchainERC20` standard is a set of properties and an interface allowing ERC20 to be fungible across the
Superchain using the official `SuperchainTokenBridge`.
The `SuperchainTokenBridge` is a predeploy that builds on the messaging protocol as the most trust-minimized bridging solution.

## `SuperchainERC20` standard

### Properties

The standard will build on top of ERC20, implement the
[`IERC7802`](https://github.com/ethereum/ERCs/pull/692)
interface, and include the following properties:

1. Implement the [ERC20](https://eips.ethereum.org/EIPS/eip-20) interface
2. Implement the [`ERC7802`](https://github.com/ethereum/ERCs/pull/692) interface
3. Allow [`SuperchainTokenBridge`](./predeploys.md#superchaintokenbridge) to call
   [`crosschainMint`](#crosschainmint) and [`crosschainBurn`](#crosschainburn).
4. Be deployed at the same address on every chain in the Superchain.

The third property will allow the `SuperchainTokenBridge` to have a liquidity guarantee,
which would not be possible in a model based on lock/unlock.
Liquidity availability is fundamental to achieving fungibility.

SuperchainTokenBridge does not have to be the exclusive caller of `crosschainMint` and `crosschainBurn`;
other addresses may also be permitted to call these functions.

The fourth property removes the need for cross-chain access control lists.
Otherwise, the `SuperchainTokenBridge` would need a way to verify if the tokens it mints on
destination correspond to the tokens that were burned on source.
Same address abstracts away cross-chain validation.

One way to guarantee the same address across the Superchain (and also bind it to the same `init_code`
and constructor arguments) is to use the
[`Create2Deployer` preinstall](../protocol/preinstalls.md#create2deployer).
There is also the [`OptimismSuperchainERC20Factory`](predeploys.md#optimismmintableerc20factory)
predeploy that facilitates this process for L1 native tokens.

Notice that ERC20s that do not implement the standard can still be fungible
using interop message passing
using a custom bridge or implementing `sendERC20` and `relayERC20` on their own contracts.

An example implementation of the standard is available at [SuperchainERC20.sol](https://github.com/ethereum-optimism/optimism/blob/develop/packages/contracts-bedrock/src/L2/SuperchainERC20.sol)

### `IERC7802`

Implementations of the `SuperchainERC20` standard will
be required to implement the `IERC7802` interface,
that includes two external functions and two events:

#### `crosschainMint`

Mints `_amount` of token to address `_account`.

```solidity
crosschainMint(address _account, uint256 _amount)
```

#### `crosschainBurn`

Burns `_amount` of token from address `_account`.

```solidity
crosschainBurn(address _account, uint256 _amount)
```

#### `CrosschainMint`

MUST trigger when `crosschainMint` is called

```solidity
event CrosschainMint(address indexed _to, uint256 _amount, address indexed _sender)
```

#### `CrosschainBurn`

MUST trigger when `crosschainBurn` is called

```solidity
event CrosschainBurn(address indexed _from, uint256 _amount, address indexed _sender)
```

## `SuperchainTokenBridge`

The `SuperchainTokenBridge` is a predeploy that works as an abstraction
on top of the [L2ToL2CrossDomainMessenger][l2-to-l2]
for token bridging.
The `L2ToL2CrossDomainMessenger` is used for replay protection,
domain binding and access to additional message information.
The `SuperchainTokenBridge` includes two functions for bridging:

- `sendERC20`: initializes a cross-chain transfer of a `SuperchainERC20`
  by burning the tokens locally and sending a message to the `SuperchainTokenBridge`
  on the target chain using the `L2toL2CrossDomainMessenger`.
  Additionally, it returns the `msgHash_` crafted by the `L2toL2CrossDomainMessenger`.
- `relayERC20`: processes incoming messages from the `L2toL2CrossDomainMessenger`
  and mints the corresponding amount of the `SuperchainERC20`.

The full specifications and invariants are detailed
in the [predeploys spec](./predeploys.md#superchaintokenbridge).

[l2-to-l2]: ./predeploys.md#l2tol2crossdomainmessenger

## Diagram

The following diagram depicts a cross-chain transfer.

```mermaid
---
config:
  theme: dark
  fontSize: 48 
---
sequenceDiagram
  participant from
  participant L2SBA as SuperchainTokenBridge (Chain A)
  participant SuperERC20_A as SuperchainERC20 (Chain A)
  participant Messenger_A as L2ToL2CrossDomainMessenger (Chain A)
  participant Inbox as CrossL2Inbox
  participant Messenger_B as L2ToL2CrossDomainMessenger (Chain B)
  participant L2SBB as SuperchainTokenBridge (Chain B)
  participant SuperERC20_B as SuperchainERC20 (Chain B)

  from->>L2SBA: sendERC20(tokenAddr, to, amount, chainID)
  L2SBA->>SuperERC20_A: crosschainBurn(from, amount)
  SuperERC20_A-->SuperERC20_A: emit CrosschainBurn(from, amount, sender)
  L2SBA->>Messenger_A: sendMessage(chainId, message)
  Messenger_A->>L2SBA: return msgHash_
  L2SBA-->L2SBA: emit SentERC20(tokenAddr, from, to, amount, destination)
  L2SBA->>from: return msgHash_
  Inbox->>Messenger_B: relayMessage()
  Messenger_B->>L2SBB: relayERC20(tokenAddr, from, to, amount)
  L2SBB->>SuperERC20_B: crosschainMint(to, amount)
  SuperERC20_B-->SuperERC20_B: emit CrosschainMint(to, amount, sender)
  L2SBB-->L2SBB: emit RelayedERC20(tokenAddr, from, to, amount, source)
```

## Implementation

An example implementation for the `sendERC20` and `relayERC20` functions is provided.

```solidity
function sendERC20(SuperchainERC20 _token, address _to, uint256 _amount, uint256 _chainId) external returns (bytes32 msgHash_) {
  _token.crosschainBurn(msg.sender, _amount);

  bytes memory _message = abi.encodeCall(this.relayERC20, (_token, msg.sender, _to, _amount));

  msgHash_ = L2ToL2CrossDomainMessenger.sendMessage(_chainId, address(this), _message);

  emit SentERC20(address(_token), msg.sender, _to, _amount, _chainId);
}

function relayERC20(SuperchainERC20 _token, address _from, address _to, uint256 _amount) external {
  require(msg.sender == address(L2ToL2CrossChainMessenger));
  require(L2ToL2CrossChainMessenger.crossDomainMessageSender() == address(this));

  uint256 _source = L2ToL2CrossChainMessenger.crossDomainMessageSource();

  _token.crosschainMint(_to, _amount);

  emit RelayedERC20(address(_token), _from, _to, _amount, _source);
}
```

## Future Considerations

### Cross Chain `transferFrom`

In addition to standard locally initialized bridging,
it is possible to allow contracts to be cross-chain interoperable.
For example, a contract in chain A could send pre-approved funds
from a user in chain B to a contract in chain C.

For the moment, the standard will not include any specific functionality
to facilitate such an action and rely on the usage of `Permit2` like this:

```mermaid
---
config:
  theme: dark
  fontSize: 48 
---
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

This approach has great potential but can also be achieved outside the standard in the following way:

```mermaid
---
config:
  theme: dark
  fontSize: 48 
---
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
  L2SBA->>SuperERC20_A: crosschainBurn(from, amount)
  SuperERC20_A-->SuperERC20_A: emit CrosschainBurn(from, amount, sender)
  L2SBA->>Messenger_A: sendMessage(chainId, message)
  L2SBA-->L2SBA: emit SentERC20(tokenAddr, from, to, amount, destination)
  Intermediate_A->>Messenger_A: sendMessage(chainId, to, data)
  Inbox->>Messenger_B: relayMessage()
  Messenger_B->>L2SBB: relayERC20(tokenAddr, from, to, amount)
  L2SBB->>SuperERC20_B: crosschainMint(to, amount)
  SuperERC20_B-->SuperERC20_B: emit CrosschainMint(to, amount, sender)
  Inbox->>Messenger_B: relayMessage(): call
  L2SBB-->L2SBB: emit RelayedERC20(tokenAddr, from, to, amount, source)
  Messenger_B->>to: call(data)
```

Adding the call to the standard would remove the dependence on the sequencer for
proper transaction ordering at the sequencer level.
However, it would also introduce additional risks for cross-chain fund transfers.
Specifically, an incorrectly formatted call could burn funds on the initiating chain,
but revert on the destination chain, and could never be successfully replayed.
