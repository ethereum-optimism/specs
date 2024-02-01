# Interoperability

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [The Dependency Set](#the-dependency-set)
  - [Chain ID](#chain-id)
- [Interop Network Upgrade](#interop-network-upgrade)
- [Derivation Pipeline](#derivation-pipeline)
  - [Depositing an Executing Message](#depositing-an-executing-message)
  - [Safety](#safety)
- [State Transition Function](#state-transition-function)
- [Predeploys](#predeploys)
  - [CrossL2Inbox](#crossl2inbox)
    - [Invariants](#invariants)
      - [Timestamp Invariant](#timestamp-invariant)
      - [ChainID Invariant](#chainid-invariant)
      - [Only EOA Invariant](#only-eoa-invariant)
    - [Executing Messages](#executing-messages)
      - [`_target`](#_target)
      - [`_msg`](#_msg)
      - [`_id`](#_id)
  - [L2ToL2CrossDomainMessenger](#l2tol2crossdomainmessenger)
    - [Versioning](#versioning)
    - [Transferring Ether in a Cross Chain Message](#transferring-ether-in-a-cross-chain-message)
    - [Interfaces](#interfaces)
      - [Sending Messages](#sending-messages)
      - [Relaying Messages](#relaying-messages)
  - [L1Block](#l1block)
- [SystemConfig](#systemconfig)
  - [`DEPENDENCY_SET` UpdateType](#dependency_set-updatetype)
- [L1Attributes](#l1attributes)
- [Fault Proof](#fault-proof)
- [Sequencer Policy](#sequencer-policy)
- [Block Building](#block-building)
- [Sponsorship](#sponsorship)
- [Security Considerations](#security-considerations)
  - [Forced Inclusion of Cross Chain Messages](#forced-inclusion-of-cross-chain-messages)
  - [Cross Chain Message Latency](#cross-chain-message-latency)
  - [Dynamic Size of L1 Attributes Transaction](#dynamic-size-of-l1-attributes-transaction)
  - [Maximum Size of the Dependency Set](#maximum-size-of-the-dependency-set)
  - [Mempool](#mempool)
  - [Reliance on History](#reliance-on-history)
  - [Cyclic Dependencies in the Dependency Set](#cyclic-dependencies-in-the-dependency-set)
  - [Light Client Proofs](#light-client-proofs)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The ability for a blockchain to easily read the state of another blockchain is called interoperability.
Low latency interoperability allows for horizontally scalable blockchains, a key feature of the superchain.

Note: this document references an "interop network upgrade" as a temporary name. The actual name of the
network upgrade will be included in this document in the future.

| Term          | Definition                                               |
|---------------|----------------------------------------------------------|
| Source Chain   | A blockchain that includes an initiating message |
| Destination Chain  | A blockchain that includes an executing message |
| Initiating Message | A transaction submitted to a source chain that emits an event |
| Executing Message | A transaction submitted to a destination chain that corresponds to an initiating message |
| Cross Chain Message | The cumulative execution and side effects of the initiating message and executing message |
| Dependency Set | The set of chains that originate initiating transactions where the executing transactions are valid |

A total of two transactions are required to complete a cross chain message. The first transaction is submitted
to the source chain which authorizes execution on a destination chain. The second transaction is submitted to a
destination chain, where the block builder SHOULD only include it if they are certain that the first transaction was
included in the source chain.

The term "block builder" is used interchangeably with the term "sequencer" for the purposes of this document but they need not be the same
entity in practice.

## The Dependency Set

The dependency set defines the set of chains that a destination chains allows as source chains. Another way of
saying it is that the dependency set defines the set of initiating messages that are valid for an executing
message to be included. An executing message MUST have an initiating message that is included in a chain
in the dependency set.

The dependency set is defined by chain id. Since it is impossible to enforce uniqueness of chain ids,
social consensus MUST be used to determine the chain that represents the canonical chain id. This
particularly impacts the block builder as they SHOULD use the chain id to assist in validation
of executing messages.

The chainid of the local chain MUST be considered as part of its own dependency set.

### Chain ID

The concept of a chain id was introduced in [EIP-155](https://eips.ethereum.org/EIPS/eip-155) to prevent
replay attacks between chains. This EIP does not specify the max size of a chain id, although
[EIP-2294](https://eips.ethereum.org/EIPS/eip-2294) attempts to add a maximum size. Since this EIP is
stagnant, all representations of chain ids MUST be the `uint256` type.

## Interop Network Upgrade

The interop network upgrade timestamp defines the timestamp at which all functionality in this document is considered
the consensus rules for an OP Stack based network. On the interop network upgrade block, a set of deposit transaction
based upgrade transactions are deterministically generated by the derivation pipeline in the following order:

- L1 Attributes Transaction calling `setL1BlockValuesEcotone`
- User deposits from L1
- Network Upgrade Transactions
  - L1Block deployment
  - CrossL2Inbox deployment
  - L2ToL2CrossDomainMessenger deployment
  - Update L1Block Proxy ERC-1967 Implementation Slot
  - Update CrossL2Inbox Proxy ERC-1967 Implementation Slot
  - Update L2ToL2CrossDomainMessenger Proxy ERC-1967 Implementation Slot
  - Mint Cross Chain Ether Liquidity in L2ToL2CrossDomainMessenger

The execution payload MUST set `noTxPool` to `false` for this block.

The exact definitions for these upgrade transactions are still to be defined.

## Derivation Pipeline

The derivation pipeline enforces invariants on safe blocks that include executing messages.

- The executing message MUST have a corresponding initiating message
- The initiating message that corresponds to an executing message MUST come from a chain in its dependency set

Blocks that contain transactions that relay cross domain messages to the destination chain where the
initiating transaction does not exist MUST be considered invalid and MUST not be allowed by the
derivation pipeline to be considered safe.

There is no concept of replay protection at the lowest level of abstractions within the protocol because
there is no replay protection mechanism that fits well for all applications. Users MAY submit an
arbitrary number of executing messages per initiating message. This greatly simplifies the protocol and allows for
applications to build application specific replay protection.

### Depositing an Executing Message

TODO: reword this

Deposit transactions (force inclusion transactions) give censorship resistance to layer two networks.
The derivation pipeline must gracefully handle the case in which a user uses a deposit transaction to
relay a cross chain message. To not couple preconfirmation security to consensus, deposit transactions
that relay cross chain messages MUST have an initiating message that is considered safe by the remote
chain's derivation pipeline. This means that the remote chain's data including the initiating message
MUST be posted to the data availability layer. This relaxes a strict synchrony assumption on the sequencer
that it MUST have all unsafe blocks of destination chains as fast as possible to ensure that it is building
correct blocks. It also prevents a class of attacks where the user can send an executing message before the
initiating message and trick the derivation pipeline into reorganizing the sequencer.

### Safety

TODO: introduce new level of safety

The initiating messages for all executing messages MUST be resolved as safe before an L2 block can transition from being unsafe to safe.
Users MAY optimistically accept unsafe blocks without any verification of the executing messages. They SHOULD optimistically verify
the initiating messages exist in destination unsafe blocks to more quickly reorganize out invalid blocks.

## State Transition Function

After the full execution of a block, the set of [logs][log] that are emitted MUST be merklized and included in the block header.
This commitment MUST be included as the block header's [extra data field][block-extra-data]. The events are serialized with using
[Simple Serialize][ssz] aka SSZ.

[block-extra-data]: https://github.com/ethereum/execution-specs/blob/1fed0c0074f9d6aab3861057e1924411948dc50b/src/ethereum/frontier/fork_types.py#L115
[ssz]: https://github.com/ethereum/consensus-specs/blob/dev/ssz/simple-serialize.md

| Name          | Value |
|---------------|-------------------------------------|
| `MAX_LOG_DATA_SIZE` | `uint64(2**24)` or 16,777,216 |
| `MAX_MESSAGES_PER_BLOCK` | `uint64(2**20)` or 1,048,576 |

```python
class Log(Container):
    address: ExecutionAddress
    topics: List[bytes32, 4]
    data: ByteList[MAX_LOG_DATA_SIZE]
    transaction_hash: bytes32
    transaction_index: uint64
    log_index: uint64

logs = List[Log, MAX_MESSAGES_PER_BLOCK](
  log_0, log_1, log_2, ...)

block.extra_data = logs.hash_tree_root()
```

## Predeploys

Two new system level predeploys are introduced for managing cross chain messaging along with
an update to the `L1Block` contract with additional functionality.

### CrossL2Inbox

Address: `0x4200000000000000000000000000000000000022`

The `CrossL2Inbox` is responsible for executing a cross chain message on the destination chain.
It is permissionless to execute a cross chain message on behalf of any user. Certain protocol
enforced invariants must be preserved to ensure safety of the protocol.

#### Invariants

- The timestamp of executing message MUST be greater than or equal to the timestamp of the initiating message
- The chain id of the initiating message MUST be in the dependency set
- The executing message MUST be initiated by an externally owned account such that the top level EVM call frame enters the `CrossL2Inbox`

##### Timestamp Invariant

The timestamp invariant ensures that initiating messages cannot come from a future block. Note that since all transactions in a block
have the same timestamp, it is possible for an executing transaction to be ordered before the initiating message in the same block.

##### ChainID Invariant

Without a guarantee on the set of dependencies of a chain, it may be impossible for the derivation pipeline to know which
chain to source the initiating message from.

##### Only EOA Invariant

The `onlyEOA` invariant on executing a cross chain message enables static analysis on executing messages.
This allows for the derivation pipeline and block builders to reject executing messages that do not
have a corresponding initiating message without needing to do any EVM execution.

It may be possible to relax this invariant in the future if the block building process is efficient
enough to do full simulations to gain the information required to verify the existence of the
initiating transaction. Instead of the `Identifier` being included in calldata, it would be emitted
in an event that can be used after the fact to verify the existence of the initiating message.
This adds complexity around mempool inclusion as it would require EVM execution and remote RPC
access to learn if a transaction can enter the mempool.

This feature could be added by adding a new function to the `CrossL2Inbox`.

One possible way to handle explicit denial of service attacks is to utilize identity
in iterated games such that the block builder can ban identities that submit malicious transactions.

#### Executing Messages

All of the information required to satisfy the invariants MUST be included in the calldata
of the function that is used to execute messages. Both the block builder and the smart contract use
this information to ensure that all system invariants are held.

The following fields are required for executing a cross chain message:

| Name          | Type | Description |
|---------------|----------------------------------|--|
| `_target` | `address` | Account that is called with `_msg`|
| `_msg` | `bytes` | An opaque [Log][log] |
| `_id` | `Identifier` | A pointer to the `_msg` in a remote chain |

[log]: https://github.com/ethereum/go-ethereum/blob/5c67066a050e3924e1c663317fd8051bc8d34f43/core/types/log.go#L29

##### `_target`

An `address` that is specified by the caller. There is no protocol enforcement on what this value is. The
`_target` is called with the `_msg`. In practice, the `_target` will be a contract that needs to know the
schema of the `_msg` so that it can be decoded. It SHOULD call back to the `CrossL2Inbox` to authenticate
properties about the `_msg` using the information in the `Identifier`.

##### `_msg`

Opaque `bytes` that represent a [Log][log]. The data is verified against the `Identifier`. It is serialized
by first concatenating the topics and then with the data.

```go
msg := make([]byte, 0)
for _, topic := range log.Topics {
    msg = append(msg, topic.Bytes()...)
}
msg = append(msg, log.Data...)
```

The `_msg` can easily be decoded into a Solidity `struct` with `abi.decode` since each topic is always 32 bytes and
the data generally ABI encoded.

##### `_id`

The `Identifier` that uniquely represents a log that is emitted from a chain. It can be considered to be a 
unique pointer to a particular log. The derivation pipeline and fault proof program MUST ensure that the
`_msg` corresponds exactly to the log that the `Identifier` points to.

```solidity
struct Identifier {
    address origin;
    uint256 blocknumber;
    uint256 logIndex;
    uint256 timestamp;
    uint256 chainid;
}
```

| Name          | Type | Description |
|---------------|----------------------------------|--|
| `origin` | `address` | Account that emits the log |
| `blocknumber` | `uint256` | Block number in which the log was emitted |
| `logIndex` | `uint256` | The index of the log in the array of all logs emitted in the block |
| `timestamp` | `uint256` | The timestamp that the log was emitted. Used to enforce the timestamt invariant |
| `chainid` | `uint256` | The chainid of the chain that emitted the log |

A simple implementation of the `executeMessage` function is included below.

```solidity
function executeMessage(address _target, bytes calldata _msg, Identifier calldata _id) public payable {
    require(msg.sender == tx.origin);
    require(_id.timestamp <= block.timestamp);
    require(L1Block.isInDependencySet(_id.chainid));

    assembly {
      tstore(ORIGIN_SLOT, _id.origin);
      tstore(BLOCKNUMBER_SLOT, _id.blocknumber)
      tstore(LOG_INDEX_SLOT, _id.logIndex)
      tstore(TIMESTAMP_SLOT, _id.timestamp)
      tstore(CHAINID_SLOT, _id.chainid)
    }

    bool success = SafeCall.call({
      _target: _target,
      _value: msg.value,
      _calldata: _msg
    });

    require(success);
}
```

By including the `Identifier` in the calldata, it makes static analysis much easier for block builders.
It is impossible to check that the `Identifier` matches the cross chain message on chain. If the block
builder includes a message that does not correspond to the `Identifier`, their block will be reorganized
by the derivation pipeline.

### L2ToL2CrossDomainMessenger

Address: `0x4200000000000000000000000000000000000024`

The `L2ToL2CrossDomainMessenger` is a higher level abstraction on top of the `CrossL2Inbox` that
provides features necessary for secure transfers of `ether` and ERC20 tokens between L2 chains.
Messages sent through the `L2ToL2CrossDomainMessenger` on the source chain receive both replay protection
as well as domain binding, ie the executing transaction can only be valid on a single chain.

#### Versioning

TODO: explicit description
Versioning is handled in the most significant bits of the nonce.

#### Transferring Ether in a Cross Chain Message

The `L2ToL2CrossDomainMessenger` MUST be initially set in state with an ether balance of `type(uint248).max`.
This initial balance exists to provide liquidity for cross chain transfers. It is large enough to always have
ether present to dispurse while still being able to accept inbound transfers of ether without overflowing.
The `L2ToL2CrossDomainMessenger` MUST only transfer out ether if the caller is the `L2ToL2CrossDomainMessenger`
from a source chain.

The `L2CrossDomainMessenger` is not updated to include the `L2ToL2CrossDomainMessenger` functionality because
there is no need to introduce complexity with L1 to L2 messages and the L2 to L2 liquidity.

#### Interfaces

The `L2ToL2CrossDomainMessenger` uses a similar interface to the `L2CrossDomainMessenger` but
the `_minGasLimit` is removed to prevent complexity around EVM gas introspection and the `_destination`
chain is included instead.

Naive implementations of sending messages and executing messages are included.

##### Sending Messages

The initiating message is represented by the following event:

```solidity
event SentMessage(bytes message) anonymous;
```

The `bytes` are an ABI encoded call to `relayMessage`. The event is defined as `anonymous` so that no topics are prefixed
to the abi encoded call.

An explicit `_destination` chain and `nonce` are used to ensure that the message can only be played on a single remote
chain a single time.

```solidity
function sendMessage(uint256 _destination, address _target, bytes calldata _message) external payable {
    bytes memory data = abi.encodeCall(L2ToL2CrossDomainMessenger.relayMessage, (_destination, nonce, msg.sender, _target, msg.value, _message));
    emit SentMessage(data);
    nonce++;
}
```

##### Relaying Messages

When relaying a message through the `L2ToL2CrossDomainMessenger`, it is important to require that the `_destination` equal to `block.chainid`
to ensure that the message is only valid on a single chain. The hash of the message is used for replay protection.

It is important to ensure that the source chain is in the dependency set of the destination chain, otherwise
it is possible to send a message that is not playable.

```solidity
function relayMessage(uint256 _destination, uint256 _nonce, address _sender, address _target, uint256 _value, bytes memory _message) external {
    require(msg.sender == address(CROSS_L2_INBOX));
    require(_destination == block.chainid);

    bytes32 messageHash = keccak256(abi.encode(_destination, _nonce, _sender, _target, _value, _message));
    require(sentMessages[messageHash] == false);

    xDomainMsgSender = _sender;

    bool success = SafeCall.call({
       _target: _target,
       _value: _value,
       _calldata: _message
    });

    require(success);

    xDomainMsgSender = Constants.DEFAULT_L2_SENDER;
    sentMessages[messageHash] = true;
}
```

### L1Block

The `L1Block` contract is updated to include the set of allowed chains. The L1 Atrributes transaction
sets the set of allowed chains. The `L1Block` contract MUST provide a public getter to check is a particular
chain is in the dependency set.

The `setL1BlockValuesInterop()` function MUST be called on every block after the interop upgrade block.
The interop upgrade block itself MUST include a call to `setL1BlockValuesEcotone`.

## SystemConfig

The `SystemConfig` is updated to manage the dependency set. The chain operator can add or remove chains from the dependency set
through the `SystemConfig`. A new `ConfigUpdate` event `UpdateType` enum is added that corresponds to a change in the dependency set.

The `SystemConfig` MUST enforce that the maximum size of the dependency set is `type(uint8).max` or 255.

### `DEPENDENCY_SET` UpdateType

When a `ConfigUpdate` event is emitted where the `UpdateType` is `DEPENDENCY_SET`, the L2 network will update its dependency set.
The chain operator SHOULD be able to add or remove chains from the dependency set.

## L1Attributes

The L1 Atrributes transaction is updated to include the dependency set. Since the dependency set is dynamically sized,
a `uint8` "interopSetSize" parameter prefixes tightly packed `uint256` values that represent each chain id.

| Input arg         | Type                    | Calldata bytes          | Segment |
| ----------------- | ----------------------- | ----------------------- | --------|
| {0x760ee04d}      | bytes4                  | 0-3                     | n/a     |
| baseFeeScalar     | uint32                  | 4-7                     | 1       |
| blobBaseFeeScalar | uint32                  | 8-11                    |         |
| sequenceNumber    | uint64                  | 12-19                   |         |
| l1BlockTimestamp  | uint64                  | 20-27                   |         |
| l1BlockNumber     | uint64                  | 28-35                   |         |
| basefee           | uint256                 | 36-67                   | 2       |
| blobBaseFee       | uint256                 | 68-99                   | 3       |
| l1BlockHash       | bytes32                 | 100-131                 | 4       |
| batcherHash       | bytes32                 | 132-163                 | 5       |
| interopSetSize    | uint8                   | 164-165                 | 6       |
| chainIds          | [interopSetSize]uint256 | 165-(32*interopSetSize) | 6+      |

## Fault Proof

TODO: need more detail

No changes to the dispute game bisection are required. The only changes required are to the fault proof program itself.
The insight is that the fault proof program can be a superset of the state transition function.

## Sequencer Policy

The sequencer can include executing messages that have corresponding initiating messages
that only have preconfirmation levels of security if they trust the destination sequencer. Using an
allowlist and identity turns sequencing into an interated game which increases the ability for
sequencers to trust each other. Better preconfirmation technology will help to scale the sequencer
set to untrusted actors.

## Block Building

The goal is to present information in a way where it is as cheap as possible for the block builder to only include
executing messages that have a corresponding initiating message.

The block builder SHOULD use static analysis on executing messages to verify that the initiating
message exists. When a transaction has a top level [to][tx-to] field that is equal to the `CrossL2Inbox`
and the 4byte selector in the calldata matches the entrypoint interface,
the block builder should use the chain id that is encoded in the `Identifier` to know which chain includes the initiating
transaction. The block builder MAY require cryptographic proof of the existence of the log that the identifier points to.
The block build MAY also trust a remote RPC and use the following algorithm to verify the existence of the log.

The following pseudocode represents how to check existence of a log based on an `Identifier`.

```python
target, message, id = abi.decode(calldata)

eth = clients[id.chainid]

logs = eth.getLogs(id.origin, from=id.blocknumber, to=id.blocknumber)
log = filter(lambda x: x.index == id.logIndex)
if len(log) == 0:
  return False

if message != encode(log):
  return False

block = eth.getBlockByNumber(id.blocknumber)

if id.timestamp != block.timestamp:
  return False

return True
```

[tx-to]: https://github.com/ethereum/execution-specs/blob/1fed0c0074f9d6aab3861057e1924411948dc50b/src/ethereum/frontier/fork_types.py#L52

## Sponsorship

If a user does not have ether to pay for the gas of an executing message, application layer sponsorship solutions can be created.
It is possible to create an MEV incentive by paying `tx.origin` in the executing message. This can be done by wrapping the
`L2ToL2CrossDomainMessenger` with a pair of relaying contracts.

## Security Considerations

### Forced Inclusion of Cross Chain Messages

The design is particular to not introduce any sort of "forced inclusion" between L2s. This design space introduces
risky synchrony assumptions and forces the introduction of a message queue to prevent denial of service attacks where
all chains in the network decide to send cross chain messages to the same chain at the same time.

"Forced inclusion" transactions are good for censorship resistance. In the worst case of censoring sequencers, it will
take at most 2 sequencing windows for the cross chain message to be processed. The initiating transaction can be sent
via a deposit which MUST be included in the source chain or the sequencer will be reorganized at the end of the sequencing
window that includes the deposit transaction. If the executing transaction is censored, it will take another sequencing window
of time to force the inclusion of the executing message per the [spec][depositing-an-executing-message].

TODO: verify exact timing of when reorg happens with deposits that are skipped

[depositing-an-executing-message]: #depositing-an-executing-message

### Cross Chain Message Latency

The latency at which a cross chain message is relayed from the moment at which it was initiated is bottlenecked by
the security of the preconfirmations. An initiating transaction and a executing transaction MAY have the same timestamp,
meaning that a secure preconfirmation scheme enables atomic cross chain composability. Any sort of equivocation on behalf
of the sequencer will result in the production of invalid blocks.

### Dynamic Size of L1 Attributes Transaction

The L1 Attributes transaction includes the dependency set which is dynamically sized. This means that
the worst case (largest size) transaction must be accounted for when ensuring that it is not possible
to create a block that has force inclusion transactions that go over the L2 block gas limit.
It MUST be impossible to produce an L2 block that consumes more than the L2 block gas limit.
Limiting the dependency set size is an easy way to ensure this.

### Maximum Size of the Dependency Set

The maximum size of the dependency set is constrained by the L2 block gas limit. The larger the dependency set,
the more costly it is to fully verify the network. It also makes the block building role more centralized
as it requires more hardware to verify executing transactions before inclusion.

### Mempool

Since the validation of the execuing message relies on a remote RPC request, this introduces a denial of
service attack vector. The cost of network access is magnitudes larger than in memory validity checks.
The mempool SHOULD perform cheaper checks before any sort of network access is performed. The results
of the check SHOULD be cached such that another request does not need to be performed when building the
block although consistency is not guaranteed.

### Reliance on History

When fully executing historical blocks, a dependency on historical receipts from remote chains is present.
[EIP-4444][eip-4444] will eventually provide a solution for making historical receipts available without
needing to require increasingly large execution client databases.

It is also possible to introduce a form of expiry on historical receipts by enforcing that the timestamp
is recent enough in the `CrossL2Inbox`.

[eip-4444]: https://eips.ethereum.org/EIPS/eip-4444

### Cyclic Dependencies in the Dependency Set

TODO: verify that existing rules don't cause a halt

If there is a cycle in the dependency set, chains MUST still be able to promote unsafe blocks
to safe blocks. A cycle in the dependency set happens anytime that two chains are in each other's
dependency set. This means that they are able to send cross chain messages to each other.
To promote unsafe blocks, the L2 data must be published to the data availability layer and
any executing messages MUST have their initiating messages verified. This process must happen
recursively for interconnected chains.

### Light Client Proofs

TODO: light client that follows remote blockhashes from L1 batches
