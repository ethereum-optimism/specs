# Fault Proof

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Security Considerations](#security-considerations)
  - [Cascading dependencies](#cascading-dependencies)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## `SuperRoot`

The `SuperRoot` is an aggregate proposal of L2 superchain state to L1,
from which other L2 activity can be proven.

The `SuperRoot` represents a snapshot of the superchain:
it aggregates the output-roots of individual L2 chains, aligned to a single global timestamp.

A `SuperSnapshot` is defined as the following SSZ data-structure:
```python
MAX_SUPERCHAIN_SIZE = 2**20 # the binary merkle-tree is 20 levels deep (excluding the SSZ length-mixin)

class SuperSnapshot(Container:
  chains: List[OutputRoot, MAX_SUPERCHAIN_SIZE]
  timestamp: uint64
```

For each `OutputRoot`, the corresponding L2 block must be the last `safe` `block` 
such that `block.timestamp <= snapshot.timestamp`.
Each `OutputRoot` must be a [version 1 output root](#output-root-version-1).

The output-roots must be ordered by ascending chain ID, with exactly one output-root
per L2 chain in the Superchain.

The `SuperRoot` is computed from SSZ hash-tree-root of the snapshot, versioned with a zero prefix byte:
`0x00 ++ hash_tree_root(super_snapshot)[1:]`,
where `||` is concatenation of bytes and `[1:]` slices out the first byte of the hash-tree-root.
The `hash_tree_root` is computed with the `keccak256` hash function rather than `SHA2` as in the beacon-chain,
for improved integration into the EVM.

The fault-proof is contained to the L1 view of the `SuperRoot` claim
(all L1 history up to and including the L1 timestamp when the claim was made),
and does not include later-included batch data.

## `OutputRoot` version 1

We adapt the output-root that commits to the state of an individual L2 like in "version 0",
but now extended with a `messages_root`.
The `messages_root` commits to accumulators of the initiating messages and executing messages.

```python
payload = state_root || withdrawal_storage_root || latest_block_hash || messages_root
version_byte = bytes32(uint256(1))  # Big-endian. Name is spec legacy, it is 32 bytes long.
output_root = keccak256(version_byte || payload)
```

## Bisection

No changes to the dispute game bisection are required.
The only changes required are to the [fault proof program](#program) itself.
The program interprets the bisection in a new way,
following the [Decision Tree](#decision-tree) to identify the sub-problem to prove.

### Entering the VM bisection

The bisection-game specifies a fixed-depth where the form of dispute changes from 
application-layer constructs to VM emulation.

Depth is defined such that `depth = 0` is the root of the tree, and each nested counter-claim increments the depth by 1.

Between depth 0 and the `SPLIT_DEPTH` (incl.) the claims represent chain constructs, such as output-roots.

From `SPLIT_DEPTH` to `MAX_DEPTH` the bisection claims represent pivots that commit to the VM-state
at the half-way point in the corresponding VM-execution-trace scope.

### Pivots in bisection

When bisecting the MIPS VM trace of Cannon, the concept of "Pivots" is used.

Pivots allow both sides of the game to argue about state snapshots in the trace,
without having to fully compute commitments for all intermediate states before or after the snapshots.

When a pivot is agreed upon, the intermediate steps that both sides took are irrelevant,
and a common pre-state is thus established quickly.

## Decision Tree

To facilitate interop between many chains, we interpret the bisection path to agree on a sub-problem to solve.
The decision-tree defines how the bisection path is interpreted, and thus how the sub-problem is identified.

The in-flight bisection identifies claims in two ways:
- relative their parent-claim, to facilitate a multi-player dispute game
- absolute to the root, to statically point to what is being disputed in the reference frame of the player.

The absolute identifier is typed as a [`Position`](../experimental/fault-proof/fault-dispute-game.md#position),
representing a generalized index, a unique number identifying the position in the binary tree.

From this position, we can derive a `depth`, and a `path`:
- The `depth` is the bisection-round relative to the root of the tree.
  This is the bit-length of the generalized index.
- The `path` is a bitfield, of left/right choices, one per `depth`,
  starting from the root of the bisection game, up to the `depth`.
  This the remaining bitstring after the leading `1` bit of the generalized index.

TODO: diagram of the binary tree

`SPLIT_DEPTH = 64`

- `path[0]`: [L1 Execution](#l1-execution-extra) [Experimental]
- `path[0] == 0`: L1 block-number bisection
  - For bits in `path` in range `[1...32)`: right-pad the bits to 31 bits with `1`s as padding.
    Interpret a big-endian `uint31`, define this as `offset`. 
    Each L1 block, relative by `max_l1_history - offset` blocks to the `l1_head` that the game started at,
    is transformed into a commitment of accumulated useful and safe L1 information.
    Where `max_l1_history = 24 * 60 * 60 / 12` (last 24 hours of L1 data).
    TODO: depends on sequencing window and other backward L1 traversal.
- `path[0] == 1`: L2 timestamp bisection
  - For bits in `path` in range `[1...32)`: right-pad the bits to 31 bits with `1`s as padding.
    Interpret a big-endian `uint31`, define this as `x`. The disputed `timestamp` is `superchain_time_offset + x`.
    Compute the `SuperRoot` for this timestamp, as pivot for a claim.
    - If `path[32] == 0`: Pending
      - For bits in `path` in range `[33, 64)`: right-pad the bits to 31 bits with `1s` as padding.
        Interpret as big-endian `uint31`, define this as `y`.
        This is the index of the L2 chain in the `super_snapshot` at `timestamp`.
        The pre-state of `y = 0` is a zeroed bytes32.
        For `y < len(super_snapshot.chains)` the pivot must match the accumulated pending state.
        For any `y >= len(super_snapshot.chains)` the pivot must repeat the pre-state.
    - If `path[32] == 1`: Dispute consolidation
      - For bits in `path` in range `[33, 64)`: parsed the same as the parallel branch `y` value.
        This is the index of the L2 chain in the `super_snapshot` at `timestamp`.
        The pre-state of `y = 0` is the last accumulated pending state commitment.
        For `y < len(super_snapshot.chains)` the pivot must match the accumulated pending state.
        For any `y > len(super_snapshot.chains)` the post-state must be a repeat of the pre-state.

## Program

The fault proof program divides the interop proving into sub-problems.

### Boot

The `Boot` routine is the part of the program that identifies
the sub-program to run based on the `Position` at the `SPLIT_DEPTH`.

The bisection contract provides the pre-state and post-state.
The pre-state is agreed upon, and the post-state is disputed.

After identifying the type of sub-problem, problem-inputs are read from the local-key space:
- `l1_head_hash`
- `pre_state`
- `post_state`

TODO: match above with latest FPAC initialization code.

### L1 Execution [Extra]

If included in the bisection game, this type of sub-problem establishes an enhanced view of the L1 chain.

This L1 game is an experimental part of the fault-proof:
L1 data is generally accessible through FP-alpha patterns & alternative large-preimage solutions.

#### Solving the Large Preimage Problem

With this solution however, we solve the "Large Preimage Problem" without introducing
additional L1 smart-contracts or challenger modifications.

This is done by loading the well-merkleized SSZ transaction data, and running the L1 EVM,
to produce the L1 receipts in-memory. These receipts can then be merkleized properly,
to be exposed as part of the `L1OutputRoot` merkle structure, for later usage in the L2 sub-problem programs.

#### Integrating L1 as read-only member of the Superchain

To read initiating messages from L1, we need to transform inaccessible L1 log-events data (due to the
"Large Preimage Problem") into accessible "initiating messages" for interop.

#### L1 program

Starting at the `max_l1_history` behind the `l1_head_hash`,
one L1 block at a time, for each `offset` towards `l1_head_hash`, the program computes the next `L1OutputRoot`

The program:
1. Retrieve the L1 head block header: `l1_head = oracle.get_header_by_hash(l1_head_hash)`
2. Retrieve the next L1 block header, by header-chain traversal:
  `next_header = oracle.get_header_by_number(l1_head_hash, l1_head.number - max_l1_history + offset + 1)`
3. Retrieve the current L1 block header, the parent-block of the above:
  `current_header = oracle.get_header_by_hash(get_header_by_hash.parent_hash)`
4. Retrieve L1 beacon block by using the prev-beacon-block-root of the next header:
  `beacon_block_root = next_header.parent_beacon_block_root`
5. Retrieve transaction input data from the SSZ merkle-tree structure in `beacon_block_root`:
   `transactions_path = beacon_block_root > beacon_block_body > execution_payload_header > transactions_root`
   `transaction_roots = list_items(traverse(beacon_block_root, transactions_path), MAX_TRANSACTIONS_PER_PAYLOAD)`
   `transactions = [bytelist(root, MAX_BYTES_PER_TRANSACTION) for root in transaction_roots]`
   where:
   - `>` represents SSZ path concatenation
   - `traverse` represents SSZ path traversal (binary-tree pre-image traversal following SSZ path)
   - `list_items(root, max)` represents retrieving the list length-mixin and then retrieving that 
     many tree leaves when traversed at a depth (rounded up) of `log2(max)`.
   - `bytelist(root, max)` represents retrieving the list bytelength-mixin and then retrieving that
     many packed bytes from the tree leaves when traversed at a depth (rounded up) of `log2(max) // 32`
6. Initialize a L1 chain config, based on the L1 chain ID
   (retrieved from rollup-config, as retrieved by L2 sub-programs).
7. Initialize a L1 EVM environment, with the block-context of `current_header`.
8. Process the L1 transactions, and hold on to the generated receipts in memory.
9. Transform the receipts into a list of initiating messages, as done with L2 receipts.
10. Merkleize the L1 receipts each as SSZ `BytesList[MAX_RECEIPT_SIZE]`,
   for later pre-image loading in the L2 sub-program.
11. Merkleize the L1 SSZ receipts, the initiating messages, the header data, and the transactions.
12. Accumulate the newly merkleized L1 block summary together with prior L1 summary data,
   to be forwarded to the next trace step.
13. The commitment to this accumulator is the correct post-state that the claim is compared against.

##### Rationale

This extension to the fault-proof program brings:

- L1 receipts data, which would otherwise require special modifications
  to the preimage oracle for large preimage loading.
- History-accumulators, which would otherwise require header-by-header L1 traversal in the L2 sub-problems.
- Initiating-messages accumulators, which would otherwise require additional receipts-data post-processing.
  This enables us to integrate L1 events into L2 interop.

### Verifying a Pending state [draft]

Each L2 can be fully derived from L1, and the correctness of the 
L2 EVM state-transition can be verified “optimistically”:
all inputs to the computation are assumed to be "valid".

However, these inputs may include “executing messages”, which depend on “initiating messages”, from other L2 chains.

The post-state is thus “pending”: validation of dependencies remains,
even though the inputs have been derived from L1 and processed into L2 blocks without issues.

TODO: it is important that we either enforce 1 L2 block to be proven at a time,
or handle invalidation of multiple L2 blocks between two `super_snapshot` claims.
This is especially tricky when an L2 chain previously lagged behind in batch-submission,
and has its latest data omitted from the pre-state `super_snapshot`,
and then has to "catch-up" with more L2 block processing.
This *is* covered by enforcing an equal block time across all chains,
and establishing the pre `SuperRoot` with the view of the current game rather 
than using the post-state result of a prior game. But this is non-obvious and may warrant some changes in design.

#### Program

TODO: define how an individual L2 block is derived

Approximately:
1. Based on the dispute position, select the L2 chain to prove a pending block of.
2. Establish safe-head L2 from pre-agreed block N-1
3. Run derivation to generate block input for N
4. Synchronously check cross-L2 dependencies of deposits,
   which are enforced to be sufficiently old, and cannot have cross-L2 intra-block dependencies.
   Invalid deposits must be dropped.
5. Run the EVM to produce the pending block state.
6. Combine with previous pending states into an accumulator commitment,
   that then eventually carries over into the cross-L2 consolidation category.


### Verifying a Cross-L2 Consolidation [draft]

After the latest pending output-roots are established for each L2 chain,
dependencies between the L2 chains can be resolved.

Dependencies of transactions can be cyclic between L2 chains,
and have transitive dependency on the validity of the blocks where 
the initiating messages along the dependency path originate from.

#### Program

Approximately:
1. Based on the dispute position, select the L2 chain to try to merge into the dependency set.
2. Traverse executing messages, by traversing the transactions of the block
3. For each, verify if the initiating message exists and is valid (not expired etc.).
   Verifying of initiating messages depends on the pending state
4. Compute a "fallback" that excludes all transactions, and only includes deposits
5. Register that we depend on the blocks with the initiating messages

Then, as final step for all L2 chains, after having processed the above for all:
- For each failed message verification, label the block as cancelled, and all blocks that depended on it.
- Replace all cancelled blocks with their safe fallback block.
- Compute the final set of output-roots with the final set of valid blocks.
- Construct the `super_root` from the final set of outputs.


## Security Considerations

TODO expand fault-proof security.

### Cascading dependencies

Deposits are a special case, synchronous with derivation, at enforced cross-L2 delay.
Thus deposits cannot reference each others events intra-block.

## Future upgrades

In a future where we fault-proof individual withdrawal messages,
the proof towards one of those messages can be a fault-proof program post-processing step
with inclusion-proof of the message in the produced superchain snapshot,
extending the common part that proves all of the superchain that is outlined here.
This then makes withdrawals independent of super-root proposals, while still allowing withdrawals
to be emitted from transactions that also involve cross-L2 messaging.
