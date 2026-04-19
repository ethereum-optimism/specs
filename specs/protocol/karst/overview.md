# Karst Network Upgrade

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Execution Layer](#execution-layer)
- [Consensus Layer](#consensus-layer)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

This document is not finalized and should be considered experimental.

## Execution Layer

- [Reduce `bn256Pairing` precompile input size](./exec-engine.md#precompile-input-size-restrictions)
- [Osaka](https://eips.ethereum.org/EIPS/eip-7607) (Execution Layer):
  - [EIP-7642: eth/69 - history expiry and simpler receipts](https://eips.ethereum.org/EIPS/eip-7642)
  - [EIP-7823: Set upper bounds for MODEXP](https://eips.ethereum.org/EIPS/eip-7823)
  - [EIP-7825 Transaction Gas Limit Cap](https://eips.ethereum.org/EIPS/eip-7825)
    (not enabled for deposits, which are already subject to a 20MGas limit)
  - [EIP-7883: ModExp Gas Cost Increase](https://eips.ethereum.org/EIPS/eip-7883)
  - [EIP-7910: eth_config JSON-RPC Method](https://eips.ethereum.org/EIPS/eip-7910)
  - [EIP-7939: Count leading zeros (CLZ) opcode](https://eips.ethereum.org/EIPS/eip-7939)
  - [EIP-7951: Precompile for secp256r1 Curve Support](https://eips.ethereum.org/EIPS/eip-7951)
    (this has been present since Fjord, but the gas cost will be updated to align with Ethereum)

## Consensus Layer

- [Network upgrade transactions](./derivation.md#network-upgrade-transactions) applied during derivation
