# Jovian Deposits

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Network upgrade transactions](#network-upgrade-transactions)
  - [L1Block Deployment](#l1block-deployment)
  - [L1Block Proxy Update](#l1block-proxy-update)
  - [GasPriceOracle Deployment](#gaspriceoracle-deployment)
  - [GasPriceOracle Proxy Update](#gaspriceoracle-proxy-update)
  - [GasPriceOracle Enable Jovian](#gaspriceoracle-enable-jovian)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

[deposits]: ../deposits.md

## Overview

The Jovian upgrade changes deposit processing. This page lists the changes to the
[deposit specification][deposits].

## Network upgrade transactions

The upgrade transaction details below are based on the monorepo at commit hash
`b3299e0ddb55442e6496512084d16c439ea2da77`, and will be updated once a contracts release is made.

### L1Block Deployment
<!-- Generated with: ./scripts/run_gen_predeploy_docs.sh --optimism-repo-path ../../optimism \
--fork-name Jovian \
--contract-name L1Block \
--from-address 0x4210000000000000000000000000000000000006 \
--from-address-nonce 0 \
--git-commit-hash 773798a67678ab28c3ef7ee3405f25c04616af19 \
--eth-rpc-url https://optimism.rpc.subquery.network/public \
--proxy-address 0x4200000000000000000000000000000000000015 \
--copy-contract-bytecode true -->

The `L1Block` contract is deployed.

A deposit transaction is derived with the following attributes:

- `from`: `0x4210000000000000000000000000000000000006`
- `to`: `null`
- `mint`: `0`
- `value`: `0`
- `nonce`: `0`
- `gasLimit`: `447315`
- `data`: `0x608060405234801561001057600080...` ([full bytecode](../../../specs/static/bytecode/jovian-l1-block-deployment.txt))
- `sourceHash`: `0xbb1a656f65401240fac3db12e7a79ebb954b11e62f7626eb11691539b798d3bf`,
  computed with the "Upgrade-deposited" type, with `intent = "Jovian: L1 Block Deployment"`

This results in the Jovian L1Block contract being deployed to
`0x3Ba4007f5C922FBb33C454B41ea7a1f11E83df2C`, to verify:

```bash
cast compute-address --nonce=0 0x4210000000000000000000000000000000000006
Computed Address: 0x3Ba4007f5C922FBb33C454B41ea7a1f11E83df2C
```

Verify `sourceHash`:

```bash
cast keccak $(cast concat-hex 0x0000000000000000000000000000000000000000000000000000000000000002 $(cast keccak "Jovian: L1 Block Deployment"))
# 0xbb1a656f65401240fac3db12e7a79ebb954b11e62f7626eb11691539b798d3bf
```

Verify `data`:

```bash
git checkout 773798a67678ab28c3ef7ee3405f25c04616af19
make build-contracts
jq -r ".bytecode.object" packages/contracts-bedrock/forge-artifacts/L1Block.sol/L1Block.json
```

This transaction MUST deploy a contract with the following code hash
`0x5f885ca815d2cf27a203123e50b8ae204fdca910b6995d90b2d7700cbb9240d1`.

To verify the code hash:

```bash
git checkout 773798a67678ab28c3ef7ee3405f25c04616af19
make build-contracts
cast k $(jq -r ".deployedBytecode.object" packages/contracts-bedrock/forge-artifacts/L1Block.sol/L1Block.json)
```

### L1Block Proxy Update

This transaction updates the L1Block Proxy ERC-1967
implementation slot to point to the new L1Block deployment.

A deposit transaction is derived with the following attributes:

- `from`: `0x0000000000000000000000000000000000000000`
- `to`: `0x4200000000000000000000000000000000000015` (L1Block Proxy)
- `mint`: `0`
- `value`: `0`
- `gasLimit`: `50,000`
- `data`: `0x3659cfe60000000000000000000000003ba4007f5c922fbb33c454b41ea7a1f11e83df2c`
- `sourceHash`: `0xf3275f829340521028f9ad5bce4ecb1c64a45d448794effa2a77674627338e76`
  computed with the "Upgrade-deposited" type, with `intent = "Jovian: L1 Block Proxy Update"`

Verify data:

```bash
cast concat-hex $(cast sig "upgradeTo(address)") $(cast abi-encode "upgradeTo(address)" 0x3Ba4007f5C922FBb33C454B41ea7a1f11E83df2C)
# 0x3659cfe60000000000000000000000003ba4007f5c922fbb33c454b41ea7a1f11e83df2c
```

Verify `sourceHash`:

```bash
cast keccak $(cast concat-hex 0x0000000000000000000000000000000000000000000000000000000000000002 $(cast keccak "Jovian: L1 Block Proxy Update"))
# 0xf3275f829340521028f9ad5bce4ecb1c64a45d448794effa2a77674627338e76
```

### GasPriceOracle Deployment
<!-- Generated with: ./scripts/run_gen_predeploy_docs.sh --optimism-repo-path ../../optimism \
--fork-name Jovian \
--contract-name GasPriceOracle \
--from-address 0x4210000000000000000000000000000000000007 \
--from-address-nonce 0 \
--git-commit-hash 773798a67678ab28c3ef7ee3405f25c04616af19 \
--eth-rpc-url https://optimism.rpc.subquery.network/public \
--proxy-address 0x420000000000000000000000000000000000000F \
--copy-contract-bytecode true -->

The `GasPriceOracle` contract is deployed.

A deposit transaction is derived with the following attributes:

- `from`: `0x4210000000000000000000000000000000000007`
- `to`: `null`
- `mint`: `0`
- `value`: `0`
- `nonce`: `0`
- `gasLimit`: `1750714`
- `data`: `0x608060405234801561001057600080...` ([full bytecode](../../../specs/static/bytecode/jovian-gas-price-oracle-deployment.txt))
- `sourceHash`: `0x239b7021a6c2cf3a918481242bbb5a9499057f24501539467536c691bb133962`,
  computed with the "Upgrade-deposited" type, with `intent = "Jovian: Gas Price Oracle Deployment"`

This results in the Jovian GasPriceOracle contract being deployed to
`0x4f1db3c6AbD250ba86E0928471A8F7DB3AFd88F1`, to verify:

```bash
cast compute-address --nonce=0 0x4210000000000000000000000000000000000007
Computed Address: 0x4f1db3c6AbD250ba86E0928471A8F7DB3AFd88F1
```

Verify `sourceHash`:

```bash
cast keccak $(cast concat-hex 0x0000000000000000000000000000000000000000000000000000000000000002 $(cast keccak "Jovian: Gas Price Oracle Deployment"))
# 0x239b7021a6c2cf3a918481242bbb5a9499057f24501539467536c691bb133962
```

Verify `data`:

```bash
git checkout 773798a67678ab28c3ef7ee3405f25c04616af19
make build-contracts
jq -r ".bytecode.object" packages/contracts-bedrock/forge-artifacts/GasPriceOracle.sol/GasPriceOracle.json
```

This transaction MUST deploy a contract with the following code hash
`0xe9fc7c96c4db0d6078e3d359d7e8c982c350a513cb2c31121adf5e1e8a446614`.

To verify the code hash:

```bash
git checkout 773798a67678ab28c3ef7ee3405f25c04616af19
make build-contracts
cast k $(jq -r ".deployedBytecode.object" packages/contracts-bedrock/forge-artifacts/GasPriceOracle.sol/GasPriceOracle.json)
```

### GasPriceOracle Proxy Update

This transaction updates the GasPriceOracle Proxy ERC-1967
implementation slot to point to the new GasPriceOracle deployment.

A deposit transaction is derived with the following attributes:

- `from`: `0x0000000000000000000000000000000000000000`
- `to`: `0x420000000000000000000000000000000000000F` (GasPriceOracle Proxy)
- `mint`: `0`
- `value`: `0`
- `gasLimit`: `50,000`
- `data`: `0x3659cfe60000000000000000000000004f1db3c6abd250ba86e0928471a8f7db3afd88f1`
- `sourceHash`: `0xa70c60aa53b8c1c0d52b39b1e901e7d7c09f7819595cb24048a6bb1983b401ff`
  computed with the "Upgrade-deposited" type, with `intent = "Jovian: Gas Price Oracle Proxy Update"`

Verify data:

```bash
cast concat-hex $(cast sig "upgradeTo(address)") $(cast abi-encode "upgradeTo(address)" 0x4f1db3c6AbD250ba86E0928471A8F7DB3AFd88F1)
# 0x3659cfe60000000000000000000000004f1db3c6abd250ba86e0928471a8f7db3afd88f1
```

Verify `sourceHash`:

```bash
cast keccak $(cast concat-hex 0x0000000000000000000000000000000000000000000000000000000000000002 $(cast keccak "Jovian: Gas Price Oracle Proxy Update"))
# 0xa70c60aa53b8c1c0d52b39b1e901e7d7c09f7819595cb24048a6bb1983b401ff
```

### GasPriceOracle Enable Jovian

This transaction informs the GasPriceOracle to start using the Jovian operator fee formula.

A deposit transaction is derived with the following attributes:

- `from`: `0xDeaDDEaDDeAdDeAdDEAdDEaddeAddEAdDEAd0001` (Depositer Account)
- `to`: `0x420000000000000000000000000000000000000F` (Gas Price Oracle Proxy)
- `mint`: `0`
- `value`: `0`
- `gasLimit`: `90,000`
- `data`: `0xb3d72079`
- `sourceHash`: `0xe836db6a959371756f8941be3e962d000f7e12a32e49e2c9ca42ba177a92716c`,  
  computed with the "Upgrade-deposited" type, with `intent = "Jovian: Gas Price Oracle Set Jovian"`

Verify data:

```bash
cast sig "setJovian()"
# 0xb3d72079
```

Verify `sourceHash`:

```bash
cast keccak $(cast concat-hex 0x0000000000000000000000000000000000000000000000000000000000000002 $(cast keccak "Jovian: Gas Price Oracle Set Jovian"))
# 0xe836db6a959371756f8941be3e962d000f7e12a32e49e2c9ca42ba177a92716c
```
