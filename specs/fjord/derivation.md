# Deriving Payload Attributes

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Deriving the Transaction List](#deriving-the-transaction-list)
  - [Network upgrade automation transactions](#network-upgrade-automation-transactions)
    - [Fjord](#fjord)
      - [GasPriceOracle Deployment - Fjord](#gaspriceoracle-deployment---fjord)
      - [GasPriceOracle Proxy Update - Fjord](#gaspriceoracle-proxy-update---fjord)
      - [GasPriceOracle Enable Fjord](#gaspriceoracle-enable-fjord)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Deriving the Transaction List

### Network upgrade automation transactions

#### Fjord

The Fjord hardfork activation block, contains the following transactions in this order:

- L1 Attributes Transaction
- User deposits from L1
- Network Upgrade Transactions
  - GasPriceOracle deployment
  - Update GasPriceOracle Proxy ERC-1967 Implementation Slot
  - GasPriceOracle Enable Fjord

To not modify or interrupt the system behavior around gas computation, this block will not include any sequenced
transactions by setting `noTxPool: true`.

##### GasPriceOracle Deployment - Fjord

The `GasPriceOracle` contract is upgraded to support the new Fjord L1 data fee computation. Post fork this contract
will use FastLZ to compute the L1 data fee.

To perform this upgrade, a deposit transaction is derived with the following attributes:

- `from`: `0x4210000000000000000000000000000000000002`
- `to`: `null`,
- `mint`: `0`
- `value`: `0`
- `gasLimit`: `1,450,000`
- `data`: `0x60806040523...` ([full bytecode](../static/bytecode/fjord-gas-price-oracle-deployment.txt))
- `sourceHash`: `0x86122c533fdcb89b16d8713174625e44578a89751d96c098ec19ab40a51a8ea3`
  computed with the "Upgrade-deposited" type, with `intent = "Fjord: Gas Price Oracle Deployment"

This results in the Fjord GasPriceOracle contract being deployed to `0xa919894851548179A0750865e7974DA599C0Fac7`,
to verify:

```bash
cast compute-address --nonce=0 0x4210000000000000000000000000000000000002
Computed Address: 0xa919894851548179A0750865e7974DA599C0Fac7
```

Verify `sourceHash`:

```bash
❯ cast keccak $(cast concat-hex 0x0000000000000000000000000000000000000000000000000000000000000002 $(cast keccak "Fjord: Gas Price Oracle Deployment"))
# 0x86122c533fdcb89b16d8713174625e44578a89751d96c098ec19ab40a51a8ea3
```

Verify `data`:

```bash
git checkout fbdba16ce5fe0207ceeb8487d762807888aa43f5 (update once merged)
pnpm clean && pnpm install && pnpm build
jq -r ".bytecode.object" packages/contracts-bedrock/forge-artifacts/GasPriceOracle.sol/GasPriceOracle.json
```

This transaction MUST deploy a contract with the following code hash
`0xc8635a80727bf5945c4f6e1fb1730c4b812347472cc760b098b341ca454af625`.

##### GasPriceOracle Proxy Update - Fjord

This transaction updates the GasPriceOracle Proxy ERC-1967 implementation slot to point to the new GasPriceOracle
deployment.

A deposit transaction is derived with the following attributes:

- `from`: `0x0000000000000000000000000000000000000000`
- `to`: `0x420000000000000000000000000000000000000F` (Gas Price Oracle Proxy)
- `mint`: `0`
- `value`: `0`
- `gasLimit`: `50,000`
- `data`: `0x3659cfe6000000000000000000000000a919894851548179a0750865e7974da599c0fac7`
- `sourceHash`: `0x1e6bb0c28bfab3dc9b36ffb0f721f00d6937f33577606325692db0965a7d58c6`
  computed with the "Upgrade-deposited" type, with `intent = "Fjord: Gas Price Oracle Proxy Update"`

Verify data:

```bash
cast concat-hex $(cast sig "upgradeTo(address)") $(cast abi-encode "upgradeTo(address)" 0xa919894851548179A0750865e7974DA599C0Fac7)
# 0x3659cfe6000000000000000000000000a919894851548179a0750865e7974da599c0fac7
```

Verify `sourceHash`:

```bash
cast keccak $(cast concat-hex 0x0000000000000000000000000000000000000000000000000000000000000002 $(cast keccak "Fjord: Gas Price Oracle Proxy Update"))
# 0x1e6bb0c28bfab3dc9b36ffb0f721f00d6937f33577606325692db0965a7d58c6
```

##### GasPriceOracle Enable Fjord

This transaction informs the GasPriceOracle to start using the Fjord gas calculation formula.

A deposit transaction is derived with the following attributes:

- `from`: `0xDeaDDEaDDeAdDeAdDEAdDEaddeAddEAdDEAd0001` (Depositer Account)
- `to`: `0x420000000000000000000000000000000000000F` (Gas Price Oracle Proxy)
- `mint`: `0`
- `value`: `0`
- `gasLimit`: `80,000`
- `data`: `0x8e98b106`
- `sourceHash`: `0xbac7bb0d5961cad209a345408b0280a0d4686b1b20665e1b0f9cdafd73b19b6b`,
  computed with the "Upgrade-deposited" type, with `intent = "Fjord: Gas Price Oracle Set Fjord"

Verify data:

```bash
cast sig "setFjord()"
0x8e98b106
```

Verify `sourceHash`:

```bash
cast keccak $(cast concat-hex 0x0000000000000000000000000000000000000000000000000000000000000002 $(cast keccak "Fjord: Gas Price Oracle Set Fjord"))
# 0xbac7bb0d5961cad209a345408b0280a0d4686b1b20665e1b0f9cdafd73b19b6b
```
