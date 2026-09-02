# Predictive Chain Deployments: Contracts

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
  - [ChainContracts struct](#chaincontracts-struct)
  - [FullConfig](#fullconfig)
  - [Supported initial game types](#supported-initial-game-types)
- [Assumptions](#assumptions)
  - [aPCD-001: OPCM address determinism](#apcd-001-opcm-address-determinism)
    - [Mitigations](#mitigations)
  - [aPCD-002: Dry-run and broadcast use the same sender and `saltMixer`](#apcd-002-dry-run-and-broadcast-use-the-same-sender-and-saltmixer)
    - [Mitigations](#mitigations-1)
  - [aPCD-003: Trusted L1 RPC](#apcd-003-trusted-l1-rpc)
    - [Mitigations](#mitigations-2)
- [Invariants](#invariants)
  - [iPCD-001: Predicting the L1 addresses is a no-op](#ipcd-001-predicting-the-l1-addresses-is-a-no-op)
    - [Impact](#impact)
  - [iPCD-002: Permissioned deployments remain valid](#ipcd-002-permissioned-deployments-remain-valid)
    - [Impact](#impact-1)
  - [iPCD-003: Invalid configurations stay rejected](#ipcd-003-invalid-configurations-stay-rejected)
    - [Impact](#impact-2)
- [Change Specification](#change-specification)
  - [DeployOPChain script](#deployopchain-script)
    - [Address prediction](#address-prediction)
    - [Broadcasting a permissionless deployment](#broadcasting-a-permissionless-deployment)
    - [Script inputs](#script-inputs)
  - [OPCMv2 config validation](#opcmv2-config-validation)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

This document describes the contracts changes that are part of the implementation of the
[Predictive Chain Deployments (PCD) design](https://github.com/ethereum-optimism/design-docs/blob/main/ecosystem/op-deployer/predictive-chain-deployments/pcd-design.md).
The bulk of the work is on the `op-deployer` side. The Solidity surface is limited to one on-chain contract
(`OPContractsManagerV2`) and one Forge script (`DeployOPChain.s.sol`).

1. **[`DeployOPChain` script](#deployopchain-script)**: broadcasts a permissionless deployment with a real
   `startingAnchorRoot` and `absolutePrestate` instead of the `0xdead` placeholder and the permissioned default. It
   also updates the script's post-deploy validation, which today asserts the permissioned dispute game as the
   respected game type and would otherwise reject a permissionless deployment.
2. **[`OPCMv2._assertValidFullConfig`](#opcmv2-config-validation)**: updated so OPCM config
   validation accepts permissionless deployment configurations instead of reverting.

## Definitions

See [Salt Mixer](./overview.md#salt-mixer), [Anchor Block](./overview.md#anchor-block),
[Selected Prestate](./overview.md#selected-prestate) and [Fallback Prestate](./overview.md#fallback-prestate).

### ChainContracts struct

The struct returned by `OPCM.deploy()` containing the deployed proxy addresses for the chain's L1 contracts. Defined
in `OPContractsManagerV2` (`src/L1/opcm/OPContractsManagerV2.sol`):

```solidity
struct ChainContracts {
    ISystemConfig systemConfig;
    IProxyAdmin proxyAdmin;
    IAddressManager addressManager;
    IL1CrossDomainMessenger l1CrossDomainMessenger;
    IL1ERC721Bridge l1ERC721Bridge;
    IL1StandardBridge l1StandardBridge;
    IOptimismPortal optimismPortal;
    IETHLockbox ethLockbox;
    IOptimismMintableERC20Factory optimismMintableERC20Factory;
    IDisputeGameFactory disputeGameFactory;
    IAnchorStateRegistry anchorStateRegistry;
    IDelayedWETH delayedWETH;
}
```

The `op-deployer` consumes a subset of these addresses when building the genesis and rollup artifacts:

- `l1CrossDomainMessenger`, `l1StandardBridge`, `l1ERC721Bridge` are inputs to `L2Genesis.s.sol` (the
  [L2 allocs](./overview.md#l2-allocs)).
- `optimismPortal` and `systemConfig` are written into `rollup.json`.

### FullConfig

The configuration struct passed into `OPCM.deploy()`. Defined in `OPContractsManagerV2.FullConfig`
(`src/L1/opcm/OPContractsManagerV2.sol`):

```solidity
struct FullConfig {
    string saltMixer;
    ISuperchainConfig superchainConfig;
    address proxyAdminOwner;
    address systemConfigOwner;
    address unsafeBlockSigner;
    address batcher;
    Proposal startingAnchorRoot;
    GameType startingRespectedGameType;
    uint32 basefeeScalar;
    uint32 blobBasefeeScalar;
    uint64 gasLimit;
    uint256 l2ChainId;
    IResourceMetering.ResourceConfig resourceConfig;
    IOPContractsManagerUtils.DisputeGameConfig[] disputeGameConfigs;
    bool useCustomGasToken;
}
```

Once the PCD pipeline has built the [starting anchor root](./overview.md#starting-anchor-root) and the
[selected prestate](./overview.md#selected-prestate), it fills these fields with real values instead of placeholders.
The prestate is carried inside the permissionless `disputeGameConfigs` entry being enabled.

### Supported initial game types

`disputeGameConfigs` always holds six entries in a fixed order. Which of them may be `enabled` at initial deployment
depends on whether the OPCM has the `SUPER_ROOT_GAMES_MIGRATION` dev feature on:

| Index | Game type | Enabled at initial deployment |
| --- | --- | --- |
| 0 | `CANNON` | Never. Legacy slot |
| 1 | `PERMISSIONED_CANNON` | Output root mode only |
| 2 | `CANNON_KONA` | Output root mode only |
| 3 | `SUPER_PERMISSIONED` | Super root mode only |
| 4 | `SUPER_CANNON_KONA` | Super root mode only |
| 5 | `ZK_DISPUTE_GAME` | Never at initial deployment. Reachable through the upgrade path |

`startingRespectedGameType` must be one of the four selectable types and **must belong to the OPCM's mode**.

## Assumptions

### aPCD-001: OPCM address determinism

OPCM deploys proxies with CREATE2 using a salt derived from `msg.sender` and `saltMixer`, and no other inputs that
change across executions.
Given the same sender and salt mixer, against the same OPCM, the produced addresses are identical.

#### Mitigations

- The dry-run executes the full `OPCM.deploy()` logic without broadcasting, exercising the same code path as the
  real broadcast.
- The remaining `FullConfig` fields do not feed the salt, so the placeholders the dry-run substitutes for them (see
  [Address prediction](#address-prediction)) cannot change the predicted addresses.

### aPCD-002: Dry-run and broadcast use the same sender and `saltMixer`

The address prediction is only valid if the dry-run uses the same `from` address and `saltMixer` as the eventual
broadcast, since `msg.sender` and `saltMixer` are inputs to the CREATE2 salt.

#### Mitigations

- op-deployer MUST use the same `from` address and `saltMixer` for the dry-run and the broadcast (see
  [FM2](./op-deployer.md#failure-modes)).
- The salt mixer is generated once and stored in op-deployer state, so separate command invocations reuse it rather
  than deriving it again (see [Salt Mixer](./overview.md#salt-mixer)).
- `prepare` and `continue` both reject a run whose deployer or OPCM differs from the one recorded in state.
- A pre-broadcast preflight re-checks the predicted addresses against current L1 state before deploying.

### aPCD-003: Trusted L1 RPC

The dry-run result is only trustworthy if the L1 RPC is not compromised and returns honest results.

#### Mitigations

- Use an independent, trusted RPC.
- `continue` re-simulates the deployment against a fresh fork before broadcasting, and post-deploy validation re-reads
  the deployed system from live L1 (see [FM3](./op-deployer.md#failure-modes)).

## Invariants

### iPCD-001: Predicting the L1 addresses is a no-op

Running the prediction MUST NOT write any state to L1. A write could change the very addresses this stage is meant
to predict.

#### Impact

**Severity: High**

A L1 state write at prediction time also costs the deployer real ETH on what should be a dry-run. Worse, it deploys a
chain that can never be used. Prediction runs before the prestate and the starting anchor root are known, so the
deployment would be seeded with neither.

### iPCD-002: Permissioned deployments remain valid

The updated `_assertValidFullConfig` MUST still accept every permissioned `FullConfig` that was valid before this
change **for an OPCM in the matching mode**: `PERMISSIONED_CANNON` in output root mode, `SUPER_PERMISSIONED` in super
root mode.

#### Impact

**Severity: High**

If violated, valid configurations for permissioned deployments would be blocked.

### iPCD-003: Invalid configurations stay rejected

The updated `_assertValidFullConfig` MUST still reject every `FullConfig` that was invalid before this change, apart
from enabling the permissionless game type of the OPCM's mode at initial deployment.

#### Impact

**Severity: Critical**

If violated, OPCM could accept an invalid dispute configuration at deployment.

## Change Specification

Two changes are needed on the Solidity surface. `DeployOPChain` predicts the L1 addresses that seed the genesis
pipeline and later broadcasts the deployment. The OPCM change lets that broadcast enable a permissionless game at
initial deployment, and checks the values such a deployment now carries.

### DeployOPChain script

`DeployOPChain.s.sol` builds the `FullConfig` and runs `OPCM.deploy()`. `op-deployer` uses the same
script for two roles: predicting the L1 addresses (a dry-run) and broadcasting the real deployment.
Using the same script for both ensures the predicted addresses are equal to the deployed ones
(see [iOPD-001](./op-deployer.md#iopd-001-the-deployed-l1-system-matches-the-committed-artifacts)).

#### Address prediction

`DeployOPChain` predicts the [`ChainContracts`](#chaincontracts-struct) for a given [`FullConfig`](#fullconfig).

**Behavior:**

- MUST execute `OPCM.deploy()` against the current L1 state.
- MUST use the same `from` address and `saltMixer` that will be used for the real broadcast.
- MUST NOT broadcast or otherwise write state to L1.
- MUST return the predicted [`ChainContracts`](#chaincontracts-struct) addresses to the caller.

The dry-run uses placeholders for some of the values. The six chain roles are substituted because prediction must not
depend on them, and the `startingAnchorRoot` because its real value is not known yet:

| Field | Dry-run value | Why |
| --- | --- | --- |
| all six chain roles | a single placeholder address | Roles do not feed the CREATE2 salt |
| `startingAnchorRoot` | a sentinel root for permissionless deploys, the `0xdead` placeholder otherwise | The real root is derived from the addresses being predicted |

Only `msg.sender`, `saltMixer`, `l2ChainId` and the OPCM address determine the deployed addresses, so these
substitutions are safe (see [aPCD-001](#apcd-001-opcm-address-determinism)).

#### Broadcasting a permissionless deployment

Before PCD the script hard-coded a permissioned-only initial deployment:

- It rejected any input game type other than `PERMISSIONED_CANNON`.
- It built the six `disputeGameConfigs` with the permissionless types disabled.
- It set `startingRespectedGameType` to the permissioned type and `startingAnchorRoot` to a placeholder.

In order to support permissionless deployments the script is updated to:

- MUST accept any of the four [supported initial game types](#supported-initial-game-types) as
  `startingRespectedGameType`, and MUST revert on any other game type.
- MUST revert when the requested game type does not belong to the OPCM's mode, so the caller's prestate and proposal
  format always match the games the OPCM installs.
- MUST enable the permissionless `disputeGameConfigs` entry, carrying its real
  [selected prestate](./overview.md#selected-prestate).
- MUST also enable the permissioned game of the same family as a guardian fallback, so a permissionless deployment
  enables **two** configs. `CANNON_KONA` enables `PERMISSIONED_CANNON`, `SUPER_CANNON_KONA` enables
  `SUPER_PERMISSIONED`. The fallback carries the [fallback prestate](./overview.md#fallback-prestate).
- MUST pass the real [starting anchor root](./overview.md#starting-anchor-root) instead of the placeholder, and MUST
  reject the placeholder for a permissionless deployment.
- MUST continue to support permissioned-only deployments.
- MUST use a `from` address consistent with the [address-prediction](#address-prediction) dry-run, so the deployed
  addresses match the prediction (see
  [iOPD-001](./op-deployer.md#iopd-001-the-deployed-l1-system-matches-the-committed-artifacts)).

#### Script inputs

A permissionless deployment supplies three values the script did not previously take:

- the [starting anchor root](./overview.md#starting-anchor-root) seeded into the `AnchorStateRegistry`,
- the [selected prestate](./overview.md#selected-prestate) of the respected game type, and
- for the output root family only, the [fallback prestate](./overview.md#fallback-prestate) of the guardian fallback
  game.

The script MUST reject an output root family input whose selected prestate equals its fallback prestate. They commit
to different fault-proof programs, **so equal values always indicate a misconfigured producer.**

### OPCMv2 config validation

`OPContractsManagerV2._assertValidFullConfig(FullConfig, bool _isInitialDeployment)` validates the config before
`_apply` runs. An initial deployment always reaches this check with `_isInitialDeployment = true`. Relaxing the
script guard in [`DeployOPChain`](#deployopchain-script) alone is not enough, because `OPCM.deploy()` would still
revert here.

Before PCD, enabling any permissionless game type during an initial deployment reverted with
`OPContractsManagerV2_InvalidGameConfigs`, on the premise that no prestate exists yet. PCD invalidates that premise.
A real prestate now exists at deployment time.

The game-type check is replaced by one scoped to the OPCM's mode:

```solidity
// Initial deployments must select game types compatible with the active mode.
bool validForInitialDeploy = superRootGamesMigrationEnabled
    ? (isSuperPermissionedGame || isSuperCannonKonaGame)
    : (isPermissionedCannonGame || isCannonKonaGame);
if (_isInitialDeployment && _cfg.disputeGameConfigs[i].enabled && !validForInitialDeploy) {
    revert OPContractsManagerV2_InvalidGameConfigs();
}
```

PCD then:

- MUST allow the permissionless game type of the OPCM's mode to be `enabled` during an initial deployment.
- MUST reject a game type from the other mode, and MUST keep `CANNON` and `ZK_DISPUTE_GAME` rejected at initial
  deployment (see [Supported initial game types](#supported-initial-game-types)).
- MUST apply the checks PCD adds:
  - `startingAnchorRoot.root` MUST be non-zero on any initial deployment, and its `l2SequenceNumber` MUST leave room
    for a `uint64` successor.
  - The `0xdead` placeholder root MUST be rejected when an enabled config is one of `CANNON`, `CANNON_KONA` or
    `SUPER_CANNON_KONA`. Only a permissioned-only deployment may still carry the placeholder.
  - An enabled config among those same three game types MUST carry a non-zero `absolutePrestate`, decoded from its
    `gameArgs`.
  - `SUPER_PERMISSIONED` MUST carry a zero init bond, whether or not it is enabled.
- MUST keep every other validation OPCM already performs intact:
  - exactly six configs in the fixed game-type order,
  - the init-bond rules for every other game type,
  - the `ZK_DISPUTE_GAME` dev-flag gate plus its non-zero prestate requirement, both reachable only through the
    upgrade path, and
  - `startingRespectedGameType` must correspond to an enabled config.

The value checks reject an unset or placeholder input. They cannot reject a wrong one, since any non-zero prestate and
any non-placeholder root pass (see
[iOPD-003](./op-deployer.md#iopd-003-absoluteprestate-matches-the-committed-chain-config)).
