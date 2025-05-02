# Derivation

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Invariants](#invariants)
- [Omit User Transactions in Fork Activation Block](#omit-user-transactions-in-fork-activation-block)
- [Replacing Invalid Blocks](#replacing-invalid-blocks)
  - [Optimistic Block Deposited Transaction](#optimistic-block-deposited-transaction)
    - [Optimistic Block Source-hash](#optimistic-block-source-hash)
- [Network Upgrade Transactions](#network-upgrade-transactions)
  - [CrossL2Inbox Deployment](#crossl2inbox-deployment)
  - [CrossL2Inbox Proxy Update](#crossl2inbox-proxy-update)
  - [L2ToL2CrossDomainMessenger Deployment](#l2tol2crossdomainmessenger-deployment)
  - [L2ToL2CrossDomainMessenger Proxy Update](#l2tol2crossdomainmessenger-proxy-update)
- [Expiry Window](#expiry-window)
- [Security Considerations](#security-considerations)
  - [Depositing an Executing Message](#depositing-an-executing-message)
  - [Expiry Window](#expiry-window-1)
  - [Reliance on History](#reliance-on-history)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

New derivation rules are added to guarantee integrity of cross chain messages.
The fork choice rule is updated to fork out unsafe blocks that contain invalid
executing messages.

## Invariants

- An executing message MUST have a corresponding initiating message
- The initiating message referenced in an executing message MUST come from a chain in its dependency set
- A block MUST be considered invalid if it is built with any invalid executing messages
- The timestamp of the identifier MUST be greater than the interop network upgrade timestamp
- The timestamp of the identifier MUST be less than or equal to the timestamp of the block that includes it
- The timestamp of the identifier MUST be greater than timestamp of the block that includes it minus the expiry window

L2 blocks that produce invalid executing messages MUST not be allowed to be considered safe.
They MAY optimistically exist as unsafe blocks for some period of time. An L2 block that is invalidated
because it includes invalid executing messages MUST be replaced by a deposits only block at the same
block height. This guarantees progression of the chain, ensuring that an infinite loop of processing
the same block in the proof system is not possible.

## Omit User Transactions in Fork Activation Block

With the interop upgrade, fork activation blocks no longer include any user transactions. Sequencers, when building
the fork activation block, MUST set `noTxPool` to `true` in the execution payload attributes for this block, instructing
the builder to exclude user transactions.

The derivation pipeline MUST enforce that the sequencer has not included any user transactions in the batch covering
the upgrade's activation block. If the sequencer does include any user transactions within the upgrade activation
block, that batch, and the remaining span batch it originated from, MUST be dropped following the
batch-dropping rules introduced in the [Holocene upgrade](../protocol/holocene/derivation.md#span-batches).

## Replacing Invalid Blocks

When the [cross chain dependency resolution](./messaging.md#resolving-cross-chain-safety) determines
that a block contains an [invalid message](./messaging.md#invalid-messages), the block is replaced
by a block with the same inputs, except for the transactions included. The transactions from the
original block are trimmed to include only deposit transactions plus an
[optimistic block info deposit transaction](#optimistic-block-deposited-transaction), which is appended
to the trimmed transaction list.

### Optimistic Block Deposited Transaction

An Optimistic Block Deposited Transaction is a system deposited transaction,
inserted into the replacement block,
to signal when a previously derived local-safe block (the "optimistic" block) was invalidated.

This transaction MUST have the following values:

1. `from` is `0xdeaddeaddeaddeaddeaddeaddeaddeaddead0002`, like the address of the
   [L1 Attributes depositor account](../protocol/deposits.md#l1-attributes-depositor-account), but incremented by 1
2. `to` is `0x0000000000000000000000000000000000000000` (the zero address as no EVM code execution is expected).
3. `mint` is `0`
4. `value` is `0`
5. `gasLimit` is set `36000` gas, to cover intrinsic costs, processing costs, and margin for change.
6. `isSystemTx` is set to `false`.
7. `data` is the preimage of the [L2 output root]
   of the replaced block. i.e. `version_byte || payload` without applying the `keccak256` hashing.
8. `sourceHash` is computed with a new deposit source-hash domain, see below.

This system-initiated transaction for L1 attributes is not charged any ETH for its allocated
`gasLimit`, as it is considered part of state-transition processing.

[L2 output root]: ../glossary.md#l2-output-root-proposals

#### Optimistic Block Source-hash

The source hash is [computed](../protocol/deposits.md#source-hash-computation)
with a source-hash domain: `4` (instead of `1`),
combined with the [L2 output root] of the optimistic block that was invalidated.

The source-hash is thus computed as:
`keccak256(bytes32(uint256(4)), outputRoot))`.

## Network Upgrade Transactions

The interop network upgrade timestamp defines the timestamp at which all functionality in this document is considered
the consensus rules for an OP Stack based network. On the interop network upgrade block, a set of deposit transaction
based upgrade transactions are deterministically generated by the derivation pipeline in the following order:

This upgrade requires `3_320_000` in gas. In order to upgrade successfully the following invariant MUST be maintained:

```plaintext
MaxResourceLimit + SystemTxMaxGas + UpgradeGasUsage ≤ L2GasLimit
```

With MaxResourceLimit set to `20_000_000` and SystemTxMaxGas set to `1_000_000`,
this mean every upgrading chain MUST have their L2GasLimit set to greater than
`24_320_000`.

The upgrade transaction details below are based on a nightly release at commit
hash `71c460ec7c7c05791ddd841b97bcb664a1f0c753`, and will be updated once a
contracts release is made.

<!-- To regenerate the deploy/upgrade tx docs below, run `./scripts/upgrades/gen_interop_upgrade_tx_specs.sh | pbcopy` and then paste here -->

### CrossL2Inbox Deployment
<!-- Generated with: ./scripts/run_gen_predeploy_docs.sh --optimism-repo-path ../optimism --fork-name Interop --contract-name CrossL2Inbox --from-address 0x4220000000000000000000000000000000000000 --from-address-nonce 0 --git-commit-hash 71c460ec7c7c05791ddd841b97bcb664a1f0c753 --eth-rpc-url https://optimism.rpc.subquery.network/public --proxy-address 0x4200000000000000000000000000000000000022 --copy-contract-bytecode true -->

The `CrossL2Inbox` contract is deployed.

A deposit transaction is derived with the following attributes:

- `from`: `0x4220000000000000000000000000000000000000`
- `to`: `null`
- `mint`: `0`
- `value`: `0`
- `nonce`: `0`
- `gasLimit`: `420000`
- `data`: `0x6080604052348015600e575f80fd5b...` ([full bytecode](../static/bytecode/interop-cross-l2-inbox-deployment.txt))
- `sourceHash`: `0x6e5e214f73143df8fe6f6054a3ed7eb472d373376458a9c8aecdf23475beb616`,  
  computed with the "Upgrade-deposited" type, with `intent = "Interop: CrossL2Inbox Deployment"`

This results in the Interop CrossL2Inbox contract being deployed to
`0x691300f512e48B463C2617b34Eef1A9f82EE7dBf`, to verify:

```bash
cast compute-address --nonce=0 0x4220000000000000000000000000000000000000
Computed Address: 0x691300f512e48B463C2617b34Eef1A9f82EE7dBf
```

Verify `sourceHash`:

```bash
cast keccak $(cast concat-hex 0x0000000000000000000000000000000000000000000000000000000000000002 $(cast keccak "Interop: CrossL2Inbox Deployment"))
# 0x6e5e214f73143df8fe6f6054a3ed7eb472d373376458a9c8aecdf23475beb616
```

Verify `data`:

```bash
git checkout 71c460ec7c7c05791ddd841b97bcb664a1f0c753
make build-contracts
jq -r ".bytecode.object" packages/contracts-bedrock/forge-artifacts/CrossL2Inbox.sol/CrossL2Inbox.json
```

This transaction MUST deploy a contract with the following code hash  
`0x0e7d028dd71bac22d1fb28966043c8d35c3232c78b7fb99fd1db112b5b60d9dd`.

To verify the code hash:

```bash
git checkout 71c460ec7c7c05791ddd841b97bcb664a1f0c753
make build-contracts
cast k $(jq -r ".deployedBytecode.object" packages/contracts-bedrock/forge-artifacts/CrossL2Inbox.sol/CrossL2Inbox.json)
```

### CrossL2Inbox Proxy Update

This transaction updates the CrossL2Inbox Proxy ERC-1967
implementation slot to point to the new CrossL2Inbox deployment.

A deposit transaction is derived with the following attributes:

- `from`: `0x0000000000000000000000000000000000000000`
- `to`: `0x4200000000000000000000000000000000000022` (CrossL2Inbox Proxy)
- `mint`: `0`
- `value`: `0`
- `gasLimit`: `50,000`
- `data`: `0x3659cfe6000000000000000000000000691300f512e48b463c2617b34eef1a9f82ee7dbf`
- `sourceHash`: `0x88c6b48354c367125a59792a93a7b60ad7cd66e516157dbba16558c68a46d3cb`
  computed with the "Upgrade-deposited" type, with `intent = "Interop: CrossL2Inbox Proxy Update"`

Verify data:

```bash
cast concat-hex $(cast sig "upgradeTo(address)") $(cast abi-encode "upgradeTo(address)" 0x691300f512e48B463C2617b34Eef1A9f82EE7dBf)
# 0x3659cfe6000000000000000000000000691300f512e48b463c2617b34eef1a9f82ee7dbf
```

Verify `sourceHash`:

```bash
cast keccak $(cast concat-hex 0x0000000000000000000000000000000000000000000000000000000000000002 $(cast keccak "Interop: CrossL2Inbox Proxy Update"))
# 0x88c6b48354c367125a59792a93a7b60ad7cd66e516157dbba16558c68a46d3cb
```

### L2ToL2CrossDomainMessenger Deployment
<!-- Generated with: ./scripts/run_gen_predeploy_docs.sh --optimism-repo-path ../optimism --fork-name Interop --contract-name L2ToL2CrossDomainMessenger --from-address 0x4220000000000000000000000000000000000001 --from-address-nonce 0 --git-commit-hash 71c460ec7c7c05791ddd841b97bcb664a1f0c753 --eth-rpc-url https://optimism.rpc.subquery.network/public --proxy-address 0x4200000000000000000000000000000000000023 --copy-contract-bytecode true -->

The `L2ToL2CrossDomainMessenger` contract is deployed.

A deposit transaction is derived with the following attributes:

- `from`: `0x4220000000000000000000000000000000000001`
- `to`: `null`
- `mint`: `0`
- `value`: `0`
- `nonce`: `0`
- `gasLimit`: `1100000`
- `data`: `0x6080604052348015600e575f80fd5b...` ([full bytecode](../static/bytecode/interop-l2-to-l2-cross-domain-messenger-deployment.txt))
- `sourceHash`: `0xf5484697c7a9a791db32a3bf0763bf2ba686c77ae7d4c0a5ee8c222a92a8dcc2`,  
  computed with the "Upgrade-deposited" type, with `intent = "Interop: L2ToL2CrossDomainMessenger Deployment"`

This results in the Interop L2ToL2CrossDomainMessenger contract being deployed to
`0x0D0eDd0ebd0e94d218670a8De867Eb5C4d37cadD`, to verify:

```bash
cast compute-address --nonce=0 0x4220000000000000000000000000000000000001
Computed Address: 0x0D0eDd0ebd0e94d218670a8De867Eb5C4d37cadD
```

Verify `sourceHash`:

```bash
cast keccak $(cast concat-hex 0x0000000000000000000000000000000000000000000000000000000000000002 $(cast keccak "Interop: L2ToL2CrossDomainMessenger Deployment"))
# 0xf5484697c7a9a791db32a3bf0763bf2ba686c77ae7d4c0a5ee8c222a92a8dcc2
```

Verify `data`:

```bash
git checkout 71c460ec7c7c05791ddd841b97bcb664a1f0c753
make build-contracts
jq -r ".bytecode.object" packages/contracts-bedrock/forge-artifacts/L2ToL2CrossDomainMessenger.sol/L2ToL2CrossDomainMessenger.json
```

This transaction MUST deploy a contract with the following code hash  
`0x458925c90ec70736600bef3d6529643a0e7a0a848e62626d61314c057b4a71a9`.

To verify the code hash:

```bash
git checkout 71c460ec7c7c05791ddd841b97bcb664a1f0c753
make build-contracts
cast k $(jq -r ".deployedBytecode.object" packages/contracts-bedrock/forge-artifacts/L2ToL2CrossDomainMessenger.sol/L2ToL2CrossDomainMessenger.json)
```

### L2ToL2CrossDomainMessenger Proxy Update

This transaction updates the L2ToL2CrossDomainMessenger Proxy ERC-1967
implementation slot to point to the new L2ToL2CrossDomainMessenger deployment.

A deposit transaction is derived with the following attributes:

- `from`: `0x0000000000000000000000000000000000000000`
- `to`: `0x4200000000000000000000000000000000000023` (L2ToL2CrossDomainMessenger Proxy)
- `mint`: `0`
- `value`: `0`
- `gasLimit`: `50,000`
- `data`: `0x3659cfe60000000000000000000000000d0edd0ebd0e94d218670a8de867eb5c4d37cadd`
- `sourceHash`: `0xe54b4d06bbcc857f41ae00e89d820339ac5ce0034aac722c817b2873e03a7e68`
  computed with the "Upgrade-deposited" type, with `intent = "Interop: L2ToL2CrossDomainMessenger Proxy Update"`

Verify data:

```bash
cast concat-hex $(cast sig "upgradeTo(address)") $(cast abi-encode "upgradeTo(address)" 0x0D0eDd0ebd0e94d218670a8De867Eb5C4d37cadD)
# 0x3659cfe60000000000000000000000000d0edd0ebd0e94d218670a8de867eb5c4d37cadd
```

Verify `sourceHash`:

```bash
cast keccak $(cast concat-hex 0x0000000000000000000000000000000000000000000000000000000000000002 $(cast keccak "Interop: L2ToL2CrossDomainMessenger Proxy Update"))
# 0xe54b4d06bbcc857f41ae00e89d820339ac5ce0034aac722c817b2873e03a7e68
```

## Expiry Window

The expiry window is the time period after which an initiating message is no longer considered valid.

| Constant | Value |
| -------- | ----- |
| `EXPIRY_WINDOW` | `604800 secs` (7 days) |

## Security Considerations

### Depositing an Executing Message

Deposit transactions (force inclusion transactions) give censorship resistance to layer two networks.
It is possible to deposit an invalid executing message, forcing the sequencer to reorg. It would
be fairly cheap to continuously deposit invalid executing messages through L1 and cause L2 liveness
instability. A future upgrade will enable deposits to trigger executing messages.

### Expiry Window

The expiry window ensures that the proof can execute in a reasonable amount of time. [`EIP-2935`][eip-2935] introduced
the capability to traverse history with sub-linear complexity, however deep lookups remain expensive. App developers and
users, in the event that they encounter a message that has expired but has yet to be relayed, can
[resend the message][resend-msg] in order to complete the process.

### Reliance on History

When fully executing historical blocks, a dependency on historical receipts from remote chains is present.
[EIP-4444][eip-4444] will eventually provide a solution for making historical receipts available without
needing to execute increasingly long chain histories.

[eip-2935]: https://eips.ethereum.org/EIPS/eip-2935
[eip-4444]: https://eips.ethereum.org/EIPS/eip-4444
[resend-msg]: https://github.com/ethereum-optimism/design-docs/blob/25ef5537e39b63cddf1c83479cee9f0e02431dce/protocol/resend-messages.md#L4
