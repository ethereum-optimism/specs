# Engine Queue Block Derivation

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Motivation](#motivation)
- [Solution](#solution)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The Engine Queue stage pulls the latest derived `PayloadAttributes` to be processed by the execution
engine. If the execution engine reports an error with the provided payload (i.e invalid transaction
or state transition in the block), the Engine Queue currently drops the payload without progessing
the safe head and will attempt to use the next batch available for the same timestamp. If no valid
batches are found within the sequencing window, the rollup node will create a deposits-only empty
payload.

## Motivation

In implementation of low-latency interop, we want to minimize the effects of cascading reorgs
and the need to wind back & rebuild chain state when executing messages have been invalidated. The
looping behavior between the engine and attributes queue presents a challenge for fault proofs as
many different block candidates can be prepared depending on the available batch data after invalidation.

We can significantly reduce this complexity by generally revisiting this looping behavior in block derivation.

## Solution

The looping behavior between the engine and attributes queue can be eliminated by always ensuring
the progression of the safe head when processing payloads. We propose that the engine queue replace
invalidated payloads with a deposits-only empty one. In other words, when provided `PayloadAttributes`,
there will always be two possible block candidates:

1. Always Valid (empty deposits-only block)
2. A proper L2 block created from the provided payload.

   > For span batches, this implies the engine queue will process every payload from the span and does not drop
   > it in its entirety. In the worst case, every block after the first invalidated one also becomes an empty
   > deposits-only block. And in the best case, the encoded txs the future payloads are unrelated and succesfully
   > processed.

This change allows block derivation to be optimistically completed in a single step rather than waiting for
either a replacement batch or full seqeuencing window to elapse to force the production of empty blocks.
