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

```
GameCreation ──► Unchallenged ──► Challenged ──► ChallengedAndValidProofProvided ──► Resolved
                      │    │           │
                      │    │           └────────────────────────────────────────────► Resolved
                      │    └─ (deadline expires) ──────────────────────────────────► Resolved
                      ▼
         UnchallengedAndValidProofProvided ──────────────────────────────────────────► Resolved
```

| Transition                                         | Trigger                                            |
| -------------------------------------------------- | -------------------------------------------------- |
| `GameCreation → Unchallenged`                      | `initialize()` called by `DisputeGameFactory`      |
| `Unchallenged → Challenged`                        | `challenge()` called before the challenge deadline |
| `Unchallenged → UnchallengedAndValidProofProvided` | `prove()` succeeds                                 |
| `Unchallenged → Resolved`                          | Deadline expires and `resolve()` is called         |
| `Challenged → ChallengedAndValidProofProvided`     | `prove()` succeeds                                 |
| `Challenged → Resolved`                            | Prove deadline expires and `resolve()` is called   |
| `UnchallengedAndValidProofProvided → Resolved`     | `resolve()` is called                              |
| `ChallengedAndValidProofProvided → Resolved`       | `resolve()` is called                              |

## Creation

Game creation is fully permissionless. Anyone may call `DisputeGameFactory.create()` with the
required `initBond`. The factory deploys an MCP clone, which then validates the proposal.

A game may start from the anchor state by setting `parentIndex = type(uint32).max`, or it may
reference a parent game.

### Parent Validation

When a parent is referenced (`parentIndex != type(uint32).max`), `initialize()` MUST revert if
any of the following checks fail:

- Parent MUST NOT be blacklisted.
- Parent MUST NOT be retired (i.e., `createdAt > retirementTimestamp`).
- Parent MUST be the same game type (`ZK_GAME_TYPE`).
- Parent MUST NOT have resolved as `CHALLENGER_WINS`.
- Parent's `l2SequenceNumber` MUST be at or above the anchor state's `l2SequenceNumber`.
- The game's `l2SequenceNumber` MUST be strictly greater than the parent's `l2SequenceNumber`.

The `isGameRespected` check on the parent is intentionally omitted. The respected game type gates
which games can finalize withdrawals (via `isGameClaimValid`), but MUST NOT prevent in-progress
proposal chains from being completed after a game type transition.

## Challenge

Challenging is fully permissionless. Anyone may call `challenge()` before the challenge deadline.
The call MUST include `challengerBond` ETH, which `challenge()` deposits into `DelayedWETH` on
the caller's behalf.

- `challenge()` MUST revert if `gameOver()` returns `true`.
- Only one challenge is allowed per game.
- Calling `challenge()` resets the deadline to `block.timestamp + maxProveDuration`.

## Proving

Proving is fully permissionless. Anyone may call `prove(proofBytes)` at any point before the
current deadline, regardless of whether the game has been challenged.

- `prove()` MUST revert if `gameOver()` returns `true` (covers both an already-submitted proof
  and an expired deadline).
- The verifier call MUST revert for invalid proofs.
- On success, `proofSubmitted` is set to `true` and `gameOver()` returns `true` immediately.
- If the game was challenged and the prover is different from the proposer, the prover earns
  `challengerBond` upon resolution.

## Resolution

Resolution is permissionless. Anyone may call `resolve()` once `gameOver()` returns `true` and
the parent game is resolved.

- The parent game MUST be resolved before the child.
- If the parent resolved as `CHALLENGER_WINS`, the child inherits `CHALLENGER_WINS` regardless of
  its own proof status.
- Otherwise (parent `DEFENDER_WINS`), the outcome is determined as follows:

| Game state at resolution                                 | Outcome           | Bond distribution                                              |
| -------------------------------------------------------- | ----------------- | -------------------------------------------------------------- |
| Unchallenged, deadline expired                           | `DEFENDER_WINS`   | Proposer recovers `initBond`                                   |
| Unchallenged, valid proof provided                       | `DEFENDER_WINS`   | Proposer recovers `initBond`; prover receives nothing          |
| Challenged, no proof by deadline                         | `CHALLENGER_WINS` | Challenger receives `initBond + challengerBond`                |
| Challenged, valid proof, prover == proposer              | `DEFENDER_WINS`   | Proposer recovers `initBond + challengerBond`                  |
| Challenged, valid proof, prover != proposer              | `DEFENDER_WINS`   | Proposer recovers `initBond`; prover receives `challengerBond` |
| Parent resolved as `CHALLENGER_WINS`, child challenged   | `CHALLENGER_WINS` | Challenger receives `initBond + challengerBond`                |
| Parent resolved as `CHALLENGER_WINS`, child unchallenged | `CHALLENGER_WINS` | `initBond` is burned                                           |

### Bond Distribution

Bond distribution follows a NORMAL or REFUND mode determined by `isGameProper` (evaluated in
`closeGame`):

| Mode       | Condition                                                             | Effect                                                                   |
| ---------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| **NORMAL** | Game is Proper (registered, not blacklisted, not retired, not paused) | Bonds go to winners as described above                                   |
| **REFUND** | Game is blacklisted, retired, or otherwise improper                   | `initBond` returned to proposer; `challengerBond` returned to challenger |

Complete distribution scenarios:

| Scenario                                     | Mode   | Proposer gets               | Challenger gets             | Prover gets      |
| -------------------------------------------- | ------ | --------------------------- | --------------------------- | ---------------- |
| Unchallenged, deadline expires               | NORMAL | `initBond`                  | —                           | —                |
| Unchallenged, proof provided                 | NORMAL | `initBond`                  | —                           | nothing          |
| Challenged, no proof                         | NORMAL | nothing                     | `initBond + challengerBond` | —                |
| Challenged, proof, prover == proposer        | NORMAL | `initBond + challengerBond` | nothing                     | _(same)_         |
| Challenged, proof, prover != proposer        | NORMAL | `initBond`                  | nothing                     | `challengerBond` |
| Parent `CHALLENGER_WINS`, child challenged   | NORMAL | nothing                     | `initBond + challengerBond` | —                |
| Parent `CHALLENGER_WINS`, child unchallenged | NORMAL | nothing (burned)            | —                           | —                |
| Game blacklisted                             | REFUND | `initBond`                  | `challengerBond`            | —                |
| Game retired                                 | REFUND | `initBond`                  | `challengerBond`            | —                |

## Closing

After resolution, bonds are distributed through a two-phase process identical to the
`FaultDisputeGame`:

**`closeGame()`** (permissionless, also called internally by `claimCredit`):

- MUST revert if `AnchorStateRegistry` is paused.
- MUST revert with `GameNotResolved` if `resolvedAt == 0`.
- MUST wait for the finality delay: `block.timestamp - resolvedAt > DISPUTE_GAME_FINALITY_DELAY_SECONDS`.
- If the game has a Valid Claim, registers the game as the new anchor state via `AnchorStateRegistry`.
- Determines NORMAL or REFUND mode and unlocks bonds in `DelayedWETH` accordingly.

**`claimCredit(recipient)`**:

1. Triggers `closeGame()` if not yet closed.
2. Calls `DelayedWETH.unlock(recipient)` to queue the withdrawal. If `recipient` has no credit
   allocated by this game, the unlock has no effect.
3. After the `DelayedWETH` delay, `withdraw()` transfers ETH to the recipient.

The `DelayedWETH` delay allows the Guardian to pause and freeze funds if a critical issue is
discovered post-resolution.
