# ZK Dispute Game Migration

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [In-Flight Withdrawal Safety](#in-flight-withdrawal-safety)
- [Common Mechanics](#common-mechanics)
- [Path A: SFDG → ZKDG (Isolated Chain)](#path-a-sfdg-%E2%86%92-zkdg-isolated-chain)
- [Path B: SPDG → ZKDG (Isolated Chain)](#path-b-spdg-%E2%86%92-zkdg-isolated-chain)
- [Path C: Interop Set (Shared Contracts)](#path-c-interop-set-shared-contracts)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

Migrations to `ZKDisputeGame` target chains that already run super-root dispute games. The standard end state
registers `ZK_DISPUTE_GAME` **in addition to** `SUPER_PERMISSIONED` and `SUPER_CANNON_KONA`, and makes
`ZK_DISPUTE_GAME` the respected game type. Both existing super-root game types MUST stay registered, because the
`OPContractsManagerStandardValidator` requires them (see
[Standard Configuration](zk-dispute-game.md#standard-configuration)).

| Path | Respected game type before migration | Context |
| --- | --- | --- |
| **A** | `SUPER_CANNON_KONA` (`SuperFaultDisputeGame`, SFDG) | Isolated chain |
| **B** | `SUPER_PERMISSIONED` (`SuperPermissionedDisputeGame`, SPDG) | Isolated chain |
| **C** | `SUPER_CANNON_KONA` or `SUPER_PERMISSIONED` | Interop set with shared contracts |

Disabling the source game type (`enabled: false`) during the migration is mechanically possible, but it leaves the
chain non-standard (`SPDG-SHAPE` or `SCKDG-SHAPE`).

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

Source-type games created after the respected game type switches to `ZK_DISPUTE_GAME` are not respected
(`wasRespectedGameTypeWhenCreated == false`), so they cannot back withdrawals. Neither mechanism for switching the
respected game type changes `retirementTimestamp`: `AnchorStateRegistry.initialize()` only sets it when it is zero,
and `setRespectedGameType()` does not touch it. Games created before the switch therefore stay valid.

## Common Mechanics

1. **Use an OPCM release that carries the ZK contracts.** The release provides `zkDisputeGameImpl` and
   `sp1PlonkAdapterImpl` (see [OPCM Integration](zk-dispute-game.md#opcm-integration)).

2. **Register `ZK_DISPUTE_GAME` with `OPCMv2.upgrade()`.** The upgrade input contains all six
   `disputeGameConfigs`. The `ZK_DISPUTE_GAME` entry is enabled, has a non-zero `initBond`, and carries
   `abi.encode(ZKDisputeGameConfig)` as `gameArgs`. The `SUPER_PERMISSIONED` and `SUPER_CANNON_KONA` entries stay
   enabled with their current configs. OPCM registers the ZK game with the 3-argument overload and sets its
   init bond:

   ```solidity
   disputeGameFactory.setImplementation(
       GameTypes.ZK_DISPUTE_GAME,
       zkDisputeGameImpl,
       gameArgs  // variable-length CWIA bytes
   );
   disputeGameFactory.setInitBond(GameTypes.ZK_DISPUTE_GAME, initBond);
   ```

   Old game clones are unaffected. New `ZK_DISPUTE_GAME` games use `zkDisputeGameImpl`.

3. **Switch the respected game type to `ZK_DISPUTE_GAME`** with one of:

   1. the same `upgrade()` call, with the extra instruction key `overrides.cfg.startingRespectedGameType` and data
      `abi.encode(GameTypes.ZK_DISPUTE_GAME)`. OPCM re-initializes the `AnchorStateRegistry` with it; or
   2. a later Guardian call:

      ```solidity
      anchorStateRegistry.setRespectedGameType(GameTypes.ZK_DISPUTE_GAME);
      ```

      This lets operators register `ZK_DISPUTE_GAME` first and switch once honest ZK actors are running.

4. **Keep the anchor state.** `upgrade()` always re-initializes the `AnchorStateRegistry`, but it preserves the
   anchor root, the anchor game, the blacklist and `retirementTimestamp`. The starting anchor root cannot be
   overridden during an upgrade. SFDG and SPDG already commit to super roots, the same `bytes32` format that `ZKDG`
   uses, so the existing anchor is a valid starting point for the first `ZKDG` game
   (`parentIndex = type(uint32).max`).

Migrating from a classic output-root `FaultDisputeGame` is not supported: its anchor is not a super root and
cannot be re-seeded during an upgrade.

## Path A: SFDG → ZKDG (Isolated Chain)

Single chain with its own `DisputeGameFactory`, `AnchorStateRegistry`, and `OptimismPortal`.

Execute [Common Mechanics](#common-mechanics) in a single `OPCMv2.upgrade()` call.

## Path B: SPDG → ZKDG (Isolated Chain)

Single chain currently using the permissioned dispute game, migrating to permissionless ZK proofs.

Execute [Common Mechanics](#common-mechanics) in a single `OPCMv2.upgrade()` call with the
following additional consideration:

- Operational readiness: permissionless infrastructure MUST be operational and funded before the respected game
  type is switched, including an honest ZK proposer/prover and challenger (see
  [Honest Actors](honest-actors.md)). This is the chain operator's responsibility and is not enforced by OPCM,
  but MUST be verified prior to executing the upgrade.

## Path C: Interop Set (Shared Contracts)

This case covers chains sharing a single `DisputeGameFactory`, `AnchorStateRegistry`, `DelayedWETH`, and
`ETHLockbox` under the interop model.

- `OPContractsManagerMigrator.migrate()` MAY register `ZK_DISPUTE_GAME` on the shared `DisputeGameFactory`. The
  config MUST be valid, otherwise `migrate()` reverts with `OPContractsManagerMigrator_InvalidZKDisputeGameConfig`.
  Whether `ZK_DISPUTE_GAME` is registered during `migrate()` or only by a later `upgrade()` is a deployment choice.
- The starting respected game type passed to `migrate()` MUST be one that `migrate()` supports, otherwise
  `migrate()` reverts with `OPContractsManagerMigrator_InvalidStartingRespectedGameType`.
- Making `ZK_DISPUTE_GAME` the respected game type is OPTIONAL at migration time. `ZK_DISPUTE_GAME` becomes the
  respected game type either directly through `migrate()`, where `migrate()` supports it, or after migration
  through mechanism 3.1 on a member's `upgrade()` or mechanism 3.2 (see [Common Mechanics](#common-mechanics)).
- `OPCMv2.upgrade()` on any member routes the upgrade of each shared contract through the `ProxyAdmin` that
  administers it. The shared `AnchorStateRegistry` and `DisputeGameFactory` updates are therefore applied once
  per call and are idempotent across members, as long as every member's upgrade uses the same dispute game
  configs.
