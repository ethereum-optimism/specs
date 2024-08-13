### 👣 Steps to take in order to properly manage the entire releases process for the OP mainnet:

## 1. Governance threshold check

- As you first step, you will need to look into governance threshold to know will your feature pass and understand the all the governance needs for your proposal.
    
    *Good reads on the topic can be found: [OPerating manual](https://github.com/ethereum-optimism/OPerating-manual/tree/main?tab=readme-ov-file), [Optimism Agora](https://vote.optimism.io/)*
    
### Process explainer for this step:

The threshold for which changes require a governance vote is based on the User Protections clause of the Law of Chains. In summary, these protections are:

1. **State Transition and Messaging Validity:** OP Chain state transitions or cross-chain messages sent to or from OP Chains must follow the rules of the latest governance-approved release of the OP Stack. This means that changes to the block derivation function or messenger contracts are always subject to a governance vote.
2. **Security, Uptime, and Liveness:** Block production, sequencing, and bridging must satisfy uniform standards for security, uptime, and liveness across all OP Chains. This means that  changes that could cause users to be unable to transact (e.g., changing the gas limit to something untenable) are subject to a governance vote.
3. **Universal, Governance-Approved Upgrades:** OP Chains must upgrade together under OP Stack releases that are approved by governance. Any upgrades that aren’t backwards compatible are therefore subject to a governance vote.

## 2. Call everything done on the development side

- Pass all check on the engineering criteria - in order to call something done on the development side, you need to go over the listed steps:
  - Code you have is implementation-complete 🏁
  - Code has automated tests, that are well explained
  - Code is behind a feature-flag 🚩
  - You have updated protocol specs and share it for reviews from the security team: https://github.com/ethereum-optimism/specs/tree/main/specs
  - Code has run on your internal-devnet for as long as necessary for you to test all features
  - Code has run on Goerli or Sepolia for a week and didn’t experience and bugs/performance/stability issues

    ## 3. Hardfork preparation (optional)

- Hardfork is prepared *[If needed - hardforks are needed if we are adding major/protocol-level changes to our stack]*
   - Named hardfork is created
   - Code has been configured to activate with the named hardfork
   - Upgrades of Fault Proof systems are prepared

    ## 4. Security standards and criteria check are done

-   Security criteria passed
    - The TL responsible for the launch needs to write a [Failure Mode Analyses (FMAs)](https://www.notion.so/Failure-Mode-Analyses-FMAs-1fb9f65a13e542e5b48af6c850763494?pvs=21) (FMA) describing failure modes and recovery paths for the launch.
        - [If Required] Security has signed-off on the FMA
    - [If Required] Audits are completed and issues fixed
    - [If Required] Security monitoring and block history integrity checks updated to support the new feature.

## 5. Governance standards and criteria check are done if

-   [If Vote Required] Governance criteria passed
    - Governance proposal is created and shared [here](https://gov.optimism.io/c/other-proposals/protocol-upgrade/58)
    - FND approves the proposal
    - Proposal is posted on Gov forums as a draft
    - Draft is finalized, shared on all relevant forums and all open comments are addressed

# Process steps explained for all required checks that we mentioned:

## 1. Determine Governance Threshold (Framework for Protocol Upgrades)

<aside>
⚠️ All upgrades which require the Security Council to take action require a governance vote, if they are not an emergency bugfix.

</aside>

The threshold for which changes require a governance vote is based on the User Protections clause of the Law of Chains. In summary, these protections are:

1. **State Transition and Messaging Validity:** OP Chain state transitions or cross-chain messages sent to or from OP Chains must follow the rules of the latest governance-approved release of the OP Stack. This means that changes to the block derivation function or messenger contracts are always subject to a governance vote.
2. **Security, Uptime, and Liveness:** Block production, sequencing, and bridging must satisfy uniform standards for security, uptime, and liveness across all OP Chains. This means that  changes that could cause users to be unable to transact (e.g., changing the gas limit to something untenable) are subject to a governance vote.
3. **Universal, Governance-Approved Upgrades:** OP Chains must upgrade together under OP Stack releases that are approved by governance. Any upgrades that aren’t backwards compatible are therefore subject to a governance vote.

Using this framework, we can define the following rough upgrade types and whether or not each upgrade type needs a governance vote. If you are uncertain if an upgrade requires governance approval, please request delegate feedback on the forum.

- **Consensus Changes**
    
    **Vote required:** Yes
    
    Consensus changes modify the state transition function or messaging validity. As such, they must be approved by governance to satisfy protection one above. 
    
    For example:
    
    - Bedrock
    - EIP-4844
    - Shanghai
    - Any L1 upgrade that modifies a contract under the control of the Security Council. The Security Council cannot make any changes to L1 unless they are approved by governance *or* the result of an active or impending security issue.
 
- **Predeploy Updates**
    
    **Vote required:** Yes
    
    Predeploy updates must be approved by governance in order to satisfy protection three above. More specifically, changes to predeploys must be rolled out across all OP Chains in order to prevent functionality on one chain from diverging from all the others.
    
- **Cross-Chain Contracts**
    
    **Vote required:** No
    
    “Cross-chain contracts” refers to smart contracts like Gnosis SAFE or `create2deployer` which are deployed at the same address across multiple chains. These contracts do not require a governance vote because anyone can deploy them at any time on any chain. This is true even if we decide to add these contracts to the genesis state, since someone could always deploy them after the chain comes online.
    
    Note that any changes to the `0x42...` namespace *do* need to go through governance, as do any contract deployments that require irregular state transitions.
    
- **Parameter Updates**
    
    **Vote required:** Change Dependent
    
    Parameter updates that impact protections one or two above will need to be approved by governance. For example, setting the gas limit or changing the EIP-1559 parameters will require governance approval since modifying these parameters can prevent users from transacting.
    
    Examples:
    
    - Updating the ProxyAdmin/challenger/guardian addresses requires a governance vote.
    - Updating gas parameters require a governance vote until they’re explicitly configurable by the Chain Governor
    - Updating the batcher/proposer addresses (among addresses already on the allowlist) do not require a governance vote as long as they are within the set of governance-approved addresses
- **Non-Consensus Client Features**
    
    **Vote required:** No
    
    Network-wide features introduce functionality that may require coordination with alt-client developers, but without risk of a chain split. As such these changes satisfy all three user protections above as long as they are backwards-compatible and meet our bar for engineering rigor.
    
    Examples:
    - Snap sync

- **Changes Affecting Transaction Inclusion/Ordering**
    
    **Vote required:** **Optional** - you proposal should be shared with other teams and presented on a relevant sync call
    
    Even though the mempool is technically not part of consensus, it affects the way in which transactions get included into the chain and can negatively effect user experience. As a result, unilateral changes that affect transaction ordering violate protection two above and therefore need a vote. If the community detects that nonstandard ordering software is being run, it is grounds for removal from the sequencer allowlist.
    Examples:

- Moving to a public mempool
- Running custom PBS/transaction pool software
- **Non-Consensus, No-Coordination, Non-Ordering Changes**
    
    **Vote required:** No
    
    These changes are a catch-all for any change that doesn’t modify consensus or require coordination. These changes can be rolled out unilaterally without input from governance since they do not impact any of the protections described above.

  
<aside>
📌 The above sets are not always mutually exclusive. If a given change might fall into multiple buckets, if any one of them requires a vote, then the change requires a vote. If you are unsure if something requires a governance vote, please check it on relevance governance forums

</aside>

<aside>

📌 All upgrades which require the Security Council to take action require a governance vote, if they are not an emergency bugfix.
</aside>
    

***Note**: If you are unsure if something requires a governance vote, ask on our core contributors Discord or check with @Ben Edgington,  @Bobby Dresser or @Ben Jones for further steps*

## 2. Do the Implementation Work

Mainnet readiness starts during development. We use a stable trunk development model, so everything we merge - even work-in-flight features - will run in someone’s production environment. This means that we must ensure all changes pass CI, receive code review, and have automated tests for any new or modified functionality. 

This also requires putting breaking changes behind feature flags until they’re ready for wider groups to test and use them.

## 3. Pass Engineering Criteria

All software we ship to mainnet must pass the following readiness criteria, regardless of whether or not it needs a vote. The goal of this criteria is to get *our internal team* to where we feel comfortable pushing a change to mainnet. As a result, some changes may involve more than just what is listed here.

As you are progressing with development, you should be able to go though following development checks:

- [ ]  is your code in implementation-complete status
- [ ]  Does your code have automated tests
- [ ]  Is your code behind a dedicated feature-flag
- [ ]  Is your change compatible with the fault proof system?
- [ ]  Did you run your code on a internal-devnet for as long as necessary(depends on your agreement with other contributors)
- [ ]  Did your code run on Sepolia Testnet for a week or more?

If the changes do not pass the governance threshold, you can stop here and ship your changes directly to mainnet. If they do pass the threshold, read on.

## 3.5. Add To or Create Named Hardfork

To make the upgrade process easier, we will batch changes together in a named hardfork. An example of this was the Regolith hardfork, where we batched together fixes for receipt handling and deposit gas.

If a named hardfork doesn’t exist, we’ll need to create one. This involves making some changes to the chain config in `op-geth` and the rollup config in the `op-node`. Then, the hardfork changes need to be configured to activate at the hardfork’s activation time.

- [ ]  Hardfork is prepared
    - [ ]  Named hardfork is created or you used the existing name  - check the list of names under this link: https://github.com/ethereum-optimism/specs/tree/main/specs/protocol
    - [ ]  Code has been configured to activate with the named hardfork

## 4. Pass Security Criteria

<aside>
We (as the security team) strongly recommend starting work on the security criteria early in the process to avoid surprises which might lead to delays.

</aside>

It is up to the tech lead responsible for the launch to decide and get approval from the Project Board on whether to write an FMA and whether to require approval from security on the FMA. If an FMA is needed:

- [ ]  write the doc [Failure Modes and Recovery Paths Analysis](https://www.notion.so/Failure-Mode-Analyses-FMAs-1fb9f65a13e542e5b48af6c850763494?pvs=21)
- [ ]  [If Required] Security has signed-off on the analysis
- [ ]  [If Applicable] Audits are completed and issues fixed
    
### Failure Modes and Recovery Paths Analysis
    
This analysis provides a description of the risks involved with the changes that developers are introducing, and the mitigations which can be taken to prevent issues or recover from them if they occur. 
    
The analysis template we have will guide you through the process, which should be completed prior to audits or testnet deployments. Please create a failure modes analysis by following the process at [Failure Mode Analyses (FMAs)](https://www.notion.so/Failure-Mode-Analyses-FMAs-1fb9f65a13e542e5b48af6c850763494?pvs=21).
    
### Auditing requirements

The framework that decides whether or not an audit is necessary is described in [this guide.](https://gov.optimism.io/t/op-labs-audit-framework-when-to-get-external-security-review-and-how-to-prepare-for-it/6864)

## 5. Make Governance Proposal

Note that governance proposals are *all-or-nothing:* if one aspect of the proposal fails, then the entire proposal fails and must be voted on again.

- [ ]  Create a governance proposal using the template below
    - Upgrade proposals need to point at some feature-complete, frozen body of code — can be a git tag, specific commit, etc
- [ ]  Post the proposal on the Governance forums as a draft under the your name
- [ ]  FND will seek out the 4 delegates to approve the proposal for a vote

### Governance Proposal Template

Format and share your governance post using the official [Standard Proposal Template](https://gov.optimism.io/t/standard-proposal-template-optimism-token-house/5443). 

Use the the [Canyon](https://gov.optimism.io/t/final-upgrade-proposal-2-canyon-network-upgrade/7088) / [Delta](https://gov.optimism.io/t/final-upgrade-proposal-3-delta-network-upgrade/7310)  or [Ecotone](https://gov.optimism.io/t/upgrade-proposal-5-ecotone-network-upgrade/7669) governance posts as guides for what to say.

Some useful tips for writing your governance post:

- Include an intro that describes your affiliation as a core dev. It should be similar to what was done in the Canyon gov post.
- In the Security Considerations section, use the FMA and the [audit framework](https://gov.optimism.io/t/op-labs-audit-framework-when-to-get-external-security-review-and-how-to-prepare-for-it/6864) to describe why we do or do not need an audit, and how we secured the system.
- In the Action Plan section make sure to describe activation times, software versions, and which testnets the changes are deployed to.
- In the Action Plan section make sure to link out to the monorepo commit hash being deployed.
- If relevant, link out to the specifications that you use fro your development, in order to showcase a full picture of your path to mainnet.
- Include any relevant data to show the impact of the proposal.

### Upcoming Change: Blockspace Charters

Governance Season 6 introduced the concept of a [Blockspace Charter](https://gov.optimism.io/t/season-6-introducing-blockspace-charters-superchain-first-governance/8133). Blockspace Charters provide a framework to define how a particular type of blockspace is governed, and what properties and guarantees each kind of blockspace provides. The linked governance post outlines the three key components of each Charter.

For example, the [Standard Blockspace Charter](https://gov.optimism.io/t/season-6-draft-standard-rollup-charter/8135) defines onchain and offchain criteria that chains must meet in order to be considered Standard Chains. These criteria include things like bridge solvency checks, unique chain ID checks, and the like. It also describes some guiding policies around governor key recovery, sequencer censorship, gas limits, and more. The net result is a document that outlines a strong set of guarantees and rules for Standard Chain blockspace.

Once Blockspace Charters are introduced, **all upgrade proposals will need to specify a Blockspace Charter to be upgraded.** The steps for upgrading a Blockspace Charter are below:

- Create a pull request that updates the charter’s text with the updated rules, and the Superchain Registry with updated implementations of the rules.
    - The charter’s text lives in the [Operating Manual](https://github.com/ethereum-optimism/OPerating-manual/tree/main) repo.
- Include justifications for the Blockspace Charter changes in the Impact Summary section of the proposal.
- Include a comprehensive justification that all Precommitments in the previous version of the Charter are still preserved by the upgrade.

## 6. Implement the Vote for your release (if coordination with the governance orgs for the OP stack)

- [ ]  Add the Hardfork activation time
- [ ]  Schedule contract deployments
