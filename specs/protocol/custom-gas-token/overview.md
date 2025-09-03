# Custom Gas Token Mode

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

**Table of Contents**

- [Execution Layer](#execution-layer)
- [Consensus Layer](#consensus-layer)
- [Smart Contracts](#smart-contracts)
  - [Core L2 Smart Contracts](#core-l2-smart-contracts)
    - [Custom Gas Token](#custom-gas-token)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

This document is not finalized and should be considered experimental.

## Execution Layer

## Consensus Layer

## Smart Contracts

- [Predeploys](./predeploys.md)
- [Bridges](./bridges.md)
- [Cross Domain Messengers](./messengers.md)
- [System Config](./system-config.md)
- [Withdrawals](./withdrawals.md)
- [Optimism Portal](./optimism-portal.md)

### Core L2 Smart Contracts

#### Custom Gas Token

The Custom Gas Token (CGT) feature allows OP Stack chains to use a native asset other than ETH as the gas
currency. This implementation introduces a streamlined approach with minimal core code intrusion through a
single `isCustomGasToken()` flag.

Key components:

- **NativeAssetLiquidity**: A predeploy contract containing pre-minted native assets, deployed only for
  CGT-enabled chains.
- **LiquidityController**: An owner-governed mint/burn router that manages supply control, deployed only for
  CGT-enabled chains.
- **ETH Transfer Blocking**: When CGT is enabled, all ETH transfer flows in bridging methods are disabled via
  the `isCustomGasToken()` flag.
- **ETH Bridging Disabled**: ETH bridging functions in `L2ToL1MessagePasser` and `OptimismPortal` MUST revert
  when CGT mode is enabled to prevent confusion about which asset is the native currency.
- **ETH as an ERC20 representation**: ETH can be bridged by wrapping it as an ERC20 token (e.g., WETH) and using the `StandardBridge` to mint an `OptimismMintableERC20` representation.

OP Stack chains that use a native asset other than ETH (or the native asset of the settlement layer)
introduce custom requirements that go beyond the current supply management model based on deposits and
withdrawals. This architecture decouples and winds down the native bridging for the native asset, shifting
the responsibility for supply management to the application layer. The chain operator becomes responsible
for defining and assigning meaning to the native asset, which is managed through a new set of predeployed
contracts.

This approach preserves full alignment with EVM equivalence and client-side compatibility as provided by the
standard OP Stack. No new functionalities outside the execution environment are required to make it work.
