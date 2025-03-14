# Superchain Configuration

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Definitions](#definitions)
  - [Guardian](#guardian)
  - [Pause Deputy](#pause-deputy)
  - [Pause Identifier](#pause-identifier)
  - [Withdrawal Liveness](#withdrawal-liveness)
- [Withdrawal Safety](#withdrawal-safety)
  - [Pause Mechanism](#pause-mechanism)
- [Invariants](#invariants)
  - [iSUPC-001: The Guardian can only cause a Withdrawal Liveness failure](#isupc-001-the-guardian-can-only-cause-a-withdrawal-liveness-failure)
    - [Impact](#impact)
  - [iSUPC-002: The Pause Deputy can only cause a temporary Withdrawal Liveness failure](#isupc-002-the-pause-deputy-can-only-cause-a-temporary-withdrawal-liveness-failure)
    - [Impact](#impact-1)
  - [iSUPC-003: The Guardian can revoke the Pause Deputy role at any time](#isupc-003-the-guardian-can-revoke-the-pause-deputy-role-at-any-time)
    - [Impact](#impact-2)
- [Function Specification](#function-specification)
  - [initialize](#initialize)
  - [guardian](#guardian)
  - [pause](#pause)
  - [unpause](#unpause)
  - [pausable](#pausable)
  - [paused](#paused)
  - [expiration](#expiration)
  - [reset](#reset)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

The SuperchainConfig contract is used to manage global configuration values for multiple OP Chains
within a single Superchain network.

## Definitions

### Guardian

The **Guardian** is a dedicated role that in the OP Stack that is permitted to trigger certain
actions to maintain the security of an OP Chain or set of OP Chains in case of a bug in the
protocol. In the Superchain, the Guardian role is held by the Optimism Security Council.

### Pause Deputy

The **Pause Deputy** is a dedicated role managed assigned by the [Guardian](#guardian) that can
execute the [Pause Mechanism](#pause-mechanism). An OP Chain does not necessarily need to assign a
Pause Deputy. The Pause Deputy is capable of triggering the Pause Mechanism but does not have the
ability to reset the mechanism or unpause the system.

The Pause Deputy is an optional role within an OP Chain and can be configured if the Guardian is
a [Safe][safe-docs] that installs the [Deputy Pause Module](./deputy-pause-module.md).

### Pause Identifier

The **Pause Identifier** is an address parameter used to specify the scope of a pause action. This
identifier determines which systems or chains are affected by the pause:

- When the identifier is the zero address (`0x0000000000000000000000000000000000000000`), the pause
  applies globally to all chains sharing the `SuperchainConfig` contract.
- When the identifier is a non-zero address, the pause applies specifically to the chain or set of
  chains associated with that identifier.

The identifier is typically expected to be an `ETHLockbox` address, as chains within the Superchain
interop set share a common `ETHLockbox`. This allows for targeted pausing of either specific chains
or the entire Superchain interop set at the same time.

OP Chains are expected to integrate with the `SuperchainConfig` via their `SystemConfig` contract,
which will check for the status of the pause by passing along the address of the `ETHLockbox`
being used within that system as the Pause Identifier.

### Withdrawal Liveness

**Withdrawal Liveness** is the ability for users to execute valid withdrawals out of any contract
that stores ETH or tokens within an OP Chain's set of smart contracts. We tend to refer to
Withdrawal Liveness in the context of the `OptimismPortal` and the rest of the Standard Bridge
because this is where a majority of the ETH/tokens in the system live. However, this also applies
to bonds deposited into dispute game contracts (and ultimately into the `DelayedWETH` contract).

## Withdrawal Safety

**Withdrawal Safety** is the condition that users are *not* able to execute *invalid* withdrawals
out of any contract that stores ETH or tokens within an OP Chain's set of smart contracts.
Generally speaking "liveness" means nothing gets bricked and "safety" means nothing gets stolen.

### Pause Mechanism

The **Pause Mechanism** is a tool that permits the [Guardian](#guardian) or the
[Pause Deputy](#pause-deputy) to pause the execution of certain actions on one or more OP Chains.
Broadly speaking, the Pause Mechanism is designed to impact the liveness of the system such that
an attack on the system is unable to actually remove ETH or ERC-20 tokens from the bridge or any
other contract that stores ETH and/or tokens.

The Pause Mechanism is temporary and is active up to a fixed maximum amount of time before
expiring. A pause cannot be triggered again unless the mechanism is explicitly reset by the
[Guardian](#guardian). That is, if the Pause Mechanism is triggered and not reset by the Guardian,
it will expire, the system will automatically become unpaused, and the system cannot be paused
again.

The Pause Mechanism can be applied globally or to individual systems. Which level the pause applies
to is determined by an identifier provided when executing or checking pause status. This identifier
is an address parameter. To support the ability to pause individual chains or the entire Superchain
interop set with a single mechanism, this address is expected to be an `ETHLockbox` address (namely
because the Superchain interop set shares a single `ETHLockbox`). If the provided identifier is the
zero address, the Guardian will trigger the pause for all chains that share the common
SuperchainConfig contract.

Chains using the Standard Configuration of the OP Stack use a pause expiry of **6 months**. Because
the Pause Mechanism can be applied to both local and global scopes, the pause could be chained to,
for instance, pause the local system first and then the global system shortly before the local
pause expires. The total potential pause time is therefore double the expiry period (12 months).

The Guardian may explicitly unpause the system rather than waiting for the pause to expire. If this
happens, the pause is automatically reset such that it can be used again. The Guardian can reset
the pause at any time so that it can be used again, even if the pause is currently active. If the
pause is reset when it is currently active, the pause can be triggered again, thereby resetting
the 6 month expiry timer (on a per address identifier basis).

## Invariants

### iSUPC-001: The Guardian can only cause a Withdrawal Liveness failure

We require that any action that the [Guardian](#guardian) can take in the system can only cause a
[Withdrawal Liveness](#withdrawal-liveness) failure. The Guardian must not be able to take any
action that can unilaterially (**without coordination with any other priviledged party**) cause a
[Withdrawal Safety](#withdrawal-safety) failure.

#### Impact

**Severity: High**

If this invariant were broken, the Guardian would be able to cause a
[Withdrawal Safety](#withdrawal-safety) failure, which would be a violation of the definition of
Stage 1 as of [January 2025][stage-1]. Because the Guardian is generally assumed to be a trusted
party and is unlikely to exploit these conditions, this invariant is considered a High but not
Critical impact condition.

### iSUPC-002: The Pause Deputy can only cause a temporary Withdrawal Liveness failure

We require that any action that the [Pause Deputy](#pause-deputy) can take in the system can
only cause a *temporary* [Withdrawal Liveness](#withdrawal-liveness) failure. This is distinct from
the [iSUPC-001][iSUPC-001] which allows the [Guardian](#guardian) to cause an indefinite liveness failure.

#### Impact

**Severity: High**

If this invariant were broken, the Pause Deputy would be able to cause a
[Withdrawal Safety](#withdrawal-safety) failure, which would be a violation of the definition of
Stage 1 as of [January 2025][stage-1]. Because the Pause Deputy is generally assumed to be a
trusted party and is unlikely to exploit these conditions, this invariant is considered a High but
not Critical impact condition.

### iSUPC-003: The Guardian can revoke the Pause Deputy role at any time

We require that the [Guardian](#guardian) be able to revoke the [Pause Deputy](#pause-deputy) role
at any time. This condition is necessary to prevent a misbehaving Pause Deputy from continuing to
trigger the [Pause Mechanism](#pause-mechanism) when this would not be desired by the Guardian
itself.

#### Impact

**Severity: High**

If this invariant were broken, assuming that [iSUPC-002][iSUPC-002] the Pause Deputy would
potentially be able to repeatedly trigger the Pause Mechanism even if the Guardian does not want
this to happen. We consider this to be a High severity condition because the Guardian can choose
not to renew the pause to allow the system to operate if truly necessary.

## Function Specification

### initialize

- MUST only be triggerable once.
- MUST set the value of the Guardian role.
- MUST set the value of the pause expiry period.

### guardian

Returns the address of the current [Guardian](#guardian).

### pause

Allows the [Guardian](#guardian) to trigger the [Pause Mechanism](#pause-mechanism). `pause` takes
an address [Pause Identifier](#pause-identifier) as an input. This identifier determines which
systems or chains are affected by the pause.

- MUST revert if called by an address other than the Guardian.
- MUST revert if the pausable flag for the given identifier is set to 1 (used/unavailable).
- MUST set the pause timestamp for the given identifier to the current block timestamp.
- MUST set the pausable flag for the given identifier to 1 (used/unavailable) to prevent repeated
  pauses without a reset.

### unpause

Allows the [Guardian](#guardian) to explicitly unpause the system for a given
[Pause Identifier](#pause-identifier) rather than waiting for the pause to expire. Unpausing a
specific identifier does NOT unpause the global pause (zero address identifier). If the global
pause is active, all systems will remain paused even if their specific identifiers are unpaused.

- MUST revert if called by an address other than the Guardian.
- MUST set the pause timestamp for the given identifier to 0, representing "not paused".
- MUST set the pausable flag for the given identifier to 0 (ready to pause), allowing the pause
  mechanism to be used again.

### pausable

Allows any user to check if the [Pause Mechanism](#pause-mechanism) can be triggered for a specific
[Pause Identifier](#pause-identifier). The pausable status of a specific identifier is independent
of the pausable status of the global pause (zero address identifier).

- MUST return true if the pausable flag for the given identifier is 0 (ready to pause).
- MUST return false if the pausable flag for the given identifier is 1 (used/unavailable).

### paused

Allows any user to check if the system is currently paused for a specific
[Pause Identifier](#pause-identifier). A system is considered paused if EITHER its specific
identifier OR the global identifier (zero address) is paused and not expired. This means that the
maximum time that a system can be paused before the pause must be reset is actually *double* the
expiry time. This can be achieved if, for instance, the individual system is paused and then the
global system is paused near the end of the expiry of the individual system.

- MUST return true if the pause timestamp for the given identifier is non-zero AND not expired
  (current time < pause timestamp + expiry duration).
- MUST return true if the pause timestamp for the zero address identifier (global pause) is
  non-zero AND not expired, regardless of the status of the specific identifier.
- MUST return false if the pause timestamp is 0 for both the given identifier and the zero address.
- MUST return false if the pause has expired (current time > pause timestamp + expiry duration) for
  both the given identifier and the zero address.

### expiration

Returns the timestamp at which the pause for a given [Pause Identifier](#pause-identifier) will
expire. This function only returns the expiration for the specific identifier provided. To
determine when a system will be fully unpaused, both the specific identifier and the global
identifier (zero address) expirations must be considered.

- MUST return the pause timestamp plus the configured expiry duration if the pause timestamp is non-zero.
- MUST return 0 if the pause timestamp is 0 (system is not paused) for the given identifier.

### reset

Allows the [Guardian](#guardian) to reset the pause mechanism for a given
[Pause Identifier](#pause-identifier), allowing it to be used again.

- MUST revert if called by an address other than the Guardian.
- MUST set the pausable flag for the given identifier to 0 (ready to pause).
- MUST NOT modify the pause timestamp for the given identifier.
- NOTE: Resetting the pausable flag for a specific identifier does not affect the pause status. If
  a system is currently paused, it will remain paused until explicitly unpaused or until the pause
  expires.

<!-- references -->
[safe-docs]: https://docs.safe.global/home/what-is-safe
[stage-1]: https://forum.l2beat.com/t/stages-update-a-high-level-guiding-principle-for-stage-1/338
[iSUPC-001]: #isupc-001-the-guardian-can-only-cause-a-withdrawal-liveness-failure
[iSUPC-002]: #isupc-002-the-pause-deputy-can-only-cause-a-temporary-withdrawal-liveness-failure
