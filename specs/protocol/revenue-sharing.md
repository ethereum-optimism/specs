# Revenue Sharing

Revenue sharing is the process by which chains in the superchain contribute a portion of their revenue or profit to the Optimism collective. They do this in return for support with the OP Stack and other benefits. 


## Definitions
| Term   | Name         | Definition  |
| -------|--------------| ----------- |
| $d$ | L1 Data Fee Revenue    | ETH transferred to the sequencer with L2 transactions to cover estimated L1 Data Fees(see below). Accumulates to `L1FeeVault`.
| $e$ | L1 Data Fee Expenditure| ETH spent by the batcher on L1 to make transaction data available
| $g$ | L2 Gas Revenue         | ETH transferred to the sequencer to cover execution of L2 transactions. Accumulates to `SequencerFeeVault` and `BaseFeeVault`.
| $r$ | Sequencer Revenue      | $e + g$
| $p$ | Sequencer Profit       | $e + g - d$
| $s$ | Revenue share due to Optimism Collective | $\max(0.15r,0.025p)$