# Honest Actors (ZK Dispute Game)

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Valid Claim](#valid-claim)
- [Honest Proposer](#honest-proposer)
- [Honest Prover](#honest-prover)
- [Honest Challenger](#honest-challenger)
- [Timeliness](#timeliness)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The `ZKDisputeGame` has three honest roles: the proposer, the prover and the challenger. Only the prover runs the
[ZK program](../../zk-proof-system.md#zk-program). All roles read super roots through
[`superroot_atTimestamp`](../../../interop/superroot.md#superroot_attimestamp) from a source that follows the
chains in the interop set.

The same party MAY play several roles. In particular, a proposer is expected to prove its own challenged games.

## Valid Claim

Consider a game with `l1Head` block `H`, `l2SequenceNumber` `t` and `rootClaim` `r`. Its validity is decided from
the `superroot_atTimestamp(t)` response of the super root source:

1. If the response's `current_l1` number is at or below the number of `H`, the source has not progressed past `H`
   and no decision is made. The actor waits for the source to make progress.
2. If the response has no verified `data`, the claim is **invalid**: the timestamp is not yet backed by the
   verified chain.
3. If `data.verified_required_l1` number is above the number of `H`, the claim is **invalid**. The proof binds
   `l1Head`, so a root that needs L1 data after `H` can never be proven.
4. Otherwise the claim is valid if and only if `data.super_root` equals `r`.

A game whose parent resolved as `CHALLENGER_WINS` is invalid regardless of its root claim.

## Honest Proposer

An honest proposer:

- SHOULD create games only while `ZK_DISPUTE_GAME` is the respected game type. Games created while it is not
  respected can never become the anchor state or back withdrawals.
- MUST propose the verified super root (`data.super_root`) at the chosen timestamp, with its preimage as the
  packed [`SuperRootProof`](zk-dispute-game.md#superrootproof) in `extraData`. The timestamp SHOULD be at or below
  the safe (or finalized) timestamp reported by the super root source.
- MUST use as parent either `parentIndex = type(uint32).max`, to start from the anchor state, or a valid
  `ZK_DISPUTE_GAME` that was created while `ZK_DISPUTE_GAME` was the respected game type, is not blacklisted or
  retired, has not resolved as `CHALLENGER_WINS`, and is not the anchor game itself. It SHOULD choose the highest
  such game.
- MUST NOT create a game unless it can produce proofs for the registered `absolutePrestate` and `verifier`. For
  SP1, the aggregation program's verification key MUST equal `absolutePrestate`, and the `VERIFIER_HASH()` of the
  verifier wrapped by the registered [`SP1PlonkAdapter`](zk-interface.md#sp1plonkadapter) MUST match the PLONK
  circuit of the prover's SP1 SDK.

## Honest Prover

An honest prover:

- MUST prove every challenged game that it considers valid before the game's prove deadline. See
  [Proof Generation](../../zk-proof-system.md#proof-generation).
- MUST submit each proof from the address committed to as `prover` in the proof's public values, because the
  proof binds `msg.sender`.
- MAY prove unchallenged valid games to end them before the challenge deadline.
- MUST keep the program artifacts for every `absolutePrestate` used by games that can still be live, otherwise it
  can no longer defend those games.

## Honest Challenger

An honest challenger challenges a game when all of the following hold:

- `claimData.status` is `Unchallenged` and the challenge deadline has not passed; and
- the parent resolved as `CHALLENGER_WINS`, or the claim is invalid per [Valid Claim](#valid-claim).

Before challenging or resolving an unchallenged game inside its challenge window because its parent resolved as
`CHALLENGER_WINS`, the challenger MUST confirm the parent's status at a finalized L1 block, and MUST challenge the
game before resolving it, because resolving it unchallenged credits all bonds to `address(0)`. The challenge MUST
include `challengerBond`.

It resolves every game whose parent is resolved and for which any of the following holds:

- the parent resolved as `CHALLENGER_WINS`;
- a valid proof was provided; or
- the current deadline has passed.

For bonds, the challenger calls `claimCredit()` for each of its addresses that has credit. When none of its
addresses has credit in a resolved game, it calls `closeGame()` so that the anchor state can advance.

## Timeliness

Honest actions MUST land on L1 before the relevant deadline: challenges within `maxChallengeDuration` of game
creation, and proofs within `maxProveDuration` of the challenge.
