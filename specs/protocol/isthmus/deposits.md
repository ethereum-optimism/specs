# Isthmus Deposits

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Changes](#changes)
  - [Upgrade deposits](#upgrade-deposits)
  - [Operator fee exemption](#operator-fee-exemption)
  - [EIP-6110 request exclusion](#eip-6110-request-exclusion)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

[deposits]: ../deposits.md
[derivation]: ./derivation.md
[exec-engine]: ./exec-engine.md

## Overview

The Isthmus upgrade changes deposit processing. This page lists the changes to the
[deposit specification][deposits].

## Changes

### Upgrade deposits

On the Isthmus activation block, the derivation pipeline generates a set of deposit transaction-based upgrade
transactions. Each transaction uses the "Upgrade-deposited" source-hash type with a distinct intent string, for
example `Isthmus: L1 Block Deployment` and `Isthmus: Gas Price Oracle Deployment`.

The full transaction list and their attributes are described in [Derivation][derivation].

### Operator fee exemption

Deposit transactions are not charged operator fees. For all deposit transactions, regardless of the operator fee
parameter configuration, the operator fee is zero. Deposit transactions also do not receive operator fee gas
refunds, since they never buy the operator fee gas.

### EIP-6110 request exclusion

The OP Stack ignores EIP-6110 deposit requests. Requests generation excludes EIP-6110 deposit requests, and the
post-block filtering of events in the deposit contract is not invoked. See [Execution Engine][exec-engine].
