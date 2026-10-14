# Canyon Deposits

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Overview](#overview)
- [Changes](#changes)
  - [`depositNonce` and `depositNonceVersion` always present](#depositnonce-and-depositnonceversion-always-present)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

[deposits]: ../deposits.md

## Overview

The Canyon upgrade changes the deposit receipt. This page lists the changes to the
[deposit specification][deposits]. The deposit specification describes the Bedrock behaviour.

## Changes

### `depositNonce` and `depositNonceVersion` always present

The `depositNonce` and `depositNonceVersion` fields of the deposit receipt are always included.
Before Canyon, these fields are always omitted.
