# Lagoon: Execution Engine

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [EVM Changes](#evm-changes)
  - [Precompile Input Size Restrictions](#precompile-input-size-restrictions)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## EVM Changes

### Precompile Input Size Restrictions

The BLS12-381 precompile input size limits are reduced from the
[Jovian limits](../jovian/exec-engine.md#precompile-input-size-restrictions) to:

- `BLS12-381 G1 MSM`: 130,720 bytes (817 pairs), from 288,960 bytes (1,806 pairs)
- `BLS12-381 G2 MSM`: 130,752 bytes (454 pairs), from 278,784 bytes (968 pairs)
- `BLS12-381 Pairing`: 130,560 bytes (340 pairs), from 156,672 bytes (408 pairs)

The other variable-input precompile limits are unchanged from
[Karst](../karst/exec-engine.md#precompile-input-size-restrictions).
