# Skill: Add New Chain Pipeline

## Description
Guide for creating a complete data pipeline for a new EVM-compatible blockchain in the Chainslake Onprem system, including: finding RPCs, updating `.env`, creating job scripts, and creating the Airflow DAG.

## Applicability Conditions
- When the user wants to add a new EVM blockchain (e.g., BNB, Polygon, Arbitrum, Base, etc.)
- The chain must support the following APIs: `eth_blockNumber`, `eth_getBlockByNumber`, `eth_getBlockReceipts`

## Steps

### Step 1: Fetch and check the RPC list

Use the reusable script `script/check_rpcs.py` (no need to write a new script for each chain):

```bash
# By chainId (recommended)
python script/check_rpcs.py <CHAIN_ID>

# Example
python script/check_rpcs.py 56          # BNB → automatically infers BNB_RPCS
python script/check_rpcs.py 137         # Polygon → automatically infers POLYGON_RPCS
python script/check_rpcs.py 1 --env-var ETHEREUM_RPCS

# Additional customization
python script/check_rpcs.py 56 --timeout 15 --workers 20
```

The script will:
- Automatically fetch the RPC list from chainlist.org by chainId
- Check in parallel: `eth_blockNumber` → `eth_getBlockByNumber` → `eth_getBlockReceipts`
- Print a `<ENV_VAR>=...` line to copy into `.env`

**Looking up chainId**: https://chainlist.org (or https://chainid.network)

### Step 2: Update `chainslake-run/.env`

Append the following line to the end of the `.env` file:
```
<CHAIN_UPPER>_RPCS=<comma_separated_rpc_list>
```

Example: `BNB_RPCS=https://bsc-dataseed1.ninicoin.io,...`

### Step 3: Create `jobs/<chain_name>/application.properties`

Copy from `jobs/ethereum/application.properties` and change:
- `chain_name=<chain_name>` (e.g., `bnb`, `polygon`)
- `rpc_name=<Full name of the chain>` (e.g., `BNB Smart Chain Mainnet`)
- `number_block_per_partition`: adjust according to the chain's block speed
  - Ethereum (~12s/block): 300
  - BNB (~3s/block): 1000
  - Polygon (~2s/block): 1500
- `origin_table=<chain_name>.blocks`

### Step 4: Create the job scripts

Create the full directory structure and `.sh` files:

```
jobs/<chain_name>/
├── application.properties
├── origin/
│   ├── transaction_blocks.sh   ← uses $<CHAIN>_RPCS, app_name=evm_origin.transaction_blocks
│   └── blocks_receipt.sh       ← uses $<CHAIN>_RPCS, app_name=evm_origin.blocks_receipt
├── extract/
│   ├── blocks.sh               ← sql.transformer, sql_file=evm/blocks.sql
│   ├── transactions.sh         ← uses $<CHAIN>_RPCS, app_name=evm.transactions
│   └── logs.sh                 ← uses $<CHAIN>_RPCS, app_name=evm.logs
├── contract/
│   ├── decoded_log.sh          ← sql.transformer, sql_file=evm_contract/decode_log.sql, accepts $1 $2
│   └── erc20_tokens.sh         ← sql.transformer, sql_file=evm_contract/erc20_tokens.sql
└── token/
    └── erc20_transfer.sh       ← sql.transformer, sql_file=evm_token/erc20_transfer.sql
```

Naming convention for `--name` in spark-submit:
- Format: `<ChainName><JobName>` (PascalCase, no hyphens)
- Example: `BnbOriginBlocksReceipt`, `BnbBlocks`, `BnbDecodedLog`

After creating: `chmod +x jobs/<chain_name>/**/*.sh`

### Step 5: Create the Airflow DAG

Create `chainslake/airflow/dags/<chain_name>.py`, copy from `ethereum.py` and replace:
- DAG name: `"<CHAIN_UPPER>"`
- `RUN_DIR` path: `"/jobs/<chain_name>"`
- All `ethereum_` prefixes → `<chain_name>_`
- `task_id` following the naming: `<chain_name>_origin.transaction_blocks`, `<chain_name>.blocks`, etc.

Standard dependency graph:
```
origin_transaction_blocks → origin_blocks_receipt
origin_blocks_receipt → [blocks, transactions, logs]
logs → decoded_erc20_evt_transfer
decoded_erc20_evt_transfer → contract_erc20_tokens
[transactions, decoded_erc20_evt_transfer] → token_erc20_transfer
contract_erc20_tokens → token_erc20_transfer
```

## Notes / Gotchas

- **`number_block_per_partition`**: BNB produces ~1 block/3 seconds, so use 1000 so each partition covers ≈ ~50 minutes of data
- **Env vars in `.sh`**: The origin jobs and extract/transactions, extract/logs need `export $(cat $CHAINSLAKE_RUN_DIR/.env)` at the top to load the RPC list. The `blocks.sh` job (uses sql.transformer) does not need it.
- **`decoded_log.sh` accepts parameters**: This script accepts `$1` (table_name) and `$2` (run_mode) like Ethereum, not hardcoded
- **RPC check**: Some RPCs return `result=null` for `eth_getBlockReceipts` — this is a sign the RPC does not support it and must be removed
- **Timeout**: Use timeout=10s when checking RPCs; some RPCs are slow but still valid — increase to 15s if needed

## Real-World Example
- First time applied: BNB Smart Chain Mainnet (chainId=56), on 2026-07-10
- 52 RPCs checked → 20 PASS, 32 FAIL
- Command used: `python script/check_rpcs.py 56`
- Reference files: `jobs/bnb/`, `airflow/dags/bnb.py`
