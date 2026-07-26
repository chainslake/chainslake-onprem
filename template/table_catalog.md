# [schema].[table_name]

## Trạng thái

<Trình bày các thông tin dưới đây dưới dạng bảng>

- Ngày tạo
- Ngày update gần nhất
- Số bản ghi
- Số file
- Dung lượng
- frequentType
- fromBlock
- toBlock
- fromEpochSecond
- toEpochSecond

## Lineage

- Upstream tables: Danh sách listInputTables
- Downstream tables: Chỗ này tính toán để ra được danh sách donwstream dựa vào listInputTables của tất cả các bảng  

## Schema 

Show danh sách column, type, example thành 1 bảng thông tin

## SQL Transform <Nếu có >

Show code SQL trong sqlSource, lưu ý cần thực hiện 1 số replace sau:
    - @ -> $
    - [nl] -> \n
    - ` -> '

```sql
<Cho code vào đây>
```

## ABI <Nếu có>

Mỗi ABI group hiển thị dưới heading `### <tên_abi>`.
Mỗi event/function hiển thị dưới heading `####` với signature, kèm block code JSON riêng.

Ví dụ:
### erc20

#### `Transfer(indexed address from, indexed address to, uint256 value)` — event

```json
{
  "anonymous": false,
  "inputs": [...],
  "name": "Transfer",
  "type": "event"
}
```

#### `balanceOf(address _owner) returns (uint256)` — view function

```json
{
  "constant": true,
  "name": "balanceOf",
  ...
}
```