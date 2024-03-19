# Driver

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Effects](#effects)
  - [Attributes generation](#attributes-generation)
    - [Conditional](#conditional)
    - [Effect](#effect)
  - [Unsafe block addition](#unsafe-block-addition)
    - [Conditional](#conditional-1)
    - [Effect](#effect-1)
  - [Unsafe block sync-trigger](#unsafe-block-sync-trigger)
    - [Conditional](#conditional-2)
    - [Effect](#effect-2)
  - [Unsafe block processing](#unsafe-block-processing)
    - [Conditional](#conditional-3)
    - [Effect](#effect-3)
  - [Sequencing](#sequencing)
    - [Conditional](#conditional-4)
    - [Effect](#effect-4)
  - [Payload attributes processing](#payload-attributes-processing)
    - [Conditional](#conditional-5)
    - [Effect](#effect-5)
  - [Interop safety progression](#interop-safety-progression)
    - [Conditional](#conditional-6)
    - [Effect](#effect-6)
  - [Interop safety reversal](#interop-safety-reversal)
    - [Conditional](#conditional-7)
    - [Effect](#effect-7)
  - [Safety progression](#safety-progression)
    - [Conditional](#conditional-8)
    - [Effect](#effect-8)
  - [Safety reversal](#safety-reversal)
    - [Conditional](#conditional-9)
    - [Effect](#effect-9)
  - [Finality progression](#finality-progression)
    - [Conditional](#conditional-10)
    - [Effect](#effect-10)
  - [Engine consistency](#engine-consistency)
    - [Conditional](#conditional-11)
    - [Effect](#effect-11)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

The "driver" is the part of the rollup-node that initiates state-transition and block-safety changes.

This document describes each of these effects.
A rollup-node implementations may implement the scheduling of these effects freely,
but is recommended to avoid unnecessary synchronous work.

The set of effects is extensible: this set may be extended or modified with upgrades, to support feature changes.  

## Effects

Effects are encapsulated, such that:

- No effects block each other unnecessarily.
  E.g. regular safe-head-consolidation may happen in parallel to unsafe-block processing,
  as there is no conflicting resource usage.
- The steps are individually testable and debuggable:
  standard-tests may utilize this enumeration of effects for unit-test.

Some effects are still effectively synchronous, due to the way they relate to the state.
E.g. attributes generation and processing of said attributes.
Encapsulation of these otherwise sequential effects does allow for faster interruption and re-scheduling.

All effect-failures must be recoverable:
effects must not leave the driver in a state where no further effects can be applied.

Effects are generally triggered by a pre-state condition, which may have the form of an event.

### Attributes generation

[derivation pipeline]: ../protocol/derivation.md#l2-chain-derivation-pipeline

Generate attributes are generated from L1 data by the [derivation pipeline], without engine-queue.
The ["Engine Queue" stage](../protocol/derivation.md#engine-queue) abstraction is deprecated,
as it combined previous effects that could have been encapsulated.

The [derivation pipeline] is thus executed up and to the attributes-generation by the
["Payload attributes derivation" stage](../protocol/derivation.md#payload-attributes-derivation),
also known as the "attributes queue".

#### Conditional

A L1 block that has not been fully consumed yet.

This includes:

- New L1 blocks, as they become available.
- L1 blocks, after previous consumption has been invalidated. E.g. invalidation after a L1 reorg.

The application of this effect may repeat, until the condition no longer applies.

#### Effect

Prestate:

- `pipeline`: derivation-pipeline instance
- `l2_safe_head`: L2 safe-head, to generate the next set of attributes on.
- `candidate`: referring to the iteration of generated attributes.

Change: run or reset derivation:

1. Reset the derivation-pipeline if the current derivation state
   does not match the L2 safe head and candidate iteration.
2. Run derivation to generate attributes.
3. Persist attributes and derivation context:
   1. `attributes`: `PayloadAttributesEnvelope`, the payload-attributes with metadata that form the block.
   2. `derived_at`: L1 block reference, of the L1 block was last consumed to fully derive the attributes.
   3. `is_last_in_span`: boolean, indicating whether the attributes are the last entry derived from a span-batch.
   4. `pipeline`: updated derivation-pipeline.

### Unsafe block addition

Received unsafe blocks are received and persisted for other effects to process.

#### Conditional

A new unsafe payload, received through sources such as [P2P gossip](../protocol/rollup-node-p2p.md#gossip-topics)
or [P2P request-response](../protocol/rollup-node-p2p.md#req-resp).

#### Effect

Queue the unsafe payload for processing.
Either as [sync-trigger](#unsafe-block-sync-trigger) or [directly processed](#unsafe-block-processing).

### Unsafe block sync-trigger

Unsafe blocks which are not sequential with previous unsafe blocks can be given to the engine,
when in execution-layer syncmode, to trigger a sync attempt.

#### Conditional

The queue of unsafe payloads contains a payload with a
block number of more than 1 ahead of that of the current unsafe head.

#### Effect

Process the block with the [execution engine API](../protocol/exec-engine.md#engine-api):

- `newPayload` call to insert the payload.
- `forkchoiceUpdated` call to persist the processed payload as canonical.

The `forkchoiceUpdated` call may be omitted if more payloads remain to be processed with this effect,
since the sync target may be moved by multiple payloads at a time.

Payloads should be processed from high to low block number, to track as close to the latest payload as possible.

### Unsafe block processing

Unsafe blocks which are sequential to the current unsafe head of the chain may be processed immediately.

#### Conditional

The queue of unsafe payloads contains a payload with a
block number of exactly 1 higher than the current unsafe block head, and a matching parent block-hash.

#### Effect

Process the block with the [execution engine API](../protocol/exec-engine.md#engine-api):

- `newPayload` call to insert the payload.
- `forkchoiceUpdated` call to persist the processed payload as canonical.

See [Engine API usage](../protocol/derivation.md#engine-api-usage) for version-specific usage of the Engine API.

### Sequencing

#### Conditional

Sequencing is time-sensitive, and consists of two sub-processes:

- `starting`: starts a payload-building job. This should be started as soon after the last block completed,
  but not earlier than 1 block-time window before the timestamp of the block that is being created.
- `sealing`: completes a previously started payload-building job.
  This should be completed just before the timestamp of the block that is being created.
  This margin may be implementation-dependent, but ideally maximizes block-building time allowance,
  while publishing the sealed block as close to the designated block-time as possible.

#### Effect

When `starting`, initiate a block-building process:

- Select a L1 origin, based on the origin of the previous L2 block.
  - Advance to the next L1 origin, if within confirmation scope.
  - Advancement of the L1 origin may be ignored temporarily, within the `max_sequencer_drift`
    as defined by the [derivation rules](../protocol/derivation.md).
- Generate a payload-attributes template, including a list of deposit transactions.
  See [deriving payload attributes](../protocol/derivation.md#deriving-payload-attributes).
- `forkchoiceUpdated` call, with payload-attributes, to start the payload-building work.
- Register the payload-building job identifier from the Engine API, for later `sealing` work.

When `sealing`, complete the block-building process:

- Retrieve the payload through a `getPayload` call.
- Process the payload in the engine with a `newPayload` call.
- Persist the payload as new canonical unsafe head with a `forkchoiceUpdated` call.
- Update local state to reflect the change of the forkchoice call.
- Publish the payload to verifiers,
  by forwarding it to services such as [P2P gossip](../protocol/rollup-node-p2p.md#gossip-topics).

Between `starting` and `sealing` the Engine may perform alternative block-processing work.
The result of `starting` is invalided upon alternative block-processing work,
and the sequencer will have to retry `starting`.

With interop, the sequencer assumes dependency safety of the block it builds,
but does not promote it instantaneously to cross-unsafe.

See [Engine API usage](../protocol/derivation.md#engine-api-usage) for version-specific usage of the Engine API.

### Payload attributes processing

When there is no prior unsafe block, or when the priors have been invalidated,
the generated payloads may be processed directly to progress the head of the chain.

This will reorg out any conflicting unsafe blocks.

This does not immediately promote the resulting block to "safe":
additional derivation and cross-L2 safety requirements may be imposed.
The attributes should be considered as "consolidated", without the safety-label progression, however.

Processing the attributes before promotion to "safe" is a hard-requirement for interop at intra-block latency:
initiating events may be emitted by the block, which can form a cyclic message dependency with other chains.

#### Conditional

The consolidated head (as defined in [Safety progression](#safety-progression))
is the tip of absolute head of the chain,
either due to invalidation prior unsafe payloads, or lack of unsafe payloads.

There exists a set of payload attributes with a parent block hash matching that of the consolidated head.

#### Effect

Apply the payload-attributes to the engine, with a `forkchoiceUpdated`, `getPayload` and `newPayload` sequence of calls
to the engine, to process and persist the attributes as block.

Persist the unsafe head as canonical, with a `forkchoiceUpdated` call to the engine.

Update the "consolidated" head, for the next payload-attributes processing/generation tasks to continue from here.

### Interop safety progression

Progress the cross-L2-unsafe head.

#### Conditional

There exists an unsafe block, after the current cross-unsafe head, in the canonical chain.

#### Effect

Verify and enforce the cross-L2 dependencies of the unsafe block:

- If valid, promote the block to cross-unsafe.
- If invalid, demote the "consolidated" status of the block and the rewind the chain head:
  a new set of attributes will need to replace the block.
- If undecided, re-analyze dependencies later, when the remote L2 information changes.

### Interop safety reversal

Remote changes of message dependencies may invalidate a previously cross-unsafe L2 block.

#### Conditional

A signal from the interop system that a non-finalized block is no longer cross-unsafe.

#### Effect

Reversal of the cross-unsafe block. The head, as well as the cross-unsafe head,
are rewound back to the parent-block of the invalidated cross-unsafe block.

The reversal of the unsafe head may be deferred until an alternative payload
or payload-attributes is available to reorg out the invalidated data.

### Safety progression

Previously processed unsafe (cross-unsafe with interop) payloads may be promoted to safe,
after successful consolidation with attributes derived from L1.

#### Conditional

There exists an unsafe block right after the current consolidated head, on the canonical chain.
The safe head is considered consolidated by definition.

An unsafe block is considered consolidated if previously matched against derived attributes from L1,
while safety was deferred till consolidation of additional attributes.

And there exists a generated set of payload attributes for this block-height,
applicable on top of the current safe head (i.e. attributes have matching parent block hash).

**interop change**: the block must have a `cross-unsafe` safety-level,
`unsafe` is insufficient after introduction of cross-L2 safety dependencies.

#### Effect

Compare the derived payload attributes to the block-inputs of the unsafe block.

See [L1 consolidation](../protocol/derivation.md#l1-consolidation-payload-attributes-matching)
for details on comparison of payload-attributes.

If mismatching, the existing unsafe block should no longer be recognized as canonical block.
In this case, proceed with payload-attributes processing of the payload-attributes.

If matching, the unsafe block can now be considered as "consolidated".

If the payload-attributes were from a singular-batch, or the last block in a span-batch,
the block will be the new `safe` head.
The safe-head chang is signaled to the engine through a `forkchoiceUpdated` call.

### Safety reversal

Upon L1 reorgs the data that the L2 blocks were derived from may differ.
These reorgs are detected by the attributes-generation effect.

#### Conditional

The attributes-generation state is no longer consistent with the canonical L1 chain.

#### Effect

Pessimistically, the safe-head is entirely reset to a L2 block guaranteed
to be consistent with the new view of the L1 chain.
This requires a significant reset, to finalized data, or over a sequencer window worth of L1 blocks.
See [Resetting the Pipeline](../protocol/derivation.md#resetting-the-pipeline) for details.

Optimistically, the safe-head is not rewound far, and quickly recovered from `derived_at` information,
by tracking down a L2 block that is derived from a L1 block that has not been reorged out.

With interop the cross-unsafe head should be rewound to apply to the canonical chain, whenever the safe-head changes.

### Finality progression

Finality is achieved by matching new L1 finality events to recently derived data from L1.

#### Conditional

A L1 finality event is received, and meets or exceeds the `derived_at` of
a recent set of payload-attributes that was promoted to safe block.

When matching multiple recently promoted safe blocks, the last one implies finality of all older blocks,
and should thus be selected as block to finalize.

The L1 beacon chain finalizes either the last or second-last beacon-epoch of blocks.
It is thus sufficient to retain only the last 2 beacon epochs worth of L1 `derived_at` information
to support finalization.

#### Effect

After having detected a safe L2 block that is derived fully from finalized L1 information,
the safe L2 block is promoted to finalized L2 block.

The finality of the block is updated with a `forkchoiceUpdated` call to the engine.

### Engine consistency

The execution-engine might complete a sync, restart, or otherwise get an unexpected state-change.
It is thus recommended to poll the forkchoice state of engine, to reset any local rollup-node state accordingly.

#### Conditional

Poll for forkchoice state changes.
Or wait for events that hints at engine state-changes.

#### Effect

Update the local safety view to match the forkchoice of the engine.
