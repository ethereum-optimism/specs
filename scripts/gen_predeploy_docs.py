import argparse
import subprocess
import sys
import os
import re
import json

SOURCE_HASH_PREFIX = "0x0000000000000000000000000000000000000000000000000000000000000002"

JINJA_TEMPLATE = """### {{ params.contract_name }} Deployment
<!-- Generated with: {{ params.command }} -->

The `{{ params.contract_name }}` contract is deployed.

A deposit transaction is derived with the following attributes:

- `from`: `{{ params.from_address }}`
- `to`: `null`
- `mint`: `0`
- `value`: `0`
- `nonce`: `{{ params.from_address_nonce }}`
- `gasLimit`: `{{ params.gas_limit }}`
- `data`: `{{ params.data_bytecode_head }}` ([full bytecode](../../{{ params.data_path }}))
- `sourceHash`: `{{ params.source_hash }}`,
  computed with the "Upgrade-deposited" type, with `intent = "{{ params.intent }}"`

This results in the {{ params.fork_name }} {{ params.contract_name }} contract being deployed to
`{{ params.deployed_address }}`, to verify:

```bash
cast compute-address --nonce={{ params.from_address_nonce }} {{ params.from_address }}
Computed Address: {{ params.deployed_address }}
```

Verify `sourceHash`:

```bash
cast keccak $(cast concat-hex 0x0000000000000000000000000000000000000000000000000000000000000002 $(cast keccak "{{ params.intent }}"))
# {{ params.source_hash }}
```

Verify `data`:

```bash
git checkout {{ params.git_commit_hash }}
make build-contracts
jq -r ".bytecode.object" {{ params.forge_artifact_path_data }}
```

This transaction MUST deploy a contract with the following code hash
`{{ params.contract_code_hash }}`.

To verify the code hash:

```bash
git checkout {{ params.git_commit_hash }}
make build-contracts
cast k $(jq -r ".deployedBytecode.object" {{ params.forge_artifact_path_data }})
```

{% if params.proxy_address %}
### {{ params.contract_name }} Proxy Update

This transaction updates the {{ params.contract_name }} Proxy ERC-1967
implementation slot to point to the new {{ params.contract_name }} deployment.

A deposit transaction is derived with the following attributes:

- `from`: `0x0000000000000000000000000000000000000000`
- `to`: `{{ params.proxy_address }}` ({{ params.contract_name }} Proxy)
- `mint`: `0`
- `value`: `0`
- `gasLimit`: `50,000`
- `data`: `{{ params.proxy_data }}`
- `sourceHash`: `{{ params.proxy_source_hash }}`
  computed with the "Upgrade-deposited" type, with `intent = "{{ params.proxy_intent }}"`

Verify data:

```bash
cast concat-hex $(cast sig "upgradeTo(address)") $(cast abi-encode "upgradeTo(address)" {{ params.deployed_address }})
# {{ params.proxy_data }}
```

Verify `sourceHash`:

```bash
cast keccak $(cast concat-hex 0x0000000000000000000000000000000000000000000000000000000000000002 $(cast keccak "{{ params.proxy_intent }}"))
# {{ params.proxy_source_hash }}
```{% endif %}
"""

def camel_to_snake(name):
    pattern = re.compile(r'(?<!^)(?=[A-Z])')
    return pattern.sub('_', name).lower()

def camel_to_kebab(name):
    pattern = re.compile(r'(?<!^)(?=[A-Z])')
    return pattern.sub('-', name).lower()

def format_args_with_alternate_newlines(args):
    """Format CLI arguments with newlines every other argument."""
    result = []
    for i, arg in enumerate(args):
        result.append(arg)
        # Add newline after every second argument (indices 1, 3, 5, etc.)
        if i % 2 == 1 and i < len(args) - 1:
            result.append(' \\\n')
        elif i < len(args) - 1:
            result.append(' ')
    return ''.join(result)

def check_dependencies():
    """Check if required commands and packages are available."""
    commands = ['git', 'make', 'jq', 'cast']
    for cmd in commands:
        try:
            result = run_cmd([cmd, '--version'], check=False)
            if not result:
                raise EnvironmentError(f"Required command '{cmd}' not found or not working in shell environment. Ensure it is installed and available in PATH via your shell (considering tools like mise).")
        except Exception as e:
            raise EnvironmentError(f"Required command '{cmd}' not found in PATH or failed to execute: {str(e)}.")
    try:
        import jinja2
    except ImportError:
        raise EnvironmentError("Required Python package 'jinja2' is not installed. Please install it with 'uv pip install jinja2'.")

def stash_and_checkout(repo_path, git_commit_hash):
    """Stash any changes in the repo and checkout the specified commit. Returns True if successful, False otherwise."""
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], cwd=repo_path, capture_output=True, text=True, check=True)
        if result.stdout.strip():
            subprocess.run(['git', 'stash', 'push', '-m', 'Temporary stash for TOML generation'], 
                           cwd=repo_path, check=True, capture_output=True, text=True)
            success(f"Changes in Optimism repo stashed successfully.")
        subprocess.run(['git', 'checkout', git_commit_hash], 
                       cwd=repo_path, check=True, capture_output=True, text=True)
        success(f"Checked out commit {git_commit_hash} in Optimism repo.")
        return True
    except subprocess.CalledProcessError as e:
        error(f"Error during git operations: {e.stderr}")
        return False

def restore_repo_state(repo_path):
    """Restore the repository to its original state."""
    try:
        result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                                cwd=repo_path, capture_output=True, text=True, check=True)
        current_ref = result.stdout.strip()
        if current_ref == 'HEAD':
            current_ref = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                         cwd=repo_path, capture_output=True, text=True, check=True).stdout.strip()
        subprocess.run(['git', 'checkout', current_ref], 
                       cwd=repo_path, check=True, capture_output=True, text=True)
        success(f"Checked out original ref {current_ref} in Optimism repo.")
        stash_result = subprocess.run(['git', 'stash', 'list'], cwd=repo_path, capture_output=True, text=True, check=True)
        if stash_result.stdout.strip() and 'Temporary stash for TOML generation' in stash_result.stdout:
            subprocess.run(['git', 'stash', 'pop'], 
                           cwd=repo_path, check=True, capture_output=True, text=True)
            success(f"Stashed changes in Optimism repo restored successfully.")
    except subprocess.CalledProcessError as e:
        error(f"Error restoring repo state: {e.stderr}")

def run_cmd(command, check=True, capture_output=True, text=True, cwd=None, env=None):
    """Runs a shell command and returns its output. Uses the user's shell to ensure environment hooks are applied."""
    # Only log commands if there's an error
    try:
        shell_cmd = os.environ.get('SHELL', '/bin/sh')
        if isinstance(command, list):
            cmd_str = ' '.join(command)
        else:
            cmd_str = command
        full_cmd = [shell_cmd, '-c', cmd_str]
        custom_env = env or os.environ.copy()
        home_dir = os.environ.get('HOME', '')
        if home_dir:
            mise_paths = [
                f"{home_dir}/.local/bin",
                f"{home_dir}/.local/share/mise/shims"
            ]
            current_path = custom_env.get('PATH', '')
            custom_env['PATH'] = ':'.join(mise_paths + [current_path])
        result = subprocess.run(
            full_cmd,
            check=check,
            capture_output=capture_output,
            text=text,
            cwd=cwd,
            env=custom_env
        )
        return result.stdout.strip() if result.stdout else ""
    except subprocess.CalledProcessError as e:
        error(f"Error running command: {' '.join(command) if isinstance(command, list) else command}")
        error(f"Return code: {e.returncode}")
        error(f"Output:\n{e.stdout}")
        error(f"Error:\n{e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        error(f"Error: Shell not found: {shell_cmd}. Please ensure SHELL environment variable is set correctly.")
        sys.exit(1)

# Helper functions for colored logging
def info(msg):
    """Print informational messages in blue."""
    print(f"\033[34m{msg}\033[0m", file=sys.stderr)

def success(msg):
    """Print success messages in green."""
    print(f"\033[32m{msg}\033[0m", file=sys.stderr)

def warning(msg):
    """Print warning messages in yellow."""
    print(f"\033[33m{msg}\033[0m", file=sys.stderr)

def error(msg):
    """Print error messages in red to stderr."""
    print(f"\033[31m{msg}\033[0m", file=sys.stderr)

def parse_constructor_signature(abi_json):
    """
    Given an ABI (as a Python list/dict structure), find the constructor entry
    and return its canonical signature string, e.g. "constructor(uint256,bool)".
    """
    for item in abi_json:
        if item.get("type") == "constructor":
            types = [inp["type"] for inp in item.get("inputs", [])]
            return f"constructor({','.join(types)})"
    return None

def extract_constructor_signature(contract_name, cwd=None):
    """
    Runs `forge inspect <contract_name> abi`, parses the JSON,
    and returns the constructor signature string (or None if not found).
    """
    # invoke forge
    result = run_cmd(
        ["forge", "inspect", contract_name, "abi", "--json"],
        cwd=cwd
    )

    try:
        abi = json.loads(result)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse ABI JSON: {e}")
    sig = parse_constructor_signature(abi)
    return sig

def get_git_status(cwd=None):
    """Gets the current git branch or commit SHA in the specified directory."""
    try:
        # Check if HEAD is detached
        sha = run_cmd(["git", "rev-parse", "HEAD"], check=False, cwd=cwd)
        # Try to get branch name
        branch = run_cmd(["git", "symbolic-ref", "--short", "-q", "HEAD"], check=False, cwd=cwd)
        if branch:
            return branch
        # If no branch, return the SHA (detached head)
        return sha
    except Exception as e:
        print(f"Warning: Could not determine git status in {cwd}: {e}", file=sys.stderr)
        return None

def git_checkout(commit_hash, repo_dir):
    """Checks out the specified git commit in the repository."""
    info(f"Checking out git commit: {commit_hash}...")
    return run_cmd(["git", "checkout", commit_hash], cwd=repo_dir)

def build_contracts(repo_dir):
    """Builds contracts using 'make build-contracts' in the repository."""
    info(f"Building contracts with 'make build-contracts'...")
    return run_cmd("make build-contracts", cwd=repo_dir)

def extract_bytecode(jq_cmd, repo_dir):
    """Extracts bytecode using jq command in the repository."""
    info(f"Extracting deployed bytecode...")
    return run_cmd(jq_cmd, cwd=repo_dir)

def compute_code_hash(bytecode):
    """Computes code hash using cast."""
    return run_cmd(["cast", "k", bytecode])

def compute_deployed_address(from_address, nonce):
    """Computes deployed address using cast."""
    info(f"Deriving deployed address...")
    result = run_cmd(["cast", "compute-address", "--nonce", str(nonce), from_address])
    result = result.split('\n')[-1]
    result = result.split(' ')[-1]
    info(f"Deployed Address: {result}")
    return result

def compute_keccak(data):
    """Computes keccak hash using cast."""
    return run_cmd(["cast", "keccak", f"\"{data}\""])

def compute_concat_hex(prefix, hash_value):
    """Computes concatenated hex using cast."""
    return run_cmd(f'cast concat-hex {prefix} {hash_value}')

def compute_proxy_update_data(proxy_address):
    """Computes proxy update data using cast."""
    return run_cmd(f'cast concat-hex $(cast sig "upgradeTo(address)") $(cast abi-encode "upgradeTo(address)" {proxy_address})')

def estimate_gas(rpc_url, creation_code, constructor_signature, constructor_args=None):
    """Estimates gas for deployment using cast."""
    info(f"Estimating gas for deployment...")
    env = os.environ.copy()
    env["ETH_RPC_URL"] = rpc_url
    gas_cmd = [
        "cast", "estimate",
        "--create",
        creation_code,
    ]
    if constructor_signature:
        gas_cmd.append(constructor_signature)
    if constructor_args:
        args_list = constructor_args.split(',')
        gas_cmd.extend(args_list)
    result = run_cmd(gas_cmd, env=env)
    result = result.split("\n")[-1]
    success(f"Estimated Gas: {result}")
    return result

def derive_contract_code_hash(commit_hash, forge_artifact_path, repo_dir):
    """Checks out commit, builds, gets code hash, and restores git state in the specified repo_dir."""
    original_git_state = get_git_status(cwd=repo_dir)
    absolute_forge_artifact_path = os.path.join(repo_dir, forge_artifact_path)
    try:
        git_checkout(commit_hash, repo_dir)
        build_contracts(repo_dir)
        if not os.path.exists(absolute_forge_artifact_path):
            error(f"Error: Forge artifact file not found after build: {absolute_forge_artifact_path}")
            sys.exit(1)
        jq_cmd = f"jq -r '.deployedBytecode.object' {forge_artifact_path}"
        bytecode = extract_bytecode(jq_cmd, repo_dir)
        if not bytecode or bytecode.startswith("jq: error"):
            error(f"Error: Failed to extract bytecode using jq. Command: {jq_cmd}")
            error(f"jq output: {bytecode}")
            sys.exit(1)
        code_hash = compute_code_hash(bytecode)
        success(f"Derived contract code hash: {code_hash}")
        return code_hash
    except Exception as e:
        error(f"An error occurred during contract code hash derivation: {e}")
        sys.exit(1)
    finally:
        if original_git_state:
            info(f"Restoring git state in {repo_dir} to: {original_git_state}...")
            git_checkout(original_git_state, repo_dir)

def forge_artifact_path(contract_name):
    """Returns the path to the forge artifact for the contract."""
    return f"packages/contracts-bedrock/forge-artifacts/{contract_name}.sol/{contract_name}.json"

def data_path(fork_name, contract_name):
    """Returns the data path for the contract."""
    return f"../specs/static/bytecode/{fork_name.lower()}-{camel_to_kebab(contract_name)}-deployment.txt"

def render_template(data):
    """Render a Jinja2 template with the provided data."""
    import jinja2
    env = jinja2.Environment()
    template = env.from_string(JINJA_TEMPLATE)
    return template.render(params=data)

def main():
    parser = argparse.ArgumentParser(description="Generate TOML config for the predeploy_upgrade Tera macro.")
    parser.add_argument("--optimism-repo-path", type=str, required=True, help="Path to the Optimism repository directory.")
    parser.add_argument("--fork-name", type=str, required=True, help="Name of the fork (e.g., Isthmus)")
    parser.add_argument("--contract-name", type=str, required=True, help="Name of the contract (e.g., CrossL2Inbox)")
    parser.add_argument("--from-address", type=str, required=True, help="Address deploying the contract")
    parser.add_argument("--from-address-nonce", type=int, required=True, help="Nonce of the deploying address")
    parser.add_argument("--git-commit-hash", type=str, required=True, help="Git commit hash to build contracts from.")
    parser.add_argument("--eth-rpc-url", type=str, required=True, help="Ethereum JSON-RPC URL for gas estimation.")
    parser.add_argument("--constructor-args", type=str, help="Comma-separated values for constructor arguments (e.g., 'arg1,arg2,arg3')")
    parser.add_argument("--template-path", type=str, default="specs/macros/predeploy_upgrade.jinja", help="Path to the Jinja template file.")
    parser.add_argument("--proxy-address", type=str, default="", help="Address of the proxy to update, find in github.com/ethereum-optimism/optimism/op-service/predeploys/addresses.go.")
    parser.add_argument("--copy-contract-bytecode", type=bool, default=False, help="Whether to copy the contract bytecode to the data path.")

    args = parser.parse_args()

    try:
        check_dependencies()
    except EnvironmentError as e:
        error(f"Dependency check failed: {e}")
        sys.exit(1)

    if not os.path.isdir(args.optimism_repo_path):
        error(f"Error: Provided Optimism repo directory does not exist or is not a directory: {args.optimism_repo_path}")
        sys.exit(1)
    if not os.path.exists(os.path.join(args.optimism_repo_path, ".git")):
        warning(f"Warning: Provided directory does not appear to be a git repository: {args.optimism_repo_path}")

    if not stash_and_checkout(args.optimism_repo_path, args.git_commit_hash):
        error(f"Failed to stash changes or checkout commit in Optimism repo. Aborting.")
        sys.exit(1)

    try:
        intent = f"{args.fork_name}: {args.contract_name} Deployment"
        info(f"Deriving parameters for {intent}...")
        deployed_address = compute_deployed_address(args.from_address, args.from_address_nonce)
        info(f"Computing source hash...")
        source_hash = compute_keccak(compute_concat_hex(SOURCE_HASH_PREFIX, compute_keccak(intent)))
        info(f"Source Hash: {source_hash}")

        info(f"Deriving Contract Bytecode...")
        forge_artifact_path_val = forge_artifact_path(args.contract_name)
        contract_code_hash = derive_contract_code_hash(args.git_commit_hash, forge_artifact_path_val, args.optimism_repo_path)
        jq_creation_cmd = f"jq -r '.bytecode.object' {forge_artifact_path_val}"
        creation_code = extract_bytecode(jq_creation_cmd, args.optimism_repo_path)
        info(f"Contract Bytecode: 0x{creation_code[:32]}...")

        constructor_signature = extract_constructor_signature(args.contract_name, cwd=args.optimism_repo_path + "/packages/contracts-bedrock")
        estimated_gas = estimate_gas(args.eth_rpc_url, creation_code, constructor_signature, args.constructor_args)

        data_path_result = data_path(args.fork_name, args.contract_name)


        template_data = {
            "fork_name": args.fork_name,
            "contract_name": args.contract_name,
            "intent": intent,

            # Comment from @geoknee on args.from_address: It would be great if there was some way we could ensure that
            # this address has not yet been used, or at least that it's nonce is equal to
            # the provided nonce. Otherwise we may have specs bugs and upgrade transactions
            # will (I think) potentially revert.
            #
            # We apparently have a convention that each deployment will come from a unique
            # address with a zero nonce. This convention guarantees the upgrade transaction
            # does not revert, so if we check the convention is adhered to we should be
            # fine.
            #
            # In lieu of automation around this, we can instruct the user to choose an
            # unused address or suggest they just increment the previous address which was
            # used (going in order through the hardforks).
            "from_address": args.from_address,
            "from_address_nonce": args.from_address_nonce,
            "gas_limit": estimated_gas,
            "data_bytecode_head": "0x" + creation_code[:32] + "...",
            "data_path": data_path_result,
            "git_commit_hash": args.git_commit_hash,
            "contract_code_hash": contract_code_hash,
            "source_hash": source_hash,
            "deployed_address": deployed_address,
            "command": "./scripts/run_gen_predeploy_docs.sh " + format_args_with_alternate_newlines(sys.argv[1:]),
            "forge_artifact_path_data": forge_artifact_path_val,
        }
        if args.proxy_address:
            proxy_intent = f"{args.fork_name}: {args.contract_name} Proxy Update"
            proxy_data = compute_proxy_update_data(deployed_address)
            proxy_source_hash = compute_keccak(compute_concat_hex(SOURCE_HASH_PREFIX, compute_keccak(proxy_intent)))
            template_data["proxy_address"] = args.proxy_address
            template_data["proxy_source_hash"] = proxy_source_hash
            template_data["proxy_data"] = proxy_data
            template_data["proxy_intent"] = proxy_intent
        info(f"\n-- Rendered Template --")
        rendered_output = render_template(template_data)
        print(rendered_output, end="")
        info(f"\n--- End Rendered Template ---\n")
        if args.copy_contract_bytecode:
            run_cmd(f"jq -r '.bytecode.object' {args.optimism_repo_path}/{forge_artifact_path_val} > ./{data_path_result}")
            success(f"Copied contract bytecode to {data_path_result}")
        else:
            info(f"Final step: copy the contract bytecode to {data_path_result} with the following command:\n")
            print(f"jq -r '.bytecode.object' {args.optimism_repo_path}/{forge_artifact_path_val} > {data_path_result}\n", file=sys.stderr)
    finally:
        restore_repo_state(args.optimism_repo_path)


if __name__ == "__main__":
    main() 
