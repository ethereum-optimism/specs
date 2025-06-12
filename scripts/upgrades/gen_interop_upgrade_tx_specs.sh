#!/bin/bash -e

GIT_COMMIT_HASH=71c460ec7c7c05791ddd841b97bcb664a1f0c753
FROM_ADDRESS_NONCE=0
FROM_ADDRESS=0x4220000000000000000000000000000000000000
FORK_NAME=Interop

# Array of contract names and their corresponding proxy addresses
declare -a contracts=(
    "CrossL2Inbox:0x4200000000000000000000000000000000000022"
    "L2ToL2CrossDomainMessenger:0x4200000000000000000000000000000000000023"
)

inc_hex() {
  # $1 : hex string, with or without 0x
  local hex="${1#0x}"      # remove leading “0x” if it’s there
  # perform the add via bc
  local next
  next=$(printf 'obase=16; ibase=16; %s + 1\n' "$hex" | bc)
  # print with 0x
  printf '0x%s\n' "$next"
}

for contract_pair in "${contracts[@]}"; do
    IFS=':' read -r contract_name proxy_address <<< "$contract_pair"
    ./scripts/run_gen_predeploy_docs.sh \
        --optimism-repo-path ../optimism \
        --fork-name $FORK_NAME \
        --contract-name "$contract_name" \
        --from-address $FROM_ADDRESS \
        --from-address-nonce $FROM_ADDRESS_NONCE \
        --git-commit-hash $GIT_COMMIT_HASH \
        --eth-rpc-url https://optimism.rpc.subquery.network/public \
        --proxy-address "$proxy_address" \
        --copy-contract-bytecode true
    # increment the from address itself by 1 in hex here
    FROM_ADDRESS=$(inc_hex "$FROM_ADDRESS")
done