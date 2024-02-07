<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Messaging

TODO: expand on initiating/executing messages and corresponding graph problem.

## Security Considerations

### Cyclic dependencies

If there is a cycle in the dependency set, chains MUST still be able to promote unsafe blocks
to safe blocks. A cycle in the dependency set happens anytime that two chains are in each other's
dependency set. This means that they are able to send cross chain messages to each other.

### Transitive dependencies

TODO
