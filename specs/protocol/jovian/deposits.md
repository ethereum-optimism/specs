# Jovian Deposits

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Changes](#changes)
  - [Upgrade deposits](#upgrade-deposits)
  - [DA footprint gas](#da-footprint-gas)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

[deposits]: ../deposits.md
[derivation]: ./derivation.md
[exec-engine]: ./exec-engine.md

## Overview

The Jovian upgrade changes deposit processing. This page lists the changes to the
[deposit specification][deposits].

## Changes

### Upgrade deposits

On the Jovian activation block, the derivation pipeline generates a set of deposit transaction-based upgrade
transactions. Each transaction uses the "Upgrade-deposited" source-hash type with a distinct intent string, for
example `Jovian: L1Block Deployment` and `Jovian: GasPriceOracle Deployment`.

The full transaction list and their attributes are described in [Derivation][derivation].

### DA footprint gas

The Jovian execution engine reads the `daFootprintGasScalar` from the deposited L1 attributes of the current L2
block. See [Execution Engine][exec-engine].
