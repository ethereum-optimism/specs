# Karst Deposits

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Changes](#changes)
  - [Upgrade deposits](#upgrade-deposits)
  - [EIP-7825 gas-cap exemption](#eip-7825-gas-cap-exemption)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

[deposits]: ../deposits.md
[derivation]: ./derivation.md

## Overview

The Karst upgrade changes deposit processing. This page lists the changes to the
[deposit specification][deposits]. The deposit specification describes the Bedrock behaviour.

## Changes

### Upgrade deposits

On the Karst activation block, the derivation pipeline generates a set of deposit transaction-based upgrade
transactions. The transactions are defined by the `karst_nut_bundle.json` file in the monorepo, which contains
31 transactions. The consensus layer node prefixes each intent string with `Karst <index>:`.

The full transaction list and the upgrade path are described in [Derivation][derivation].

### EIP-7825 gas-cap exemption

Deposits are exempt from the EIP-7825 transaction gas cap. Deposits are already subject to a 20M gas limit.
