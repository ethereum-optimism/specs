# System Config

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
  - [`Roles`](#roles)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The `SystemConfig` is updated to set a new role: the `OPERATOR_FEE_MANAGER`. This role is set once upon
initialization and can only be set again with another call to `initialize`.

### `Roles`

The `Roles` struct is updated to include the new `OPERATOR_FEE_MANAGER` role.

```solidity
struct Roles {
    address owner;
    address feeAdmin;
    address operatorFeeManager; // new role
}
```

The operator may only change the `operatorFeeManager` role with a call to `initialize`.
