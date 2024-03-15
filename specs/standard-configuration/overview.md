# Standard OP Stack Configuration

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

**Table of Contents**

- [Standard OP Stack Configuration](#standard-op-stack-configuration)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

TODO add copy about standard chains / why a chain may want to be a standard chain

The Standard Configuration is the set of requirements for an OP Stack chain to be considered a Standard Chain.
These requirements are split into three components:

- [Protocol Parameters](./protocol-parameters.md): Parameters and properties of the chain that may
  be set at genesis and fixed for the lifetime of the chain, or may be changeable through a privileged
  account.
- [Admin Roles](./admin-roles.md): These roles can upgrade contracts, change role owners, or update
  protocol parameters. These are typically cold wallets not used directly in day to day operations.
- [Service Roles](./servicer-roles.md): These roles are used to manage the day-to-day operations
  of the chain, and therefore are often hot wallets.
