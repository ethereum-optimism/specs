# OptimismMintableERC721Factory

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
  - [Local Token](#local-token)
  - [Remote Token](#remote-token)
- [Assumptions](#assumptions)
  - [a01-001: Bridge Contract Integrity](#a01-001-bridge-contract-integrity)
    - [Mitigations](#mitigations)
- [Invariants](#invariants)
- [Function Specification](#function-specification)
  - [constructor](#constructor)
  - [bridge](#bridge)
  - [remoteChainID](#remotechainid)
  - [createOptimismMintableERC721](#createoptimismmintableerc721)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

Factory contract for deploying L2 ERC721 tokens that represent L1 NFTs in the OP Stack bridge system.

## Definitions

### Local Token

An ERC721 token deployed on L2 by this factory that represents a remote token from another chain.

### Remote Token

The original ERC721 token on the remote chain (typically L1) that a local token represents.

## Assumptions

### a01-001: Bridge Contract Integrity

The bridge address provided at deployment is a trusted ERC721 bridge contract that will properly manage minting
and burning of tokens created by this factory.

#### Mitigations

- Bridge address is immutable and set at deployment
- Factory is typically deployed as a predeploy with governance-controlled configuration

## Invariants

This contract has no cross-function invariants. All security properties are enforced within individual function
boundaries and documented in the Function Specification section.

## Function Specification

### constructor

Initializes the factory with bridge and remote chain configuration.

**Parameters:**

- `_bridge`: Address of the ERC721 bridge on this network
- `_remoteChainId`: Chain ID for the remote network

**Behavior:**

- MUST set `BRIDGE` to `_bridge`
- MUST set `REMOTE_CHAIN_ID` to `_remoteChainId`

### bridge

Returns the address of the ERC721 bridge on this network.

**Behavior:**

- MUST return the `BRIDGE` immutable value

### remoteChainID

Returns the chain ID for the remote network.

**Behavior:**

- MUST return the `REMOTE_CHAIN_ID` immutable value

### createOptimismMintableERC721

Creates a new OptimismMintableERC721 token contract that represents a remote token.

**Parameters:**

- `_remoteToken`: Address of the corresponding token on the remote chain
- `_name`: ERC721 name for the new token
- `_symbol`: ERC721 symbol for the new token

**Behavior:**

- MUST revert if `_remoteToken` is the zero address
- MUST compute a salt as `keccak256(abi.encode(_remoteToken, _name, _symbol))`
- MUST deploy a new OptimismMintableERC721 contract using CREATE2 with the computed salt
- MUST pass `BRIDGE`, `REMOTE_CHAIN_ID`, `_remoteToken`, `_name`, and `_symbol` to the token constructor
- MUST set `isOptimismMintableERC721[localToken]` to `true` for the deployed token address
- MUST emit `OptimismMintableERC721Created` event with the local token address, remote token address, and
  `msg.sender` as the deployer
- MUST return the address of the deployed token
