# Messaging

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Message](#message)
  - [Message payload](#message-payload)
  - [Message Identifier](#message-identifier)
- [Messaging ends](#messaging-ends)
  - [Initiating Messages](#initiating-messages)
  - [Executing Messages](#executing-messages)
- [Messaging Invariants](#messaging-invariants)
  - [Timestamp Invariant](#timestamp-invariant)
  - [ChainID Invariant](#chainid-invariant)
  - [Only EOA Invariant](#only-eoa-invariant)
  - [Message Expiry](#message-expiry)
- [Message dependency resolution](#message-dependency-resolution)
- [Security Considerations](#security-considerations)
  - [Cyclic dependencies](#cyclic-dependencies)
  - [Transitive dependencies](#transitive-dependencies)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Message

A message is a [broadcast payload](#message-payload) emitted from an [identified source](#message-identifier).

### Message payload

Opaque `bytes` that represent a [Log][log].

It is serialized by first concatenating the topics and then with the data.

```go
msg := make([]byte, 0)
for _, topic := range log.Topics {
    msg = append(msg, topic.Bytes()...)
}
msg = append(msg, log.Data...)
```

The `_msg` can easily be decoded into a Solidity `struct` with `abi.decode` since each topic is always 32 bytes and
the data generally ABI encoded.

### Message Identifier

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

| Name          | Type      | Description                                                                     |
|---------------|-----------|---------------------------------------------------------------------------------|
| `origin`      | `address` | Account that emits the log                                                      |
| `blocknumber` | `uint256` | Block number in which the log was emitted                                       |
| `logIndex`    | `uint256` | The index of the log in the array of all logs emitted in the block              |
| `timestamp`   | `uint256` | The timestamp that the log was emitted. Used to enforce the timestamp invariant |
| `chainid`     | `uint256` | The chainid of the chain that emitted the log                                   |

The `Identifier` includes the set of information to uniquely identify a log. When using an absolute
log index within a particular block, it makes ahead of time coordination more complex. Ideally there
is a better way to uniquely identify a log that does not add ordering constraints when building
a block. This would make building atomic cross chain messages more simple by not coupling the
exact state of the block templates between multiple chains together.

## Messaging ends

### Initiating Messages

[log]: https://github.com/ethereum/go-ethereum/blob/5c67066a050e3924e1c663317fd8051bc8d34f43/core/types/log.go#L29

Each Log (also known as `event` in solidity) forms an initiating message.
The raw log data froms the [Message Payload](#message-payload).

Messages are *broadcast*: the protocol does not enshrine address-targeting within messages.

The initiating message is uniquely identifiable with an [`Identifier`](#message-identifier),
such that it can be distinguished from other duplicate messages within the same transaction or block.

An initiating message may be executed many times: no replay-protection is enshrined in the protocol.

### Executing Messages

All the information required to satisfy the invariants MUST be included in the calldata
of the function that is used to execute messages.

Both the block builder and the verifier use this information to ensure that all system invariants are held.

The executing message is verified by checking if there is an existing initiating-message
that originates at [`Identifier`](#message-identifier) with matching [Message Payload](#message-payload).

## Messaging Invariants

- The timestamp of executing message MUST be greater than or equal to the timestamp of the initiating message
- The chain id of the initiating message MUST be in the dependency set
- The executing message MUST be initiated by an externally owned account such that the top level EVM
  call frame enters the `CrossL2Inbox`

### Timestamp Invariant

The timestamp invariant ensures that initiating messages cannot come from a future block. Note that since
all transactions in a block have the same timestamp, it is possible for an executing transaction to be
ordered before the initiating message in the same block.

### ChainID Invariant

Without a guarantee on the set of dependencies of a chain, it may be impossible for the derivation
pipeline to know which chain to source the initiating message from. This also allows for chain operators
to explicitly define the set of chains that they depend on.

### Only EOA Invariant

The `onlyEOA` invariant on executing a cross chain message enables static analysis on executing messages.
This allows for the derivation pipeline and block builders to reject executing messages that do not
have a corresponding initiating message without needing to do any EVM execution.

It may be possible to relax this invariant in the future if the block building process is efficient
enough to do full simulations to gain the information required to verify the existence of the
initiating transaction. Instead of the `Identifier` being included in calldata, it would be emitted
in an event that can be used after the fact to verify the existence of the initiating message.
This adds complexity around mempool inclusion as it would require EVM execution and remote RPC
access to learn if a transaction can enter the mempool.

This feature could be added in a backwards compatible way by adding a new function to the `CrossL2Inbox`.

One possible way to handle explicit denial of service attacks is to utilize identity
in iterated games such that the block builder can ban identities that submit malicious transactions.

### Message Expiry

TODO: define message expiry.

## Message dependency resolution

TODO: expand on initiating/executing messages and corresponding graph problem.

## Security Considerations

### Cyclic dependencies

If there is a cycle in the dependency set, chains MUST still be able to promote unsafe blocks
to safe blocks. A cycle in the dependency set happens anytime that two chains are in each other's
dependency set. This means that they are able to send cross chain messages to each other.

### Transitive dependencies

TODO
