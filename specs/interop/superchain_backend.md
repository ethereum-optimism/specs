# Superchain Backend

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Message Safety](#message-safety)
- [Message Safety Resolution](#message-safety-resolution)
  - [Unsafe to Cross-Unsafe](#unsafe-to-cross-unsafe)
  - [Cross-Unsafe to (Safe|Finalized)](#cross-unsafe-to-safefinalized)

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

This method MUST enforce the [Identifier](./messaging.md#message-identifier)'s chainId is present in the chain's
[dependency set](./dependency_set.md).

This method MUST enforce the attributes listed in the [Identifier](./messaging.md#message-identifier) matches the log
and block attributes returned by peer's `eth_getLogs` request with the `blockNumber` and `logIndex` parameters.

This method MUST enforce the provided payload matches the bytes computed when
constructing the [MessagePayload](./messaging.md#message-payload) against the fetched log.

This method MUST return the applicable [safety label](./verifier.md#safety) for the message, or `Invalid` upon failures.

This method MUST NOT enforce the [timestamp invariant](./messaging.md#timestamp-invariant) on the provided messages. The
block builders and verifiers must locally do so based on their configured level of safety.

## Message Safety Resolution

### Unsafe to Cross-Unsafe

In order to discern between unsafe and cross-unsafe blocks, the backend maintains a graph of
dependencies between blocks can include interop messages between them.

We describe a psuedo-implementation of cross-unsafe message resolution using this graph. Every node in
this graph represents a block with edges representing the dependent relationship between them. Upon
receipt of unsafe payloads, the graph is extended with edges added on detection of interop transactions.

```python
## Graph Nodes
blocks = dict() # (hash) -> block
number_to_block_hash = dict() # (chain_id, int) -> hash
latest_blocks = dict() # (chain_id) -> hash

## Graph Edge
##   - The initiating side is represented with the block number since the corresponding payload may
##   not have been seen at the time the executing message has been processed.
dependents = dict() # (initiating_chain_id, block_number) -> List[(executing_chain_id, block_hash)]
dependencies = dict() # (executing_chain_id, block_hash) -> List[(initiating_chain_id, block_number)]

class Block:
    chain_id: int
    number: int
    parent: Block

    executing_messages: List[(MsgId, MsgPayload)]
    unverified_msg_ref_count: int

def block_safety(chain_id, block_hash):
    block = blocks[block_hash]
    if block.unverified_msg_ref_count > 0:
        return UNSAFE

    ## All messages were validated but we also need to ensure all
    ## transitive block dependencies have had their messages also
    ## validated
    for initiating_chain_id, block_number in dependencies[(chain_id, block_hash)]:
        if block_bumber > latest_heights[tx.msg_origin]:
            return UNSAFE

        dependency_block = blocks[number_to_block_hash[(initiating_chain_id, block_number)]]
        if block_safety(initiating_chain_id, dependency_block.hash) == UNSAFE:
            return UNSAFE

    return CROSS_UNSAFE

def add_unsafe_payload(chain_id, payload):
    # **Out of Scope** unsafe reorg handling
    require(payload.number == blocks[latest_blocks[chain_id]].number + 1)

    blocks[payload.hash] = Block(payload)
    latest_blocks[chain_id] = payload.hash

    # add edges
    for tx in blocks[payload.hash].executing_txs:
        dependents[(tx.msg_origin, tx.block_number)].add((chain_id, payload.hash))
        dependencies[(chain_id, payload.hash)].add((tx.msg_origin, tx.block_number))

    # try resolve any messages for this block
    resolve_unverified_messages(chain_id, payload.hash);

    # for existing dependents, trigger resolution
    for executing_chain_id, block_hash in dependents[(chain_id, payload.number)]:
        resolve_unverified_messages(executing_chain_id, payload.hash);

def resolve_unverified_messages(chain_id, block_hash):
    block = blocks[block_hash]
    for tx in block.executing_txs:
        if tx.msg_block_number > latest_heights[tx.msg_origin]:
            continue

        if is_valid_executing_message(tx):
            block.unverified_msg_ref_counts -= 1
        else:
            handle_invalidation(chain_id, block_hash);

def handle_invalidation(chain_id, block_hash):
    block = blocks[block_hash]
    if block.hash == latest_blocks[chain_id]:
        latest_blocks[chain_id] = block.parent

    ## Note: There's a chance that a replacement block includes the same
    ## initiated message at the same tx index but we'll eagerly process
    ## the invalidation for simplicity.

    # invalidate the dependent blocks
    for executing_chain_id, block_hash in dependents[(chain_id, block.number)]:
        handle_invalidation(executing_chain_id, block_hash)
        dependencies[(executing_chain_id, block_hash)].pop((chain_id, block.number))

    delete(blocks[block_hash)
    delete(dependents[(chain_id, block.number)])
```

### Cross-Unsafe to (Safe|Finalized)

Along with the unsafe payloads, the backend should also maintain the safe heads of the
chains in the graph to ensure progression of the dependency graph. Per the [spec](./verifier.md#safety),
`block_safety()` can be extended to appropriately return the `safe` safety label when all relevant cross-unsafe
data has been posted to L1.

Independent of the graph, the `finalized` safety label of the local chain strictly follows L1.
