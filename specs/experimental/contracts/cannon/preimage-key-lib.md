# PreimageKeyLib

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
  - [Preimage Key](#preimage-key)
  - [Key Type](#key-type)
  - [Local Key](#local-key)
  - [Global Key](#global-key)
  - [Localization](#localization)
- [Assumptions](#assumptions)
- [Invariants](#invariants)
  - [i01-001: Localized keys are unique per caller and context](#i01-001-localized-keys-are-unique-per-caller-and-context)
    - [Impact](#impact)
  - [i01-002: Key type byte is always preserved in most significant byte](#i01-002-key-type-byte-is-always-preserved-in-most-significant-byte)
    - [Impact](#impact-1)
- [Function Specification](#function-specification)
  - [localizeIdent](#localizeident)
  - [localize](#localize)
  - [keccak256PreimageKey](#keccak256preimagekey)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

PreimageKeyLib provides utility functions for generating and transforming preimage keys used in the fault proof
system. The library supports both local keys (scoped to specific callers and contexts) and global keys (universally
accessible). These keys are used by the PreimageOracle contract to store and retrieve preimage data during fault
proof execution.

## Definitions

### Preimage Key

A 32-byte identifier used to retrieve preimage data from the PreimageOracle. The most significant byte encodes the
[Key Type](#key-type), while the remaining 31 bytes contain type-specific data.

### Key Type

An 8-bit value stored in the most significant byte of a [Preimage Key](#preimage-key) that determines how the key
is interpreted and accessed. Type 1 indicates a [Local Key](#local-key), while type 2 indicates a
[Global Key](#global-key) for keccak256 preimages.

### Local Key

A [Preimage Key](#preimage-key) with [Key Type](#key-type) 1 that is scoped to a specific caller address and local
context. Local keys are generated through [Localization](#localization) to ensure isolation between different
callers and execution contexts.

### Global Key

A [Preimage Key](#preimage-key) with [Key Type](#key-type) 2 that can be accessed by any caller. Global keys are
derived directly from the keccak256 hash of the preimage data without caller-specific scoping.

### Localization

The transformation operation that converts a key into a caller-specific and context-specific [Local Key](#local-key).
Defined as: `localize(k) = H(k || sender || local_context) & ~(0xFF << 248) | (0x01 << 248)` where H is the
keccak256 hash function. This ensures that different callers and contexts cannot access each other's local preimage
data.

## Assumptions

N/A

## Invariants

### i01-001: Localized keys are unique per caller and context

For any given input key and local context, the [Localization](#localization) operation produces a unique
[Local Key](#local-key) for each distinct caller address. Two different callers with the same input key and local
context will always receive different localized keys, preventing cross-caller data access.

#### Impact

**Severity: Critical**

If localized keys were not unique per caller, different contracts or execution contexts could access each other's
local preimage data. This would break the isolation guarantees required for secure fault proof execution, potentially
allowing malicious actors to manipulate or access sensitive preimage data from other execution contexts.

### i01-002: Key type byte is always preserved in most significant byte

All functions that generate or transform [Preimage Keys](#preimage-key) must ensure that the most significant byte
contains a valid [Key Type](#key-type) value. The `localize` and `localizeIdent` functions always set type 1 for
local keys, while `keccak256PreimageKey` always sets type 2 for global keys. The remaining 31 bytes may contain
arbitrary data, but the type byte must never be corrupted.

#### Impact

**Severity: High**

If the key type byte were corrupted or inconsistent, the PreimageOracle would be unable to correctly interpret and
validate preimage keys. This could lead to incorrect preimage data retrieval, failed fault proof verification, or
denial of service in the dispute resolution system.

## Function Specification

### localizeIdent

Generates a context-specific [Local Key](#local-key) from a local data identifier.

**Parameters:**

- `_ident`: The identifier of the local data (only bytes [1, 32) are used; byte 0 is replaced with type byte)
- `_localContext`: The local context for the key

**Behavior:**

- MUST extract bytes [1, 32) from `_ident` (masking out the most significant byte)
- MUST set the most significant byte to 1 (local key type)
- MUST call `localize` with the constructed key and `_localContext`
- MUST return the resulting localized key

### localize

Localizes a given [Local Key](#local-key) for the caller's context using the [Localization](#localization) operation.

**Parameters:**

- `_key`: The local data key to localize
- `_localContext`: The local context for the key

**Behavior:**

- MUST compute `keccak256(_key || msg.sender || _localContext)` where `||` denotes concatenation
- MUST mask out the most significant byte of the hash result
- MUST set the most significant byte to 1 (local key type)
- MUST return the resulting 32-byte localized key
- MUST preserve the free memory pointer (restore to original value after computation)

### keccak256PreimageKey

Computes and returns the [Global Key](#global-key) for a keccak256 preimage.

**Parameters:**

- `_preimage`: The preimage data (arbitrary length bytes)

**Behavior:**

- MUST compute `keccak256(_preimage)`
- MUST mask out the most significant byte of the hash result
- MUST set the most significant byte to 2 (global keccak256 key type)
- MUST return the resulting 32-byte key
