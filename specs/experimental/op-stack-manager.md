# OP Stack Manager

[`op-contracts/v1.3.0`]: https://github.com/ethereum-optimism/optimism/releases/tag/op-contracts%2Fv1.3.0
[Optimism Monorepo releases]: https://github.com/ethereum-optimism/optimism/releases
[contract releases]: https://github.com/ethereum-optimism/optimism/blob/main/packages/contracts-bedrock/VERSIONING.md
[interop specification]: ../interop/overview.md
[ethereum-optimism/specs#94]: https://github.com/ethereum-optimism/specs/issues/94
[admin roles]: https://specs.optimism.io/protocol/configurability.html#admin-roles
[`SystemConfig` contract]: https://github.com/ethereum-optimism/optimism/blob/op-contracts/v1.3.0/packages/contracts-bedrock/src/L1/SystemConfig.sol
[`L2OutputOracle` contract]: https://github.com/ethereum-optimism/optimism/blob/op-contracts/v1.3.0/packages/contracts-bedrock/src/L1/L2OutputOracle.sol
[standard configuration]: ../protocol/configurability.md
[superchain registry]: https://github.com/ethereum-optimism/superchain-registry
[ethereum-lists/chains]: https://github.com/ethereum-lists/chains
[Batch Inbox]: ../protocol/configurability.md#consensus-parameters

The OP Stack Manager is a contract that deploys the L1 contracts for an OP Stack chain in a single
transaction. It provides a minimal set of user-configurable parameters to ensure that the resulting
chain meets the [standard configuration] requirements.

The version deployed is always a governance-approved contract release. The set
of governance approved [contract releases] can be found on the
[Optimism Monorepo releases] page, and is the set of releases named
`op-contracts/vX.Y.Z`.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

**Table of Contents**

- [OP Stack Manager](#op-stack-manager)
  - [Deployment](#deployment)
  - [Interface](#interface)
    - [`deploy`](#deploy)
    - [Getter Methods](#getter-methods)
  - [Implementation](#implementation)
    - [Batch Inbox Address](#batch-inbox-address)
    - [Contract Deployments](#contract-deployments)
  - [Security Considerations](#security-considerations)
    - [Chain ID Source of Truth](#chain-id-source-of-truth)
    - [Chain ID Frontrunning](#chain-id-frontrunning)
    - [Chain ID Value](#chain-id-value)
    - [Proxy Admin Owner](#proxy-admin-owner)
    - [Upgradeability (ABI Changes)](#upgradeability-abi-changes)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Deployment

The OP Stack Manager is deployed at `0xTODO`. It can be deployed as follows:

TODO.

## Interface

Version 1.0.0 of the OP Stack Manager deploys the [`op-contracts/v1.3.0`]
contracts release.

### `deploy`

The `deploy` method is the only non-view method in the contract. It is used to
deploy the full set of L1 contracts required to setup a new OP Stack chain that
complies with the [standard configuration]. It has the following interface:

```solidity
function deploy(
  uint64 l2ChainId,
  address proxyAdminOwner,
  SystemConfigInputs memory systemConfigInputs,
  L2OutputOracleInputs memory l2OutputOracleInputs
) external returns (SystemConfig systemConfig);
```

where:

- `l2ChainId` is the chain ID of the OP Stack chain.
- `proxyAdminOwner` is the address that will own the `ProxyAdmin` contract that will be deployed.
This corresponds to the L1 ProxyAdmin owner and L2 ProxyAdmin owner [admin roles].
- `systemConfigInputs` is a struct defining configuration of the `SystemConfig` inputs.
- `l2OutputOracleInputs` is a struct defining configuration of the `L2OutputOracle` inputs.

The `l2ChainId` has the following restrictions:

- It is limited to a `uint64`. This contradicts the [interop specification],
which allows chain ID to be a `uint256`. This contradiction exists because it is
currently unspecified how to unify a 256-bit chain ID with the existing batch inbox
address convention, as tracked in [ethereum-optimism/specs#94]. This limitation
may be removed in a future version of the OP Stack Manager once a solution to
that issue is found.
- It must not be equal to 0.
- It must not be equal to the chain ID of the chain the OP Stack Manager is
deployed on.
- It must not be equal to a chain ID that is already present in the
[ethereum-lists/chains] repository. This is not enforced onchain, but may matter
for future versions of OP Stack Manager that handle upgrades via a privileged role.

The `SystemConfigInputs` struct is defined as follows:

```solidity
struct SystemConfigInputs {
  address systemConfigOwner;
  uint256 overhead;
  uint256 scalar;
  bytes32 batcherHash;
  address unsafeBlockSigner;
}
```

Details on each parameter can be found in the code comments of the [`SystemConfig` contract].
Note that not all `SystemConfig` parameters are able to be configured.
This is because the OP Stack Manager enforces compliance with the [standard configuration], and only allows
configuration where allowed by the standard configuration.

The `L2OutputOracleInputs` struct is defined as follows:

```solidity
struct L2OutputOracleInputs {
  address proposer;
  address challenger;
}
```

Details on each parameter can be found in the code comments of the [`L2OutputOracle` contract].
Note that not all `L2OutputOracle` parameters are able to be configured, for the same reason as the `SystemConfig`.

On success, the following event is emitted:

```solidity
event Deployed(uint256 indexed l2ChainId, SystemConfig indexed systemConfig);
```

This method reverts on failure. This occurs when:

- The input `l2ChainId` does not comply with the restrictions above.
- The resulting configuration is not compliant with the [standard configuration].

### Getter Methods

The following interface defines the available getter methods:

```solidity
/// @notice The logic address and initializer selector for an implementation contract.
struct Implementation {
  address logic; // Address containing the deployed logic contract.
  bytes4 initializer; // Function selector for the initializer.
}

/// @notice Returns the latest approved release of the OP Stack contracts.
/// @notice Release strings follow semver and are named with the
/// format `op-contracts/vX.Y.Z`.
function latestRelease() external view returns (bytes32);

/// @notice Maps a release version to a contract name to its implementation data.
function implementation(
  bytes32 release,
  bytes32 contractName
) external view returns (Implementation memory);

/// @notice Maps an L2 Chain ID to the SystemConfig address for that chain.
/// @notice Most information for a chain can be found from it's the SystemConfig,
/// with ProtocolVersions being the exception. ProtocolVersions is a singleton
/// for all chains deployed by this contract.
function systemConfig(uint256 chainId) external view returns (SystemConfig);
```

## Implementation

### Batch Inbox Address

Limiting the L2 chain ID to a `uint64` allows the chain's [Batch Inbox] address
to be computed and set by the OP Stack Manager at `deploy` time. The batch
inbox address follows the convention `0xFF000...000{l2ChainId}`. Specifically,
it is computed as follows:

```solidity
/// @notice Maps an L2 chain ID to an L1 batch inbox address of the
/// form `0xFF000...000{chainId}`.
function chainIdToBatchInboxAddress(uint256 l2ChainId) public pure returns (address) {
    return address(uint160(0xFF) << 152 | uint160(l2ChainId));
}
```

This provides the property of ensuring a chain's batch inbox address can be
derived as a pure function of chain ID. Aside from the UX benefit of easily
converting between batch inbox address and chain ID, it also ensures
uniqueness of batch inbox addresses.

### Contract Deployments

All contracts deployed by the OP Stack Manager are deployed with CREATE2, with a
salt equal to either:

- The L2 chain ID, or
- `keccak256(bytes.concat(bytes32(uint256(l2ChainId)), contractName))`.

The former is used when we are only deploying a single instance of given bytecode
which is the case for the `ProxyAdmin`, `L1ChugSplashProxy`, `ResolvedDelegateProxy`, and `AddressManager` contracts.

The latter is used when we are deploying multiple instances of given bytecode,
which is the case of all `Proxy` contracts. For these, the `contractName`
is the name of the implementation contract that will be used with the proxy.

This provides the following benefits:

- All contract addresses for a chain can be derived as a function of chain
ID without any RPC calls.
- Chain ID uniqueness is enforced for free, as a deploy using the same chain ID
will result in attempting to deploy to the same address, which is prohibited by
the EVM.
  - This property is contingent on the proxy and `AddressManager` code not
  changing when OP Stack Manager is upgraded. Both of these are not planned to
  change.

## Security Considerations

### Chain ID Source of Truth

One of the restrictions on chain ID is that `deploy` can only be called once per
chain ID, because contract addresses are a function of chain ID. However,
future versions of OP Stack Manager may manage upgrades, which will require
"registering" existing pre-OP Stack Manager chains in the OP Stack Manager.
Registration will be a privileged action, and the [superchain registry] will be
used as the source of truth for registrations.

This means, for example, if deploying a chain with a chain ID of 10—which is OP
Mainnet's chain ID—deployment will execute successfully, but the entry in OP
Stack Manager may be overwritten in a future upgrade. Therefore, it is strongly
recommended to only use chain IDs that are not already present in the
[ethereum-lists/chains] repository.

### Chain ID Frontrunning

Contract addresses for a chain are a function of chain ID, which implies you
can counterfactually compute and use those chain addresses before the chain is
deployed. However, this property should not be relied upon—new chain deployments
are permissionless, so you cannot guarantee usage of a given chain ID, as deploy
transactions can be frontrun.

### Chain ID Value

While not specific to OP Stack Manager, when choosing a chain ID is important
to consider that not all chain IDs are well supported by tools. For example,
MetaMask [only supports](https://gist.github.com/rekmarks/a47bd5f2525936c4b8eee31a16345553)
chain IDs up to `4503599627370476`, well below the max allowable `uint64` value.

OP Stack Manager does not consider factors such as these. The EVM supports
256-bit chain IDs, so OP Stack Manager sticks with the full `uint64` range to
maximize compatibility.

### Proxy Admin Owner

The proxy admin owner is a very powerful role, as it allows upgrading protocol
contracts. When choosing the initial proxy admin owner, a Safe is recommended
to ensure admin privileges are sufficiently secured.

### Upgradeability (ABI Changes)

This contract is upgradeable, and breaking changes are expected, as upgrades
are required to update the contracts release that is deployed. This is because
the required inputs to the `deploy` method may change as new contract releases
are supported. Therefore, if calling this contract from another contract, be
sure to account for future breaking changes to the ABI.
