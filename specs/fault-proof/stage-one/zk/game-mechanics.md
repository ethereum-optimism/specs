# ZK Dispute Game Mechanics

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [State Transitions](#state-transitions)
- [Creation](#creation)
  - [Parent Validation](#parent-validation)
- [Challenge](#challenge)
- [Proving](#proving)
- [Resolution](#resolution)
  - [Bond Distribution](#bond-distribution)
- [Closing](#closing)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## State Transitions

The game tracks its lifecycle through two enums:

**`GameStatus`** (external, defined in `Types.sol`): the authoritative resolution outcome read by
`OptimismPortal` and `AnchorStateRegistry`.

```solidity
enum GameStatus {
    IN_PROGRESS,     // Default state; game has not yet resolved
    CHALLENGER_WINS,
    DEFENDER_WINS
}
```

**`ProposalStatus`** (internal, defined in `ZKDisputeGame`): tracks the proposal's internal
lifecycle independently of the resolution outcome.

```solidity
enum ProposalStatus {
    Unchallenged,
    Challenged,
    UnchallengedAndValidProofProvided,
    ChallengedAndValidProofProvided,
    Resolved
}
```

`claimData.status` (`ProposalStatus`) transitions on `challenge()` and `prove()`. `status`
(`GameStatus`) transitions only inside `resolve()`. These two state variables evolve independently
and MUST NOT be conflated.

```text
                     claimData.status (ProposalStatus)

GameCreation ──► Unchallenged ──────────────────────────────────────────────────────────┐
                     │                                                                  │
                     ├──► Challenged ──► ChallengedAndValidProofProvided ──────────────┤
                     │         │                                                        │
                     │         └─ (prove deadline expires) ─────────────────────────── ┤
                     │                                                                  │
                     └──► UnchallengedAndValidProofProvided ─────────────────────────── ┤
                               │                                                        │
                               └─ (challenge deadline expires) ────────────────────────┤
                                                                                        ▼
                                                                                    resolve()
                                                                                        │
                     status (GameStatus)                                                │
                     IN_PROGRESS ───────────────────────────────────────────────────── ┤
                                                                                        │
                                                              ┌─── DEFENDER_WINS ◄──── ┤
                                                              └─── CHALLENGER_WINS ◄── ┘
```

| Transition | Trigger |
| --- | --- |
| `GameCreation → Unchallenged` | `initialize()` called by `DisputeGameFactory` |
| `Unchallenged → Challenged` | `challenge()` called before deadline |
| `Unchallenged → UnchallengedAndValidProofProvided` | `prove()` succeeds |
| `Challenged → ChallengedAndValidProofProvided` | `prove()` succeeds |
| Any non-terminal `ProposalStatus` → `Resolved` | `resolve()` succeeds |
| `IN_PROGRESS → DEFENDER_WINS \| CHALLENGER_WINS` | `resolve()` succeeds |

## Creation

Game creation is fully permissionless. Anyone may call `DisputeGameFactory.create()` with the
required `initBond`. The factory deploys an MCP clone, which then validates the proposal.

`initBond` is the ETH value the proposer must send when creating a game. The factory forwards it
to `initialize()` as `msg.value`. Its exact amount is set per deployment and can be updated by
governance; the game contract reads it from the factory at creation time.

A game may start from the anchor state by setting `parentIndex = type(uint32).max`, or it may
reference a parent game.

The `_extraData` passed to `DisputeGameFactory.create()` has a variable-length layout:

| Field | Type | Description |
| --- | --- | --- |
| `parentIndex` | `uint32` | Index of the parent game; `type(uint32).max` if starting from the anchor state |
| `superRootProof` | `bytes` | ABI-encoded `SuperRootProof` preimage committed to by `rootClaim`. The L2 sequence number (super root timestamp) is part of this preimage and is exposed by the contract via `l2SequenceNumber()` for convenience. |

The variable-length layout is parsed via `_preExtraDataByteCount()` and `_extraDataByteCount()`
helpers, following the same pattern as `SuperFaultDisputeGame`. All CWIA field offsets after
`extraData` are computed dynamically.

During `initialize()`, the game:

1. Validates the `SuperRootProof` preimage: `hashSuperRootProof(decode(extraData)) == rootClaim`.
2. Snapshots `wasRespectedGameTypeWhenCreated`. `AnchorStateRegistry.isGameClaimValid()` reads
   this flag when determining if a game's root claim can advance the anchor state or finalize
   withdrawals via the Portal.

### Parent Validation

When a parent is referenced (`parentIndex != type(uint32).max`), `initialize()` MUST revert if
any of the following checks fail:

- Parent MUST NOT be blacklisted.
- Parent MUST NOT be retired (i.e., `createdAt > retirementTimestamp`).
- Parent MUST be the same game type (`ZK_GAME_TYPE`).
- Parent MUST NOT have resolved as `CHALLENGER_WINS`.
- Parent's `l2SequenceNumber` (timestamp) MUST be strictly above the anchor state's
  `l2SequenceNumber`.
- The game's `l2SequenceNumber` MUST be strictly greater than the parent's `l2SequenceNumber`.

The `isGameRespected` check on the parent is intentionally omitted. The respected game type gates
which games can finalize withdrawals (via `isGameClaimValid`), but MUST NOT prevent in-progress
proposal chains from being completed after a game type transition.

## Challenge

Challenging is fully permissionless. Anyone may call `challenge()` before the challenge deadline.
The call MUST include `challengerBond` ETH, which `challenge()` deposits into `DelayedWETH` on
the caller's behalf.

- `challenge()` MUST revert if `gameOver()` returns `true`.
- `challenge()` MUST revert if `claimData.status != ProposalStatus.Unchallenged`.
- `challenge()` MUST revert if `msg.value != challengerBond`.
- Only one challenge is allowed per game.
- Calling `challenge()` resets the deadline to `block.timestamp + maxProveDuration`.

## Proving

Proving is fully permissionless. Anyone may call `prove(proofBytes)` at any point before the
current deadline, regardless of whether the game has been challenged.

- `prove()` MUST revert if `status != GameStatus.IN_PROGRESS` (i.e., the game is already
  resolved).
- `prove()` MUST revert if the parent game has resolved as `CHALLENGER_WINS`.
- `prove()` MUST revert if `gameOver()` returns `true` (covers an already-submitted proof and an
  expired deadline).
- The verifier call MUST revert for invalid proofs.
- On success, `claimData.prover` is set to `msg.sender` and `claimData.status` transitions to
  `UnchallengedAndValidProofProvided` or `ChallengedAndValidProofProvided` (depending on whether
  the game was challenged). `gameOver()` returns `true` immediately after.

`gameOver()` returns `true` when:

- `claimData.deadline < block.timestamp`, OR
- `claimData.prover != address(0)`.

## Resolution

Resolution is permissionless. Anyone may call `resolve()` once `gameOver()` returns `true` and
the parent game is resolved.

- `resolve()` MUST revert if `status != GameStatus.IN_PROGRESS` (i.e., game is already resolved).
- If the game references a parent (`parentIndex != type(uint32).max`), `resolve()` MUST revert if
  the parent game's `status == GameStatus.IN_PROGRESS`.
- If the parent resolved as `CHALLENGER_WINS`, the child inherits `CHALLENGER_WINS` regardless of
  its own proof status.
- Otherwise (parent `DEFENDER_WINS`), the outcome is determined by `claimData.status`:

| `claimData.status` at resolution | `GameStatus` outcome | `normalModeCredit` allocation |
| --- | --- | --- |
| `Unchallenged` (deadline expired) | `DEFENDER_WINS` | `gameCreator` ← `totalBonds` |
| `UnchallengedAndValidProofProvided` | `DEFENDER_WINS` | `gameCreator` ← `totalBonds` |
| `Challenged` (prove deadline expired) | `CHALLENGER_WINS` | `challenger` ← `totalBonds` |
| `ChallengedAndValidProofProvided`, prover == proposer | `DEFENDER_WINS` | `prover` ← `totalBonds` |
| `ChallengedAndValidProofProvided`, prover != proposer | `DEFENDER_WINS` | `prover` ← `challengerBond`; `gameCreator` ← `totalBonds - challengerBond` |
| Parent `CHALLENGER_WINS`, child challenged | `CHALLENGER_WINS` | `challenger` ← `totalBonds` |
| Parent `CHALLENGER_WINS`, child unchallenged | `CHALLENGER_WINS` | `address(0)` ← `totalBonds` (burned) |

`totalBonds` equals `initBond` for unchallenged games and `initBond + challengerBond` for
challenged games.

Note: when a parent resolves as `CHALLENGER_WINS` and the child was never challenged,
`claimData.challenger == address(0)`, so `normalModeCredit[address(0)] = totalBonds`. This credit
is effectively burned inside `DelayedWETH` where the owner can recover it via `hold()`/`recover()`.

### Bond Distribution

Bond distribution follows a NORMAL or REFUND mode determined by `isGameProper` (evaluated in
`closeGame`):

| Mode | Condition | Effect |
| --- | --- | --- |
| **NORMAL** | Game is proper (registered, not blacklisted, not retired, not paused) | `normalModeCredit` allocations from `resolve()` are honored |
| **REFUND** | Game is blacklisted, retired, or otherwise improper | `refundModeCredit` is used: `initBond` returned to proposer; `challengerBond` returned to challenger |

Complete distribution scenarios:

| Scenario | Mode | Proposer gets | Challenger gets | Prover gets |
| --- | --- | --- | --- | --- |
| Unchallenged, deadline expires | NORMAL | `initBond` | — | — |
| Unchallenged, proof provided | NORMAL | `initBond` | — | nothing |
| Challenged, no proof | NORMAL | nothing | `initBond + challengerBond` | — |
| Challenged, proof, prover == proposer | NORMAL | `initBond + challengerBond` | nothing | _(same)_ |
| Challenged, proof, prover != proposer | NORMAL | `initBond` | nothing | `challengerBond` |
| Parent `CHALLENGER_WINS`, child challenged | NORMAL | nothing | `initBond + challengerBond` | — |
| Parent `CHALLENGER_WINS`, child unchallenged | NORMAL | burned to `address(0)` | — | — |
| Game blacklisted | REFUND | `initBond` | `challengerBond` | — |
| Game retired | REFUND | `initBond` | `challengerBond` | — |

## Closing

After resolution, bonds are distributed through a two-phase process.

**`closeGame()`** (permissionless, also called internally by `claimCredit`):

- Returns early if `bondDistributionMode` is already set (NORMAL or REFUND).
- MUST revert if `AnchorStateRegistry` is paused.
- MUST revert with `GameNotResolved` if `resolvedAt == 0`.
- MUST revert if `AnchorStateRegistry.isGameFinalized(this)` returns `false`.
- Attempts to register the game as the new anchor state via `AnchorStateRegistry.setAnchorState()`.
  This may silently fail if the game is not eligible; the failure is caught and ignored.
- Calls `AnchorStateRegistry.isGameProper(this)` to determine NORMAL or REFUND mode and sets
  `bondDistributionMode` accordingly.

**`claimCredit(recipient)`**:

Uses a two-phase `DelayedWETH` withdrawal pattern.

1. Records whether the game was open (`bondDistributionMode == UNDECIDED`) before the call.
2. Triggers `closeGame()` if not yet closed.
3. **Phase 1 — unlock:** If `recipient` still has credit allocated by this game (checked against
   the active mode's credit mapping), zeroes out **both** `normalModeCredit[recipient]` and
   `refundModeCredit[recipient]`, then calls `DelayedWETH.unlock(recipient, amount)` and returns.
   A second call is required to complete the withdrawal once the `DelayedWETH` delay has elapsed.
4. **Phase 2 — withdraw:** If credit has already been zeroed (phase 1 completed), checks
   `DelayedWETH` for a pending withdrawal amount. If the amount is zero and the game was open
   before this call, returns without reverting (so `closeGame()` state changes persist). If the
   amount is zero and the game was already closed, reverts with `NoCreditToClaim`. Otherwise,
   calls `DelayedWETH.withdraw(recipient)` and transfers ETH to the recipient, reverting on
   transfer failure.

The `DelayedWETH` delay allows the Guardian to pause and freeze funds if a critical issue is
discovered post-resolution.
