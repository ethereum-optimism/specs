# Sequencer

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Sequencer Policy](#sequencer-policy)
- [Block Building](#block-building)
- [Sponsorship](#sponsorship)
- [Security Considerations](#security-considerations)
  - [Cross Chain Message Latency](#cross-chain-message-latency)
  - [Mempool](#mempool)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

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
the block builder should use the chain id that is encoded in the `Identifier` to know which chain includes
the initiating transaction. The block builder MAY require cryptographic proof of the existence of the log
that the identifier points to. The block build MAY also trust a remote RPC and use the following algorithm
to verify the existence of the log.

The following pseudocode represents how to check existence of a log based on an `Identifier`.

```python
target, message, id = abi.decode(calldata)

eth = clients[id.chainid]

if eth is None:
  return False

logs = eth.getLogs(id.origin, from=id.blocknumber, to=id.blocknumber)
log = filter(lambda x: x.index == id.logIndex)
if len(log) == 0:
  return False

if message != encode(log[0]):
  return False

block = eth.getBlockByNumber(id.blocknumber)

if id.timestamp != block.timestamp:
  return False

return True
```

[tx-to]: https://github.com/ethereum/execution-specs/blob/1fed0c0074f9d6aab3861057e1924411948dc50b/src/ethereum/frontier/fork_types.py#L52

## Sponsorship

If a user does not have ether to pay for the gas of an executing message, application layer sponsorship
solutions can be created. It is possible to create an MEV incentive by paying `tx.origin` in the executing
message. This can be done by wrapping the `L2ToL2CrossDomainMessenger` with a pair of relaying contracts.

## Security Considerations

### Cross Chain Message Latency

The latency at which a cross chain message is relayed from the moment at which it was initiated is bottlenecked by
the security of the preconfirmations. An initiating transaction and a executing transaction MAY have the same timestamp,
meaning that a secure preconfirmation scheme enables atomic cross chain composability. Any sort of equivocation on
behalf of the sequencer will result in the production of invalid blocks.

### Mempool

Since the validation of the execuing message relies on a remote RPC request, this introduces a denial of
service attack vector. The cost of network access is magnitudes larger than in memory validity checks.
The mempool SHOULD perform cheaper checks before any sort of network access is performed. The results
of the check SHOULD be cached such that another request does not need to be performed when building the
block although consistency is not guaranteed.
