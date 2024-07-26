# Honest Nodes

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Sequencing](#sequencing)
- [Unsafe](#unsafe)
- [Cross-Unsafe](#cross-unsafe)
- [Local Safe](#local-safe)
  - [Magic `derive` Function](#magic-derive-function)
  - [Task Processing Details](#task-processing-details)
    - [No Derivation Required](#no-derivation-required)
    - [L1 Canonical Checks](#l1-canonical-checks)
    - [Normal Blocks](#normal-blocks)
    - [Deposit Only Blocks](#deposit-only-blocks)
    - [Deposit-only Bisection Process](#deposit-only-bisection-process)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

Defines one possible implementation of a sequencing or verifying node that uses the [supervisor API] to perform
efficient verification of executing message dependencies. Implementations MAY differ from this approach providing they
still adhere to the protocol rules.

## Sequencing

Sequencing nodes continue building new `unsafe` blocks on top of the existing `unsafe` chain head. For
each [ExecutingMessage event][event] emitted by a transaction being added to the new block, the sequencer MUST
call [`interop_checkMessage`] with the identifier and payload hash from the event.

Sequencers MUST remove any transactions with any `conflicts` or `unknown` events from the block.

Sequencers MAY require a higher `SafetyLevel` be met before including any transactions. The required `SafetyLevel` may
vary based on the chain the initiating message is from or other policy decisions of the sequencer.

Sequencers MUST prioritize transactions where all dependencies have `SafetyLevel` of `finalized` in the same way as
transactions that do not emit executing message events. Delaying or excluding these transactions is considered
censorship.

## Unsafe

Nodes SHOULD track the unsafe head by importing blocks gossiped from the sequencer according to the regular rules
for [unsafe payload processing].

## Cross-Unsafe

Nodes SHOULD track the `cross-unsafe` head by periodically calling [`interop_crossUnsafe`] and specifying the node's
chain
ID and the number of its current unsafe head. If the `cross-unsafe` head is not persisted, it SHOULD initially be set to
the `safe` head.

If the returned block is canonical in the node's local view of the chain:

- If the returned block is before the node's current `safe` head, the `cross-safe` head is set to the `safe` head.
- Otherwise, the `cross-safe` head is set to the returned block.

Otherwise:

- The response MUST be ignored
- The node MAY retry with a block number between its current `cross-unsafe` head and `unsafe` head (exclusive).

If the current `cross-unsafe` head becomes non-canonical due to a reorg, it MUST be reset to the `safe` head.

## Local Safe

### Magic `derive` Function

Given a function to derive the latest L2 local safe block using L1 chain
head: `derive(l2Parent, depositOnly, l1Head) l2Block`. When `depositOnly` is `true`, the function MUST process batch
data from L1 to determine the L1 origin of the block, but then omit any non-deposit transactions in the produced block.

This method is defined as a pure function, therefore a given set of inputs MUST always result in the same output L2
block. However, node implementations SHOULD optimise execution and reuse existing computation when possible.

An honest node runs a continuous loop of calling `interop_nextDeriveTask` and executing the task it supplies and
reporting the result to `interop_blockDerived`. i.e.:

```pseudocode
for {
  task = interop_nextDeriveTask(localChainID)
  if !task.deriveRequired {
    sleep()
    continue
  }
  if !isCanonical(task.l1) {
    sleep()
    continue
  }
  localSafeHead = derive(task.l2Parent, task.depositOnly, task.l1)
  interop_blockDerived(localChainID, localSafeHead, task.l2Parent, task.depositOnly, task.l1)
}
```

All the important details for processing a task correctly are hidden in the `derive` function here which is unhelpful.

### Task Processing Details

Additional detail on how to process a task retrieved from `interop_nextDeriveTask`.

#### No Derivation Required

If `deriveRequired` is `false`, stop.

#### L1 Canonical Checks

If `l1` is not canonical in the local view, stop. Need to wait for L1 views to converge.

If the currently `local-safe` block was derived from a block that is no longer canonical, reset derivation back to a
point where the derived chain uses only canonical L1 data. ie same handling as for a L1 reorg pre-interop.

#### Normal Blocks

When `depositOnly` is `false`:

- If the node has not yet processed blocks up to `l1` process blocks up to `l1`.
- If `l2Parent` timestamp is ahead of the `local-safe` timestamp, op-supervisor has progressed safe head beyond
  local-safe and needs to rewind to recover. We don't currently have a way to trigger that.
- If `l2Parent` is the current safe head, report it to `interop_derivedBlock` and stop.
- Otherwise `l2Parent` timestamp must be before the `local-safe` timestamp:
  - If the node has not processed blocks past `l1`, report the current `local-safe` head via `interop_derivedBlock` and
    stop.
  - Otherwise, the supervisor is behind but needs more input to catch up:
    - If `l2Parent` is canonical:
      - reset the `local-safe` head back to `l2Parent` and reset the processed L1 head block back as appropriate
      - Process blocks up to `l1`
      - Report the resulting `local-safe` head via `interop_derivedBlock` and stop
    - Otherwise, there is a deposit-only block somewhere prior to `l2Parent`, run the deposit-only bisection process and
      stop.

#### Deposit Only Blocks

When `depositOnly` is `true`:

- If `l2Parent` timestamp is prior to the `local-safe` head:
  - If `l2Parent` is canonical, replace the block after `l2Parent` with a deposit-only block with the same l1 origin.
    Reset `local-safe` to this deposit-only block and stop (don't report via `interop_derivedBlock`).
  - Otherwise `l2Parent` is not canonical. There must be a deposit-only block prior to `l2Parent`. Run the deposit-only
    bisection process and stop.
- If `l2Parent` timestamp is after the `local-safe` head:
  - Process blocks until either `l2Parent` becomes the `local-safe` head or `l1` is reached
  - If `l1` is reached and `l2Parent` timestamp is still after `local-safe`, op-supervisor has progressed safe head
    beyond local-safe and needs to rewind to recover. We don't currently have a way to trigger that. Stop.
  - If `l1` is reached and `l2Parent` is not canonical, there must be a deposit-only block prior to `l2Parent`. Run the
    deposit-only bisection process and stop.
  - Otherwise, continue processing blocks until either `l1` is reached or a `local-safe` block is derived on top
    of `l2Parent`.
    - If `l1` is reached without deriving a new `local-safe` block, report `l2Parent` via `interop_derivedBlock` and
      stop
    - Otherwise, replace the new `local-safe` block with one that has the same L1 origin but contains only
      deposit-transactions. Report the deposit-only block via `interop_derivedBlock`.

#### Deposit-only Bisection Process

We need to find the first block that was replaced by a deposit-only block for which we still have a full block. But
given the super-safe db only has sparse records of L2 blocks, we can't identify the precise block just using hashes.

To start, bisect between our `finalized` block's L1 origin and the task's `l1` calling `interop_safe` to find the
highest L2 block where the node and supervisor have the same block hash and the lowest L2 block where the
node and supervisor have different block hashes.

For each L2 block in the identified range, find all executing messages and check validity with `interop_checkMessage`.
The first block with a message that returns `conflict` must be replaced by a deposit-only block and set as then
new `local-safe` head, then stop.

If any calls return `unknown`, stop. Likely a reorg occurred - otherwise something is very out of whack.

If no calls return `conflict`, stop. Likely a reorg occurred - otherwise something is very out of whack.

Note that we can't use a `interop_checkBlock` method for this because the supervisor has a different view of the chain
to the node and must have already replaced the problematic block with a deposit-only one.

[unsafe payload processing]: ../protocol/derivation.md#processing-unsafe-payload-attributes

[event]: ./predeploys.md#executingmessage-event

[`interop_checkMessage`]: ./supervisor-api.md#interop_checkmessage

[`interop_crossUnsafe`]: ./supervisor-api.md#interop_crossunsafe

[supervisor API]: supervisor-api.md
