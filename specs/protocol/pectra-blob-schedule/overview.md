# Pectra Blob Schedule (Optional) Network Upgrade

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Execution Layer](#execution-layer)
- [Consensus Layer](#consensus-layer)
- [Smart Contracts](#smart-contracts)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

The Pectra Blob Schedule hardfork is an optional hardfork which delays the adoption of the
Prague blob base fee update fraction until the specified time. Until that time, the Cancun
update fraction from the previous fork is retained.

Note that the activation logic for this upgrade is different to most other upgrades.
Usually, specific behaviour is activated at the _hard fork timestamp_, if it is not nil,
and continues until overriden by another hardfork.
Here, specific behaviour is activated for all times up to the hard fork timestamp,
if it is not nil, and then _deactivated_ at the hard fork timestamp.

## Execution Layer

## Consensus Layer

- [Derivation](./derivation.md)

## Smart Contracts
