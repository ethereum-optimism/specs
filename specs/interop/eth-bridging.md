# ETH Bridging

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Design](#design)
  - [Interface and properties](#interface-and-properties)
    - [`SuperchainETHBridge`](#superchainethbridge)
      - [`sendETH`](#sendeth)
      - [`relayETH`](#relayeth)
    - [`ETHLiquidity`](#ethliquidity)
      - [`mint`](#mint)
      - [`burn`](#burn)
  - [Events](#events)
    - [`SuperchainETHBridge`](#superchainethbridge-1)
      - [`SendETH`](#sendeth)
      - [`RelayETH`](#relayeth)
    - [`ETHLiquidity`](#ethliquidity-1)
      - [`LiquidityMinted`](#liquidityminted)
      - [`LiquidityBurned`](#liquidityburned)
- [Constants](#constants)
- [Invariants](#invariants)
  - [System level invariants](#system-level-invariants)
    - [`ETHLiquidity`](#ethliquidity-2)
  - [Contract level invariants](#contract-level-invariants)
    - [`SuperchainETHBridge`](#superchainethbridge-2)
      - [`sendETH`](#sendeth-1)
      - [`relayETH`](#relayeth-1)
    - [`ETHLiquidity`](#ethliquidity-3)
      - [`mint`](#mint-1)
      - [`burn`](#burn-1)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The `SuperchainETHBridge` is a predeploy that is an abstraction on top of the
`L2toL2CrossDomainMessenger` that facilitates cross-chain ETH bridging using interop.
`SuperchainETHBridge` integrates with the `ETHLiquidity` contract to manage native
ETH liquidity across chains, ensuring seamless cross-chain transfers of native ETH.
The `SuperchainETHBridge` only handles native ETH cross-chain transfers, for how
interoperable ETH withdrawals are handled see the [`ETHLockbox`](./eth-lockbox.md) spec.

## Design

The `SuperchainETHBridge` contract is designed to manage native ETH transfers between
interoperable chains in the Superchain. The `SuperchainETHBridge` implements two
functions: `sendETH` for depositing ETH into the `ETHLiquidity` contract and sending a cross-chain
message to the destination chain to call `relayETH`, and `relayETH` which withdraws ETH from the
`ETHLiquidity` contract and sends it to the recipient on the destination chain.

The `ETHLiquidity` contract is a predeploy that allows the `SuperchainETHBridge` contract to access
ETH liquidity without needing to modify the EVM to generate new ETH. The `ETHLiquidity` contract
comes "pre-loaded" with `uint248.max` balance to prevent liquidity shortages. The `ETHLiquidity`
contract implements two functions: `burn` which allows an address to lock ETH into this contract,
and `mint` which allows an address to unlock ETH from this contract. The `burn` and `mint` functions
are only callable by the `SuperchainETHBridge` contract. `burn` is called by `SuperchainETHBridge`'s
`sendETH` function and `mint` is called by `SuperchainETHBridge`'s `relayETH` function.

### Interface and properties

#### `SuperchainETHBridge`

##### `sendETH`

Deposits the `msg.value` of ETH into the `ETHLiquidity` contract and sends a cross-chain message
to the specified `_chainId` to call `relayETH` with the `_to` address as the recipient and the
`msg.value` as the amount.

- The function MUST accept ETH.
- The function MUST emit a `SendETH` event with the `msg.sender`, `_to`, `msg.value`, and `_chainId`.
- The function MUST revert if the `_to` address is the zero address.

```solidity
function sendETH(address _to, uint256 _chainId) external payable returns (bytes32 msgHash_);
```

##### `relayETH`

Withdraws ETH from the `ETHLiquidity` contract equal to the `_amount` and sends it to the `_to` address.

- The function MUST revert if called by any address other than the `L2ToL2CrossDomainMessenger`.
- The function MUST revert if the cross-domain sender is not `SuperchainETHBridge` contract.
- The function MUST emit a `RelayETH` event with the `_from` address, `_to` address, `_amount`, and `source` chain.
- The function MUST transfer the `_amount` of ETH to the `_to` address using `SafeSend`.

```solidity
function relayETH(address _from, address _to, uint256 _amount) external;
```

#### `ETHLiquidity`

##### `mint`

Withdraws ETH from the `ETHLiquidity` contract equal to the `_amount` and sends it to the `msg.sender`.

- The function MUST revert if called by any address other than `SuperchainETHBridge`.
- The function MUST emit a `LiquidityMinted` event with the `msg.sender` and `_amount`.
- The function MUST transfer the `_amount` of ETH to the `msg.sender` using `SafeSend`.

```solidity
function mint(uint256 _amount) external
```

##### `burn`

Locks ETH into the `ETHLiquidity` contract.

- The function MUST accept ETH.
- The function MUST revert if called by any address other than `SuperchainETHBridge`.
- The function MUST emit a `LiquidityBurned` event with the `msg.sender` and `msg.value`.

```solidity
function burn() external payable;
```

### Events

#### `SuperchainETHBridge`

##### `SendETH`

MUST be triggered when `sendETH` is called.

```solidity
event SendETH(address indexed from, address indexed to, uint256 amount, uint256 destination);
```

##### `RelayETH`

MUST be triggered when `relayETH` is called.

```solidity
event RelayETH(address indexed from, address indexed to, uint256 amount, uint256 source);
```

#### `ETHLiquidity`

##### `LiquidityMinted`

MUST be triggered when `mint` is called.

```solidity
event LiquidityMinted(address indexed caller, uint256 value);
```

##### `LiquidityBurned`

MUST be triggered when `burn` is called.

```solidity
event LiquidityBurned(address indexed caller, uint256 value);
```

## Constants

| Name                     | Value                                        |
| ------------------------ | -------------------------------------------- |
| `SuperchainETHBridge` Address | `0x4200000000000000000000000000000000000024` |
| `ETHLiquidity` Address   | `0x4200000000000000000000000000000000000025` |

## Invariants

### System level invariants

#### `ETHLiquidity`

- The ETH held in the `ETHLiquidity` contract MUST never be less than the amount of ETH on the
chain where the `ETHLiquidity` contract is deployed.

- The initial balance of the `ETHLiquidity` contract MUST be set to `type(uint248).max` (wei). The
purpose for using `type(uint248).max` is to guarantee that the balance will be sufficient to credit
all use within the `SuperchainETHBridge` contract, but will never overflow on calls to `burn` because
there is not enough ETH in the total ETH supply to cause such an overflow. The invariant that
avoids overflow is maintained by `SuperchainETHBridge`, but could theoretically be broken by some
future contract that is allowed to integrate with `ETHLiquidity`. Maintainers should be careful
to ensure that such future contracts do not break this invariant.

### Contract level invariants

#### `SuperchainETHBridge`

##### `sendETH`

- It MUST revert if the `msg.sender`'s balance is less than the `msg.value` being sent

- It MUST revert if the `_to` address is the zero address.

- It MUST create a cross-chain message to send ETH to the recipient on the destination chain equal to the `msg.value`.
  - Note: if the target chain is not in the initiating chain dependency set,
    funds will be locked, similar to sending funds to the wrong address.
    If the target chain includes it later, these could be unlocked.

- It MUST transfer `msg.value` of ETH from the `msg.sender` to the `ETHLiquidity` contract.

- It MUST emit:

  - A `SendETH` event with details about the sender, recipient, amount, and destination chain.

##### `relayETH`

- It MUST revert if called by any address other than the `L2ToL2CrossDomainMessenger`.

- It MUST revert if the cross-domain sender is not the `SuperchainETHBridge` contract on the source chain.

- It MUST transfer the `_amount` of ETH to the `_to` address.

- The minted `amount` in `relayETH()` MUST match the `amount` that was burnt in `sendETH()`.

- It MUST emit:

  - A `RelayETH` event with details about the sender, recipient, amount, and source chain.

#### `ETHLiquidity`

##### `mint`

- It MUST never be callable such that balance would decrease below `0`.
  - This is an invariant and NOT a revert.
  - Maintained by considering total available ETH supply and the initial balance of `ETHLiquidity`.

- It MUST revert if called by any address other than the `SuperchainETHBridge`.

- It MUST transfer the requested ETH value to the sending address.

- It MUST emit:

  - A `LiquidityMinted` event including the address that triggered the mint and the minted ETH value.

##### `burn`

- It MUST never be callable such that balance would increase beyond `type(uint256).max`.
  - This is an invariant and NOT a revert.
  - Maintained by considering total available ETH supply and the initial balance of `ETHLiquidity`.

- It MUST revert if called by any address other than the `SuperchainETHBridge` contract.

- It MUST accept ETH value.

- It MUST emit:

  - A `LiquidityBurned` event including the address that triggered the burn and the burned ETH value.
