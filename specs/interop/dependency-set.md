# The Dependency Set

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Chain ID](#chain-id)
- [Updating the Dependency Set](#updating-the-dependency-set)
- [Security Considerations](#security-considerations)
  - [Dependency Set Size](#dependency-set-size)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

The dependency set defines the set of chains that destination chains allow as source chains. Another way of
saying it is that the dependency set defines the set of initiating messages that are valid to be used
as part of an executing message. An executing message MUST have an initiating message that is created by a chain
in the dependency set.

The dependency set is defined by a set of chain ids. Since it is impossible to enforce uniqueness of chain ids,
social consensus MUST be used to determine the chain that represents the canonical chain id. This
particularly impacts the block builder as they SHOULD use the chain id to assist in validation
of executing messages.

The dependency set is configured on a per cluster basis. All chains that are in the dependency set
can accept initiating messages from any other chain in the dependency set, resulting in a mesh.

The chain id of the local chain MUST be considered as part of its own dependency set. This allows a chain
to consume logs that it has produced much more cheaply than providing a block hash proof.

## Chain ID

All chain IDs used in interop dependency sets must fit within a `uint64`.
Software should be designed to support up to uint256 chain IDs.

## Updating the Dependency Set

The dependency set is managed in the client software. Adding a chain to the dependency set is
considered an upgrade to the network. It is not possible to remove chains from the dependency set.

## Security Considerations

### Dependency Set Size

It becomes increasingly expensive to fully validate the full cluster as the size of the dependency
set grows. The proof system requires validating all of the chains so the size of the dependency
set is limited by the performance of the proof.
