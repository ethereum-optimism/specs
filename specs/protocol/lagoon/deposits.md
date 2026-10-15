# Lagoon Deposits

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Changes](#changes)
  - [Post-exec transactions](#post-exec-transactions)
  - [SDM refund eligibility](#sdm-refund-eligibility)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

[deposits]: ../deposits.md
[post-exec]: ./post-exec.md
[sdm]: ./sdm.md

## Overview

The Lagoon upgrade changes deposit processing. This page lists the changes to the
[deposit specification][deposits].

## Changes

### Post-exec transactions

Lagoon introduces post-exec transactions, a new transaction type (`0x7F`) that is distinct from deposits (`0x7E`).
Post-exec transactions are included in the block payload alongside user transactions and deposited transactions.
See [Post-Execution Transactions][post-exec].

### SDM refund eligibility

Deposits are not eligible for a Sequencer-Defined Metering (SDM) refund. Deposits buy gas on L1 and have no
L2-side gas-price to refund. See [Sequencer-Defined Metering][sdm].
