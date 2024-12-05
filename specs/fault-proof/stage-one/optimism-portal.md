<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

**Table of Contents**

- [Optimism Portal](#optimism-portal)
  - [Overview (What this contract is actually supposed to do)](#overview-what-this-contract-is-actually-supposed-to-do)
  - [Definitions](#definitions)
  - [Top-Level Invariants](#top-level-invariants)
- [Function-Level Invariants](#function-level-invariants)
  - [Initialize the thing somehow](#initialize-the-thing-somehow)
  - [Prove a withdrawal transaction](#prove-a-withdrawal-transaction)
  - [Finalize a withdrawal transaction](#finalize-a-withdrawal-transaction)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Optimism Portal

## Overview (What this contract is actually supposed to do)

## Definitions

## Top-Level Invariants

- A withdrawal transaction must be proven against a game that is not `invalid`.
- A withdrawal transaction must be finalized against a game that is `valid`.
- A withdrawal transaction must be used only once to finalize a withdrawal.
- A withdrawal can only be finalized if it has been proven.
- A withdrawal transaction that is finalized must attempt execution.

# Function-Level Invariants

## Initialize the thing somehow

- Need an **authorized** input for proof maturity delay seconds.
- Need an **authorized** reference to the anchor state registry.
- Need an **authorized** reference to the dispute game factory.
- Need an **authorized** input to system config.
- Need an **authorized** reference to superchain config.

## Prove a withdrawal transaction

## Finalize a withdrawal transaction
