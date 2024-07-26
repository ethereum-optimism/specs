# L2 Output Root Proposals

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [L2 Output Commitment Construction](#l2-output-commitment-construction)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

<!-- All glossary references in this file. -->

[g-mpt]: ../glossary.md#merkle-patricia-trie

An updated version of this specification is in progress.
In the meantime, refer to the [Dispute Game Interface](../fault-proof/stage-one/dispute-game-interface.md#disputegamefactory-interface)
document and the `DisputeGameFactory` in particular to understand the basics of L2 output root proposals after the
introduction of Fault Proofs to the OP Stack.

## L2 Output Commitment Construction

The `output_root` is a 32 byte string, which is derived based on the a versioned scheme:

```pseudocode
output_root = keccak256(version_byte || payload)
```

where:

1. `version_byte` (`bytes32`) a simple version string which increments anytime the construction of the output root
   is changed.

2. `payload` (`bytes`) is a byte string of arbitrary length.

In the initial version of the output commitment construction, the version is `bytes32(0)`, and the payload is defined
as:

```pseudocode
payload = state_root || withdrawal_storage_root || latest_block_hash
```

where:

1. The `latest_block_hash` (`bytes32`) is the block hash for the latest L2 block.

1. The `state_root` (`bytes32`) is the Merkle-Patricia-Trie ([MPT][g-mpt]) root of all execution-layer accounts.
   This value is frequently used and thus elevated closer to the L2 output root, which removes the need to prove its
   inclusion in the pre-image of the `latest_block_hash`. This reduces the merkle proof depth and cost of accessing the
   L2 state root on L1.

1. The `withdrawal_storage_root` (`bytes32`) elevates the Merkle-Patricia-Trie ([MPT][g-mpt]) root of the [Message
   Passer contract](withdrawals.md#the-l2tol1messagepasser-contract) storage. Instead of making an MPT proof for a
   withdrawal against the state root (proving first the storage root of the L2toL1MessagePasser against the state root,
   then the withdrawal against that storage root), we can prove against the L2toL1MessagePasser's storage root directly,
   thus reducing the verification cost of withdrawals on L1.
