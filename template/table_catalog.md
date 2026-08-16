# <schema>.<table_name>

> **Template file thiết kế bảng** — dùng cho file `docs/<problem-name>/design/<schema>.<table>.md`.
> Format này **GIỐNG HỆT file thông tin bảng trong `catalog/`** (file do `build_catalog.py` sinh ra).
> Giữ nguyên cấu trúc mục, tiêu đề, bảng biểu, code block; chỉ thay các `<placeholder>`.
> Bảng thiết kế mới: các giá trị chưa xác định ghi `N/A` (bắt buộc có `frequentType`).

## Trạng thái

| Thuộc tính | Giá trị |
|---|---|
| Ngày tạo | <yyyy-mm-dd hh:mm:ss hoặc N/A> |
| Ngày update gần nhất | <yyyy-mm-dd hh:mm:ss hoặc N/A> |
| Số bản ghi | <số hoặc N/A> |
| Số file | <số hoặc N/A> |
| Dung lượng | <ví dụ: 10.0 KB, 5.2 MB, 1.20 GB, hoặc N/A> |
| frequentType | block |
| fromBlock | <block bắt đầu hoặc N/A> |
| toBlock | <block kết thúc hoặc N/A> |
| fromEpochSecond | <epoch second hoặc N/A> |
| toEpochSecond | <epoch second hoặc N/A> |

<!-- frequentType: block, hoặc minute / hour / day.
     Bảng theo dõi bằng block number → điền fromBlock/toBlock.
     Bảng theo dõi bằng thời gian → điền fromEpochSecond/toEpochSecond. -->

## Lineage

- **Upstream tables**: <bảng1>, <bảng2>
- **Downstream tables**: <bảng1>, <bảng2>

<!-- Bảng nguồn RPC (chain origin) không có upstream → ghi: _RPC Node (Blockchain)_
     Bảng không có downstream → ghi: _None_
     Upstream phải khớp với list_input_tables trong Header bên dưới. -->

## Schema

| Column | Type | Index | Partition | Example |
|---|---|---|---|---|
| <column_name> | <type> | <số thứ tự index> | <x hoặc để trống> | `<giá trị ví dụ>` |
| ... | ... | ... | ... | ... |

<!-- Type hợp lệ: string, bigint, int, double, decimal, date, timestamp.
     Index: đánh số thứ tự index bắt đầu từ 1 (thường là block_date, block_number, block_time).
     Partition: đánh dấu x ở cột partition.
     Example: giá trị minh họa dạng `value`. -->

## SQL Transform

### Header

| Key | Value |
|---|---|
| frequent_type | `block` |
| list_input_tables | `<bảng1>,<bảng2>` |
| output_table | `<schema>.<table_name>` |
| partition_by | `<column_partition>` |
| write_mode | `Append` |
| number_index_columns | `<số cột index>` |
| <key khác nếu có> | `<value>` |

<!-- frequent_type: block hoặc time.
     write_mode: Append hoặc Overwrite.
     Job decode (output <chain>_decoded.*): thêm key pre_decode_tables = <tên event>, tên cách nhau dấu phẩy không dấu cách.
     Job contract metadata (output <chain>_contract.*): thêm key register_evm_call = <tên abi>, tên cách nhau dấu phẩy không dấu cách. -->

### SQL Body

```sql
<code SQL đầy đủ; dùng ${from}/${to}, ${table_name},
các biến tham chiếu bảng input đã khai báo trong Header>
```

## ABI

### <tên_abi>

#### `<EventName(indexed type param, ...)>` — event

```json
{
  "anonymous": false,
  "inputs": [
    {
      "indexed": true,
      "name": "<param>",
      "type": "<type>"
    }
  ],
  "name": "<EventName>",
  "type": "event"
}
```

#### `<functionName(params) returns (type)>` — view function

```json
{
  "constant": true,
  "inputs": [],
  "name": "<functionName>",
  "outputs": [
    {
      "name": "",
      "type": "<type>"
    }
  ],
  "payable": false,
  "stateMutability": "view",
  "type": "function"
}
```

<!-- Mục ABI CHỈ có khi bảng dùng decode (pre_decode_tables) hoặc call view function (register_evm_call).
     Mỗi ABI group dưới heading ### <tên_abi>.
     Mỗi event/function dưới heading #### <signature> kèm 1 block JSON riêng (đầy đủ, không dùng dấu ...). -->
