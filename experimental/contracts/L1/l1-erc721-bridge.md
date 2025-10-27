# L1ERC721Bridge

## Overview

The L1ERC721Bridge enables trustless transfer of ERC721 tokens between Ethereum L1 and Optimism L2 by escrowing
tokens on L1 during deposits and releasing them upon withdrawal finalization.

## Definitions

### Bridge Pair

A specific combination of L1 token address and L2 token address that represents the same logical ERC721 collection
across both chains.

### Escrowed Token

An ERC721 token held by the L1ERC721Bridge contract, tracked in the deposits mapping, representing a token that has
been bridged to L2 and is awaiting withdrawal back to L1.

## Assumptions

### a01-001: CrossDomainMessenger delivers messages reliably

The CrossDomainMessenger contract correctly delivers cross-chain messages between L1 and L2 without loss or
corruption.

#### Mitigations

- CrossDomainMessenger is a core protocol contract with extensive testing and auditing
- Message delivery is secured by L1 data availability and fault proof system

### a01-002: L2ERC721Bridge validates withdrawals correctly

The L2ERC721Bridge contract on L2 only initiates withdrawal messages for tokens that were legitimately deposited
from L1.

#### Mitigations

- L2ERC721Bridge is a protocol-controlled predeploy contract
- Withdrawal validation logic is part of the core protocol specification

### a01-003: ProxyAdmin owner operates within governance constraints

The ProxyAdmin owner (governance) acts honestly when initializing or upgrading the contract.

#### Mitigations

- ProxyAdmin owner is typically a multisig or governance contract
- Upgrades follow established governance processes with time delays

## Invariants

### i01-001: Escrow accounting consistency

For any L1 token, L2 token, and token ID combination, if deposits[L1][L2][tokenId] is true, then the L1ERC721Bridge
contract must hold that specific token ID of the L1 token contract. Conversely, any token held by the bridge must
have a corresponding true entry in the deposits mapping.

#### Impact

**Severity: Critical**

Violation would allow unauthorized withdrawal of escrowed tokens or prevent legitimate withdrawals, resulting in
permanent loss of user assets.

### i01-002: Cross-chain message authentication

Only messages originating from the L2ERC721Bridge contract on L2 and delivered through the CrossDomainMessenger can
trigger finalizeBridgeERC721. This prevents unauthorized withdrawal of escrowed tokens.

#### Impact

**Severity: Critical**

Violation would allow attackers to drain all escrowed ERC721 tokens from the bridge without legitimate L2 withdrawals.

## Function Specification

### initialize

Initializes the L1ERC721Bridge contract with the CrossDomainMessenger and SystemConfig addresses.

**Parameters:**

- `_messenger`: Address of the CrossDomainMessenger contract on L1
- `_systemConfig`: Address of the SystemConfig contract on L1

**Behavior:**

- MUST revert if caller is not the ProxyAdmin or ProxyAdmin owner
- MUST revert if already initialized at the current initialization version
- MUST set the systemConfig state variable to `_systemConfig`
- MUST set the messenger state variable to `_messenger`
- MUST set the otherBridge state variable to the L2ERC721Bridge predeploy address (0x4200000000000000000000000000000000000014)
- MUST emit an Initialized event

### bridgeERC721

Initiates a bridge transfer of an ERC721 token to the caller's address on L2.

**Parameters:**

- `_localToken`: Address of the ERC721 token contract on L1
- `_remoteToken`: Address of the corresponding ERC721 token contract on L2
- `_tokenId`: Token ID to bridge
- `_minGasLimit`: Minimum gas limit for the L2 transaction
- `_extraData`: Optional additional data forwarded to L2 (not used for execution, only emitted)

**Behavior:**

- MUST revert if the contract is paused
- MUST revert if caller is not an externally owned account (EOA)
- MUST revert if `_remoteToken` is address(0)
- MUST revert if the caller has not approved this contract to transfer the token
- MUST set deposits[_localToken][_remoteToken][_tokenId] to true
- MUST transfer the token from caller to this contract using transferFrom
- MUST send a cross-chain message to L2ERC721Bridge calling finalizeBridgeERC721
- MUST emit ERC721BridgeInitiated event with caller as both _from and _to addresses

### bridgeERC721To

Initiates a bridge transfer of an ERC721 token to a specified recipient address on L2.

**Parameters:**

- `_localToken`: Address of the ERC721 token contract on L1
- `_remoteToken`: Address of the corresponding ERC721 token contract on L2
- `_to`: Address to receive the token on L2
- `_tokenId`: Token ID to bridge
- `_minGasLimit`: Minimum gas limit for the L2 transaction
- `_extraData`: Optional additional data forwarded to L2 (not used for execution, only emitted)

**Behavior:**

- MUST revert if the contract is paused
- MUST revert if `_to` is address(0)
- MUST revert if `_remoteToken` is address(0)
- MUST revert if the caller has not approved this contract to transfer the token
- MUST set deposits[_localToken][_remoteToken][_tokenId] to true
- MUST transfer the token from caller to this contract using transferFrom
- MUST send a cross-chain message to L2ERC721Bridge calling finalizeBridgeERC721 with `_to` as recipient
- MUST emit ERC721BridgeInitiated event with caller as _from and `_to` as recipient

### finalizeBridgeERC721

Completes an ERC721 bridge withdrawal from L2 by releasing the escrowed token to the recipient on L1.

**Parameters:**

- `_localToken`: Address of the ERC721 token contract on L1
- `_remoteToken`: Address of the ERC721 token contract on L2
- `_from`: Address that initiated the withdrawal on L2
- `_to`: Address to receive the token on L1
- `_tokenId`: Token ID being withdrawn
- `_extraData`: Optional additional data (not used for execution, only emitted)

**Behavior:**

- MUST revert if caller is not the CrossDomainMessenger
- MUST revert if the CrossDomainMessenger's xDomainMessageSender is not the L2ERC721Bridge
- MUST revert if the contract is paused
- MUST revert if `_localToken` is the address of this contract
- MUST revert if deposits[_localToken][_remoteToken][_tokenId] is false
- MUST set deposits[_localToken][_remoteToken][_tokenId] to false
- MUST transfer the token from this contract to `_to` using safeTransferFrom
- MUST emit ERC721BridgeFinalized event

### paused

Returns whether the bridge is currently paused.

**Behavior:**

- MUST return the paused status from the SystemConfig's SuperchainConfig contract
- MUST NOT revert under any circumstances

### superchainConfig

Returns the SuperchainConfig contract address.

**Behavior:**

- MUST return the SuperchainConfig address from the SystemConfig contract
- MUST NOT revert under any circumstances

### proxyAdmin

Returns the ProxyAdmin contract that owns this proxy.

**Behavior:**

- MUST return the ProxyAdmin address from the EIP-1967 admin storage slot if non-zero
- MUST return the owner of the AddressManager if this is a ResolvedDelegateProxy
- MUST revert if no ProxyAdmin can be found

### proxyAdminOwner

Returns the owner of the ProxyAdmin contract.

**Behavior:**

- MUST return the owner address from the ProxyAdmin contract
- MUST revert if the ProxyAdmin cannot be determined

### MESSENGER

Legacy getter for the messenger contract address.

**Behavior:**

- MUST return the messenger state variable
- MUST NOT revert under any circumstances

### OTHER_BRIDGE

Legacy getter for the other bridge contract address.

**Behavior:**

- MUST return the otherBridge state variable
- MUST NOT revert under any circumstances
