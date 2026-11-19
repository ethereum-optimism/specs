# Jovian L1Block Scalar Parsing Guide

With the Jovian upgrade, the `l1FeeScalar` in the `L1Block` predeploy (`0x4200000000000000000000000000000000000015`) is a packed 32-byte word. This guide specifies the extraction logic for application developers.

### Extraction Logic
Developers must shift the 32-byte raw value to isolate the individual 4-byte scalars:

- **Base Fee Scalar:** bits [192:224]
- **Blob Base Fee Scalar:** bits [160:192]

```solidity
function getScalars() public view returns (uint32 baseScalar, uint32 blobScalar) {
    uint256 raw = IL1Block(0x4200000000000000000000000000000000000015).l1FeeScalar();
    baseScalar = uint32(raw >> 192);
    blobScalar = uint32(raw >> 160);
}
Contributor: Lesedi37
Rabby Wallet Address: 0x1db618e6bfc35bd48b91431a55c4948b27e7a539
