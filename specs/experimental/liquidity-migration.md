## OptimismMintableERC20Factory

| Constant | Value                                        |
| -------- | -------------------------------------------- |
| Address  | `0x4200000000000000000000000000000000000012` |

### OptimismMintableERC20

The `OptimismMintableERC20Factory` creates ERC20 contracts on L2 that can be used to deposit
native L1 tokens into (`OptimismMintableERC20`). Anyone can deploy `OptimismMintableERC20` contracts.

Each `OptimismMintableERC20` contract created by the `OptimismMintableERC20Factory`
allows for the `L2StandardBridge` to mint
and burn tokens, depending on whether the user is
depositing from L1 to L2 or withdrawing from L2 to L1.

### Updates

The `OptimismMintableERC20Factory` is updated to include a `deployments` mapping
that stores the `remoteToken` address for each deployed `OptimismMintableERC20`.
This is essential for the liquidity migration process defined in the liquidity migration spec.

### Functions

#### `createOptimismMintableERC20WithDecimals`

Creates an instance of the `OptimismMintableERC20` contract with a set of metadata defined by:

- `_remoteToken`: address of the underlying token in its native chain.
- `_name`: `OptimismMintableERC20` name
- `_symbol`: `OptimismMintableERC20` symbol
- `_decimals`: `OptimismMintableERC20` decimals

```solidity
createOptimismMintableERC20WithDecimals(address _remoteToken, string memory _name, string memory _symbol, uint8 _decimals) returns (address)
```

**Invariants**

- The function MUST use `CREATE2` to deploy new contracts.
- The salt MUST be computed by applying `keccak256` to the `abi.encode`
  of the four input parameters (`_remoteToken`, `_name`, `_symbol`, and `_decimals`).
  This ensures a unique `OptimismMintableERC20` for each set of ERC20 metadata.
- The function MUST store the `_remoteToken` address for each deployed `OptimismMintableERC20` in a `deployments` mapping.

#### `createOptimismMintableERC20`

Creates an instance of the `OptimismMintableERC20` contract with a set of metadata defined
by `_remoteToken`, `_name` and `_symbol` and fixed `decimals` to the standard value 18.

```solidity
createOptimismMintableERC20(address _remoteToken, string memory _name, string memory _symbol) returns (address)
```

#### `createStandardL2Token`

Creates an instance of the `OptimismMintableERC20` contract with a set of metadata defined
by `_remoteToken`, `_name` and `_symbol` and fixed `decimals` to the standard value 18.

```solidity
createStandardL2Token(address _remoteToken, string memory _name, string memory _symbol) returns (address)
```

This function exists for backwards compatibility with the legacy version.

### Events

#### `OptimismMintableERC20Created`

It MUST trigger when `createOptimismMintableERC20WithDecimals`,
`createOptimismMintableERC20` or `createStandardL2Token` is called.

```solidity
event OptimismMintableERC20Created(address indexed localToken, address indexed remoteToken, address deployer);
```

#### `StandardL2TokenCreated`

It MUST trigger when `createOptimismMintableERC20WithDecimals`,
`createOptimismMintableERC20` or `createStandardL2Token` is called.
This event exists for backward compatibility with legacy version.

```solidity
event StandardL2TokenCreated(address indexed remoteToken, address indexed localToken);
```
