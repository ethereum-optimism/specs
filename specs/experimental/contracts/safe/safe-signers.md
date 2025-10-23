# SafeSigners

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
  - [Signature Type](#signature-type)
  - [Compact Signature Format](#compact-signature-format)
- [Assumptions](#assumptions)
  - [aSS-001: Safe contract validates signatures correctly](#ass-001-safe-contract-validates-signatures-correctly)
    - [Mitigations](#mitigations)
- [Invariants](#invariants)
  - [iSS-001: Signature extraction must match Safe's signature interpretation](#iss-001-signature-extraction-must-match-safes-signature-interpretation)
    - [Impact](#impact)
- [Function Specification](#function-specification)
  - [signatureSplit](#signaturesplit)
  - [getNSigners](#getnsigners)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

SafeSigners is a utility library that extracts signer addresses from Safe multisig signature data. It provides
functionality to parse concatenated signature bytes and recover the addresses that signed a given data hash,
supporting all signature types used by Safe contracts including EOA signatures, contract signatures, approved
hashes, and eth_sign flow signatures.

## Definitions

### Signature Type

The signature encoding scheme used by Safe contracts, indicated by the `v` value:
- `v = 0`: Contract signature (address encoded in `r`)
- `v = 1`: Approved hash (address encoded in `r`)
- `v > 30`: eth_sign flow (standard ECDSA with adjusted `v` value)
- `v = 27 or 28`: Standard ECDSA signature

### Compact Signature Format

The signature encoding used by Safe where each signature consists of 65 bytes in the format `{bytes32 r}{bytes32
s}{uint8 v}`. Multiple signatures are concatenated without padding, resulting in a total length of `65 * N` bytes
for `N` signatures.

## Assumptions

### aSS-001: Safe contract validates signatures correctly

The Safe contract has already validated that the provided signatures are valid for the given data hash and meet
the required threshold. SafeSigners trusts this validation and only extracts signer addresses without performing
additional signature verification.

#### Mitigations

- SafeSigners is designed to be used only after Safe's `checkNSignatures()` or `checkSignatures()` has validated
  the signatures
- The library is stateless and performs no state modifications, limiting the impact of incorrect usage
- Clear documentation indicates this library should not be used for signature validation

## Invariants

### iSS-001: Signature extraction must match Safe's signature interpretation

The signer addresses extracted by `getNSigners()` MUST exactly match the addresses that the Safe contract would
identify as signers for the same signature data. This includes correctly handling all four signature types (EOA,
contract, approved hash, eth_sign) according to Safe's specification.

#### Impact

**Severity: Critical**

If signer extraction does not match Safe's interpretation:
- Incorrect addresses would be attributed as signers of Safe transactions
- Systems relying on this library for attribution or access control would be compromised
- Audit trails and accountability mechanisms would be invalidated

## Function Specification

### signatureSplit

Splits concatenated signature bytes into individual `v`, `r`, and `s` components for a signature at a specified
position.

**Parameters:**
- `_signatures`: Concatenated signature bytes in [Compact Signature Format]
- `_pos`: Zero-indexed position of the signature to extract

**Behavior:**
- MUST extract the signature at position `_pos` from the concatenated `_signatures` bytes
- MUST return `r` as the first 32 bytes of the signature (bytes 0-31)
- MUST return `s` as the second 32 bytes of the signature (bytes 32-63)
- MUST return `v` as the 65th byte of the signature (byte 64)
- MUST calculate the byte offset as `65 * _pos`
- MUST use assembly for efficient memory access
- MUST NOT perform bounds checking on `_pos` (caller responsibility)

### getNSigners

Extracts signer addresses from a set of signatures for a given data hash.

**Parameters:**
- `_dataHash`: The hash of the data that was signed
- `_signatures`: Concatenated signature bytes in [Compact Signature Format]
- `_requiredSignatures`: The number of signatures to extract

**Behavior:**
- MUST return an array of exactly `_requiredSignatures` addresses
- MUST iterate through the first `_requiredSignatures` signatures in `_signatures`
- MUST extract each signature using `signatureSplit()`
- MUST determine the [Signature Type] based on the `v` value
- MUST handle `v = 0` by extracting the contract address from the `r` value
- MUST handle `v = 1` by extracting the approver address from the `r` value
- MUST handle `v > 30` by computing `keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32",
  _dataHash))` and recovering the address via `ecrecover()` with `v - 4`
- MUST handle `v = 27 or 28` by recovering the address via `ecrecover()` with the original `_dataHash`
- MUST store each recovered address in the output array at the corresponding index
- MUST NOT validate signature correctness (assumes Safe has already validated)
- MUST NOT check for duplicate signers
- MUST NOT enforce signer ordering
