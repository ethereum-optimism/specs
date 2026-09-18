# Optimism Overview

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Architecture Design Goals](#architecture-design-goals)
- [Architecture Overview](#architecture-overview)
  - [Core L1 Smart Contracts](#core-l1-smart-contracts)
    - [Notes for Core L1 Smart Contracts](#notes-for-core-l1-smart-contracts)
  - [Core L2 Smart Contracts](#core-l2-smart-contracts)
    - [Notes for Core L2 Smart Contracts](#notes-for-core-l2-smart-contracts)
  - [Smart Contract Proxies](#smart-contract-proxies)
    - [L2 contract upgrades](#l2-contract-upgrades)
  - [L2 Node Components](#l2-node-components)
  - [Transaction/Block Propagation](#transactionblock-propagation)
- [Key Interactions In Depth](#key-interactions-in-depth)
  - [Deposits](#deposits)
  - [Block Derivation](#block-derivation)
    - [Overview](#overview)
    - [Epochs and the Sequencing Window](#epochs-and-the-sequencing-window)
    - [Block Derivation Loop](#block-derivation-loop)
  - [Engine API](#engine-api)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

This document is a high-level technical overview of the Optimism protocol. It aims to explain how the protocol works in
an informal manner, and direct readers to other parts of the specification so that they may learn more.

This document assumes you've read the [background](../background.md).

## Architecture Design Goals

- **Execution-Level EVM Equivalence:** The developer experience should be identical to L1 except where L2 introduces a
  fundamental difference.
  - No special compiler.
  - No unexpected gas costs.
  - Transaction traces work out-of-the-box.
  - All existing Ethereum tooling works - all you have to do is change the chain ID.
- **Maximal compatibility with ETH1 nodes:** The implementation should minimize any differences with a vanilla Geth
  node, and leverage as many existing L1 standards as possible.
  - The execution engine/rollup node uses the ETH2 Engine API to build the canonical L2 chain.
  - The execution engine leverages Geth's existing mempool and sync implementations, including snap sync.
- **Minimize state and complexity:**
  - Whenever possible, services contributing to the rollup infrastructure are stateless.
  - Stateful services can recover to full operation from a fresh DB using the peer-to-peer network and on-chain sync
    mechanisms.
  - Running a replica is as simple as running a Geth node.

## Architecture Overview

Blue nodes are upgradeable contracts, green nodes have fixed implementations, and orange nodes are actors or protocol
transactions. Grey nodes show other contracts, addresses, or configuration. Dotted arrows indicate reads.

### Core L1 Smart Contracts

Below you'll find architecture diagrams describing the core L1 smart contracts for the OP Stack.
Smart contracts that are considered "peripheral" and not core to the operation of the OP Stack system are described separately.

These diagrams assume a single ETH-gas chain with `ETHLockbox` enabled.

```mermaid
%%{init: {"theme": "base", "themeVariables": {"lineColor": "#64748b", "edgeLabelBackground": "#f1f5f9"}, "themeCSS": ".nodeLabel a { color: inherit !important; }"}}%%
graph TB
    ExternalERC20(External ERC20 Contracts)
    ExternalERC721(External ERC721 Contracts)
    L1StandardBridge(<a href="./bridges.html">L1StandardBridge</a>)
    L1ERC721Bridge(<a href="./bridges.html">L1ERC721Bridge</a>)
    L1CrossDomainMessenger(<a href="./messengers.html">L1CrossDomainMessenger</a>)
    OptimismPortal(<a href="./withdrawals.html#the-optimism-portal-contract">OptimismPortal</a>)
    ETHLockbox(<a href="../interop/eth-lockbox.html">ETHLockbox</a>)

    ExternalERC20 <-->|mint/burn/transfer tokens| L1StandardBridge
    ExternalERC721 <-->|lock/unlock| L1ERC721Bridge
    L1StandardBridge <-->|send/receive messages| L1CrossDomainMessenger
    L1ERC721Bridge <-->|send/receive messages| L1CrossDomainMessenger
    L1CrossDomainMessenger <-->|send/receive messages| OptimismPortal
    OptimismPortal <-->|lock/unlock ETH| ETHLockbox

    classDef proxy fill:#e8f1ff,stroke:#3971b8,color:#17375e,stroke-width:1.5px;
    classDef other fill:#f1f3f5,stroke:#98a2b3,color:#344054,stroke-width:1.5px;
    class L1StandardBridge,L1ERC721Bridge,L1CrossDomainMessenger,OptimismPortal,ETHLockbox proxy;
    class ExternalERC20,ExternalERC721 other;
```

The portal uses dispute games to verify withdrawals. Permissionless games dispute super roots at L2 timestamps;
the portal reads the output root for its chain from the selected game.

<!-- cspell:ignore preimageoracle -->

```mermaid
%%{init: {"theme": "base", "themeVariables": {"lineColor": "#64748b", "edgeLabelBackground": "#f1f5f9"}, "themeCSS": ".nodeLabel a { color: inherit !important; }"}}%%
graph TB
    OptimismPortal(<a href="../fault-proof/stage-one/optimism-portal.html">OptimismPortal</a>)
    DisputeGameFactory(<a href="../fault-proof/stage-one/dispute-game-interface.html#disputegamefactory-interface">DisputeGameFactory</a>)
    subgraph Games[Dispute games]
        SuperFaultDisputeGame(<a href="../fault-proof/stage-one/super-fault-dispute-game.html">SuperFault<br/>DisputeGame</a>)
        SuperPermissionedDisputeGame(<a href="https://github.com/ethereum-optimism/optimism/blob/develop/packages/contracts-bedrock/src/dispute/SuperPermissionedDisputeGame.sol">SuperPermissioned<br/>DisputeGame</a>)
    end
    AnchorStateRegistry(<a href="../fault-proof/stage-one/anchor-state-registry.html">AnchorStateRegistry</a>)
    DelayedWETH(<a href="../fault-proof/stage-one/bond-incentives.html#delayedweth">DelayedWETH</a>)
    MIPS64(<a href="../fault-proof/cannon-fault-proof-vm.html">MIPS64</a>)
    PreimageOracle(<a href="../fault-proof/stage-one/fault-dispute-game.html#preimageoracle">PreimageOracle</a>)

    OptimismPortal -.->|look up games| DisputeGameFactory
    OptimismPortal -.->|validity/finality| AnchorStateRegistry
    OptimismPortal -.->|chain output root| Games
    DisputeGameFactory -->|clone| Games
    SuperFaultDisputeGame -->|store bonds| DelayedWETH
    SuperFaultDisputeGame -->|query/update<br/>anchor states| AnchorStateRegistry
    SuperPermissionedDisputeGame -.->|anchor/game type| AnchorStateRegistry
    SuperFaultDisputeGame -->|verify step| MIPS64
    SuperFaultDisputeGame -->|local data| PreimageOracle
    MIPS64 -.->|preimages| PreimageOracle

    classDef proxy fill:#e8f1ff,stroke:#3971b8,color:#17375e,stroke-width:1.5px;
    classDef fixed fill:#e5f3ec,stroke:#3b8363,color:#173f2e,stroke-width:1.5px;
    class OptimismPortal,DisputeGameFactory,AnchorStateRegistry,DelayedWETH proxy;
    class SuperFaultDisputeGame,SuperPermissionedDisputeGame,MIPS64,PreimageOracle fixed;
    style Games fill:#f8fafc,stroke:#cbd5e1,color:#334155;
```

#### Notes for Core L1 Smart Contracts

- The `Batch Inbox Address` shown below (**highlighted in GREY**) is _not_ a smart contract and is instead an arbitrarily
  selected account that is assumed to have no known private key. The convention for deriving this account's address is
  provided on the [Configurability](./configurability.md#consensus-parameters) page.
  - Historically, it was often derived as
    `0xFF0000....<L2 chain ID>` where `<L2 chain ID>` is chain ID of the Layer 2 network for which the data is being posted.
    This is why many chains, such as OP Mainnet, have a batch inbox address of this form.
- Smart contracts that sit behind `Proxy` contracts are **highlighted in BLUE**. Refer to the
  [Smart Contract Proxies](#smart-contract-proxies) section below to understand how these proxies are designed.
  - The `L1CrossDomainMessenger` contract sits behind the [`ResolvedDelegateProxy`](https://github.com/ethereum-optimism/optimism/tree/develop/packages/contracts-bedrock/src/legacy/ResolvedDelegateProxy.sol)
    contract, a legacy proxy contract type used within older versions of the OP Stack. This proxy type is used exclusively
    for the `L1CrossDomainMessenger` to maintain backwards compatibility.
  - The `L1StandardBridge` contract sits behind the [`L1ChugSplashProxy`](https://github.com/ethereum-optimism/optimism/tree/develop/packages/contracts-bedrock/src/legacy/L1ChugSplashProxy.sol)
    contract, a legacy proxy contract type used within older versions of the OP Stack. This proxy type is used exclusively
    for the `L1StandardBridge` contract to maintain backwards compatibility.
- Green contracts have fixed implementations. The factory creates dispute games as clones with immutable arguments;
  `MIPS64` and `PreimageOracle` are deployed directly.
- `SuperFaultDisputeGame` uses game type `SUPER_CANNON_KONA` (`9`). `SuperPermissionedDisputeGame` uses
  `SUPER_PERMISSIONED` (`5`) and accepts proposals only from its configured proposer. It resolves immediately in favor of
  the proposal, without challenges or bonds. Withdrawal finality and Guardian checks still apply.
- Users deposit or withdraw ETH and tokens through the bridges. They can also deposit directly through `OptimismPortal`,
  where they prove and execute withdrawals.
- The bridges, messenger, portal, `ETHLockbox`, `AnchorStateRegistry`, and `DelayedWETH` read pause state through
  [SystemConfig](./system-config.md). It combines the global pause state from [SuperchainConfig](./superchain-config.md)
  with the chain-specific pause state, identified by `ETHLockbox`. The portal also reads its configuration from `SystemConfig`.
- The Guardian pauses or unpauses `SuperchainConfig`. It can blacklist or retire games and set the respected game type
  in `AnchorStateRegistry`. The factory owner configures game types and bonds; the `ProxyAdmin` owner can hold or recover
  bonds in `DelayedWETH`.
- Proposers create games through `DisputeGameFactory`; `AnchorStateRegistry` checks game registration with the factory.
  Participants challenge or defend permissionless games and supply preimages to `PreimageOracle`.

### Core L2 Smart Contracts

Here you'll find architecture diagrams describing the core OP Stack smart contracts that exist natively on the L2 chain
itself.

```mermaid
%%{init: {"theme": "base", "themeVariables": {"lineColor": "#64748b", "edgeLabelBackground": "#f1f5f9"}, "themeCSS": ".nodeLabel a { color: inherit !important; }"}}%%
graph TB
    L2Node(L2 Node)
    L1Block(<a href="./predeploys.html#l1block">L1Block</a>)
    GasPriceOracle(<a href="./predeploys.html#gaspriceoracle">GasPriceOracle</a>)
    subgraph FeeVaults[Fee vaults]
        direction TB
        L1FeeVault(<a href="./predeploys.html#l1feevault">L1FeeVault</a>)
        BaseFeeVault(<a href="./predeploys.html#basefeevault">BaseFeeVault</a>)
        SequencerFeeVault(<a href="./predeploys.html#sequencerfeevault">SequencerFeeVault</a>)
        OperatorFeeVault(<a href="./predeploys.html#operator-fee-vault">OperatorFeeVault</a>)
    end

    L2Node -->|updates| L1Block
    L2Node -->|credit fees| FeeVaults
    GasPriceOracle -.->|queries| L1Block

    classDef proxy fill:#e8f1ff,stroke:#3971b8,color:#17375e,stroke-width:1.5px;
    classDef actor fill:#fff1df,stroke:#bf7b2a,color:#664515,stroke-width:1.5px;
    class L1Block,GasPriceOracle,L1FeeVault,BaseFeeVault,SequencerFeeVault,OperatorFeeVault proxy;
    class L2Node actor;
    style FeeVaults fill:#f8fafc,stroke:#cbd5e1,color:#334155;
```

The L2 bridges mint, burn, or transfer tokens and send withdrawal messages through `L2ToL1MessagePasser`.
Deposits can call `L2CrossDomainMessenger` to relay messages from L1. Both deposits and user transactions can also
target other L2 contracts or addresses.

```mermaid
%%{init: {"theme": "base", "themeVariables": {"lineColor": "#64748b", "edgeLabelBackground": "#f1f5f9"}, "themeCSS": ".nodeLabel a { color: inherit !important; }"}}%%
graph TB
    ExternalERC20(External ERC20 Contracts)
    ExternalERC721(External ERC721 Contracts)
    L2StandardBridge(<a href="./predeploys.html#l2standardbridge">L2StandardBridge</a>)
    L2ERC721Bridge(<a href="./predeploys.html">L2ERC721Bridge</a>)
    L2CrossDomainMessenger(<a href="./predeploys.html#l2crossdomainmessenger">L2CrossDomainMessenger</a>)
    L2ToL1MessagePasser(<a href="./predeploys.html#l2tol1messagepasser">L2ToL1MessagePasser</a>)

    ExternalERC20 <-->|mint/burn/transfer| L2StandardBridge
    ExternalERC721 <-->|mint/burn| L2ERC721Bridge
    L2StandardBridge <-->|sends/receives messages| L2CrossDomainMessenger
    L2ERC721Bridge <-->|sends/receives messages| L2CrossDomainMessenger
    L2CrossDomainMessenger -->|sends messages| L2ToL1MessagePasser

    classDef proxy fill:#e8f1ff,stroke:#3971b8,color:#17375e,stroke-width:1.5px;
    classDef other fill:#f1f3f5,stroke:#98a2b3,color:#344054,stroke-width:1.5px;
    class L2StandardBridge,L2ERC721Bridge,L2CrossDomainMessenger,L2ToL1MessagePasser proxy;
    class ExternalERC20,ExternalERC721 other;
```

#### Notes for Core L2 Smart Contracts

- L1 attributes transactions update `L1Block`, and the execution engine credits transaction fees to the fee vaults.
  `GasPriceOracle` reads fee parameters from `L1Block`.
  Users typically do not mutate these contracts directly, except in the case of the `FeeVault` contracts where
  any user may trigger a withdrawal of collected fees to the pre-determined withdrawal address.
- Fee vault withdrawals can target L1 through `L2ToL1MessagePasser`, or L2 directly, depending on the vault's configuration.
- The execution engine also updates the [beacon roots contract](./exec-engine.md#ecotone-beacon-block-root) with the
  L1 origin's parent beacon block root and the
  [history storage contract](./isthmus/derivation.md#eip-2935-contract-deployment) with L2 block hashes.
- Smart contracts that sit behind `Proxy` contracts are **highlighted in BLUE**. Refer to the
  [Smart Contract Proxies](#smart-contract-proxies) section below to understand how these proxies are designed.
- User interactions for the "L2 Bridge Contracts" have been omitted from these diagrams but largely follow the same user
  interactions described in the notes for the [Core L1 Smart Contracts](#core-l1-smart-contracts).

### Smart Contract Proxies

Most OP Stack smart contracts sit behind `Proxy` contracts that are managed by a `ProxyAdmin` contract.
The `ProxyAdmin` contract is controlled by some `owner` address that can be any EOA or smart contract.
Below you'll find a diagram that explains the behavior of the typical proxy contract.

```mermaid
%%{init: {"theme": "base", "themeVariables": {"lineColor": "#64748b", "edgeLabelBackground": "#f1f5f9"}, "themeCSS": ".nodeLabel a { color: inherit !important; }"}}%%
graph LR
    ProxyAdminOwner(Proxy Admin Owner)
    ProxyAdmin(<a href="https://github.com/ethereum-optimism/optimism/blob/develop/packages/contracts-bedrock/src/universal/ProxyAdmin.sol">ProxyAdmin</a>)

    subgraph LogicalContract[Logical Smart Contract]
        Proxy(<a href="https://github.com/ethereum-optimism/optimism/blob/develop/packages/contracts-bedrock/src/universal/Proxy.sol">Proxy</a>)
        Implementation(Implementation)
    end

    ProxyAdminOwner -->|manages| ProxyAdmin
    ProxyAdmin -->|upgrades| Proxy
    Proxy -->|delegatecall| Implementation

    classDef proxy fill:#e8f1ff,stroke:#3971b8,color:#17375e,stroke-width:1.5px;
    classDef fixed fill:#e5f3ec,stroke:#3b8363,color:#173f2e,stroke-width:1.5px;
    classDef actor fill:#fff1df,stroke:#bf7b2a,color:#664515,stroke-width:1.5px;
    class Proxy proxy;
    class ProxyAdmin,Implementation fixed;
    style LogicalContract fill:#f8fafc,stroke:#cbd5e1,color:#334155;
    class ProxyAdminOwner actor;
```

On L1, the `ProxyAdmin` owner uses [OP Contracts Manager](../experimental/op-contracts-manager.md) to coordinate upgrades.
The owner's Safe delegatecalls the manager, so its calls to `ProxyAdmin` execute with the owner's authority.

#### L2 contract upgrades

[Network upgrade transactions](./l2-upgrades-1-execution.md#bundle-format) run at fork activation. They deploy the new
implementations and a version of `L2ContractsManager`, then call `L2ProxyAdmin.upgradePredeploys` from `DEPOSITOR_ACCOUNT`.
`L2ProxyAdmin` delegatecalls the manager, which upgrades the predeploy proxies atomically and preserves their existing
chain configuration. Only `DEPOSITOR_ACCOUNT` can call `upgradePredeploys`; the `L2ProxyAdmin` owner can still use its
ordinary administrative upgrade methods.

```mermaid
%%{init: {"theme": "base", "themeVariables": {"lineColor": "#64748b", "edgeLabelBackground": "#f1f5f9"}, "themeCSS": ".nodeLabel a { color: inherit !important; }"}}%%
graph TB
    NetworkUpgrade(Network Upgrade<br/>Transactions)
    ConditionalDeployer(<a href="https://github.com/ethereum-optimism/optimism/blob/develop/packages/contracts-bedrock/src/L2/ConditionalDeployer.sol">ConditionalDeployer</a>)
    DeterministicDeploymentProxy(Deterministic<br/>DeploymentProxy)
    Implementations(Predeploy Implementations)
    L2ContractsManager(<a href="https://github.com/ethereum-optimism/optimism/blob/develop/packages/contracts-bedrock/src/L2/L2ContractsManager.sol">L2ContractsManager</a>)
    L2ProxyAdmin(<a href="https://github.com/ethereum-optimism/optimism/blob/develop/packages/contracts-bedrock/src/L2/L2ProxyAdmin.sol">L2ProxyAdmin</a>)
    ProxyAdminOwner(ProxyAdmin Owner)
    PredeployProxies(Predeploy Proxies)
    Configuration(Existing Predeploy<br/>Configuration)
    L1Block(L1Block)
    L2DevFeatureFlags(<a href="https://github.com/ethereum-optimism/optimism/blob/develop/packages/contracts-bedrock/src/L2/L2DevFeatureFlags.sol">L2DevFeatureFlags</a>)

    NetworkUpgrade -->|request deployments| ConditionalDeployer
    ConditionalDeployer -->|call if target absent| DeterministicDeploymentProxy
    DeterministicDeploymentProxy -->|CREATE2| Implementations
    DeterministicDeploymentProxy -->|CREATE2| L2ContractsManager
    NetworkUpgrade -->|upgradePredeploys| L2ProxyAdmin
    ProxyAdminOwner -->|ordinary admin methods| L2ProxyAdmin
    L2ProxyAdmin -->|delegatecall upgrade| L2ContractsManager
    L2ProxyAdmin -->|upgrade and initialize| PredeployProxies
    PredeployProxies -->|delegatecall| Implementations
    L2ContractsManager -.->|read config| Configuration
    L2ContractsManager -.->|read feature flags| L1Block
    L2ContractsManager -.->|read development flags| L2DevFeatureFlags

    classDef proxy fill:#e8f1ff,stroke:#3971b8,color:#17375e,stroke-width:1.5px;
    classDef fixed fill:#e5f3ec,stroke:#3b8363,color:#173f2e,stroke-width:1.5px;
    classDef actor fill:#fff1df,stroke:#bf7b2a,color:#664515,stroke-width:1.5px;
    classDef other fill:#f1f3f5,stroke:#98a2b3,color:#344054,stroke-width:1.5px;
    class ConditionalDeployer,L2ProxyAdmin,PredeployProxies,L1Block,L2DevFeatureFlags proxy;
    class DeterministicDeploymentProxy,Implementations,L2ContractsManager fixed;
    class NetworkUpgrade,ProxyAdminOwner actor;
    class Configuration other;
```

`ConditionalDeployer`, `L2ProxyAdmin`, and `L2DevFeatureFlags` are proxied predeploys. Green contracts have fixed
implementations; `L2ContractsManager` is deployed separately for each upgrade. Its upgrade calls execute in
`L2ProxyAdmin`'s context. See the
[L2 upgrade contracts specification](https://github.com/ethereum-optimism/optimism/blob/develop/packages/contracts-bedrock/specs/l2-upgrades-2-contracts.md)
for the deployment and configuration rules.

### L2 Node Components

Below you'll find a diagram illustrating the basic interactions between the components that make up an L2 node as well
as demonstrations of how different actors use these components to fulfill their roles.

```mermaid
%%{init: {"theme": "base", "themeVariables": {"lineColor": "#64748b", "edgeLabelBackground": "#f1f5f9"}, "themeCSS": ".nodeLabel a { color: inherit !important; }"}}%%
graph LR
    subgraph NodeComponents[L2 Node]
        RollupNode(<a href="./rollup-node.html">Rollup Node</a>)
        ExecutionEngine(<a href="./exec-engine.html">Execution Engine</a>)
    end

    subgraph SystemActors[System Interactions]
        BatchSubmitter(<a href="./batcher.html">Batch Submitter</a>)
        OutputSubmitter(Proposer)
        Challenger(Challenger)
    end

    BatchDataEOA(<a href="../glossary.html#batcher-transaction">Batch Inbox Address</a>)

    subgraph L1Contracts[L1 Smart Contracts]
        OptimismPortal(<a href="./withdrawals.html#the-optimism-portal-contract">OptimismPortal</a>)
        DisputeGameFactory(<a href="../fault-proof/stage-one/dispute-game-interface.html#disputegamefactory-interface">DisputeGameFactory</a>)
        SuperFaultDisputeGame(<a href="../fault-proof/stage-one/super-fault-dispute-game.html">SuperFaultDisputeGame</a>)
    end

    BatchSubmitter -.->|fetch transaction<br/>batch info| RollupNode
    BatchSubmitter -.->|fetch transaction<br/>batch info| ExecutionEngine
    BatchSubmitter -->|send transaction<br/>batches| BatchDataEOA

    RollupNode -.->|fetch transaction<br/>batches| BatchDataEOA
    RollupNode -.->|fetch deposit<br/>transactions| OptimismPortal
    RollupNode -->|drives| ExecutionEngine

    OutputSubmitter -.->|fetch super roots| RollupNode
    OutputSubmitter -->|propose super roots| DisputeGameFactory

    Challenger -.->|fetch dispute games| DisputeGameFactory
    Challenger -.->|fetch super roots| RollupNode
    Challenger -->|verify/challenge/<br/>defend games| SuperFaultDisputeGame

    classDef proxy fill:#e8f1ff,stroke:#3971b8,color:#17375e,stroke-width:1.5px;
    classDef fixed fill:#e5f3ec,stroke:#3b8363,color:#173f2e,stroke-width:1.5px;
    classDef actor fill:#fff1df,stroke:#bf7b2a,color:#664515,stroke-width:1.5px;
    classDef other fill:#f1f3f5,stroke:#98a2b3,color:#344054,stroke-width:1.5px;
    class RollupNode,ExecutionEngine actor;
    class BatchSubmitter,OutputSubmitter,Challenger actor;
    class OptimismPortal,DisputeGameFactory proxy;
    class BatchDataEOA other;
    class SuperFaultDisputeGame fixed;
    style NodeComponents fill:#f8fafc,stroke:#cbd5e1,color:#334155;
    style SystemActors fill:#f8fafc,stroke:#cbd5e1,color:#334155;
    style L1Contracts fill:#f8fafc,stroke:#cbd5e1,color:#334155;
```

The rollup node also reads configuration updates from `SystemConfig` on L1.

### Transaction/Block Propagation

**Spec links:**

- [Execution Engine](exec-engine.md)

Since the EE uses Geth under the hood, Optimism uses Geth's built-in peer-to-peer network and transaction pool to
propagate transactions. The same network can also be used to propagate submitted blocks and support snap-sync.

Unsubmitted blocks, however, are propagated using a separate peer-to-peer network of Rollup Nodes. This is optional,
however, and is provided as a convenience to lower latency for verifiers and their JSON-RPC clients.

The below diagram illustrates how the sequencer and verifiers fit together:

![Propagation](../static/assets/propagation.svg)

## Key Interactions In Depth

### Deposits

**Spec links:**

- [Deposits](deposits.md)

Optimism supports user deposits and L1 attributes deposits. To perform a user deposit, users
call the `depositTransaction` method on the `OptimismPortal` contract. This in turn emits `TransactionDeposited` events,
which the rollup node reads during block derivation.

L1 attributes deposits are used to register L1 block attributes (number, timestamp, etc.) on L2 via a call to the L1
Attributes Predeploy. They cannot be initiated by users, and are instead added to L2 blocks automatically by the rollup
node.

Both deposit types are represented by a single custom EIP-2718 transaction type on L2.
[Network upgrade transactions](./l2-upgrades-1-execution.md#network-upgrade-transaction-nut) also use this type at fork
activation to deploy and upgrade L2 contracts.

### Block Derivation

#### Overview

The rollup chain can be deterministically derived given an L1 Ethereum chain. The fact that the entire rollup chain can
be derived based on L1 blocks is _what makes Optimism a rollup_. This process can be represented as:

```text
derive_rollup_chain(l1_blockchain) -> rollup_blockchain
```

Optimism's block derivation function is designed such that it:

- Requires no state other than what is easily accessible using L1 and L2 execution engine APIs.
- Supports sequencers and sequencer consensus.
- Is resilient to sequencer censorship.

#### Epochs and the Sequencing Window

The rollup chain is subdivided into epochs. There is a 1:1 correspondence between L1 block numbers and epoch numbers.

For L1 block number `n`, there is a corresponding rollup epoch `n` which can only be derived after a _sequencing window_
worth of blocks has passed, i.e. after L1 block number `n + SEQUENCING_WINDOW_SIZE` is added to the L1 chain.

Each epoch contains at least one block. Every block in the epoch contains an L1 info transaction which contains
contextual information about L1 such as the block hash and timestamp. The first block in the epoch also contains all
deposits initiated via the `OptimismPortal` contract on L1. All L2 blocks can also contain _sequenced transactions_,
i.e. transactions submitted directly to the sequencer.

Whenever the sequencer creates a new L2 block for a given epoch, it must submit it to L1 as part of a _batch_, within
the epoch's sequencing window (i.e. the batch must land before L1 block `n + SEQUENCING_WINDOW_SIZE`). These batches are
(along with the `TransactionDeposited` L1 events) what allows the derivation of the L2 chain from the L1 chain.

The sequencer does not need for a L2 block to be batch-submitted to L1 in order to build on top of it. In fact, batches
typically contain multiple L2 blocks worth of sequenced transactions. This is what enables
_fast transaction confirmations_ on the sequencer.

Since transaction batches for a given epoch can be submitted anywhere within the sequencing window, verifiers must
search all blocks within the window for transaction batches. This protects against the uncertainty of transaction
inclusion of L1. This uncertainty is also why we need the sequencing window in the first place: otherwise the sequencer
could retroactively add blocks to an old epoch, and validators wouldn't know when they can finalize an epoch.

The sequencing window also prevents censorship by the sequencer: deposits made on a given L1 block will be included in
the L2 chain at worst after `SEQUENCING_WINDOW_SIZE` L1 blocks have passed.

The following diagram describes this relationship, and how L2 blocks are derived from L1 blocks (L1 info transactions
have been elided):

![Epochs and Sequencing Windows](../static/assets/sequencer-block-gen.svg)

#### Block Derivation Loop

A sub-component of the rollup node called the _rollup driver_ is actually responsible for performing block derivation.
The rollup driver is essentially an infinite loop that runs the block derivation function. For each epoch, the block
derivation function performs the following steps:

1. Downloads deposit and transaction batch data for each block in the sequencing window.
2. Converts the deposit and transaction batch data into payload attributes for the Engine API.
3. Submits the payload attributes to the Engine API, where they are converted into blocks and added to the canonical
   chain.

This process is then repeated with incrementing epochs until the tip of L1 is reached.

### Engine API

The rollup driver doesn't actually create blocks. Instead, it directs the execution engine to do so via the Engine API.
For each iteration of the block derivation loop described above, the rollup driver will craft a _payload attributes_
object and send it to the execution engine. The execution engine will then convert the payload attributes object into a
block, and add it to the chain. The basic sequence of the rollup driver is as follows:

1. Call [fork choice updated][EngineAPIVersion] with the payload attributes object. We'll skip over the details of the
   fork choice state parameter for now - just know that one of its fields is the L2 chain's `headBlockHash`, and that it
   is set to the block hash of the tip of the L2 chain. The Engine API returns a payload ID.
2. Call [get payload][EngineAPIVersion] with the payload ID returned in step 1. The engine API returns a payload object
   that includes a block hash as one of its fields.
3. Call [new payload][EngineAPIVersion] with the payload returned in step 2. (Ecotone blocks, must use V3, pre-Ecotone
   blocks MUST use the V2 version)
4. Call [fork choice updated][EngineAPIVersion] with the fork choice parameter's `headBlockHash` set to the block hash
   returned in step 2. The tip of the L2 chain is now the block created in step 1.

[EngineAPIVersion]: derivation.md#engine-api-usage

The swimlane diagram below visualizes the process:

![Engine API](../static/assets/engine.svg)
