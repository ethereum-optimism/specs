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
dependencies between blocks that can include interop messages between them.

We describe a psuedo-implementation of cross-unsafe message resolution using this graph. Every node in
this graph represents a block with edges representing the dependent relationship between them. Upon
receipt of unsafe blocks, the graph is extended with edges added on detection of interop transactions.

```python
## Graph Nodes
blocks = dict() # (hash) -> block

block_unverified_executing_messages = dict() # (hash) -> List[(MsgId, MsgPaylaod)]

chain_block_number_to_hash = dict() # (chain_id, int) -> hash
chain_block_head = dict() # (chain_id) -> hash

## Graph Edge
##   The initiating side is represented with the block number since the corresponding block may
##   not have been seen at the time the executing message has been processed.
dependents = dict() # (initiating_chain_id, block_number) -> List[(executing_chain_id, block_hash)]
dependencies = dict() # (executing_chain_id, block_hash) -> List[(initiating_chain_id, block_number)]

class Block:
    header: Header
    transactions: List[Transaction]

def parse_executing_messages(block: Block):
    """
    Extract all executing messages in this block
    """
    messages = []
    for tx in block.transactions:
        if is_executing_tx(tx):
            msg_id, payload = parse_executing_tx_data(tx.data)
            messages.append(msg_id, payload)
    return messages

def block_safety(chain_id: int, block_hash: Bytes32):
    """
    Return the safety level for a given block, Used by the message safety backend API
    to determine the safety of the remote block specified in the message identifier.
    """
    if len(block_unverified_executing_messages[block_hash]) > 0:
        return UNSAFE

    ## All messages were validated but we also need to ensure all transitive
    ## block dependencies have had their messages also validated
    for initiating_chain_id, block_number in dependencies[(chain_id, block_hash)]:

        # we should never reach here as `len(block_unverified_executing_messages[block_hash]) == 0`.
        if block.header.number > chain_block_head[initiating_chain_id].header.number:
            return UNSAFE

        # check that transitive blocks are not unsafe
        dependency_block = blocks[chain_block_number_to_hash[(initiating_chain_id, block_number)]]
        if block_safety(initiating_chain_id, dependency_block.header.hash) == UNSAFE:
            return UNSAFE

    return CROSS_UNSAFE

def add_unsafe_block(chain_id: int, block: Bytes32):
    """
    Extend the graph with a new block for the specified chain.
    - Called when receiving an unsafe block over p2p from the sequencer
    - Called when the safe head progress and the prior unsafe blocks was
      not propogated.

    For simplicity of this pseudocode, we exepct the caller to supply
    the expected height and leave out reorg handling when either a new
    unsafe block is supplied at the same height or the safe head mismatches
    with a previously added unsafe block.
    """
    require(block.header.number == blocks[chain_block_head[chain_id]].header.number + 1)
    require(block.header.parent_hash == chain_block_head[chain_id])

    blocks[block.header.hash] = block
    chain_block_head[chain_id] = block.header.hash

    executing_messages = parse_executing_messages(block)
    block_unverified_executing_messages[block.header.hash] = executing_messages

    # add a default edge for the parent block. Invalidation of the parent should
    # cascade to this block and the safety of this block also depends on the parent
    parent_block = blocks[block.header.parent_hash]
    dependents[(chain_id, block.header.number - 1)].add((chain_id, block.header.hash))
    dependencies[(chain_id, block.header.hash)].add((chain_id, block.header.number - 1))

    # add edges based on the executing messages present
    for msg_id, _ in executing_messages:
        # initiating block linked with the executing block
        dependents[(msg_id.chain_id, msg_id.block_number)].add((chain_id, block.header.hash))
        # executing block has a dependency on the initiating block
        dependencies[(chain_id, block.header.hash)].add((msg_id.origin, msg_id.block_number))

    # try resolve any messages for this block as some initiating blocks may be present
    resolve_unverified_messages(chain_id, block.header.hash)

    # for any existing dependents set, trigger resolution now that initiating data is available
    for executing_chain_id, block_hash in dependents[(chain_id, block.header.number)]:
        resolve_unverified_messages(executing_chain_id, block_hash)

def resolve_unverified_messages(chain_id, block_hash):
    """
    Check the validity of executing messages present in this block. If an invalid
    executing message is found, the block along with any dependent blocks are
    invalidated out of the graph.
    """
    unverified_executing_messages = block_unverified_executing_messages[block_hash]
    for msg_id, msg_payload in unverified_executing_messages:
        # this message is waiting on data
        if msg_id.block_number > chain_block_head[block_hash].header.number:
            continue

        if is_valid_executing_message(msg_id, msg_payload):
            unverified_executing_messages.pop((msg_id, msg_payload))
        else:
            handle_invalidation(chain_id, block_hash)

def handle_invalidation(chain_id, block_hash):
    """
    Invalidate a block from the graph. Invalidates dependent blocks as well

    Note: There's a chance that replacement blocks includes the same initiated message
    at the same tx index but we'll eagerly process the invalidation.
    """
    # set the parent as the new chain head. Any derived blocks from this will
    # also be invalidated in the next step via the dependents
    block = blocks[block_hash]
    chain_block_head[chain_id] = block.header.parent_hash

    # invalidate the dependent blocks
    for executing_chain_id, dependent_block_hash in dependents[(chain_id, block.header.number)]:
        handle_invalidation(executing_chain_id, dependent_block_hash)

        # remove dependencies as the dependency block deleted after invalidation
        delete(dependencies[(executing_chain_id, dependent_block_hash)])

    # remove block & dependents from the graph
    delete(blocks[block_hash)
    delete(dependents[(chain_id, block.number)])
```

### Cross-Unsafe to (Safe|Finalized)

Along with the unsafe blocks, the backend should also maintain the safe heads of the
chains in the graph to ensure progression of the dependency graph. Per the [spec](./verifier.md#safety),
`block_safety()` can be extended to appropriately return the `safe` safety label when all relevant cross-unsafe
data has been posted to L1.

Independent of the graph, the `finalized` safety label of the local chain strictly follows L1.
