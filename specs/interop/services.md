# Superchain Backend

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Message Safety](#message-safety)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

The superchain backend provides the methods available for both the block builder and
verifier for message safety checks. The backend can consumed over a JSON-RPC server,
with the methods exposed under the `superchain` namespace, or as a go libary.

```go
type MessageSafetyLabel int

const (
    Invalid MessageSafetyLabel = iota
    Unsafe
    CrossUnsafe
    Safe
    Finalized
)

type SuperchainBackend interface {
    MessageSafety(id Identifier, payload []byte) (MessageSafetyLabel, error)
}
```

The backend maintains a view against the local network & registered peers in the [dependency set](./dependency_set.md).

## Message Safety

This method MUST enforce the [Identifier](./messaging.md#message-identifier)'s chainId is present in the chain's [dependency set](./dependency_set.md).

This method MUST enforce the attributes listed in the [Identifier](./messaging.md#message-identifier) matches the log & block attributes
returned by peer's `eth_getLogs` request with the `blockNumber` and `logIndex` parameters.

This method MUST enforce the provided payload matches the bytes computed when
constructing the [MessagePayload](./messaging.md#message-payload) against the fetched log.

This method MUST return the applicable [safety label](./verifier.md#safety) for the message, or `Invalid`
upon failures.

This method MUST NOT enforce the [timestamp invariant](./messaging.md#timestamp-invariant) on the provided messages. The block builders
and verifiers must locally do so based on their configured level of safety.
