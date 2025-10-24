# DeputyPauseModule

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
  - [Deputy](#deputy)
  - [Pause Identifier](#pause-identifier)
- [Assumptions](#assumptions)
  - [a01-DPM: Deputy key is not compromised](#a01-dpm-deputy-key-is-not-compromised)
    - [Mitigations](#mitigations)
  - [a02-DPM: Deputy key is not deleted](#a02-dpm-deputy-key-is-not-deleted)
    - [Mitigations](#mitigations-1)
  - [a03-DPM: Ethereum will not censor transactions for extended periods](#a03-dpm-ethereum-will-not-censor-transactions-for-extended-periods)
    - [Mitigations](#mitigations-2)
- [Invariants](#invariants)
  - [i01-DPM: Only the Deputy may act through the module](#i01-dpm-only-the-deputy-may-act-through-the-module)
    - [Impact](#impact)
  - [i02-DPM: Deputy can only trigger the pause action](#i02-dpm-deputy-can-only-trigger-the-pause-action)
    - [Impact](#impact-1)
  - [i03-DPM: Deputy authorizations are not replayable](#i03-dpm-deputy-authorizations-are-not-replayable)
    - [Impact](#impact-2)
  - [i04-DPM: Deputy can always act through the module](#i04-dpm-deputy-can-always-act-through-the-module)
    - [Impact](#impact-3)
- [Function Specification](#function-specification)
  - [constructor](#constructor)
  - [pause](#pause)
  - [setDeputy](#setdeputy)
  - [guardianSafe](#guardiansafe)
  - [foundationSafe](#foundationsafe)
  - [superchainConfig](#superchainconfig)
  - [deputy](#deputy)
  - [usedNonces](#usednonces)
  - [pauseMessageTypehash](#pausemessagetypehash)
  - [deputyAuthMessageTypehash](#deputyauthmessagetypehash)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The DeputyPauseModule is a Safe Module that enables a designated [Deputy](#deputy) address to trigger
the pause mechanism in the SuperchainConfig contract on behalf of the Guardian Safe. This module
provides a fast-response capability for emergency situations while maintaining security through
signature-based authorization.

## Definitions

### Deputy

An externally owned account (EOA) authorized to create ECDSA signatures that trigger the pause
mechanism through this module. The Deputy acts on behalf of the Guardian Safe but with limited
permissions restricted to pause operations only.

### Pause Identifier

An address parameter passed to the SuperchainConfig pause function that identifies which system
component or chain should be paused. This allows selective pausing of specific chains or components
within the Superchain.

## Assumptions

### a01-DPM: Deputy key is not compromised

The Deputy private key is maintained securely and has not been compromised by a malicious actor. If
the Deputy key is compromised, an attacker could trigger unauthorized pauses of the Superchain.

#### Mitigations

- Enforce strong access control around the Deputy key
- Monitor for any usage of the Deputy key
- Regular rotation of the Deputy key via the setDeputy function

### a02-DPM: Deputy key is not deleted

The Deputy private key has not been permanently deleted or lost. Loss of the Deputy key would
prevent fast emergency response through this module, though the Guardian Safe could still act
directly or replace the Deputy.

#### Mitigations

- Maintain duplicate copies of the key in multiple secure locations
- Foundation Safe can replace the Deputy if the key is lost

### a03-DPM: Ethereum will not censor transactions for extended periods

Ethereum L1 will not censor transactions for extended periods, and any transaction submitted to the
network can be processed within a reasonable time bound. Extended censorship could delay emergency
pause activation beyond acceptable response times.

#### Mitigations

- Use extremely high priority fees if necessary to ensure transaction inclusion

## Invariants

### i01-DPM: Only the Deputy may act through the module

The [Deputy](#deputy) account must be the only address that can successfully execute actions through
this module. Other accounts may submit transactions on behalf of the Deputy if they possess a valid
ECDSA signature from the Deputy for that specific action, but no account may act without explicit
Deputy authorization.

#### Impact

**Severity: High**

If this invariant is violated, unauthorized accounts could trigger the pause mechanism without
proper authorization from the Deputy or the governance process. This would cause unexpected liveness
failures for withdrawals and other critical system functions until the Guardian unpauses the system.

### i02-DPM: Deputy can only trigger the pause action

The [Deputy](#deputy) can only cause the module to call the pause function on the SuperchainConfig
contract with a specified [Pause Identifier](#pause-identifier). The Deputy cannot trigger any other
privileged actions on behalf of the Guardian Safe, including unpause, ownership transfers, or any
other Guardian Safe operations.

#### Impact

**Severity: Critical**

If this invariant is violated, the Deputy would gain unauthorized control over the Guardian Safe,
potentially allowing arbitrary actions including fund transfers, contract upgrades, or other
critical operations. This would represent a complete compromise of the Guardian Safe's security
model.

### i03-DPM: Deputy authorizations are not replayable

A Deputy authorization signature must be usable exactly once within this specific DeputyPauseModule
instance on this specific chain. The same signature cannot be reused within this module, and
signatures created for other DeputyPauseModule instances or other chains cannot be used in this
module.

#### Impact

**Severity: High**

If this invariant is violated, old or cross-chain Deputy signatures could be replayed to trigger
unauthorized pauses. An attacker could reuse a legitimate signature from a previous emergency or
from a different chain to cause unexpected system pauses, resulting in liveness failures until the
Guardian intervenes.

### i04-DPM: Deputy can always act through the module

The [Deputy](#deputy) account must always be able to execute the pause action through this module,
regardless of the Deputy account's ETH balance or other state. The only conditions that may prevent
Deputy action are total deletion of the Deputy private key or extended Ethereum censorship.

#### Impact

**Severity: High**

If this invariant is violated, the system cannot guarantee fast emergency response through the
Deputy mechanism. This defeats the primary purpose of the module, which is to enable rapid pause
activation within bounded time (typically 30 minutes) when authorized by the governance process.

## Function Specification

### constructor

Initializes the DeputyPauseModule with immutable references to the Guardian Safe, Foundation Safe,
and SuperchainConfig contract.

**Parameters:**

- `_guardianSafe`: Address of the Guardian Safe that this module will be installed into
- `_foundationSafe`: Address of the Foundation Safe authorized to change the Deputy
- `_superchainConfig`: Address of the SuperchainConfig contract that will be paused
- `_deputy`: Initial Deputy address
- `_deputySignature`: EIP-712 signature from the Deputy proving control of the private key

**Behavior:**

- MUST set the EIP-712 domain name to "DeputyPauseModule"
- MUST set the EIP-712 domain version to "1"
- MUST verify that `_deputySignature` is a valid EIP-712 signature over a DeputyAuthMessage struct
containing `_deputy`, signed by `_deputy`
- MUST revert if the signature verification fails
- MUST set the `deputy` state variable to `_deputy`
- MUST set the immutable `GUARDIAN_SAFE` to `_guardianSafe`
- MUST set the immutable `FOUNDATION_SAFE` to `_foundationSafe`
- MUST set the immutable `SUPERCHAIN_CONFIG` to `_superchainConfig`
- MUST emit DeputySet event with the `_deputy` address

### pause

Executes a pause action on the SuperchainConfig contract using a signature from the [Deputy](#deputy).
This function can be called by any address but requires a valid Deputy signature.

**Parameters:**

- `_nonce`: Unique bytes32 value to prevent signature replay
- `_identifier`: The [Pause Identifier](#pause-identifier) to pass to SuperchainConfig.pause()
- `_signature`: ECDSA signature from the Deputy over the EIP-712 PauseMessage

**Behavior:**

- MUST verify that `_nonce` has not been used previously
- MUST revert if `_nonce` is already in the `usedNonces` mapping
- MUST verify that `_signature` is a valid EIP-712 signature over a PauseMessage struct containing
`_nonce` and `_identifier`, signed by the current `deputy` address
- MUST revert if the signature verification fails
- MUST mark `_nonce` as used in the `usedNonces` mapping
- MUST call `GUARDIAN_SAFE.execTransactionFromModuleReturnData()` with parameters to execute
`SUPERCHAIN_CONFIG.pause(_identifier)`
- MUST revert if the call to the Guardian Safe fails
- MUST verify that `SUPERCHAIN_CONFIG.paused(_identifier)` returns true after the call
- MUST revert if the SuperchainConfig is not paused after the call
- MUST emit PauseTriggered event with the `deputy` address, `_nonce`, and `_identifier`

### setDeputy

Changes the [Deputy](#deputy) address to a new EOA. Can only be called by the Foundation Safe.

**Parameters:**

- `_deputy`: New Deputy address
- `_deputySignature`: EIP-712 signature from the new Deputy proving control of the private key

**Behavior:**

- MUST revert if `msg.sender` is not the `FOUNDATION_SAFE` address
- MUST verify that `_deputySignature` is a valid EIP-712 signature over a DeputyAuthMessage struct
containing `_deputy`, signed by `_deputy`
- MUST revert if the signature verification fails
- MUST set the `deputy` state variable to `_deputy`
- MUST emit DeputySet event with the new `_deputy` address

### guardianSafe

Returns the address of the Guardian Safe that this module is installed into.

**Behavior:**

- MUST return the `GUARDIAN_SAFE` immutable value set in the constructor

### foundationSafe

Returns the address of the Foundation Safe authorized to change the Deputy.

**Behavior:**

- MUST return the `FOUNDATION_SAFE` immutable value set in the constructor

### superchainConfig

Returns the address of the SuperchainConfig contract that this module can pause.

**Behavior:**

- MUST return the `SUPERCHAIN_CONFIG` immutable value set in the constructor

### deputy

Returns the current [Deputy](#deputy) address authorized to trigger pause actions.

**Behavior:**

- MUST return the current value of the `deputy` state variable

### usedNonces

Returns whether a specific nonce has been used in a pause action.

**Parameters:**

- `nonce`: The bytes32 nonce to check

**Behavior:**

- MUST return true if the nonce has been used in a previous pause action
- MUST return false if the nonce has not been used

### pauseMessageTypehash

Returns the EIP-712 typehash for PauseMessage structs.

**Behavior:**

- MUST return `keccak256("PauseMessage(bytes32 nonce,address identifier)")`

### deputyAuthMessageTypehash

Returns the EIP-712 typehash for DeputyAuthMessage structs.

**Behavior:**

- MUST return `keccak256("DeputyAuthMessage(address deputy)")`
