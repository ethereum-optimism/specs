# Derivation

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Network upgrade automation transactions](#network-upgrade-automation-transactions)
  - [Isthmus](#isthmus)
    - [L1Block Deployment](#l1block-deployment)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Network upgrade automation transactions

[network upgrade automation transactions]: #network-upgrade-automation-transactions

Some network upgrades require automated contract changes or deployments at specific blocks.
To automate these, without adding persistent changes to the execution-layer,
special transactions may be inserted as part of the derivation process.

### Isthmus

The Isthmus hardfork activation block contains the following transactions, in this order:

- L1 Attributes Transaction, using the Ecotone `setL1BlockValuesEcotone`
- User deposits from L1
- Network Upgrade Transactions
  - L1Block deployment

To not modify or interrupt the system behavior around gas computation, this block will not include any sequenced
transactions by setting `noTxPool: true`.

#### L1Block Deployment

The `L1Block` contract is upgraded to process the new Isthmus L1 consensus nonces.

A deposit transaction is derived with the following attributes:

- `from`: `0x4210000000000000000000000000000000000005`
- `to`: `null`
- `mint`: `0`
- `value`: `0`
- `gasLimit`: `375,000`
- `data`: `0x60806040523480156100105...` ([full bytecode](../../static/bytecode/isthmus-l1-block-deployment.txt))
- `sourceHash`: `0x3b2d0821ca2411ad5cd3595804d1213d15737188ae4cbd58aa19c821a6c211bf`,
  computed with the "Upgrade-deposited" type, with `intent = "Isthmus: L1 Block Deployment"

This results in the Isthmus L1Block contract being deployed to `0x4fa2Be8cd41504037F1838BcE3bCC93bC68Ff537`, to verify:

```bash
cast compute-address --nonce=0 0x4210000000000000000000000000000000000005
Computed Address: 0x4fa2Be8cd41504037F1838BcE3bCC93bC68Ff537
```

Verify `sourceHash`:

```bash
cast keccak $(cast concat-hex 0x0000000000000000000000000000000000000000000000000000000000000002 $(cast keccak "Isthmus: L1 Block Deployment"))
# 0x3b2d0821ca2411ad5cd3595804d1213d15737188ae4cbd58aa19c821a6c211bf
```

Verify `data`:

```bash
git checkout <INSERT_GIT_SHA_HERE>
pnpm clean && pnpm install && pnpm build
jq -r ".bytecode.object" packages/contracts-bedrock/forge-artifacts/L1Block.sol/L1Block.json
```

This transaction MUST deploy a contract with the following code hash
`0x68d031cd7a8147e7799609e42996a2b798d7c9e3dffad8960012432c146af8ad`.
