# StorageSetter

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
- [Assumptions](#assumptions)
- [Invariants](#invariants)
- [Function Specification](#function-specification)
  - [setBytes32](#setbytes32)
  - [setBytes32 (batch)](#setbytes32-batch)
  - [getBytes32](#getbytes32)
  - [setUint](#setuint)
  - [getUint](#getuint)
  - [setAddress](#setaddress)
  - [getAddress](#getaddress)
  - [setBool](#setbool)
  - [getBool](#getbool)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

Provides low-level storage manipulation capabilities for reading and writing arbitrary storage slots during contract
upgrades and migrations.

## Definitions

N/A

## Assumptions

N/A

## Invariants

N/A

## Function Specification

### setBytes32

Writes a bytes32 value to an arbitrary storage slot.

**Parameters:**

- `_slot`: The storage slot to write to
- `_value`: The bytes32 value to store

**Behavior:**

- MUST write `_value` to storage slot `_slot`

### setBytes32 (batch)

Writes multiple bytes32 values to their respective storage slots in a single transaction.

**Parameters:**

- `_slots`: Array of Slot structs, each containing a key (storage slot) and value (bytes32 data)

**Behavior:**

- MUST iterate through all elements in `_slots` array
- MUST write each `_slots[i].value` to storage slot `_slots[i].key`
- MUST process slots in array order

### getBytes32

Reads a bytes32 value from an arbitrary storage slot.

**Parameters:**

- `_slot`: The storage slot to read from

**Behavior:**

- MUST return the bytes32 value stored at slot `_slot`
- MUST return zero if the slot has never been written to

### setUint

Writes a uint256 value to an arbitrary storage slot.

**Parameters:**

- `_slot`: The storage slot to write to
- `_value`: The uint256 value to store

**Behavior:**

- MUST write `_value` to storage slot `_slot`

### getUint

Reads a uint256 value from an arbitrary storage slot.

**Parameters:**

- `_slot`: The storage slot to read from

**Behavior:**

- MUST return the uint256 value stored at slot `_slot`
- MUST return zero if the slot has never been written to

### setAddress

Writes an address value to an arbitrary storage slot.

**Parameters:**

- `_slot`: The storage slot to write to
- `_address`: The address value to store

**Behavior:**

- MUST write `_address` to storage slot `_slot`

### getAddress

Reads an address value from an arbitrary storage slot.

**Parameters:**

- `_slot`: The storage slot to read from

**Behavior:**

- MUST return the address value stored at slot `_slot`
- MUST return the zero address if the slot has never been written to

### setBool

Writes a bool value to an arbitrary storage slot.

**Parameters:**

- `_slot`: The storage slot to write to
- `_value`: The bool value to store

**Behavior:**

- MUST write `_value` to storage slot `_slot`

### getBool

Reads a bool value from an arbitrary storage slot.

**Parameters:**

- `_slot`: The storage slot to read from

**Behavior:**

- MUST return the bool value stored at slot `_slot`
- MUST return false if the slot has never been written to
