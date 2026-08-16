# Data Warehouse Lineage

Diagram showing the dependency (lineage) between tables in the warehouse.
The `-->` arrow means "used to create".

## Mermaid Graph

```mermaid
graph LR
    RPC["RPC Node (Blockchain)"]
    T0["ethereum.blocks"]
    T1["ethereum.logs"]
    T2["ethereum.transactions"]
    T3["ethereum_contract.erc20_tokens"]
    T4["ethereum_decoded.erc20_evt_transfer"]
    T5["ethereum_origin.blocks_receipt"]
    T6["ethereum_origin.transaction_blocks"]
    T7["ethereum_token.erc20_transfer"]
    RPC --> T6
    T6 --> T0
    T5 --> T0
    T5 --> T1
    T6 --> T2
    T5 --> T2
    T4 --> T3
    T1 --> T4
    T6 --> T5
    T2 --> T7
    T4 --> T7
    T3 --> T7
```

## Table Details

| Table | Upstream | Downstream |
|---|---|---|
| `ethereum.blocks` | ethereum_origin.transaction_blocks, ethereum_origin.blocks_receipt | _none_ |
| `ethereum.logs` | ethereum_origin.blocks_receipt | ethereum_decoded.erc20_evt_transfer |
| `ethereum.transactions` | ethereum_origin.transaction_blocks, ethereum_origin.blocks_receipt | ethereum_token.erc20_transfer |
| `ethereum_contract.erc20_tokens` | ethereum_decoded.erc20_evt_transfer | ethereum_token.erc20_transfer |
| `ethereum_decoded.erc20_evt_transfer` | ethereum.logs | ethereum_contract.erc20_tokens, ethereum_token.erc20_transfer |
| `ethereum_origin.blocks_receipt` | ethereum_origin.transaction_blocks | ethereum.blocks, ethereum.logs, ethereum.transactions |
| `ethereum_origin.transaction_blocks` | _none_ (RPC Node)_ | ethereum.blocks, ethereum.transactions, ethereum_origin.blocks_receipt |
| `ethereum_token.erc20_transfer` | ethereum.transactions, ethereum_decoded.erc20_evt_transfer, ethereum_contract.erc20_tokens | _none_ |

## Root tables (no upstream)

- `ethereum_origin.transaction_blocks`

## Leaf tables (no downstream)

- `ethereum.blocks`
- `ethereum_token.erc20_transfer`
