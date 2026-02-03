#!/bin/bash -e

# Function to display usage information
usage() {
    echo "Usage: $0 <constants_file>"
    echo "  constants_file: Path to the file containing configuration constants"
    echo "                  (e.g., ./upgrades/interop.sh)"
    exit 1
}

# Check if constants file argument is provided
if [ $# -ne 1 ]; then
    echo "Error: Constants file argument is required."
    usage
fi

CONSTANTS_FILE="$1"

# Check if the constants file exists and is readable
if [ ! -f "$CONSTANTS_FILE" ]; then
    echo "Error: Constants file '$CONSTANTS_FILE' not found."
    exit 1
fi

if [ ! -r "$CONSTANTS_FILE" ]; then
    echo "Error: Constants file '$CONSTANTS_FILE' is not readable."
    exit 1
fi

# Source the constants file
echo "Loading constants from: $CONSTANTS_FILE"
# shellcheck disable=SC1090
source "$CONSTANTS_FILE"

# Validate that required constants are defined
# shellcheck disable=SC2154
if [ -z "$GIT_COMMIT_HASH" ] || [ -z "$FROM_ADDRESS" ] || [ -z "$FORK_NAME" ] || [ ${#contracts[@]} -eq 0 ]; then
    echo "Error: One or more required constants are not defined in the constants file."
    echo "Required: GIT_COMMIT_HASH, FROM_ADDRESS, FORK_NAME, contracts array"
    exit 1
fi

inc_hex() {
  # $1 : hex string, with or without 0x
  local hex="${1#0x}"      # remove leading “0x” if it’s there
  # perform the add via bc
  local next
  next=$(printf 'obase=16; ibase=16; %s + 1\n' "$hex" | bc)
  # print with 0x
  printf '0x%s\n' "$next"
}

# shellcheck disable=SC2154
for contract_pair in "${contracts[@]}"; do
    IFS=':' read -r contract_name proxy_address <<< "$contract_pair"
    ./run_gen_predeploy_docs.sh \
        --optimism-repo-path ../../optimism \
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
