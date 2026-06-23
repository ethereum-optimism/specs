# ZK Dispute Game Migration

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [In-Flight Withdrawal Safety](#in-flight-withdrawal-safety)
- [Common Mechanics](#common-mechanics)
- [Path A: SFDG → ZKDG (Isolated Chain)](#path-a-sfdg-%E2%86%92-zkdg-isolated-chain)
- [Path B: SPDG → ZKDG (Isolated Chain)](#path-b-spdg-%E2%86%92-zkdg-isolated-chain)
- [Path C: Shared SFDG → Shared ZKDG](#path-c-shared-sfdg-%E2%86%92-shared-zkdg)
  - [Shared Infrastructure and Idempotent Upgrades](#shared-infrastructure-and-idempotent-upgrades)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

All migrations from an existing dispute game type to `ZKDisputeGame` are performed via
`OPCMv2.upgrade()`. No standalone `migrate()` contract is in scope. Three migration paths are
supported:

| Path | Source | Target | Context |
| --- | --- | --- | --- |
| **A** | `SuperFaultDisputeGame` (SFDG) | `ZKDisputeGame` (ZKDG) | Isolated chain |
| **B** | `SuperPermissionedDisputeGame` (SPDG) | `ZKDisputeGame` (ZKDG) | Isolated chain |
| **C** | `SuperFaultDisputeGame` (SFDG) | `ZKDisputeGame` (ZKDG) | Interop set (e.g., OPM + Unichain) |

All paths share the same core mechanics. Path-specific differences are concentrated in a small
number of steps.

## In-Flight Withdrawal Safety

MCP clones embed the implementation address at deployment time. Old SFDG/SPDG game clones created
before the migration retain their original implementation bytecode forever. New game clones
created after `setImplementation()` in `DisputeGameFactory` use the `ZKDG` implementation.

`wasRespectedGameTypeWhenCreated` is snapshotted at game creation. `AnchorStateRegistry.isGameClaimValid()`
reads this flag during withdrawal finalization. Games created under the old respected type remain
valid for in-flight withdrawal finalization even after the migration.

`rootClaimByChainId` is declared on all game types in scope (SFDG, SPDG, ZKDG). The Portal
calls it on all games whose type is in the `isSuperGame` allowlist. Old games already return the
correct answer via their existing implementation. No special handling is needed for pre-migration
games during Portal withdrawal verification.

## Common Mechanics

The following steps are executed in every migration path via `OPCMv2.upgrade()`:

1. **Deploy the new implementation.** Deploy `ZKDisputeGame` and register it in
   `OPContractsManagerContainer.Implementations`.

2. **Swap the implementation in `DisputeGameFactory`.** Call the 3-argument overload:

   ```solidity
   disputeGameFactory.setImplementation(
       GameTypes.ZK_GAME_TYPE,
       address(zkImpl),
       gameArgs  // variable-length CWIA bytes
   );
   ```

   Old game clones are unaffected. New games created after this call use `zkImpl`.

3. **Disable the old implementation.**

   ```solidity
   disputeGameFactory.setImplementation(sourceGameType, address(0), "");
   ```

   This prevents new games from being created under the old type.

4. **Update the respected game type in `AnchorStateRegistry`.**

   ```solidity
   anchorStateRegistry.setRespectedGameType(GameTypes.ZK_GAME_TYPE);
   ```

5. **Add `ZK_GAME_TYPE` to `GameTypes.isSuperGame()`.** Required for `OptimismPortal`
   to call `rootClaimByChainId` on `ZKDG` games during withdrawal verification. If this was
   already shipped at initial `ZKDG` launch, this step is a no-op.

6. **Reinitialize `AnchorStateRegistry` (no-op for these paths).** Both SFDG and SPDG already
   commit to super roots — the same `bytes32` hash format that `ZKDG` uses as its starting
   state. The existing anchor root is therefore a valid starting point for `ZKDG` parent
   validation without modification. No ASR reinitializer is required for Path A, B, or C.

   > **Note:** An ASR reinitializer would only be necessary when migrating from a classic
   > `FaultDisputeGame` (which commits to a per-chain output root rather than a super root). That
   > path is not in scope here.

## Path A: SFDG → ZKDG (Isolated Chain)

Single chain with its own `DisputeGameFactory`, `AnchorStateRegistry`, and `OptimismPortal`.

Execute [Common Mechanics](#common-mechanics) in a single `OPCMv2.upgrade()` call.

The ASR reinitializer fires once. No idempotency concerns arise since there is only one chain in
scope.

## Path B: SPDG → ZKDG (Isolated Chain)

Single chain currently using the permissioned dispute game, migrating to permissionless ZK proofs.

Execute [Common Mechanics](#common-mechanics) in a single `OPCMv2.upgrade()` call with the
following additional considerations:

- Cross-mode transition: this is a permissioned → permissionless transition. The OPCM upgrade
  logic MUST explicitly allow `SPDG → ZK_GAME_TYPE` as a valid source-to-target game type
  pair (i.e., it cannot assume source and target share the same permission model).
- Operational readiness: permissionless infrastructure (op-challenger, prover network) MUST be
  operational and funded before the respected game type is switched. This is the chain operator's
  responsibility and is not enforced by OPCM, but MUST be verified prior to executing the upgrade.

## Path C: Shared SFDG → Shared ZKDG

> **Note:** This path is intended as future work. The design below documents the intended approach
> but has not yet been implemented.

This case covers chains sharing a single `DisputeGameFactory`,
`AnchorStateRegistry`, and `ETHLockbox` under the interop model.

Execute [Common Mechanics](#common-mechanics). Because multiple chains share the same
`AnchorStateRegistry`, steps 4 and 5 (updating the respected game type and the `isSuperGame`
allowlist) affect the shared ASR and must be applied exactly once regardless of how many chains
are in the interop set.

### Shared Infrastructure and Idempotent Upgrades

`OPCMv2.upgrade()` was designed to process one chain at a time. When applied to an interop set,
the shared `AnchorStateRegistry` upgrade steps may be triggered multiple times (once per chain
processed). Two approaches are available:

Option 1 — Idempotent operations: Design the ASR update steps so that applying them a second time
for a subsequent chain in the set is a safe no-op (e.g., a stateful check such as "already set to
this game type").

Option 2 — Multi-chain bulk function: Introduce a function that accepts multiple `SystemConfig`
addresses, upgrades shared infrastructure once, and handles per-chain state in a loop. This
follows the existing bulk migration patterns but is scoped to the SFDG → ZKDG transition.

The choice between these options is left to the OPCM implementation. Either approach MUST
guarantee that shared infrastructure (ASR, ETHLockbox) is updated exactly once, regardless of
how many chains are in the interop set.

Because SFDG already commits to super roots, no ASR anchor reinitialization is required (see
step 6 in [Common Mechanics](#common-mechanics)).
