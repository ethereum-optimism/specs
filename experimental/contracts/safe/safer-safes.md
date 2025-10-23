# SaferSafes

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

SaferSafes combines liveness module and timelock guard functionality into a single contract that can be enabled
simultaneously as both a module and guard on a Safe multisig. The liveness module prevents multisig deadlock through
challenge-based ownership transfer, while the timelock guard enforces transaction delays with cancellation capabilities.

## Definitions

### Liveness Response Period

The duration in seconds that Safe owners have to respond to a liveness challenge before ownership can be transferred to
the fallback owner.

### Fallback Owner

The address that can initiate liveness challenges and claim sole ownership of the Safe if owners fail to demonstrate
liveness within the response period.

### Timelock Delay

The minimum duration in seconds that must elapse between scheduling a transaction and executing it, providing time for
transaction review and potential cancellation.

### Cancellation Threshold

The number of owner signatures required to cancel a scheduled transaction. Starts at 1 and increases by 1 after each
cancellation, capped at the maximum cancellation threshold.

### Maximum Cancellation Threshold

The upper bound for the cancellation threshold, calculated as the minimum of the blocking threshold and the quorum.
This ensures honest owners can always cancel malicious transactions.

### Blocking Threshold

The minimum number of owners that must coordinate to block a transaction from being executed by refusing to sign,
calculated as `owners.length - threshold + 1`.

### Challenge Period

The time window during which a liveness challenge is active, starting when the fallback owner calls `challenge()` and
ending at `challengeStartTime + livenessResponsePeriod`.

### Scheduled Transaction

A transaction that has been scheduled for execution after the timelock delay. Contains execution time, state, and
transaction parameters.

### Pending Transaction

A scheduled transaction that has not yet been executed or cancelled, tracked in the enumerable set for efficient
querying.

## Assumptions

### a01-001: Safe Version Compatibility

SaferSafes depends on Safe contract version 1.4.1 for proper functionality. The contract uses Safe's signature
verification, module execution, and guard interfaces that may not be compatible with other versions.

#### Mitigations

- Version check enforced in `configureTimelockGuard()` requiring Safe version >= 1.3.0
- Contract documentation explicitly states compatibility with Safe 1.4.1 only

### a02-001: Fallback Owner Honesty

The fallback owner must not abuse challenge capabilities by initiating challenges when the Safe is responsive. Malicious
challenges can disrupt normal Safe operations even if ultimately unsuccessful.

#### Mitigations

- Safe owners can respond to challenges at any time to cancel them
- Reconfiguring the module cancels active challenges
- Safe can disable the module to prevent future challenges

### a03-001: Owner Key Security

Safe owners must maintain control of their private keys. If a quorum of keys is compromised, attackers can schedule
malicious transactions that may execute after the timelock delay.

#### Mitigations

- Cancellation mechanism allows subset of owners to cancel malicious transactions
- Cancellation threshold increases after each cancellation to prevent griefing
- Timelock delay provides window for detection and response

## Invariants

### i01-001: Liveness Response Period Exceeds Timelock Delay

When both components are enabled and configured, the liveness response period MUST be at least twice the timelock delay.

**Severity: High**

If the liveness response period is less than twice the timelock delay, a Safe may be unable to respond to a challenge
because there is insufficient time to schedule and execute a response transaction after the timelock delay expires. This
could result in unintended ownership transfer to the fallback owner despite the Safe being responsive.

### i02-001: Configuration Validation Consistency

The `_checkCombinedConfig()` validation MUST be called at the end of both `configureLivenessModule()` and
`configureTimelockGuard()` to ensure the resulting configuration is valid.

**Severity: High**

Without consistent validation, a Safe could end up in an invalid configuration state where the liveness response period
is insufficient for the timelock delay. This would violate the fundamental safety property that responsive Safes can
always defend against challenges.

### i03-001: Challenge Cancellation on Reconfiguration

Configuring or reconfiguring the liveness module MUST cancel any active challenge.

**Severity: Medium**

If challenges persist through reconfiguration, changing the liveness response period would create ambiguous timing for
active challenges. Additionally, a Safe that successfully reconfigures demonstrates liveness and should not remain under
challenge.

### i04-001: Ownership Transfer Atomicity

The `changeOwnershipToFallback()` function MUST verify that the fallback owner is the sole owner after the ownership
transfer completes.

**Severity: Critical**

If ownership transfer fails to complete correctly, the Safe could end up in an inconsistent state with multiple owners
or no owners, potentially locking funds permanently. The verification check ensures the transfer succeeded as intended.

### i05-001: Guard Removal on Ownership Transfer

When ownership transfers to the fallback owner, any guard enabled on the Safe MUST be disabled.

**Severity: High**

The guard may have been the cause of the liveness failure. Removing it ensures the fallback owner has full control and
can recover the Safe without being blocked by a malfunctioning guard.

### i06-001: Transaction Scheduling Uniqueness

A transaction can only be scheduled once, regardless of whether it has been cancelled or executed.

**Severity: High**

Allowing rescheduling would enable attackers to reuse signatures to reschedule cancelled transactions or extend the
delay for pending transactions by updating the execution time. This would undermine the security model of both
scheduling and cancellation.

### i07-001: Cancellation Threshold Bounds

The cancellation threshold MUST be capped at the [Maximum Cancellation Threshold] to preserve honest owners' ability to
cancel malicious transactions.

**Severity: Critical**

Without this cap, the cancellation threshold could increase beyond the number of honest owners, preventing them from
cancelling malicious transactions even when they have sufficient keys to block execution.

### i08-001: Cancellation Threshold Reset on Execution

The cancellation threshold MUST reset to 1 when any transaction executes successfully.

**Severity: Medium**

Resetting the threshold prevents the cancellation threshold from permanently increasing to a level where legitimate
transactions become difficult to execute. Successful execution demonstrates normal Safe operation.

## Function Specification

### configureLivenessModule

Configures the liveness module for a Safe that has already enabled it as a module.

**Parameters:**

- `_config`: ModuleConfig struct containing `livenessResponsePeriod` and `fallbackOwner`

**Behavior:**

- MUST revert if `livenessResponsePeriod` is 0
- MUST revert if `fallbackOwner` is the zero address
- MUST revert if the module is not enabled on the calling Safe
- MUST store the configuration for the calling Safe
- MUST cancel any existing challenge
- MUST emit `ModuleConfigured` event with safe address, response period, and fallback owner
- MUST call `_checkCombinedConfig()` to validate combined configuration

### clearLivenessModule

Clears the liveness module configuration for a Safe.

**Parameters:** None (called by Safe)

**Behavior:**

- MUST revert if the module is not configured for the calling Safe
- MUST revert if the module is still enabled on the calling Safe
- MUST delete the configuration data for the calling Safe
- MUST cancel any active challenge
- MUST emit `ModuleCleared` event with safe address

### challenge

Initiates a liveness challenge against a configured Safe.

**Parameters:**

- `_safe`: The Safe address to challenge

**Behavior:**

- MUST revert if the module is not configured for the target Safe
- MUST revert if the module is not enabled on the target Safe
- MUST revert if caller is not the configured fallback owner
- MUST revert if a challenge already exists for the target Safe
- MUST set `challengeStartTime` to current block timestamp
- MUST emit `ChallengeStarted` event with safe address and timestamp

### respond

Responds to a liveness challenge, canceling it.

**Parameters:** None (called by Safe)

**Behavior:**

- MUST revert if the module is not configured for the calling Safe
- MUST revert if the module is not enabled on the calling Safe
- MUST revert if no challenge exists for the calling Safe
- MUST delete the challenge start time
- MUST emit `ChallengeCancelled` event with safe address

### changeOwnershipToFallback

Transfers Safe ownership to the fallback owner after a successful challenge.

**Parameters:**

- `_safe`: The Safe address to transfer ownership of

**Behavior:**

- MUST revert if the module is not configured for the target Safe
- MUST revert if the module is not enabled on the target Safe
- MUST revert if caller is not the configured fallback owner
- MUST revert if no challenge exists for the target Safe
- MUST revert if the challenge period has not ended
- MUST delete the challenge start time
- MUST remove all owners except one
- MUST swap the remaining owner with the fallback owner
- MUST revert if the fallback owner is not the sole owner after transfer
- MUST disable any guard enabled on the Safe
- MUST emit `ChallengeSucceeded` event with safe address and fallback owner

### getChallengePeriodEnd

Returns the timestamp when the challenge period ends, or 0 if no challenge exists.

**Parameters:**

- `_safe`: The Safe address to query

**Behavior:**

- MUST return 0 if no challenge exists
- MUST return `challengeStartTime + livenessResponsePeriod` if challenge exists

### livenessSafeConfiguration

Returns the liveness module configuration for a given Safe.

**Parameters:**

- `_safe`: The Safe address to query

**Behavior:**

- MUST return ModuleConfig struct containing `livenessResponsePeriod` and `fallbackOwner`

### configureTimelockGuard

Configures the timelock guard for a Safe.

**Parameters:**

- `_timelockDelay`: The timelock delay in seconds (0 to clear configuration)

**Behavior:**

- MUST revert if the calling Safe version is less than 1.3.0
- MUST revert if `_timelockDelay` exceeds 365 days
- MUST store the timelock delay for the calling Safe
- MUST reset the cancellation threshold to 1
- MUST emit `GuardConfigured` event with safe address and timelock delay
- MUST emit `CancellationThresholdUpdated` event
- MUST call `_checkCombinedConfig()` to validate combined configuration

### clearTimelockGuard

Clears the timelock guard configuration for a Safe.

**Parameters:** None (called by Safe)

**Behavior:**

- MUST revert if the guard is not configured for the calling Safe
- MUST revert if the guard is still enabled on the calling Safe
- MUST set the timelock delay to 0
- MUST set the cancellation threshold to 0
- MUST cancel up to 100 pending transactions
- MUST emit `TransactionCancelled` event for each cancelled transaction
- MUST emit `TransactionsNotCancelled` event if more than 100 pending transactions exist

### scheduleTransaction

Schedules a transaction for execution after the timelock delay.

**Parameters:**

- `_safe`: The Safe address to schedule the transaction for
- `_nonce`: The nonce of the Safe for the transaction
- `_params`: ExecTransactionParams struct containing transaction details
- `_signatures`: The signatures of the owners scheduling the transaction

**Behavior:**

- MUST revert if the guard is not enabled on the target Safe
- MUST revert if the guard is not configured for the target Safe
- MUST revert if the transaction has already been scheduled
- MUST verify signatures using the Safe's `checkSignatures()` function
- MUST calculate execution time as `block.timestamp + timelockDelay`
- MUST store the scheduled transaction with Pending state
- MUST add the transaction hash to the pending transactions set
- MUST emit `TransactionScheduled` event with safe address, transaction hash, and execution time

### cancelTransaction

Cancels a scheduled transaction if the cancellation threshold is met.

**Parameters:**

- `_safe`: The Safe address to cancel the transaction for
- `_txHash`: The hash of the transaction being cancelled
- `_nonce`: The nonce for the cancellation transaction
- `_signatures`: The signatures of the owners cancelling the transaction

**Behavior:**

- MUST revert if the transaction state is Cancelled
- MUST revert if the transaction state is Executed
- MUST revert if the transaction state is NotScheduled
- MUST verify signatures using the Safe's `checkNSignatures()` function with the current cancellation threshold
- MUST set the transaction state to Cancelled
- MUST remove the transaction hash from the pending transactions set
- MUST increase the cancellation threshold by 1 if below the maximum
- MUST emit `TransactionCancelled` event with safe address and transaction hash
- MUST emit `CancellationThresholdUpdated` event if threshold was increased

### checkTransaction

Guard interface function called by the Safe before executing a transaction.

**Parameters:**

- `_to`: The address of the contract to call
- `_value`: The value to send with the transaction
- `_data`: The data to send with the transaction
- `_operation`: The operation to perform
- `_safeTxGas`: The gas to use for the transaction
- `_baseGas`: The base gas to use for the transaction
- `_gasPrice`: The gas price to use for the transaction
- `_gasToken`: The token to use for the transaction
- `_refundReceiver`: The address to receive the refund
- `_msgSender`: The address that called execTransaction on the Safe

**Behavior:**

- MUST return immediately if the timelock delay is 0
- MUST revert if `_msgSender` is not an owner of the calling Safe
- MUST calculate the transaction hash using the Safe's nonce minus 1
- MUST revert if the transaction state is Cancelled
- MUST revert if the transaction state is Executed
- MUST revert if the transaction state is NotScheduled
- MUST revert if the execution time has not been reached
- MUST reset the cancellation threshold to 1
- MUST set the transaction state to Executed
- MUST remove the transaction hash from the pending transactions set
- MUST emit `TransactionExecuted` event with safe address and transaction hash
- MUST emit `CancellationThresholdUpdated` event

### checkAfterExecution

Guard interface function called by the Safe after executing a transaction.

**Parameters:**

- `_txHash`: The transaction hash
- `_success`: Whether the transaction succeeded

**Behavior:**

- MUST perform no operations (empty implementation)

### cancellationThreshold

Returns the current cancellation threshold for a given Safe.

**Parameters:**

- `_safe`: The Safe address to query

**Behavior:**

- MUST return the current cancellation threshold value

### maxCancellationThreshold

Returns the maximum cancellation threshold for a given Safe.

**Parameters:**

- `_safe`: The Safe address to query

**Behavior:**

- MUST calculate the blocking threshold as `owners.length - threshold + 1`
- MUST return the minimum of the blocking threshold and the Safe's quorum

### timelockDelay

Returns the timelock delay for a given Safe.

**Parameters:**

- `_safe`: The Safe address to query

**Behavior:**

- MUST return the timelock delay in seconds

### scheduledTransaction

Returns the scheduled transaction details for a given Safe and transaction hash.

**Parameters:**

- `_safe`: The Safe address to query
- `_txHash`: The transaction hash to query

**Behavior:**

- MUST return ScheduledTransaction struct containing execution time, state, and parameters

### pendingTransactions

Returns all pending transactions for a given Safe.

**Parameters:**

- `_safe`: The Safe address to query

**Behavior:**

- MUST return an array of ScheduledTransaction structs for all pending transactions
- MUST copy the entire set of pending transactions to memory

### signCancellation

Dummy function provided as a utility to facilitate signing cancellation data in the Safe UI.

**Parameters:**

- Unnamed bytes32 parameter (transaction hash)

**Behavior:**

- MUST emit `Message` event with informational text
