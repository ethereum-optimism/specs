# Supervisor

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [RPC API](#rpc-api)
  - [`supervisor_checkMessage`](#supervisor_checkmessage)
    - [Parameters](#parameters)
    - [Returns](#returns)
  - [`supervisor_superRootAtTimestamp`](#supervisor_superrootattimestamp)
    - [Parameters](#parameters-1)
    - [Returns](#returns-1)
    - [Description](#description)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The supervisor is an implementation detail of OP Stack native interop and is not the only
architecture that can be used to implement it. The supervisor is responsible for indexing
data from all of the chains in a cluster so that the [safety level](./verifier.md#safety)
of executing messages can quickly be determined.

## RPC API

### `supervisor_checkMessage`

Checks the safety level of a specific message based on its identifier and message hash.
This RPC is useful for the block builder to determine if a message is should be included
in a block.

#### Parameters

- identifier: [Identifier](./messaging.md#message-identifier) - The identifier of the message to check.
- message hash: Hash - Hash of the initiating message.

#### Returns

- SafetyLevel: [SafetyLevel](./verifier.md#safety) (string) - The safety level of the message.
  - Oneof:
    - Invalid: "invalid"
    - LocalUnsafe: "unsafe"
    - CrossUnsafe: "cross-unsafe"
    - LocalSafe: "local-safe"
    - CrossSafe: "safe"
    - Finalized: "finalized"

### `supervisor_superRootAtTimestamp`

Gets the super root at a specific timestamp.

#### Parameters

- timestamp: hexutil.Uint64 - Timestamp to query.

#### Returns

- object
  - timestamp: hexutil.Uint64 - The timestamp of the super root
  - superRoot: Hash - The root of the super root
  - chains: []object - List of chains included in the super root
    - chainId: hexutil.Uint64 - The chainid
    - canonical: Hash - output root at the latest canonical block
    - pending: hexutil.Bytes - output root preimage

#### Description

Retrieves the super root state at the specified timestamp, which represents the global state across all monitored chains.
