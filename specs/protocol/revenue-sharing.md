<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Revenue Sharing](#revenue-sharing)
  - [Definitions](#definitions)
  - [`RevenueSharer` predeploy](#revenuesharer-predeploy)
    - [Deploying `RevenueSharer`](#deploying-revenuesharer)
      - [Existing Chains](#existing-chains)
      - [Chains after version X.Y.Z of OP Stack](#chains-after-version-xyz-of-op-stack)
    - [Execution](#execution)
  - [Simplified L1 Data Fee Expenditure](#simplified-l1-data-fee-expenditure)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Revenue Sharing

Revenue sharing is the process by which chains in the superchain contribute a portion of their revenue or profit to the Optimism collective. They do this in return for support with the OP Stack and other benefits. 


## Definitions
| Term   | Name         | Definition  |
| -------|--------------| ----------- |
| $d$ | L1 Data Fee Revenue    | ETH transferred to the sequencer with L2 transactions to cover estimated L1 Data Fees(see below). Accumulates to `L1FeeVault`.
| $e$ | L1 Data Fee Expenditure| ETH spent by the batcher on L1 to make transaction data available
| $b$ | L2 Base Gas Revenue         | Base fee portion of L2 Gas Fee (ETH transferred to the sequencer to cover execution of L2 transactions). Accumulates to `BaseFeeVault`.
| $p$ | L2 Priority Gas Revenue         | Priority fee portion of L2 Gas Fee (ETH transferred to the sequencer to cover execution of L2 transactions). Accumulates to `SequencerFeeVault`.
| $g$ | L2 Gas Revenue         | $b+p$
| $r$ | Sequencer Revenue      | $d + g$
| $p$ | Sequencer Profit       | $d + g - e$
| $s$ | Revenue share due to Optimism Collective | $\max(0.15r,0.025p)$

## `RevenueSharer` predeploy
Revenue sharing is achieved through an L2 [predeploy](./predeploys.md) contract `RevenueSharer` with address

```
0x4200000000000000000000000000000000000024
```

### Deploying `RevenueSharer`


#### Existing Chains
The `RevenueSharer` can be deployed manually to an arbitrary address, and the existing `Proxy` at `0x4200000000000000000000000000000000000024` can have its implementation set by calling `upgrade` on the `ProxyAdmin`.

#### Chains after version X.Y.Z of OP Stack 
The `RevenueSharer` can be made a part of the genesis creation for new chains. 

### Reconfiguring existing predeploys
The three `FeeVault` contracts need to be upgraded so that their immutable `RECIPIENT` variable points at the `RevenueSharer`.

#### Existing Chains
Appropriate transactions can be bundled with the deployment itself.

#### Chains after version X.Y.Z of OP Stack 
Appropriate changes to the genesis will be made.



### Execution
Revenue sharing is executed periodically. 
The `RevenueSharer` is responsible for computing $s$ and sending it to a predetermined address controlled by the Optimism Collective. At the end of execution, `SequencerFeeVault`, `L1FeeVault` and `BaseFeeVault` and `RevenueSharer` should be completely depleted of ETH. This allows the contract to be stateless.

```mermaid
   flowchart TD
   SequencerFeeVault
   BaseFeeVault
   L1FeeVault
   OptimismCollectiveWallet
   RemainderWallet
   RevenueSharer
   SequencerFeeVault-->|p|RevenueSharer
   L1FeeVault-->|d|RevenueSharer
   BaseFeeVault-->|b|RevenueSharer
   RevenueSharer-->|s|OptimismCollectiveWallet
   RevenueSharer-->|r-s|RemainderWallet
```
## Simplified L1 Data Fee Expenditure
As a part of a gradual rollout of protocol enshrined revenue sharing, the `RevenueSharer` uses a fixed value of $e=0$. The sequencer makes a profit on data availability of $d-e$. Note that a negative profit, i.e. a loss, is possible.  By assuming $e=0$, the simplification implies that data availability revenue is all profit. This will be addressed in a future protocol upgrade. 

