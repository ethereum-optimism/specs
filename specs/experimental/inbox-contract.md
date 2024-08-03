<!-- omit in toc -->
# Inbox Contract

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**
- [Motivation](#motivation)
- [How It Works](#how-it-works)
- [Supporting Dynamic Updates to Inbox Address](#supporting-dynamic-updates-to-inbox-address)
  - [SystemConfig](#systemconfig)
    - [setBatchInbox](#setbatchinbox)
    - [initialize](#initialize)
    - [UpdateType](#updatetype)
  - [L1 Info Deposit Transaction](#l1-info-deposit-transaction)
  - [L1Block](#l1block)
    - [batchInbox](#batchinbox)
    - [setL1BlockValuesEcotone](#setl1blockvaluesecotone)
  - [How `op-node` knows the canonical batch inbox](#how-op-node-knows-the-canonical-batch-inbox)
  - [How `op-batcher` knows canonical batch inbox](#how-op-batcher-knows-canonical-batch-inbox)
- [Upgrade](#upgrade)
  - [L1Block Deployment](#l1block-deployment)
  - [L1Block Proxy Update](#l1block-proxy-update)
  - [SystemConfig Upgrade](#systemconfig-upgrade)
- [Security Considerations](#security-considerations)
  - [Inbox Sender](#inbox-sender)
- [Reference Implementation](#reference-implementation)

## Motivation

The batch inbox is currently an Externally Owned Account (EOA), which has both advantages and disadvantages:

Advantages:
- Low submission gas cost due to the absence of onchain execution.
- Verification logic is moved offchain to the derivation part, protected by a fault dispute game with a correct absolute prestate.

Disadvantage:
- Onchain verification is not possible.


This specification aims to allow the batch inbox to be a contract, enabling customized batch submission conditions such as:
- Requiring the batch transaction to be signed by a quorum of sequencers in a decentralized sequencing network; or
- Mandating that the batch transaction call a BLOB storage contract (e.g., EthStorage) with a long-term storage fee, which is then distributed to data nodes that prove BLOB storage over time.


## How It Works

The integration process consists of three primary components:
1. The [`BatchInboxAddress`](https://github.com/ethereum-optimism/optimism/blob/db107794c0b755bc38a8c62f11c49320c95c73db/op-chain-ops/genesis/config.go#L77) can now be set to either an Externally Owned Account (EOA) or a smart contract. When a contract is used, it assumes responsibility for verifying and enforcing batch submission conditions.
2. Modification of the `op-node` derivation process: The `op-node` will be updated to exclude failed batch transactions during the derivation process. This change ensures that only successfully executed batch transactions are processed and included in the derived state. 
3. Modification of the op-batcher submission process: The op-batcher will be updated to [call `recordFailedTx`](https://github.com/blockchaindevsh/optimism/blob/02e3b7248f1b590a2adf1f81488829760fa2ba03/op-batcher/batcher/driver.go#L537) for failed batch transactions. This modification ensures that the data contained in failed transactions will be resubmitted automatically.
   1. Most failures will be detected during the [`EstimateGas`](https://github.com/ethereum-optimism/optimism/blob/8f516faf42da416c02355f9981add3137a3db190/op-service/txmgr/txmgr.go#L266) call. However, under certain race conditions, failures may occur after the transaction has been included in a block.

These modifications aim to enhance the security and efficiency of the batch submission and processing pipeline, allowing for more flexible and customizable conditions while maintaining the integrity of the derived state.


## Supporting Dynamic Updates to Inbox Address

### SystemConfig

The `SystemConfig` is the source of truth for the address of inbox. It stores information about the inbox address and passes the information to L2 as well. 


#### setBatchInbox

A new function `setBatchInbox` is introduced to the `SystemConfig` contract, enabling dynamic updates to the inbox:

```solidity
/// @notice Updates the batch inbox address. Can only be called by the owner.
/// @param _batchInbox New batch inbox address.
function setBatchInbox(address _batchInbox) external onlyOwner {
    _setBatchInbox(_batchInbox);
}

/// @notice Updates the batch inbox address.
/// @param _batchInbox New batch inbox address.
function _setBatchInbox(address _batchInbox) internal {
    Storage.setAddress(BATCH_INBOX_SLOT, _batchInbox);

    bytes memory data = abi.encode(_batchInbox);
    emit ConfigUpdate(VERSION, UpdateType.BATCH_INBOX, data);
}

```


#### initialize

The `SystemConfig` now emits an event when the inbox is initialized, while retaining its existing support for inbox configuration during initialization.

```solidity
function initialize(
    address _owner,
    uint32 _basefeeScalar,
    uint32 _blobbasefeeScalar,
    bytes32 _batcherHash,
    uint64 _gasLimit,
    address _unsafeBlockSigner,
    ResourceMetering.ResourceConfig memory _config,
    address _batchInbox,
    SystemConfig.Addresses memory _addresses
)
    public
    initializer
{
    ...
    // Storage.setAddress(BATCH_INBOX_SLOT, _batchInbox);
    // initialize inbox by `_setBatchInbox` so that an event is emitted.
    _setBatchInbox(_batchInbox);
    ...
}
```

#### UpdateType

A new enum value `BATCH_INBOX` is added to the `UpdateType` enumeration.

```solidity
enum UpdateType {
    BATCHER,
    GAS_CONFIG,
    GAS_LIMIT,
    UNSAFE_BLOCK_SIGNER,
    BATCH_INBOX
}
```

### L1 Info Deposit Transaction

The [`L1InfoDeposit`](https://github.com/ethereum-optimism/optimism/blob/5e317379fae65b76f5a6ee27581f0e62d2fe017a/op-node/rollup/derive/l1_block_info.go#L264) function creates a L1 Info deposit transaction based on the L1 block. It is extended to add an additional `batchInbox` parameter for the [`setL1BlockValuesEcotone`](https://github.com/ethereum-optimism/optimism/blob/5e317379fae65b76f5a6ee27581f0e62d2fe017a/packages/contracts-bedrock/src/L2/L1Block.sol#L136) function after the inbox contract feature is activated.

```golang
func L1InfoDeposit(rollupCfg *rollup.Config, sysCfg eth.SystemConfig, seqNumber uint64, block eth.BlockInfo, l2BlockTime uint64) (*types.DepositTx, error) {
    ...
    if isInboxForkButNotFirstBlock(rollupCfg, l2BlockTime) {
        l1BlockInfo.BatchInbox = sysCfg.BatchInbox
        l1BlockInfo.BlobBaseFee = block.BlobBaseFee()
        if l1BlockInfo.BlobBaseFee == nil {
          // The L2 spec states to use the MIN_BLOB_GASPRICE from EIP-4844 if not yet active on L1.
          l1BlockInfo.BlobBaseFee = big.NewInt(1)
        }
        scalars, err := sysCfg.EcotoneScalars()
        if err != nil {
          return nil, err
        }
        l1BlockInfo.BlobBaseFeeScalar = scalars.BlobBaseFeeScalar
        l1BlockInfo.BaseFeeScalar = scalars.BaseFeeScalar
        // marshalBinaryInboxFork adds an additional `batchInbox` parameter based on marshalBinaryEcotone.
        out, err := l1BlockInfo.marshalBinaryInboxFork()
        if err != nil {
          return nil, fmt.Errorf("failed to marshal InboxFork l1 block info: %w", err)
        }
        data = out
    } else if isEcotoneButNotFirstBlock(rollupCfg, l2BlockTime) {
    ...
}
```

The `marshalBinaryInboxFork` function is added to [`L1BlockInfo`](https://github.com/ethereum-optimism/optimism/blob/5e317379fae65b76f5a6ee27581f0e62d2fe017a/op-node/rollup/derive/l1_block_info.go#L41). This new function incorporates an additional `batchInbox` parameter for the [`setL1BlockValuesEcotone`](https://github.com/ethereum-optimism/optimism/blob/5e317379fae65b76f5a6ee27581f0e62d2fe017a/packages/contracts-bedrock/src/L2/L1Block.sol#L136) function:

```golang
func (info *L1BlockInfo) marshalBinaryInboxFork() ([]byte, error) {
    w := bytes.NewBuffer(make([]byte, 0, L1InfoEcotoneLen))
    if err := solabi.WriteSignature(w, L1InfoFuncEcotoneBytes4); err != nil {
      return nil, err
    }
    if err := binary.Write(w, binary.BigEndian, info.BaseFeeScalar); err != nil {
      return nil, err
    }
    if err := binary.Write(w, binary.BigEndian, info.BlobBaseFeeScalar); err != nil {
      return nil, err
    }
    if err := binary.Write(w, binary.BigEndian, info.SequenceNumber); err != nil {
      return nil, err
    }
    if err := binary.Write(w, binary.BigEndian, info.Time); err != nil {
      return nil, err
    }
    if err := binary.Write(w, binary.BigEndian, info.Number); err != nil {
      return nil, err
    }
    if err := solabi.WriteUint256(w, info.BaseFee); err != nil {
      return nil, err
    }
    blobBasefee := info.BlobBaseFee
    if blobBasefee == nil {
      blobBasefee = big.NewInt(1) // set to 1, to match the min blob basefee as defined in EIP-4844
    }
    if err := solabi.WriteUint256(w, blobBasefee); err != nil {
      return nil, err
    }
    if err := solabi.WriteHash(w, info.BlockHash); err != nil {
      return nil, err
    }
    // ABI encoding will perform the left-padding with zeroes to 32 bytes, matching the "batcherHash" SystemConfig format and version 0 byte.
    if err := solabi.WriteAddress(w, info.BatcherAddr); err != nil {
      return nil, err
    }
    // This is where marshalBinaryInboxFork differs from marshalBinaryEcotone
    if err := solabi.WriteAddress(w, info.BatchInbox); err != nil {
      return nil, err
    }
    return w.Bytes(), nil
}
```

### L1Block

The `L1Block` stores Layer 1 (L1) related information on Layer 2 (L2). It is extended to store the dynamic inbox address.

#### batchInbox

A new field `batchInbox` is added to the `L1Block`:

```solidity
    /// @notice The canonical batch inbox.
    bytes32 public batchInbox;
```

#### setL1BlockValuesEcotone

This function stores Layer 1 (L1) block values for Layer 2 (L2) since the Ecotone upgrade of the OP Stack. It is enhanced to also store the inbox address.

```solidity
function setL1BlockValuesEcotone() external {
    ...
    sstore(batchInbox.slot, calldataload(164)) // bytes32
}

```

### How `op-node` knows the canonical batch inbox

We define that the canonical batch inbox at a specific L2 block is the batch inbox of `SystemConfig` of the origin of the L2 block.

Under normal conditions, `op-node` knows the canonical batch inbox through the derivation pipeline:
1. The `L1Traversal` component first identifies the L1 `SystemConfig` changes while traversing the L1 block, via [`UpdateSystemConfigWithL1Receipts`](https://github.com/ethereum-optimism/optimism/blob/71928829ca7ece48152159daa1d231eac2df03b3/op-node/rollup/derive/l1_traversal.go#L78).
   1. The [`ProcessSystemConfigUpdateLogEvent`](https://github.com/ethereum-optimism/optimism/blob/71928829ca7ece48152159daa1d231eac2df03b3/op-node/rollup/derive/system_config.go#L59) function will be modified to parse the newly added inbox change.
2. The `L1Retrieval` component then fetches the canonical batch inbox from the `L1Traversal` componenet and [pass](https://github.com/ethereum-optimism/optimism/blob/71928829ca7ece48152159daa1d231eac2df03b3/op-node/rollup/derive/l1_retrieval.go#L57) it to the `DataSourceFactory` component, via `OpenData` function, similar to how [`SystemConfig.BatcherAddr`](https://github.com/ethereum-optimism/optimism/blob/71928829ca7ece48152159daa1d231eac2df03b3/op-service/eth/types.go#L382) is handled.
3. The `FetchingAttributesBuilder` component is updated to incorporate the canonical batch inbox into the `DepositTx`, via [`L1InfoDeposit`](https://github.com/ethereum-optimism/optimism/blob/71928829ca7ece48152159daa1d231eac2df03b3/op-node/rollup/derive/l1_block_info.go#L263). This modified `DepositTx` is subsequently used to obtain the `SystemConfig` during L2 chain reorganization.

During L2 reorganization, `op-node` knows the canonical batch inbox using the `SystemConfig` parameter of [`ResettableStage.Reset(context.Context, eth.L1BlockRef, eth.SystemConfig)`](https://github.com/ethereum-optimism/optimism/blob/71928829ca7ece48152159daa1d231eac2df03b3/op-node/rollup/derive/pipeline.go#L38) function, where `SystemConfig` is derived from the `DepositTx` of the corresponding L2 block.

### How `op-batcher` knows canonical batch inbox

Immediately before submitting a new batch, `op-batcher` fetches the current inbox address from L1 and submits to that address. After the transaction is successfully included in L1 at block `N`, `op-batcher` verifies that the inbox address hasn't changed at block `N`. If the address has changed, it resubmits the batch to the new address.

## Upgrade

The custom gas token upgrade is not yet defined to be part of a particular network upgrade, but it will be scheduled as part of a future hardfork. On the network upgrade block, a set of deposit transaction based upgrade transactions are deterministically generated by the derivation pipeline in the following order:

- L1 Attributes Transaction calling `setL1BlockValuesEcotone`
- User deposits from L1
- Network Upgrade Transactions
  - L1Block deployment
  - Update L1Block Proxy ERC-1967 Implementation Slot

The deployment transactions MUST have a `from` value that has no code and has no known
private key. This is to guarantee it cannot be frontran and have its nonce modified.
If this was possible, then an attacker would be able to modify the address that the
implementation is deployed to because it is based on `CREATE` and not `CREATE2`.
This would then cause the proxy implementation set transactions to set an incorrect
implementation address, resulting in a bricked contract. The calldata is not generated
dynamically to enable deterministic upgrade transactions across all networks.

The proxy upgrade transactions are from `address(0)` because the `Proxy` implementation
considers `address(0)` to be an admin. Going straight to the `Proxy` guarantees that
the upgrade will work because there is no guarantee that the `Proxy` is owned by the
`ProxyAdmin` and going through the `ProxyAdmin` would require stealing the identity
of its owner, which may be different on every chain. That would require adding L2
RPC access to the derivation pipeline and make the upgrade transactions non deterministic.

### L1Block Deployment

- `from`: `0x4210000000000000000000000000000000000002`
- `to`: `null`
- `mint`: `0`
- `value`: `0`
- `gasLimit`: TODO
- `data`: TODO
- `sourceHash`: TODO

### L1Block Proxy Update

- `from`: `0x0000000000000000000000000000000000000000`
- `to`: `0x4200000000000000000000000000000000000015`
- `mint`: `0`
- `value`: `0`
- `gasLimit`: `50,000`
- `data`: TODO
- `sourceHash`: TODO

### SystemConfig Upgrade

Finally, to dynamically change the inbox address, `SystemConfig` on L1 will be upgraded to accept a new inbox address.

Note that according to the [Optimism Style Guide](https://github.com/ethereum-optimism/optimism/blob/9d31040ecf8590423adf267ad24b03bc1bf7273b/packages/contracts-bedrock/STYLE_GUIDE.md), The process for upgrading the implementation is as follows:
1. Upgrade the implementation to the `StorageSetter` contract.
2. Use that to set the initialized slot (typically slot 0) to zero.
3. Upgrade the implementation to the desired new implementation and initialize it.

For a practical example of this process, refer to [this](https://github.com/ethereum-optimism/superchain-ops/blob/55e9520e27c7e916d8992ce351c6d5cfa8a511d8/tasks/eth/009-fp-upgrade/EXEC.md) execution document in the Optimism Superchain Operations repository.

## Security Considerations

### Inbox Sender

The inbox contract is a special contract that, if invoked by the batcher, all of its calldata / blob will be used as L2 derivation data, unless the transaction fails. In order to invoke and modify the state of the inbox contract, it is recommended to use a non-batcher sender.


## Reference Implementation

1. [example inbox contract for EthStorage](https://github.com/blockchaindevsh/es-op-batchinbox/blob/main/src/BatchInbox.sol)
2. [op-node & op-batcher changes](https://github.com/blockchaindevsh/optimism/compare/5137f3b74c6ebcac4f0f5a118b0f4909df03aec6...02e3b7248f1b590a2adf1f81488829760fa2ba03)

TODO: implement `Supporting Dynamic Updates to Inbox Address` mentioned above.