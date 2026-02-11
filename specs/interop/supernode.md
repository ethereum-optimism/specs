# Supernode

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Architecture](#architecture)
  - [Chain Containers](#chain-containers)
    - [Chain Isolation](#chain-isolation)
    - [Virtual Nodes](#virtual-nodes)
    - [Engine Controller](#engine-controller)
  - [Shared Resources](#shared-resources)
    - [L1 Client](#l1-client)
    - [Beacon Client](#beacon-client)
    - [RPC Router](#rpc-router)
    - [Metrics](#metrics)
  - [Activities](#activities)
    - [Heartbeat](#heartbeat)
    - [Superroot](#superroot)
    - [Interop](#interop)
- [RPC API](#rpc-api)
  - [Common Types](#common-types)
    - [`HexUint64`](#hexuint64)
    - [`ChainID`](#chainid)
    - [`Hash`](#hash)
    - [`BlockID`](#blockid)
    - [`OutputWithRequiredL1`](#outputwithrequiredl1)
    - [`SuperRootResponseData`](#superrootrootresponsedata)
    - [`SuperRootAtTimestampResponse`](#superrootattimestampresponse)
  - [Root Namespace Methods](#root-namespace-methods)
    - [`heartbeat_check`](#heartbeat_check)
    - [`superroot_atTimestamp`](#superroot_attimestamp)
  - [Per-Chain Namespace Methods](#per-chain-namespace-methods)
- [Configuration](#configuration)
  - [Required Flags](#required-flags)
  - [Optional Flags](#optional-flags)
  - [Virtual Node Flags](#virtual-node-flags)
    - [Global Virtual Node Flags](#global-virtual-node-flags)
    - [Per-Chain Virtual Node Flags](#per-chain-virtual-node-flags)
  - [Activity Flags](#activity-flags)
- [Example Usage](#example-usage)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

OP-Supernode is an implementation of an Optimism Consensus Client which
implements the Interop Protocol.

The Interop Protocol is implemented fully outside of the existing
OP-Node Consensus Client, and instead runs as a corrective process
that enforces eventual-correctness of the Locally Safe Chain,
and promotion to Safe and ultimately Finalized.

## Architecture

### Chain Containers

Chain Containers represent the concerns of one specific chain being managed by the Supernode.
It contains a client connection to the Execution Client, and a process
which runs `op-node` as an in-memory "Virtual Node".

All interactions with a chain are abstracted through the Chain Container,
which routes and coordinates the response.


#### Virtual Nodes

Each Chain Container manages a Virtual Node, which is an in-process `op-node` instance
configured for the specific chain.
Virtual Nodes are created with shared resources injected via initialization overrides,
allowing them to share L1 clients and beacon clients while maintaining isolation.

Virtual Nodes are ephemeral: when a Virtual Node encounters an error or needs to restart,
the Chain Container automatically creates a new Virtual Node instance
and resumes derivation from the last known safe state.

### Shared Resources

Chain Containers benefit from running in a shared environment through the use of shared resources.
Shared resources are dependencies injected into Virtual Nodes such that the original behavior is intact,
but redundant access is eliminated.


### RPC Router

The Supernode exposes a single HTTP endpoint that routes requests to the appropriate chain
based on the URL path prefix.

- Root path (`/`) routes to the Supernode's root RPC handler for Activity RPCs
- Chain-prefixed paths (`/<chainID>/`) route to the corresponding chain's RPC handler

For example:

- `http://localhost:8545/` - Root namespace (heartbeat, superroot)
- `http://localhost:8545/11155420/` - OP Sepolia's RPC namespace
- `http://localhost:8545/84532/` - Base Sepolia's RPC namespace


### Verification Activities

Activities represent the concerns of the Supernode which fall outside of any one chain.
They are modular plugins that extend the capabilities of the software.

Verification Activities in particular help to inform Chain Containers
when Chain Content is Valid or Invalid. The Chain Container, in turn,
ensures the Chain State is correct, given what is known to be verified.

### Interop

Interop is implemented as a Verification Activity.
It is enabled when the `--interop.activation-timestamp` flag is set.

The Interop activity:

1. Maintains a tracking of the extent of the L1 that has been considered
by the activity.
2. Waits for all Chains to reach a target L2 Timestamp. Each chain must
have derived the timestamp (ie it must be Local Safe).
3. Performs Interop Executing Message Validation per this spec.
4. Record the Verified Result, or notify the Chain Container on Invalid
Blocks.