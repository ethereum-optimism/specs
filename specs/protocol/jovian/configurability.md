# Configurability

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [`SystemConfig`](#systemconfig)
  - [`ConfigUpdate`](#configupdate)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The `version` argument of the `ConfigUpdate` event CAN now
include a nonce, and has been renamed `nonceAndVersion`.

## `SystemConfig`

### `ConfigUpdate`

Config updates MUST emit a `ConfigUpdate` event. The `version` argument CAN now
include a `nonce`, and has been renamed `nonceAndVersion`.

```solidity
event ConfigUpdate(uint256 indexed nonceAndVersion, UpdateType indexed updateType, bytes data);
```

The `nonceAndVersion` argument is either `uint256(0)`, or
`uint256(nonce << 128 | version)`, where `version` is `1` and `nonce` increments
by `1` for each `ConfigUpdate` event emitted.
