<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

**Table of Contents** _generated with [DocToc](https://github.com/thlorenz/doctoc)_

- [Pectra Blob Schedule Derivation](#pectra-blob-schedule-derivation)
  - [If enabled](#if-enabled)
  - [If disabled (default)](#if-disabled-default)
  - [Motivation and Rationale](#motivation-and%C2%A0rationale)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Pectra Blob Schedule Derivation

## If enabled

If this hardfork is enabled (i.e. if there is a non nil hardfork activation timestamp set), the following rules apply:

When setting the [L1 Attributes Deposited Transaction](../../glossary.md#l1-attributes-deposited-transaction),
the adoption of the Pectra blob base fee update fraction
(see [EIP-7691](https://github.com/ethereum/EIPs/blob/master/EIPS/eip-7691.md))
occurs for L2 blocks with an L1 origin equal to or greater than the hard fork timestamp.
For L2 blocks with an L1 origin less than the hard fork timestamp, the Cancun blob base fee update fraction is used
(see [EIP-4844](https://github.com/ethereum/EIPs/blob/master/EIPS/eip-4844.md)).

## If disabled (default)

If the hardfork activation timestamp is nil, the blob base fee update rules which are active
at any given L1 block will apply to the L1 Attributes Deposited Transaction.

## Motivation and Rationale

Due to a consensus layer bug, OPStack chains on Holesky and Sepolia did not update their blob base fee update
fraction (for L1 Attributes Deposited Transaction) in tandem with the Prague upgrade on L1.
This optional fork is a mechanism to bring those chains back in line.
It is unecessary for chains using Ethereum mainnet for L1.

Activating by L1 origin preserves the invariant that the L1BlockInfo is constant for blocks with the same epoch.
