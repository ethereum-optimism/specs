# Holocene Chain Derivation Changes

# Stricter Derivation Rules

The Holocene hardfork introduces several changes to batch derivation rules that render the
derivation pipeline stricter and simpler.
The changes are:

- _Steady Batch Derivation_ derives invalid singluar batches immediately as deposit-only
blocks.
- _Partial Span Batch Validity_ determines the validity of singular batches within a span batch
individually, only invalidating the remaining span batch upon the first invalid batch.
- _Strict Batch Ordering_ required batches within and across channels to be strictly ordered.

The channel and frame format are not changed, see also [A note on the current channel
format](#a-note-on-the-current-channel-format) for a discussion about a possible future
simplification of the channel and frame format under the stricter derivation rules.

## Steady Batch Derivation

TODO

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

### Frame Queue

The frame queue retains its function and holds all frames of the last batcher transaction. Holocene
still allows multiple frames per batcher transaction. As before, this allows for optionally filling
up remaining space of a batcher transactions with a starting frame of the next channel.

### Channel Bank

The Channel Bank becomes much simpler and only builds up a single channel.
Channel frames have to arrive in order, and only one channel can be open at a time.

#### Pruning

Pruning is vastly simplified as there's at most only one open channel in the channel bank. So the
channel bank's queue becomes effectively a staging slot for a single channel, the _staging channel_.
The `MAX_CHANNEL_BANK_SIZE` parameter becomes ineffective and the size of a channel is bounded, as
before, during decompression to be at most of size `MAX_RLP_BYTES_PER_CHANNEL`.

#### Timeout

The timeout is applied as before, just only to the single staging channel.

#### Reading & Frame Loading

Since the channel bank now only holds a single staging channel, and frames have to arrive in
order, frames are read until the channel is complete, and then the complete channel can be pulled
form the channel bank.

The following rules are applied to incoming frames:
- A first frame for a new channel starts a new channel as the staging channel.
  - If there already is an open staging channel, it is dropped and replaced by this new channel.
- An out of order frame is immediately dropped.
  - If it belongs to the currently open channel, that channel is also dropped as the staging channel.
  - This rule also covers dropping duplicate frames, as before Holocene.

Otherwise, the pre-Holocene rules are applied:
- If the current channel is timed-out, but not yet pruned, and the incoming frame would be the next
  correct frame for this channel, it is dropped.
- If a channel got closed by a _last_ frame, new frames for that channel are dropped.

### Batch Queue

The batch queue is also simplified in that batches are required to arrive strictly ordered, and gaps
are immediately derived as empty deposit-only blocks.

TODO: details

## Activation

The new batch rules activate when the _L1 inclusion block timestamp_ is greater or equal to the
Holocene activation timestamp. Note that this is in contrast to how span batches activated, namely
via the span batch L1 origin timestamp.

## Rationale

### Steady Batch Derivation

Steady Batch Derivation ensures a more timely progression of the derivation pipeline. Invalid
batches are not substituted by possible future batch replacements any more, but instead are directly
derived as deposit-only blocks. Prior to this change, in a worst case scenario, an invalid batch
could be replaced by a valid batch for a full sequencing window, and batches after the gap would
need to be buffered for that period.

Steady Batch Derivation has benefits for Fault Proofs and Interop, because it guarantees that each
block is final when derived once from a batch, which simplifies the reasoning about block
progression and avoids larger derivation pipeline resets.

### Strict Batch Ordering

Combining Steady Batch Derivationwith Strict Batch Ordering yields even stronger guarantees of
derivation progress. This way, not only any (even invalid) batches finalize the decision about that
block height, but any batch guarantees progress for _at least_ the next block height. A consequence
of the strict ordering rules guarantee that gaps are immediately derived as deposit-only blocks.

### Partial Span Batch Validity

Finally, Partial Span Batch Validity guarantees that a valid singular batch derived from a span batch can
immediately be processed as valid, instead of being in an undecided state until the full span batch is
converted into singular batches. This leads to swifter derivation and gives strong worst-case
guarantees for Fault Proofs because the vailidty of a block doesn't depend on the validity
of any future blocks any more. Note that before Holocene, to verify the first block of a span batch
required validating the full span batch.

### Less Defensive Protocol

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
