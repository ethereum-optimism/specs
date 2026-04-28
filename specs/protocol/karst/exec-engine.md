# Karst: Execution Engine

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [EVM Changes](#evm-changes)
  - [Precompile Input Size Restrictions](#precompile-input-size-restrictions)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## EVM Changes

### Precompile Input Size Restrictions

The `bn256Pairing` precompile input size is reduced from the
[Jovian limit](../jovian/exec-engine.md#precompile-input-size-restrictions) of 81,984 bytes (427 pairs) to
57,600 bytes (300 pairs).

The lower limit restores Jovian-era headroom under the
[EIP-7825](https://eips.ethereum.org/EIPS/eip-7825) L1 transaction gas cap, accommodating the
[EIP-7904](https://eips.ethereum.org/EIPS/eip-7904) pairing cost increase plus plausible variance without
requiring a further adjustment.

The other variable-input precompile limits are unchanged from Jovian.
