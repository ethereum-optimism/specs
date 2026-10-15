# Ecotone Deposits

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Changes](#changes)
  - [L1 attributes calldata](#l1-attributes-calldata)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

[deposits]: ../deposits.md
[l1-attributes]: ./l1-attributes.md

## Overview

The Ecotone upgrade changes the L1 attributes deposit calldata. This page lists the changes to the
[deposit specification][deposits].

## Changes

### L1 attributes calldata

After the Ecotone activation block, the L1 attributes deposit calls `setL1BlockValuesEcotone` instead of
`setL1BlockValues`. The calldata is no longer ABI-encoded; the arguments are packed into 5 32-byte aligned
segments, and the total calldata length is exactly 164 bytes.

The full calldata layout and the migration of the pre-Ecotone values are described in
[Ecotone L1 Attributes][l1-attributes].
