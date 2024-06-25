<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
  - [Deposit Context](#deposit-context)
- [Security Considerations](#security-considerations)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview 

This is an experimental section and may be changed in the future. It is not required
for the initial release.

### Deposit Context

Derivation is extended to create **deposit contexts**, which signifies the execution of a depositing transaction. A deposit context is scoped to a single block, commencing with the execution of the first deposited transaction and concluding immediately after the execution of the final deposited transaction within that block. As such, there is exactly one deposit context per block.

## Security Considerations

TODO
