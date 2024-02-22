<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Superchain Backend](#superchain-backend)
  - [Message Safety](#message-safety)
- [Optimism Transaction Pool Policies](#optimism-transaction-pool-policies)
  - [SuperchainMessagingPolicy](#superchainmessagingpolicy)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


## Superchain Backend

The superchain backend provides the methods available for both
the block builder and and verifier for message safety checks
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

The backend is instantiated per chain executing interop messages, maintaning a view
against the peers in it's [dependency set](./dependency_set.md).

### Message Safety

This method MUST enforce the [Identifier](./messaging.md#message-identifier)'s chainId is present in the chain's [dependency set](./dependency_set.md).

This method MUST enforce the attributes listed in the [Identifier](./messaging.md#message-identifier) matches the log & block attributes
returned by peer's `eth_getLogs` request with the `blockNumber` and `logIndex` parameters.

This method MUST enforce the provided payload matches the bytes computed when
constructing the [MessagePayload](./messaging.md#message-payload) against the fetched log.

This method MUST return the applicable [safety label](./verifier.md#safety) for the message, or `Invalid` 
upon failures.

This method MUST NOT enforce the [timestamp invariant](./messaging.md#timestamp-invariant) on the provided messages. The block builders
and verifiers must locally do so based on their configured level of safety.

## Optimism Transaction Pool Policies

The `OptimismTxPoolPolicy` is an abstraction provided to the execution engine to apply additional
logic to validation logic to the transaction pool.

```go
type OptimismTxPolicyStatus uint

const (
	OptimismTxPolicyInvalid OptimismTxPolicyStatus = iota
	OptimismTxPolicyValid
)

type OptimismTxPoolPolicy interface {
	ValidateTx(tx *types.Transaction) (OptimismTxPolicyStatus, error)
}
```
The block builder MUST discard transactions that is marked invalid by the set policy.

### SuperchainMessagingPolicy

This policy is an implementation of the interface adhering to the interop [message invariants](./messaging.md#messaging-invariants)
and the block-builder's configured [dependency confirmations](./sequencer.md#dependency-confirmations) requirement.

This policy MUST skip transactions that does not have a `to` field equal to the `CrossL2Inbox`
predeploy and `executeMessage` function selector.

This policy SHOULD leverage the [SuperchainBackend](#superchain-backend) to verify the integrity of the identifier and
message supplied as calldata to the transaction and obtain the correct safety label.

This policy MUST apply the [depedency confirmation](./sequencer.md#dependency-confirmationS) requirement relative to the retrieved safety
label for the message.
