# Servicer Roles

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

**Table of Contents**

- [Servicer Roles](#servicer-roles)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

Servicer roles are related to actions taken by Chain Servicers in the
[Law of Chains](https://github.com/ethereum-optimism/OPerating-manual/blob/main/Law%20of%20Chains.md).
They are typically hot wallets, as they take active roles in chain progression and are used to
participate in day-to-day, ongoing operations.

| Configuration Option                       | Requirement                                                      | Justification/Notes |
| ------------------------------------------ | ---------------------------------------------------------------- | ------------------- |
| Guardian Account                           | Optimism Foundation Safe                                         | Security            |
| Batch Submitter Account                    | TODO can we standardize as a deterministic function of chain ID? |                     |
| Sequencer P2P / Unsafe Head Signer Account | No requirement                                                   |                     |
| Challenger Account                         | TODO                                                             |                     |
| Proposer Account                           | No requirement                                                   |                     |
