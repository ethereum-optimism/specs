# Stage 1 Roles and Requirements

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Permissionless Fault Proofs](#permissionless-fault-proofs)
- [Roles for Stage 1](#roles-for-stage-1)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

This document outlines configuration requirements (including roles and other parameters)
for an implementation of the OP Stack to satsify the Stage 1 decentralization requirements as defined
by
L2 Beat [[1](https://medium.com/l2beat/introducing-stages-a-framework-to-evaluate-rollups-maturity-d290bb22befe), [2](https://medium.com/l2beat/stages-update-security-council-requirements-4c79cea8ef52)].

## Permissionless Fault Proofs

Stage 1 requires a chain to be operating with Permissionless Fault Proofs.

## Roles for Stage 1

Within the context of an OP Stack, the following roles are required for Stage 1:

1. **Upgrade Controller:** ALthough named for its ability to perform an upgarde, more generally this
   account is in charge of _safety_, meaning it MUST control any action which has an impact
   on the determination of a valid L2 state, or the custody of bridged assets.

   This includes upgrading L1 contracts, and modifying the implementation of the dispute game, and
   any other safety-critical function.

2. **Guardian:** This account is in charge of _liveness_, meaning it MUST control any action which
   may cause a delay in the finalization of L2 states and the resulting settlement on L1.

   This includes but is not limited to pausing code paths related to withdrawals.

There may be additional [roles](./configurability.md#admin-roles) in the system, however they MUST
not be able to perform any actions which have an impact on either the safety or liveness of the
system. Any example of such a role is the `SystemConfig` owner (AKA Chain Operator), which can
modify fees and other protocol parameters.
