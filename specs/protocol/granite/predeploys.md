# Protocol Predeploys

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Predeploys](#predeploys)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

[stage-1]: https://ethereum-magicians.org/t/proposed-milestones-for-rollups-taking-off-training-wheels/11571#stage-1-limited-training-wheels-3

## Overview

The OP Stack has a permissive management system for L2 predeploys that makes it
difficult for an OP Stack chain to be considered a [Stage 1 Rollup][stage-1].
This upgrade is meant to solve the problem of chain operators being able to
easily break invariants important to the system by being able to arbitrarily
modify the predeploys themselves.

The `ProxyAdmin` on L2 is upgraded to the `L2ProxyAdmin`, which removes
the code for handling the L1 legacy proxies and delineates cleanly between
system ownership and chain operator ownership of different predeploys.

## Constants

| Constant          | Value                           | Description |
| ----------------- | ------------------------------- | ----------- |
| `PREDEPLOY_COUNT` |  2048 | The total number of predeploys on L2 |
| `L2ProxyAdmin` address | `0x4200000000000000000000000000000000000018` | The predeploy of the `ProxyAdmin` on L2 |
| `DEPOSITOR_ACCOUNT` | `address(0xDeaDDEaDDeAdDeAdDEAdDEaddeAddEAdDEAd0001)` | Account that represents the system |
| `COLLECTIVE_ACCOUNT` | `address(0xDeaDDEaDDeAdDeAdDEAdDEaddeAddEAdDEAd0002)` | Account that represents the collective |
| `CHAIN_ACCOUNT` | `address(0xDeaDDEaDDeAdDeAdDEAdDEaddeAddEAdDEAd0003)` | Account that represents the chain operator |

## System Predeploys

System predeploys are predeploys that can only be modified via protocol upgrades. This means
that the chain governance cannot modify them at the application layer. These predeploys
are important for maintaining protocol level invariants and therefore the security of
the system.

TODO: define range of system predeploys

## Userland Predeploys

Userland predeploys are predeploys that can be modified by governance. They should not
be responsible for managing the security of the system, meaning that if governance was
to go rogue, then the system should still be considered secure.

Userland predeploys are broken down into two categories, collective governed and chain
governed.

TODO: define range of userland predeploys, both collective and chain

### Collective Governed

The collective governed userland predeploys are managed at the superchain level. This means
that the governance of the superchain as a whole is responsible for upgrading these predeploys.

### Chain Governed

The chain governed userland predeploys are managed on a per chain level. This is a commitment
that these predeploys will never be used by the protocol or superchain governance and can be
safely used by the chain operator for whatever purposes they desire.

## L2ProxyAdmin

The `L2ProxyAdmin` is a minimal proxy admin that is the ERC-1967 admin for each of the predeploys.
For any permissioned call, the required caller is different depending on the address that is being
called.

To modify the implementation:
- For system predeploys, it MUST be the `DEPOSITOR_ACCOUNT`
- For collective governed predeploys, it MUST be the `COLLECTIVE_ACCOUNT`
- For chain governed predeploys, it MUST be the `CHAIN_ACCOUNT`

None of these accounts have known private keys, therefore they must come from specially crafted
`TransactionDeposited` events that come from the `OptimismPortal`.

## OptimismPortal

A method for emitting special `TransactionDeposited` events is added to the `OptimismPortal`.
Authorization must be set up such that the only the `SystemConfig` can result in a deposit
transaction from the `CHAIN_ACCOUNT` and only the `SuperchainConfig` can result in a deposit
transaction from the `COLLECTIVE_ACCOUNT`.

## SuperchainConfig

A new method is added that can call an `OptimismPortal` that can only be called by the superchain
governance system.

## Network Upgrade Transactions

TODO: perhaps break this section into its own document

The granite network upgrade includes a routine upgrade
of all L2 predeploys using system transactions. The exact
and upgrade transactions themselves will be finalized in
the future. This ensures that the L1 and L2 pairs of contracts
(CrossDomainMessengers and StandardBridges) don't drift too
far in their versioning.

## Security Considerations

### Why put ownership delineation in the `L2ProxyAdmin`?

This prevents the need for tons of upgrade transactions that change the existing `admin`
values that are set in the predeploys.

### Why use deposit transactions for this management?

This allows the hardfork to be uniform across all chains in the superchain. The config
values that are different live on L1, otherwise we would have to hardfork in a way
that enshrines a particular address (which may be different per L2 network).
This also prevents the need to maintain balances on every chain in the superchain.

### Is this susceptible to deposit transaction griefing?

No, if it follows the same pattern used by the custom gas token upgrade where the
deposit transaction path skips the gas burn and emits a special "system deposit transaction"
that originates on L1. There is precedent for this kind of pattern based on the custom
gas token feature.
