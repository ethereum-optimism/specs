# Predictive Chain Deployments: Contracts

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
  - [ChainContracts struct](#chaincontracts-struct)
  - [FullConfig](#fullconfig)
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
  - [OPCMv2 config validation](#opcmv2-config-validation)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

This document describes the contracts changes that are part of the implementation of the
[Predictive Chain Deployments (PCD) design](https://github.com/ethereum-optimism/design-docs/pull/385). The bulk of
the work is on the `op-deployer` side and the Solidity surface is deliberately minimal: one on-chain contract change
(`OPContractsManagerV2`) and one Forge script (`DeployOPChain.s.sol`).

1. **[`DeployOPChain` script](#deployopchain-script)**: broadcasts a permissionless deployment with a real
   `startingAnchorRoot` and `absolutePrestate` instead of the `0xdead` placeholder and the permissioned default. It
   also updates the script's post-deploy validation, which today asserts the permissioned dispute game as the
   respected game type and would otherwise reject a permissionless deployment.
2. **[`OPCMv2._assertValidFullConfig`](#opcmv2-config-validation)**: updated so OPCM config
   validation accepts permissionless deployment configurations instead of reverting.

## Definitions

See [Salt Mixer](./overview.md#salt-mixer) and [Anchor Block](./overview.md#anchor-block).

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

Once the PCD pipeline has built the `startingAnchorRoot` and the per-game `absolutePrestate`, it fills these fields
with real values instead of placeholders: `startingAnchorRoot` is the genesis
[output root](./overview.md#output-root) with `l2SequenceNumber = 0`, and the per-game `absolutePrestate` is carried
inside `disputeGameConfigs`.

## Assumptions

### aPCD-001: OPCM address determinism

OPCM deploys proxies with CREATE2 using a salt derived from `msg.sender` and `saltMixer`, and no other inputs that
change across executions.
Given the same sender and config, against the same OPCM, the produced addresses are identical.

#### Mitigations

- The dry-run executes the full `OPCM.deploy()` logic without broadcasting, exercising the same code path as the
  real broadcast.

### aPCD-002: Dry-run and broadcast use the same sender and `saltMixer`

The address prediction is only valid if the dry-run uses the same `from` address and `saltMixer` as the eventual broadcast,
since `msg.sender` and `saltMixer` are inputs to the CREATE2 salt.

#### Mitigations

- op-deployer MUST use the same `from` address and `saltMixer` for the dry-run and the broadcast (see
  [FM2](./op-deployer.md#failure-modes)).
- A pre-broadcast preflight re-checks the predicted addresses against current L1 state before deploying.

### aPCD-003: Trusted L1 RPC

The dry-run result is only trustworthy if the L1 RPC is not compromised and returns honest results.

#### Mitigations

- Use an independent, trusted RPC.
- Cross-check the dry-run against a second, independent L1 RPC. Divergent addresses flag a compromised endpoint before
  broadcast (see [FM3](./op-deployer.md#failure-modes)).

## Invariants

### iPCD-001: Predicting the L1 addresses is a no-op

Running the prediction MUST NOT write any state to L1.

#### Impact

**Severity: High**

A prediction that mutated state could change the very addresses it is meant to predict.

### iPCD-002: Permissioned deployments remain valid

The updated `_assertValidFullConfig` MUST still accept every `FullConfig` that was valid before this change.

#### Impact

**Severity: High**

If violated, valid configurations for permissioned deployments would be blocked.

### iPCD-003: Invalid configurations stay rejected

The updated `_assertValidFullConfig` MUST still reject every `FullConfig` that was invalid before this change, apart
from enabling other dispute game types at initial deployment.

#### Impact

**Severity: Critical**

If violated, OPCM could accept an invalid dispute configuration at deployment.

## Change Specification

Two changes are needed on the Solidity surface. `DeployOPChain` predicts the L1 addresses that seed the genesis
pipeline and later broadcasts the deployment. The OPCM change lets that broadcast enable a permissionless game at
initial deployment.

### DeployOPChain script

`DeployOPChain.s.sol` builds the `FullConfig` and runs `OPCM.deploy()`. `op-deployer` uses the same
script for two roles: predicting the L1 addresses (a dry-run) and broadcasting the real deployment.
Using the same script for both ensures the predicted addresses are equal to the deployed ones
(see [iOPD-001](./op-deployer.md#iopd-001-the-deployed-l1-system-matches-the-committed-artifacts)).

#### Address prediction

`DeployOPChain` predicts the [`ChainContracts`](#chaincontracts-struct) for a given [`FullConfig`](#fullconfig).

**Behavior:**

- MUST execute `OPCM.deploy()` against the current L1 state.
- MUST use the same `from` address that will be used for the real broadcast.
- MUST NOT broadcast or otherwise write state to L1.
- MUST return the predicted [`ChainContracts`](#chaincontracts-struct) addresses to the caller.

#### Broadcasting a permissionless deployment

Today the script hard-codes a permissioned-only initial deployment:

- It `require`s the initial game type to be `PERMISSIONED_CANNON` (or `SUPER_PERMISSIONED_CANNON` in super-root mode),
  reverting with *"only PERMISSIONED_CANNON game type is supported for initial deployment"*.
- It builds the six `disputeGameConfigs` with the permissionless types disabled.
- It sets `startingRespectedGameType` to the permissioned type and `startingAnchorRoot` to a placeholder.

In order to support permissionless deployments the script is updated to:

- MUST permit an arbitrary dispute game type as `startingRespectedGameType` at initial deployment.
- MUST enable the permissionless `disputeGameConfigs` entries, each carrying its real `absolutePrestate`.
- MUST pass the real genesis output root as `startingAnchorRoot` instead of the placeholder.
- MUST continue to support permissioned-only deployments.
- MUST use a `from` address consistent with the [address-prediction](#address-prediction) dry-run, so the deployed
  addresses match the prediction (see
  [iOPD-001](./op-deployer.md#iopd-001-the-deployed-l1-system-matches-the-committed-artifacts)).

Carrying those values into the script requires extending its Solidity input struct. `Types.DeployOPChainInput`
(`scripts/libraries/Types.sol`) today exposes only a single `disputeGameType` and
`disputeAbsolutePrestate`. It MUST gain a `startingAnchorRoot` field
and per-game-type prestate hashes so a permissionless config can be included.

### OPCMv2 config validation

`OPContractsManagerV2._assertValidFullConfig(FullConfig, bool _isInitialDeployment)` validates the config before
`_apply` runs. An initial deployment always reaches this check with `_isInitialDeployment = true`. Relaxing the
script guard in [`DeployOPChain`](#deployopchain-script) alone is not enough, because `OPCM.deploy()` would still
revert here.

During an initial deployment, enabling any permissionless game type reverts with
`OPContractsManagerV2_InvalidGameConfigs`, on the premise that no prestate exists yet:

```solidity
// During initial deployment, only permissioned types can be enabled, because no
// prestate exists for permissionless games.
if (_isInitialDeployment && !isPermissioned && _cfg.disputeGameConfigs[i].enabled) {
    revert OPContractsManagerV2_InvalidGameConfigs();
}
```

PCD invalidates that premise. A real prestate now exists at deployment time. The change:

- MUST allow a permissionless game type to be `enabled` during an initial deployment.
- MUST keep every other validation intact:
  - exactly six configs in the fixed game-type order,
  - the init-bond rules,
  - the `ZK_DISPUTE_GAME` dev-flag gate, and
  - `startingRespectedGameType` must correspond to an enabled config.
