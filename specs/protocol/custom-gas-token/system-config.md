# System Config

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Definitions](#definitions)
  - [Custom Gas Token Flag](#custom-gas-token-flag)
- [Function Specification](#function-specification)
  - [isCustomGasToken](#iscustomgastoken)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Definitions

### Custom Gas Token Flag

## Function Specification

### isCustomGasToken

Returns true if the gas token is a custom gas token, false otherwise.

- MUST return the result of a call to `optimismPortal.isCustomGasToken()`.
