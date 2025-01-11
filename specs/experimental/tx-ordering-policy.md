# Transaction Ordering Policy

## Overview

Enforcement of arbitrary transaction ordering rules can enable application specific rollups
to operate more efficiently. The ability to further constrict the set of valid blocks
based on the properties of the transactions included in the block can be called
"enforcement of a transaction ordering policy". The enforcement can be done using a
predicate that is opaque to the protocol itself, meaning that chain operators can
design their own policies without needing to modify consensus.

## Derivation Pipeline

The derivation pipeline is modified to add a new stage in between the attributes queue and
the engine queue. This new stage applies a predicate against the `PayloadAttributes` before passing
them on to the engine queue. This predicate is defined with EVM bytecode. The `PayloadAttributes`
are ABI encoded before being being used as the calldata to the predicate contract. The account
to use for the predicate is read from a particular storage slot in the `L1Block` contract.

```python
class PayloadAttributes:
    timestamp: uint64
    prev_randao: bytes32
    suggested_fee_recipient: address
    withdrawals: Withdrawal[]
    Transactions: Transaction[]
    NoTxPool: bool
    GasLimit: uint64
    ParentBeaconBlockRoot: bytes32

enum PayloadValidity:
  DROP = 1
  ACCEPT = 2

def on_next_payload_attributes(payload):
    slot = l2.getStorageAt(L1Block, PREDICATE_SLOT, "latest")
    addr = slot[12:]
    predicate_code = l2.getCode(addr, "latest")

    tx_context = {
        origin: payload.suggested_fee_recipient,
        gas_price: 0,
        blob_hashes: []
        blob_fee_cap: 0
    }

    evm.tx_context = tx_context
    data = abi.encode(payload)

    returndata, error = evm.call(
      from=payload.suggested_fee_recipient,
      to=addr,
      data=payload
      to=addr
      gas_limit=PREDICATE_GAS_LIMIT,
      value=0
    )

    if error is not None:
      return PayloadValidity.Drop
      
    return PayloadValidity.ACCEPT
```

## Predicate Contract

The predicate contract should be implemented as a single `fallback` function that operates over the calldata.
The calldata is the next ABI encoded `PayloadAttributes`. If the predicate does not revert, then the `PayloadAttributes`
are not dropped and can be passed along to the engine queue to be sent to the execution client. If the predicate contract
does revert, then the `PayloadAttributes` are dropped.

It is not immediately clear if the call to the predicate contract should be completely stateless, or if the contract should
be able to access the latest state of L2. Access to L2 state could be implemented using a "forking provider" similar to foundry
network forking where stateful EVM opcodes pull in remote data fetched via RPC. This would enable entire smart contract systems
to be defined on L2 that govern the ordering policy of the L2 blocks. If arbitrary L2 state can be accessed during the execution
of the predicate contract, then the gas limit of the call should be constrained to prevent too many blocking remote requests.

### Transaction Ordering Policy

The predicate contract is able to introspect the exact set of transactions that are going to be pushed to the
execution client as the next block. To implement a custom transaction ordering policy, the predicate contract
should RLP decode the transactions and then iterate over them. While iterating, the contract can accumulate
information about the transactions and enforce invariants about the ordering or fee recipient.

#### Application Specific Invariants

Application specific invariants exist to enforce particular behavior on application functionality that is deemed too important to
the network to fail where the application design is not able to operate in an incentive compatible way for some reason.
An example invariant could be that a particular oracle update MUST be backrun by a transaction that arbitrages the state update
and the profits are sent to a governance controlled contract. Oracles like Chainlink are currently necessary for the proper functioning
of lending markets and other defi applications but the latency games and asymmetic advantage of the oracle provider for backrunning
are centralization vectors to the network.

Application specific invariants are useful for application specific chains, where the majority of the functionality on the
chain is driven by a single application. The ability for developers to develop ordering rules at the application layer
is a new primitive that could defend from applications from MEV and enable applications that otherwise wouldn't be possible.

#### General Invariants

General invariants do not observe anything particular about the applications that are called as part of the
execution of a `PayloadAttributes`. An example invariant is that the transactions are exactly ordered by
their tip. This sort of rule may eliminate some timing games, although searchers that learn information faster
will always be able to use more information when determining how much to bid.

### L1 Attributes Transaction

The L1 Attributes transaction is assumed to be updated with a [diff based serialization](https://github.com/ethereum-optimism/specs/pulls/13).
When the `SystemConfig` `ConfigUpdate` event is emitted that corresponds to the update of the predicate
bytecode, the event will contain the initcode of the new predicate contract. The L1 Attributes transaction
will include the initcode from the event and the `L1Block` contract will `CREATE` the code and then
store the address of the deployed contract in a particular storage slot.

## Security Concerns

### EVM in EVM

If it is possible to write an EVM in the EVM then it may be possible to write assertions on the 
resulting outputs of the `PayloadAttributes`. It is not clear the extent of what is possible
under this model, although it seems like a very powerful tool.

### Operating over PayloadAttributes

It may be the case that only a subset or a mapping of the `PayloadAttributes` are a more ideal input to
the predicate contract. Further exploration is required.
