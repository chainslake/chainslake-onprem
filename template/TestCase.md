# Test Case — ethereum_token.erc20_transfer

## Thông tin chung

| Thuộc tính | Giá trị |
|---|---|
| Bảng kiểm tra | `ethereum_token.erc20_transfer` |
| Ngày tạo | 2026-07-26 |
| Version | 1 |
| frequentType | `block` |
| Job script | `chainslake/jobs/ethereum/token/erc20_transfer.sh` |
| SQL file | `chainslake/sql/evm_token/erc20_transfer.sql` |

## Upstream

| Bảng | Loại join | Ghi chú |
|---|---|---|
| `ethereum_decoded.erc20_evt_transfer` | Main source | Bảng chính, mỗi bản ghi = 1 event Transfer ERC-20 |
| `ethereum.transactions` | INNER JOIN | Phải có transaction tương ứng; nếu thiếu → bản ghi bị loại |
| `ethereum_contract.erc20_tokens` | LEFT JOIN | Có thể NULL nếu contract chưa có metadata trong registry |

---

## Nhóm 1: Kiểm tra Schema và Cấu trúc

### TC-1.1: Kiểm tra tồn tại bảng

**Mục đích**: Xác nhận bảng đã được tạo thành công trong data warehouse.

```sql
DESCRIBE ethereum_token.erc20_transfer
```

**Kỳ vọng**: Trả về danh sách 15 cột với đúng kiểu dữ liệu.

### TC-1.2: Kiểm tra kiểu dữ liệu từng cột

**Mục đích**: Đảm bảo schema khớp với thiết kế catalog.

| Cột | Kiểu kỳ vọng | Kiểu thực tế |
|---|---|---|
| `block_date` | `date` | |
| `block_number` | `bigint` | |
| `block_time` | `timestamp` | |
| `updated_time` | `timestamp` | |
| `contract_address` | `string` | |
| `symbol` | `string` | |
| `decimals` | `int` | |
| `tx_hash` | `string` | |
| `evt_index` | `int` | |
| `from` | `string` | |
| `to` | `string` | |
| `value` | `double` | |
| `tx_from` | `string` | |
| `tx_to` | `string` | |
| `tx_method_id` | `string` | |

### TC-1.3: Kiểm tra Partition

**Mục đích**: Xác nhận bảng được partition theo `block_date`.

```sql
SHOW PARTITIONS ethereum_token.erc20_transfer
```

**Kỳ vọng**: Kết quả trả về dạng `block_date=YYYY-MM-DD`.

### TC-1.4: Kiểm tra Index columns

**Mục đích**: Xác nhận 3 cột index đầu tiên đúng thứ tự: `block_date`, `block_number`, `block_time`.

```sql
DESCRIBE EXTENDED ethereum_token.erc20_transfer
```

**Kỳ vọng**: 3 cột đầu tiên theo đúng thứ tự index.

---

## Nhóm 2: Kiểm tra Dữ liệu Cơ bản

### TC-2.1: Kiểm tra số lượng bản ghi tổng

**Mục đích**: Đảm bảo bảng có dữ liệu.

```sql
SELECT count(*) as total_rows FROM ethereum_token.erc20_transfer
```

**Kỳ vọng**: `total_rows > 0`.

### TC-2.2: Kiểm tra khoảng block_number

**Mục đích**: Đảm bảo dữ liệu nằm trong khoảng block hợp lý.

```sql
SELECT
    min(block_number) as min_block,
    max(block_number) as max_block,
    count(*) as total_rows
FROM ethereum_token.erc20_transfer
```

**Kỳ vọng**:
- `min_block` >= 0
- `max_block` > `min_block`
- `total_rows` > 0

### TC-2.3: Kiểm tra phân bổ dữ liệu theo block_date

**Mục đích**: Đảm bảo dữ liệu phân bổ đều theo ngày, không bị thiếu ngày.

```sql
SELECT
    block_date,
    count(*) as row_count,
    min(block_number) as min_block,
    max(block_number) as max_block
FROM ethereum_token.erc20_transfer
GROUP BY block_date
ORDER BY block_date
```

**Kỳ vọng**:
- Mỗi ngày có dữ liệu > 0 bản ghi
- `min_block` và `max_block` tăng dần theo `block_date`
- Không có ngày bị thiếu (gap)

### TC-2.4: Kiểm tra không có bản ghi trùng lặp

**Mục đích**: Đảm bảo mỗi transfer event chỉ xuất hiện 1 lần.

```sql
SELECT
    tx_hash, evt_index, count(*) as cnt
FROM ethereum_token.erc20_transfer
GROUP BY tx_hash, evt_index
HAVING cnt > 1
```

**Kỳ vọng**: Kết quả trả về 0 dòng (không có duplicate).

---

## Nhóm 3: Kiểm tra Logic SQL Transform

### TC-3.1: Kiểm tra INNER JOIN với transactions

**Mục đích**: Xác nhận mỗi bản ghi erc20_transfer đều có transaction tương ứng. Nếu có transfer event mà không match transaction → bị loại (đúng logic INNER JOIN).

```sql
SELECT count(*) as orphan_count
FROM ethereum_decoded.erc20_evt_transfer e
LEFT JOIN ethereum_token.erc20_transfer t
ON e.tx_hash = t.tx_hash AND e.evt_index = t.evt_index
WHERE t.tx_hash IS NULL
AND e.block_number >= 25516917 AND e.block_number <= 25517819
```

**Kỳ vọng**: `orphan_count` = 0 hoặc rất nhỏ (do inner join loại bỏ).

### TC-3.2: Kiểm tra LEFT JOIN với erc20_tokens —_token có metadata

**Mục đích**: Xác nhận token đã có trong registry có symbol và decimals.

```sql
SELECT
    contract_address,
    symbol,
    decimals,
    count(*) as cnt
FROM ethereum_token.erc20_transfer
WHERE symbol IS NOT NULL AND decimals IS NOT NULL
GROUP BY contract_address, symbol, decimals
ORDER BY cnt DESC
LIMIT 10
```

**Kỳ vọng**: Kết quả trả về danh sách token phổ biến (USDC, USDT, WETH, DAI, ...).

### TC-3.3: Kiểm tra LEFT JOIN với erc20_tokens — token chưa có metadata

**Mục đích**: Xác nhận transfer event từ contract chưa có trong erc20_tokens vẫn được giữ lại, nhưng symbol và decimals là NULL.

```sql
SELECT count(*) as null_metadata_count
FROM ethereum_token.erc20_transfer
WHERE symbol IS NULL OR decimals IS NULL
```

**Kỳ vọng**: Nếu > 0 thì là hợp lý (contract chưa register trong registry).

### TC-3.4: Kiểm tra phép tính chuyển đổi value

**Mục đích**: Xác nhận `value = raw_value * 10^(-decimals)` được tính đúng.

```sql
SELECT
    t.contract_address,
    t.symbol,
    t.decimals,
    t.value as converted_value,
    e.value as raw_value,
    CAST(e.value AS DOUBLE) * POW(10, -t.decimals) as expected_value
FROM ethereum_token.erc20_transfer t
JOIN ethereum_decoded.erc20_evt_transfer e
ON t.tx_hash = e.tx_hash AND t.evt_index = e.evt_index
WHERE t.symbol IS NOT NULL
LIMIT 10
```

**Kỳ vọng**: `converted_value` = `expected_value` (sai số < 0.000001 do lỗi làm tròn double).

### TC-3.5: Kiểm tra trường hợp decimals = 0 (token không có decimals)

**Mục đích**: Xác nhận phép tính vẫn đúng khi decimals = 0 (value gốc giữ nguyên).

```sql
SELECT
    contract_address, symbol, decimals,
    value
FROM ethereum_token.erc20_transfer
WHERE decimals = 0
```

**Kỳ vọng**: `value` bằng với raw value từ erc20_evt_transfer (vì `10^0 = 1`).

### TC-3.6: Kiểm tra trường hợp decimals lớn (18 — token phổ biến nhất)

**Mục đích**: Xác nhận phép tính chuyển đổi đúng với token có 18 decimals (ví dụ: WETH, DAI).

```sql
SELECT
    contract_address, symbol, decimals,
    value
FROM ethereum_token.erc20_transfer
WHERE decimals = 18 AND symbol IN ('WETH', 'DAI', 'USDC')
LIMIT 10
```

**Kỳ vọng**: `value` là số thực hợp lý (ví dụ: WETH transfer 1 ETH → value ≈ 1.0).

---

## Nhóm 4: Kiểm tra Tính toàn vẹn Dữ liệu

### TC-4.1: Kiểm tra không có block_number NULL

```sql
SELECT count(*) as null_count
FROM ethereum_token.erc20_transfer
WHERE block_number IS NULL
```

**Kỳ vọng**: `null_count` = 0.

### TC-4.2: Kiểm tra không có tx_hash NULL

```sql
SELECT count(*) as null_count
FROM ethereum_token.erc20_transfer
WHERE tx_hash IS NULL
```

**Kỳ vọng**: `null_count` = 0.

### TC-4.3: Kiểm tra không có from/to NULL

```sql
SELECT count(*) as null_count
FROM ethereum_token.erc20_transfer
WHERE `from` IS NULL OR `to` IS NULL
```

**Kỳ vọng**: `null_count` = 0.

### TC-4.4: Kiểm tra không có value NULL hoặc NaN

```sql
SELECT count(*) as null_count
FROM ethereum_token.erc20_transfer
WHERE value IS NULL OR isNaN(value)
```

**Kỳ vọng**: `null_count` = 0.

### TC-4.5: Kiểm tra block_time >= block_date

**Mục đích**: Đảm bảo block_time nằm trong block_date tương ứng.

```sql
SELECT count(*) as invalid_count
FROM ethereum_token.erc20_transfer
WHERE CAST(block_time AS DATE) != block_date
```

**Kỳ vọng**: `invalid_count` = 0.

### TC-4.6: Kiểm tra contract_address có định dạng hex hợp lệ

```sql
SELECT count(*) as invalid_count
FROM ethereum_token.erc20_transfer
WHERE contract_address IS NOT NULL
AND NOT contract_address RLIKE '^0x[0-9a-fA-F]{40}$'
```

**Kỳ vọng**: `invalid_count` = 0.

### TC-4.7: Kiểm tra tx_from và tx_to có định dạng hex hợp lệ

```sql
SELECT count(*) as invalid_count
FROM ethereum_token.erc20_transfer
WHERE (tx_from IS NOT NULL AND NOT tx_from RLIKE '^0x[0-9a-fA-F]{40}$')
OR (tx_to IS NOT NULL AND NOT tx_to RLIKE '^0x[0-9a-fA-F]{40}$')
```

**Kỳ vọng**: `invalid_count` = 0.

---

## Nhóm 5: Kiểm tra Business Logic

### TC-5.1: Kiểm tra USDC transfer (decimals=6)

**Mục đích**: Xác nhận USDC transfer có value hợp lý. USDC có 6 decimals, nên 1 USDC = 1.0.

```sql
SELECT
    tx_hash, evt_index,
    contract_address, symbol, decimals,
    `from`, `to`, value
FROM ethereum_token.erc20_transfer
WHERE symbol = 'USDC' AND decimals = 6
AND value BETWEEN 100 AND 1000
LIMIT 5
```

**Kỳ vọng**: Kết quả trả về các transfer USDC với value hợp lý (phản ánh đúng giá trị USD).

### TC-5.2: Kiểm tra USDT transfer (decimals=6)

```sql
SELECT
    tx_hash, evt_index,
    contract_address, symbol, decimals,
    `from`, `to`, value
FROM ethereum_token.erc20_transfer
WHERE symbol = 'USDT' AND decimals = 6
AND value > 0
LIMIT 5
```

**Kỳ vọng**: USDT transfer có value > 0, symbol = 'USDT'.

### TC-5.3: Kiểm tra WETH transfer (decimals=18)

```sql
SELECT
    tx_hash, evt_index,
    contract_address, symbol, decimals,
    `from`, `to`, value
FROM ethereum_token.erc20_transfer
WHERE symbol = 'WETH' AND decimals = 18
AND value BETWEEN 0.01 AND 100
LIMIT 5
```

**Kỳ vọng**: WETH transfer có value > 0, symbol = 'WETH'.

### TC-5.4: Kiểm tra DAI transfer (decimals=18)

```sql
SELECT
    tx_hash, evt_index,
    contract_address, symbol, decimals,
    `from`, `to`, value
FROM ethereum_token.erc20_transfer
WHERE symbol = 'DAI' AND decimals = 18
AND value > 0
LIMIT 5
```

**Kỳ vọng**: DAI transfer có value > 0, symbol = 'DAI'.

### TC-5.5: Kiểm tra from ≠ to (không transfer cho chính mình)

**Mục đích**: Phần lớn transfers có from ≠ to. Nếu from = to vẫn hợp lý nhưng ít gặp.

```sql
SELECT count(*) as self_transfer_count
FROM ethereum_token.erc20_transfer
WHERE `from` = `to`
```

**Kỳ vọng**: `self_transfer_count` = 0 hoặc rất nhỏ so với tổng.

### TC-5.6: Kiểm tra tx_method_id có hợp lệ

**Mục đích**: ERC-20 transfer thường có method_id = `0xa9059cbb` (transfer) hoặc `0x23b872dd` (transferFrom).

```sql
SELECT
    tx_method_id,
    count(*) as cnt
FROM ethereum_token.erc20_transfer
GROUP BY tx_method_id
ORDER BY cnt DESC
LIMIT 10
```

**Kỳ vọng**: Method_id phổ biến nhất là `0xa9059cbb` và `0x23b872dd`.

### TC-5.7: Kiểm tra tx_to = contract_address

**Mục đích**: Trong trường hợp, `tx_to` trong transaction = `contract_address` của token (vì user gọi function trên contract token).

```sql
SELECT count(*) as mismatch_count
FROM ethereum_token.erc20_transfer
WHERE tx_to != contract_address
```

**Kỳ vọng**: `mismatch_count` = 0 hoặc rất nhỏ (trường hợp multisig, proxy, batch transfer có thể lệch).

---

## Nhóm 6: Kiểm tra Range và Partition

### TC-6.1: Kiểm tra block_number nằm trong khoảng từ/to của SQL filter

**Mục đích**: Xác nhận mỗi bản ghi đều nằm trong khoảng block mà job đã xử lý.

```sql
SELECT
    min(block_number) as min_block,
    max(block_number) as max_block,
    count(*) as total
FROM ethereum_token.erc20_transfer
```

**Kỳ vọng**: Kết quả khớp với catalog (fromBlock=25516917, toBlock=25517819).

### TC-6.2: Kiểm tra phân bổ bản ghi theo partition

**Mục đích**: Đảm bảo dữ liệu phân bổ đều, không partition nào quá lớn hoặc quá nhỏ.

```sql
SELECT
    block_date,
    count(*) as row_count,
    count(DISTINCT block_number) as block_count
FROM ethereum_token.erc20_transfer
GROUP BY block_date
ORDER BY block_date
```

**Kỳ vọng**:
- Mỗi partition có dữ liệu
- Số block_count / ngày ≈ 900–1100 block/ngày (≈ 12s/block × 86400s/ngày)

### TC-6.3: Kiểm tra block_number tăng dần trong cùng partition

```sql
SELECT count(*) as disorder_count
FROM (
    SELECT block_number,
           LAG(block_number) OVER (PARTITION BY block_date ORDER BY block_number) as prev_block
    FROM ethereum_token.erc20_transfer
) t
WHERE prev_block IS NOT NULL AND block_number <= prev_block
```

**Kỳ vọng**: `disorder_count` = 0.

---

## Nhóm 7: Kiểm tra Edge Cases

### TC-7.1: Kiểm tra token có decimals rất lớn (> 30)

**Mục đích**: Một số token non-standard có decimals rất lớn. Phép tính `pow(10, -decimals)` có thể tạo ra số rất nhỏ hoặc 0.

```sql
SELECT
    contract_address, symbol, decimals,
    count(*) as cnt
FROM ethereum_token.erc20_transfer
WHERE decimals > 30
GROUP BY contract_address, symbol, decimals
```

**Kỳ vọng**: Nếu có → xác nhận value đã bị làm tròn về 0 hoặc rất nhỏ (hợp lý về mặt toán).

### TC-7.2: Kiểm tra value = 0

**Mục đích**: Có thể có transfer event với value = 0 (burn token, hoặc test transaction).

```sql
SELECT count(*) as zero_value_count
FROM ethereum_token.erc20_transfer
WHERE value = 0
```

**Kỳ vọng**: `zero_value_count` = 0 hoặc rất nhỏ.

### TC-7.3: Kiểm tra value < 0 (bất thường)

```sql
SELECT count(*) as negative_count
FROM ethereum_token.erc20_transfer
WHERE value < 0
```

**Kỳ vọng**: `negative_count` = 0 (ERC-20 transfer value luôn >= 0).

### TC-7.4: Kiểm tra同一 block_number có nhiều transfers

**Mục đích**: Một block có thể chứa nhiều transfer events.

```sql
SELECT
    block_number,
    count(*) as transfer_count
FROM ethereum_token.erc20_transfer
GROUP BY block_number
ORDER BY transfer_count DESC
LIMIT 10
```

**Kỳ vọng**: Kết quả trả về các block có nhiều transfers (normal behavior).

### TC-7.5: Kiểm tra同一 tx_hash có nhiều transfers

**Mục đích**: Một transaction có thể chứa nhiều transfer events (batch transfer, multicall).

```sql
SELECT
    tx_hash,
    count(*) as transfer_count
FROM ethereum_token.erc20_transfer
GROUP BY tx_hash
HAVING transfer_count > 1
ORDER BY transfer_count DESC
LIMIT 10
```

**Kỳ vọng**: Kết quả trả về các transaction có nhiều transfers (hợp lý, đặc biệt trên DEX).

---

## Nhóm 8: Kiểm tra Consistency với Upstream

### TC-8.1: Kiểm tra số lượng bản ghi khớp giữa erc20_transfer và erc20_evt_transfer

**Mục đích**: Xác nhận số lượng transfer events trong erc20_transfer = số lượng trong erc20_evt_transfer (trong cùng khoảng block).

```sql
SELECT
    (SELECT count(*) FROM ethereum_decoded.erc20_evt_transfer
     WHERE block_number >= 25516917 AND block_number <= 25517819) as upstream_count,
    (SELECT count(*) FROM ethereum_token.erc20_transfer) as token_count
```

**Kỳ vọng**: `upstream_count` = `token_count` (hoặc rất gần nhau, do inner join có thể loại bỏ một vài bản ghi không match transaction).

### TC-8.2: Kiểm tra symbol và decimals khớp với erc20_tokens

```sql
SELECT
    t.contract_address,
    t.symbol as token_symbol,
    t.decimals as token_decimals,
    c.symbol as contract_symbol,
    c.decimals as contract_decimals
FROM ethereum_token.erc20_transfer t
LEFT JOIN ethereum_contract.erc20_tokens c
ON t.contract_address = c.contract_address
WHERE t.symbol != c.symbol OR t.decimals != c.decimals
```

**Kỳ vọng**: Kết quả trả về 0 dòng (tất cả symbol/decimals khớp).

### TC-8.3: Kiểm tra tx_from, tx_to khớp với transactions

```sql
SELECT
    t.tx_hash,
    t.tx_from as token_tx_from,
    t.tx_to as token_tx_to,
    tx.`from` as tx_table_from,
    tx.`to` as tx_table_to
FROM ethereum_token.erc20_transfer t
JOIN ethereum.transactions tx
ON t.tx_hash = tx.hash
WHERE t.tx_from != tx.`from` OR t.tx_to != tx.`to`
```

**Kỳ vọng**: Kết quả trả về 0 dòng.

---

## Tổng hợp

| Nhóm | Số test case | Ghi chú |
|---|---|---|
| 1. Schema & Cấu trúc | 4 | Kiểm tra bảng, kiểu dữ liệu, partition, index |
| 2. Dữ liệu Cơ bản | 4 | Kiểm tra tồn tại, khoảng block, phân bổ, duplicate |
| 3. Logic SQL Transform | 6 | Kiểm tra JOIN, phép tính value, edge cases decimals |
| 4. Tính toàn vẹn | 7 | Kiểm tra NULL, format hex, block_time vs block_date |
| 5. Business Logic | 7 | Kiểm tra token cụ thể (USDC/USDT/WETH/DAI), method_id |
| 6. Range & Partition | 3 | Kiểm tra block range, phân bổ partition, thứ tự block |
| 7. Edge Cases | 5 | Kiểm tra decimals lớn, value = 0, value < 0, batch transfer |
| 8. Consistency Upstream | 3 | Kiểm tra khớp dữ liệu với upstream tables |
| **Tổng cộng** | **39** | |

## Cách chạy Test

1. Kết nối vào Spark SQL (truy cập qua container hoặc JDBC)
2. Chạy từng test case theo thứ tự nhóm
3. Ghi kết quả thực tế vào cột "Kết quả thực tế" (thêm cột khi sử dụng)
4. Nếu test case fail → Phân tích nguyên nhân, ghi chú tại mục "Ghi chú" (thêm cột khi sử dụng)
