# Holocene Chain Derivation Changes

The Holocene hardfork introduces several changes to block derivation rules that render the
derivation pipeline mostly stricter and simpler, improve worst-case scenarios for Fault Proofs and
Interop. The changes are:

- _Strict Batch Ordering_ required batches within and across channels to be strictly ordered.
- _Partial Span Batch Validity_ determines the validity of singular batches from a span batch
individually, only invalidating the remaining span batch upon the first invalid singular batch.
- _Fast Channel Invalidation_, similarly to Partial Span Batch Validity applied to the channel
layer, forward-invalidates a channel upon finding an invalid batch.
- _Steady Block Derivation_ derives invalid payload attributes immediately as deposit-only
blocks.

The combined effect of these changes is that the impact of an invalid batch is contained to the
block number at hand, instead of propagating forwards or backwards in the safe chain, while also
containing invalid payloads at the engine stage to the engine, not propagating backwards in the
derivation pipeline.

The channel and frame format are not changed, see also [A note on the current channel
format](#a-note-on-the-current-channel-format) for a discussion about a possible future
simplification of the channel and frame format under the changed derivation rules.

Holocene derivation comprises the following changes to the derivation pipeline to achieve the above.

## Frame Queue

The frame queue retains its function and queues all frames of the last batcher transaction(s) that
weren't assembled into a channel yet. Holocene still allows multiple frames per batcher transaction,
possibly from different channels. As before, this allows for optionally filling up the remaining
space of a batcher transaction with a starting frame of the next channel.

However, Strict Batch Ordering leads to the following additional checks and rules to the frame
queue:
- If a _non-first frame_ (i.e., a frame with index >0) decoded from a batcher transaction is _out of
order_, it is *immediately dropped*, where the frame is called _out of order_ if
  - the frame queue is empty, or
  - the non-first frame has a different channel ID than the previous frame in the frame queue, or
  - the previous frame already closed the channel with the same ID.
- If a _first frame_ is decoded while the previous frame isn't a _last frame_ (i.e., `is_last` is
`false`), all previous frames for the same channel are dropped and this new first frame remains in
the queue.

These rules guarantee that the frame queue always holds frames whose indices are ordered,
contiguous and include the first frame, per channel. Plus, a first frame of a channel is either the
first frame in the queue, or is preceded by a closing frame of a previous channel.

Note that these rules are in contrast to pre-Holocene rules, where out of order frames were
buffered. Pre-Holocene, frame validity checks were only done at the Channel Bank stage. Performing
these checks already at the Frame Queue stage leads to faster discarding of invalid frames, keeping
the memory consumption of any implementation leaner.

## Channel Bank

Because channel frames have to arrive in order, the Channel Bank becomes much simpler and only
holds at most a single channel at a time.

### Pruning

Pruning is vastly simplified as there's at most only one open channel in the channel bank. So the
channel bank's queue becomes effectively a staging slot for a single channel, the _staging channel_.
The `MAX_CHANNEL_BANK_SIZE` parameter becomes ineffective and the size of a channel is bounded, as
before, during decompression to be at most of size `MAX_RLP_BYTES_PER_CHANNEL`.

### Timeout

The timeout is applied as before, just only to the single staging channel.

### Reading & Frame Loading

The frame queue is guaranteed to hold ordered and contiguous frames, per channel. So reading and
frame loading becomes simpler in the channel bank:
- A first frame for a new channel starts a new channel as the staging channel.
  - If there already is an open, non-completed staging channel, it is dropped and replaced by this
  new channel. This is consistent with how the frame queue drops all frames of an non-closed channel
  upon the arrival of a first frame for a new channel.
- If the current channel is timed-out, but not yet pruned, and the incoming frame would be the next
correct frame for this channel, the frame and channel are dropped, including all future frames for
the channel that might still be in the frame queue. Note that the equivalent rule was already
present pre-Holocene.

## Span Batches

Partial Span Batch Validity changes the atomic validity model of [Span Batches](../delta/span-batches.md).
In Holocene, a span batch is treated as an optional stage in the derivation pipeline that sits
before the batch queue, so that the batch queue pulls singular batches from this previous Span Batch
stage. When encountering an invalid singular batch, it is dropped, as is the remaining span batch
for consistency reasons. We call this _forwards-invalidation_. However, we don't
_backwards-invalidate_ previous valid batches that came from the same span batch, as pre-Holocene.

An implementation may choose to put the current span batch, from which singular batches are derived
from, into a separate stage, or process it within the batch queue under the new rules.

When a batch derived from the current staging channel is a singular batch, it is directly forwarded
to the batch queue. Otherwise, it is set as the current span batch in the span batch stage. The
following span batch validity checks are done, before singular batches are derived from it.
Definitions are borrowed from the [original Span Batch specs](../delta/span-batches.md).
- If the span batch _L1 origin check_ is not part of the canonical L1 chain, the span batch is
invalid.
- A failed parent check invalidates the span batch.
- If `span_start.timestamp > next_timestamp`, the span batch is invalid, because we disallow gaps
due to the new strict batch ordering rules.
- If `span_end.timestamp < next_timestamp`, the span batch is invalid, as it doesn't contain any new
batches (this would also happen if applying timestamp checks to each derived singular batch
individually).
- Note that we still allow span batches to overlap with the safe chain (`span_start.timestamp < next_timestamp`).

If any of the above checks invalidate the span batch, it is dropped and the remaining channel from
which the span batch was derived, is also immediately dropped (see also
[Fast Channel Invalidation](#fast-channel-invalidation)).

## Batch Queue

The batch queue is also simplified in that batches are required to arrive strictly ordered, and any
batches that violate the ordering requirements are immediately dropped, instead of buffered.

So the following changes are made to the [Bedrock Batch Queue](../derivation.md#batch-queue):
- The reordering step is removed, so that later checks will drop batches that are not sequential.
- The `future` batch validity status is removed, and batches that were determined to be in the
future are now directly `drop`-ped. This effectively disallows gaps, instead of buffering future batches.
- The other rules stay the same, including empty batch generation when the sequencing window
elapses.

If a batch is found to be invalid and is dropped, the remaining span batch it originated from, if
applicable, is also discarded.

### Fast Channel Invalidation

Furthermore, upon finding an invalid batch, the remaining channel it got derived from is also discarded.

TODO: I believe that the batch queue, similarly to the channel bank, now actually only holds at most
one single staging batch, because we eagerly derive payloads from any valid singular batch. And the
span batch stage before it would similarly only hold at most one staging span batch.

## Engine Queue

If the engine returns an `INVALID` status for a regularly derived payload, the payload is replaced
by a payload with the same fields, except for the `transaction_list`, which is replaced
- by the deposit transactions included in the L1 block, if the payloads are for the first block of
the current sequencing epoch,
- by an empty list otherwise.

As before, a failure to then process the deposit-only attributes is a critical error.

If an invalid payload is replaced by a deposit-only payload, for consistency reasons, the remaining
span batch, if applicable, and channel it originated from are dropped as well.

## Activation

The new batch rules activate when the _L1 inclusion block timestamp_ is greater or equal to the
Holocene activation timestamp. Note that this is in contrast to how span batches activated, namely
via the span batch L1 origin timestamp.

TODO: state reset at activation.

## Sync Start

TODO: details on sync start simplifications.

# Rationale

## Partial Span Batch Validity

Partial Span Batch Validity changes the span batch validation rules by only invalidating the
remaining span batch once an invalid singular batch is encountered. Prior to this, span batch
validity was treated atomically, so earlier pending valid singular batches could be invalidated by a
later invalid singular batch pulled from a span batch.
To accomplish this new behavior, the [Delta span batch batch queue rules](../delta/span-batches.md#batch-queue)
are changed in the following ways.

The max sequencer time drift check is applied to each singluar batch derived from a span batch
individually. Once a singular batch is found to be invalid, only the remaining span batch is
dropped. Note that the sequencing window check still applies to the span batch in full, because the
oldest blocks would be the first to be invalidated and if dropped would also invalidate newer
blocks.

TODO: other changes to validation checks.

## Strict Batch Ordering

The new Strict Batch Ordering rule requires batches within and across channels to be strictly
ordered. Note that this is already guaranteed for singular batcher derived from span batches by design.

The strict ordering rules are implemented in the derivation pipeline by applying the following
changes. 

## Steady Block Derivation

Steady Block Derivation changes the derivation rules for invalid payload attributes, replacing an
invalid payload by a deposit-only/empty payload. Crucially, this means that an invalid payload
doesn't propagate backwards in the derivation pipeline.

Invalid batches are still dropped, as before, and given another chance to be replaced by a batch in
a later channel for the same block number.

Steady Block Derivation ensures a more timely progression of the derivation pipeline. Invalid
batches are not substituted by possible future batch replacements any more, but instead are directly
derived as deposit-only blocks. Prior to this change, in a worst case scenario, an invalid batch
could be replaced by a valid batch for a full sequencing window, and batches after the gap would
need to be buffered for that period.

Steady Block Derivation has benefits for Fault Proofs and Interop, because it guarantees that each
block is final when derived once from a batch, which simplifies the reasoning about block
progression and avoids larger derivation pipeline resets.

## Strict Batch Ordering

Combining Steady Block Derivation with Strict Batch Ordering yields even stronger guarantees of
derivation progress. This way, not only any (even invalid) batches finalize the decision about that
block height, but any batch guarantees progress for _at least_ the next block height. A consequence
of the strict ordering rules guarantee that gaps are immediately derived as deposit-only blocks.

## Partial Span Batch Validity

Finally, Partial Span Batch Validity guarantees that a valid singular batch derived from a span batch can
immediately be processed as valid, instead of being in an undecided state until the full span batch is
converted into singular batches. This leads to swifter derivation and gives strong worst-case
guarantees for Fault Proofs because the vailidty of a block doesn't depend on the validity
of any future blocks any more. Note that before Holocene, to verify the first block of a span batch
required validating the full span batch.

## Fast Channel Invalidation

The new Fast Channel Invalidation rule is a consistency implication of the Strict Ordering Rules.
Because batches inside channels must be ordered and contiguous, assuming that all batches inside a
channel are self-consistent (i.e., parent L2 hashes point to the block resulting from the previous
batch), an invalid batch also forward-invalidates all remaining batches of the same channel.

Similarly to Partial Span Batch Validity, the 

## Less Defensive Protocol

The stricter derivation rules lead to a less defensive protocol. The old protocol rules
allowed for second chances for invalid batches and submitting frames and channels out of order.
Experiences from running OP Stack chains for over one and a half years have shown that these
relaxed derivation rules are almost never needed, so stricter rules that improve worst-case
scenarios for Fault Proofs and Interop are favorable.

## Security Considerations

### Reorgs

TODO

### Batcher Hardening

TODO

## Outlook on a new channel format

With these new consensus rules, several features that the current channel and frame format provide
become unnecessary. The current format allows for frames to arrive out of order,
and to already submit frames while the channel is still being built. These features required each
frame to be self-contained, so they have to contain as metadata the channel ID, frame number, frame
data length and a marker whether they are the last frame of a channel.

Technically, with the Stricter Derivation rules, the channel and frame format could be vastly simplified.
With the streaming feature of channels dropped, and the strict ordering rules, a new channel format
could be as simple as holding a single `uint32` channel size at the start of the first frame, while
still splitting a channel as frames over batcher transactions. Channel IDs could be dropped. The
introduction of such a simplified channel format is out of scope for Holocene.
