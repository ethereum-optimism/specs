# Karst Deposits

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Network upgrade transactions](#network-upgrade-transactions)
- [EIP-7825 gas-cap exemption](#eip-7825-gas-cap-exemption)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

[deposits]: ../deposits.md

## Overview

The Karst upgrade changes deposit processing. This page lists the changes to the
[deposit specification][deposits].

## Network upgrade transactions

The contents of the transaction are defined by the file
[`karst_nut_bundle.json`](https://github.com/ethereum-optimism/optimism/blob/develop/op-core/nuts/bundles/karst_nut_bundle.json)
in the monorepo, which contains 31 transactions. In addition to the contents of the files, the consensus layer
node MUST prefix each intent string with `Karst <index>:` followed by a space, where `<index>` is the zero-based
position of the transaction within the bundle.

These transactions can be classified into the following groups:

1. **ConditionalDeployer Deployment**: One transaction to deploy the ConditionalDeployer contract
2. **ConditionalDeployer Upgrade** One transaction to upgrade a new predeploy to the ConditionalDeployer implementation
3. **Implementation Deployments**: One transaction for _each_ predeploy being upgraded, to deploy its implementation  
  (26 total)
4. **ProxyAdmin Upgrade** One transactions to upgrade the L2ProxyAdmin implementation
5. **L2ContractsManager Deployment**: One transaction to deploy the L2ContractsManager for this upgrade
6. **Upgrade Execution**: One transactions to call `L2ProxyAdmin.upgradePredeploys(l2ContractsManagerAddress)`

More information regarding the upgrade path implemented by the bundle transactions can be found in [L2 Upgrade Execution](../l2-upgrades-1-execution.md).

## EIP-7825 gas-cap exemption

Deposits are exempt from the EIP-7825 transaction gas cap. Deposits are already subject to a 20M gas limit,
enforced by the L1 contracts.
