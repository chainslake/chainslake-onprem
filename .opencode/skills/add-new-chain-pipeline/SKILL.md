---
name: add-new-chain-pipeline
description: Create a complete data pipeline for a new EVM-compatible blockchain — find RPCs, update .env, create job scripts, create Airflow DAG
---

# Skill: Add New Chain Pipeline

## Description
Guide to creating a complete data pipeline for a new EVM-compatible blockchain in the Chainslake Onprem system, including: finding RPCs, updating `.env`, creating job scripts, and creating an Airflow DAG.

## When to Use
- When the user wants to add a new EVM blockchain (e.g., BNB, Polygon, Arbitrum, Base, etc.)
- The chain needs to be compatible with APIs: `eth_blockNumber`, `eth_getBlockByNumber`, `eth_getBlockReceipts`

## Implementation Steps

### Step 1: Fetch and Validate RPC List

Use the reusable script `script/check_rpcs.py` (no need to write a new script for each chain):

```bash
# By chainId (recommended)
python script/check_rpcs.py <CHAIN_ID>

# Examples
python script/check_rpcs.py 56          # BNB → auto-infers BNB_RPCS
python script/check_rpcs.py 137         # Polygon → auto-infers POLYGON_RPCS
python script/check_rpcs.py 1 --env-var ETHEREUM_RPCS

# Additional customization
python script/check_rpcs.py 56 --timeout 15 --workers 20
```

The script will:
- Automatically fetch RPC list from chainlist.org by chainId
- Parallel validation: `eth_blockNumber` → `eth_getBlockByNumber` → `eth_getBlockReceipts`
- Output `<ENV_VAR>=...` line to copy into `.env`

**Lookup chainId**: https://chainlist.org (or https://chainid.network)

### Step 2: Update `chainslake-run/.env`

Append the following line to the end of `.env`:
```
<CHAIN_UPPER>_RPCS=<comma_separated_passing_rpc_list>
```

Example: `BNB_RPCS=https://bsc-dataseed1.ninicoin.io,...`

### Step 3: Create `jobs/<chain_name>/application.properties`

Copy from `jobs/ethereum/application.properties`, modify:
- `chain_name=<chain_name>` (e.g., `bnb`, `polygon`)
- `rpc_name=<Full chain name>` (e.g., `BNB Smart Chain Mainnet`)
- `number_block_per_partition`: adjust based on chain block speed
  - Ethereum (~12s/block): 300
  - BNB (~3s/block): 1000
  - Polygon (~2s/block): 1500
- `origin_table=<chain_name>.blocks`

### Step 4: Create Job Scripts

Create the complete directory structure and `.sh` files:

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

After creation: `chmod +x jobs/<chain_name>/**/*.sh`

### Step 5: Create Airflow DAG

Create `chainslake/airflow/dags/<chain_name>.py`, copy from `ethereum.py` and replace:
- DAG name: `"<CHAIN_UPPER>"`
- `RUN_DIR` path: `"/jobs/<chain_name>"`
- All `ethereum_` prefixes → `<chain_name>_`
- `task_id` naming: `<chain_name>_origin.transaction_blocks`, `<chain_name>.blocks`, etc.

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

- **`number_block_per_partition`**: BNB produces ~1 block/3 seconds, so use 1000 to make each partition ≈ ~50 minutes of data
- **Env variables in .sh**: Origin jobs and extract/transactions, extract/logs need `export $(cat $CHAINSLAKE_RUN_DIR/.env)` at the beginning to load the RPC list. The `blocks.sh` job (using sql.transformer) does not need this.
- **`decoded_log.sh` accepts parameters**: This script accepts `$1` (table_name) and `$2` (run_mode) like Ethereum, don't hardcode
- **RPC check**: Some RPCs return `result=null` for `eth_getBlockReceipts` — this indicates no support, must be filtered out
- **Timeout**: Use timeout=10s when checking RPCs; some RPCs are slow but still valid — increase to 15s if needed

## Real-world Example
- First applied: BNB Smart Chain Mainnet (chainId=56), on 2026-07-10
- 52 RPCs checked → 20 PASS, 32 FAIL
- Command used: `python script/check_rpcs.py 56`
- Reference files: `jobs/bnb/`, `airflow/dags/bnb.py`