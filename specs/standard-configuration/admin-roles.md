# Admin Roles

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

**Table of Contents**

- [Admin Roles](#admin-roles)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

Admin roles are roles that can upgrade contracts, change role owners, or update protocol parameters.
These are typically cold wallets not used directly in day to day operations.

The table below defines admin role requirements for an OP Stack chain to be considered a Standard Chain.
The table references the Optimism Foundation (OF) and the Security Council (SC).
The Chain Governor is TODO.

| Configuration Option | Requirement                                                 | Justification/Notes                                                                                                     |
| -------------------- | ----------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| L1 Proxy Admin Owner | 2/2 Safe between OF and SC                                  | Governance-controlled, high security.                                                                                   |
| L2 Proxy Admin Owner | 2/2 Safe between OF and SC                                  | Governance-controlled, high security.                                                                                   |
| L1 Proxy Admin       | 2/2 Safe between OF and SC                                  | Governance-controlled, high security.                                                                                   |
| L2 Proxy Admin       | TODO                                                        | Governance-controlled, high security.                                                                                   |
| Mint Manager Owner   | TODO not relevant on other chains since no native OP token? | TODO                                                                                                                    |
| System Config Owner  | Chain Governor                                              | As defined in the [Law of Chains](https://github.com/ethereum-optimism/OPerating-manual/blob/main/Law%20of%20Chains.md) |
