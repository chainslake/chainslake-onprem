# Chainslake Job Mechanics — Guide Book

Tài liệu này mô tả cơ chế hoạt động bên trong của các job trong hệ thống Chainslake, giúp người dùng và Agent hiểu rõ cách dữ liệu được xử lý, theo dõi và đảm bảo tính chính xác — từ đó cấu hình pipeline một cách chính xác.

---

## Mục lục

1. [Nguyên tắc cơ bản: 1 Job = 1 Bảng](#1-nguyên-tắc-cơ-bản-1-job--1-bảng)
2. [Bảng Properties — Cơ chế theo dõi dữ liệu](#2-bảng-properties--cơ-chế-theo-dõi-dữ-liệu)
3. [Upstream — Mạng lưới phụ thuộc giữa các bảng](#3-upstream--mạng-lưới-phụ-thuộc-giữa-các-bảng)
4. [Cơ chế tính toán khoảng dữ liệu](#4-cơ-chế-tính-toán-khoảng-dữ-liệu)
5. [Hai loại bảng: Block-based và Time-based](#5-hai-loại-bảng-block-based-đi-time-based)
6. [Cơ chế xử lý lỗi và đảm bảo dữ liệu](#6-cơ-chế-xử-lý-lỗi-và-đảm-bảo-dữ-liệu)
7. [Tóm tắt flow chạy của một job](#7-tóm-tắt-flow-chạy-của-một-job)
8. [Ví dụ thực tế](#8-ví-dụ-thực-tế)

---

## 1. Nguyên tắc cơ bản: 1 Job = 1 Bảng

Mỗi job trong hệ thống Chainslake được thiết kế để đẩy dữ liệu vào **duy nhất một bảng** trong data warehouse. Đây là nguyên tắc nền tảng giúp:

- Theo dõi chính xác tiến trình xử lý của từng bảng
- Quản lý dependencies giữa các bảng một cách rõ ràng
- Khôi phục dữ liệu khi gặp lỗi mà không ảnh hưởng đến các bảng khác

Khi cấu hình một job mới, bạn cần xác định rõ **đầu ra** (output table) của job đó là bảng nào. Toàn bộ logic xử lý sẽ xoay quanh việc biến đổi dữ liệu từ các bảng input sang bảng output duy nhất đó.

---

## 2. Bảng Properties — Cơ chế theo dõi dữ liệu

### 2.1 Khái niệm

Mỗi bảng trong data warehouse không chỉ lưu trữ dữ liệu business mà còn lưu trữ **metadata** dưới dạng **properties**. Các properties này là chìa khóa giúp hệ thống biết được dữ liệu trong bảng đã được xử lý đến đâu.

### 2.2 Các thuộc tính theo dõi khoảng dữ liệu

Tùy thuộc vào loại bảng (xem [Phần 5](#5-hai-loại-bảng-block-based-đi-time-based)), hệ thống sử dụng một trong hai cặp thuộc tính:

| Cặp thuộc tính | Áp dụng cho | Mô tả |
|---|---|---|
| `fromBlock`, `toBlock` | Bảng `frequentType=block` | Khoảng block_number dữ liệu hiện có trong bảng |
| `fromEpochSecond`, `toEpochSecond` | Bảng `frequentType=minute/hour/day` | Khoảng thời gian (epoch seconds) dữ liệu hiện có trong bảng |

### 2.3 Khi nào properties được cập nhật

Properties chỉ được cập nhật **sau khi dữ liệu đã được ghi thành công vào bảng** trong một vòng lặp (partition). Cụ thể:

```
Job bắt đầu chạy
    │
    ▼
Đọc properties của bảng output (nếu bảng đã tồn tại)
    │
    ▼
Tính toán khoảng dữ liệu cần xử lý
    │
    ▼
Xử lý và ghi dữ liệu (write to table)
    │
    ├── Thành công → Cập nhật properties (from/toBlock hoặc from/toEpochSecond)
    │
    └── Thất bại → Properties KHÔNG thay đổi
```

**Tại sao phải ghi thành công mới update properties?**

Nếu properties được cập nhật trước khi ghi xong, và job bị crash giữa chừng, thì ở lần chạy sau hệ thống sẽ tin rằng dữ liệu đã được xử lý xong → **dữ liệu bị thiếu** mà không có cơ chế tự sửa. Việc cập nhật sau khi ghi đảm bảo rằng properties luôn phản ánh chính xác dữ liệu thực tế trong bảng.

---

## 3. Upstream — Mạng lưới phụ thuộc giữa các bảng

### 3.1 Khái niệm Upstream

Mỗi bảng (trừ các **bảng origin** — bảng đầu nguồn lấy trực tiếp từ RPC) đều có một danh sách các bảng input mà nó phụ thuộc vào. Danh sách này được gọi là **upstream**.

Upstream được khai báo trong file `.sql` thông qua thuộc tính `list_input_tables`:

```sql
frequent_type=block
list_input_tables=${chain_name}_origin.transaction_blocks,${chain_name}_origin.blocks_receipt
output_table=${chain_name}.blocks
```

Trong ví dụ trên, bảng `ethereum.blocks` có upstream là:
- `ethereum_origin.transaction_blocks`
- `ethereum_origin.blocks_receipt`

### 3.2 Upstream được lưu ở đâu

Khi job chạy, danh sách upstream được set vào **properties của bảng output**. Thông tin này giúp:

- Hệ thống (và người dùng) có thể truy vết nguồn gốc dữ liệu (data lineage)
- Các job downstream biết được dependencies của mình
- Agent có thể tự động xây dựng graph phụ thuộc

### 3.3 Bảng origin

Bảng origin là các bảng **đầu nguồn** trong pipeline, dữ liệu được lấy trực tiếp từ RPC node của blockchain. Các bảng này **không có upstream** vì chúng là điểm bắt đầu của toàn bộ chuỗi xử lý.

Trong hệ thống hiện tại, các bảng origin thường nằm trong schema `<chain_name>_origin`, ví dụ:
- `ethereum_origin.transaction_blocks`
- `ethereum_origin.blocks_receipt`

---

## 4. Cơ chế tính toán khoảng dữ liệu

### 4.1 Đọc properties khi job bắt đầu

Khi một job được chạy, trước khi xử lý dữ liệu, hệ thống thực hiện các bước sau:

1. **Đọc properties của bảng output** — để biết dữ liệu trong bảng hiện tại đang ở khoảng nào (from/to)
2. **Đọc properties của tất cả các bảng upstream** — để biết dữ liệu trong các bảng input đã được xử lý đến đâu

### 4.2 Nguyên tắc tính toán khoảng

Hệ thống tính toán khoảng dữ liệu cần xử lý trong lần chạy hiện tại dựa trên nguyên tắc: **phải có đủ dữ liệu từ tất cả các bảng upstream**.

Điều này có nghĩa là khoảng dữ liệu mà job sẽ xử lý phải là **giao (intersection)** của khoảng dữ liệu khả dụng trên tất cả upstream, đồng thời phải **mở rộng** so với khoảng hiện tại của bảng output (để xử lý dữ liệu mới).

### 4.3 Hỗ trợ cả backward và forward

Hệ thống hỗ trợ hai chiều xử lý:

| Chế độ | Mô tả | Ví dụ |
|---|---|---|
| `backward` | Xử lý từ block mới nhất về quá khứ | Bảng output có data đến block 1000, upstream có data đến block 1100 → xử lý block 1001–1100 |
| `forward` | Xử lý từ quá khứ đến block mới nhất | Bảng output có data đến block 1000, upstream có data đến block 1100 → xử lý block 1001–1100 |

Trong cả hai trường hợp, hệ thống luôn đảm bảo rằng khoảng dữ liệu được xử lý có đủ data từ **tất cả** các bảng upstream.

### 4.4 Xử lý upstream có khoảng dữ liệu khác nhau

Trong thực tế, các bảng upstream có thể có dữ liệu ở các khoảng khác nhau. Ví dụ:

```
ethereum_origin.transaction_blocks:  block 0 → 1100  (đã xử lý xong)
ethereum_origin.blocks_receipt:      block 0 → 1050  (đang xử lý, chưa xong)
ethereum.blocks (output):            block 0 → 1000  (đã xử lý xong)
```

Trong trường hợp này, job sẽ tính toán khoảng cần xử lý là block **1001 → 1050** (giao của upstream, mở rộng so với output), vì đây là khoảng mà cả hai upstream đều đã có đủ dữ liệu.

---

## 5. Hai loại bảng: Block-based và Time-based

Về mặt kỹ thuật, bảng được chia thành 2 loại chính dựa trên `frequentType`. Đây là yếu tố quan trọng nhất khi cấu hình job, vì nó xác định cách hệ thống theo dõi dữ liệu và cách xử lý upstream.

### 5.1 Loại 1: `frequentType = block`

**Đặc điểm:**
- Theo dõi dữ liệu bằng **block number** (`fromBlock`, `toBlock`)
- Tất cả các bảng upstream **cũng phải có** `frequentType = block`
- Khoảng dữ liệu được xác định bởi block range

**Khi nào dùng:**
- Bảng dữ liệu cấp block, mỗi bản ghi tương ứng với một block trên blockchain
- Bảng origin (dữ liệu thô từ RPC)
- Các bảng extract/contract/token cần truy xuất chính xác theo block

**Ví dụ — Bảng `ethereum.blocks`:**

```sql
frequent_type=block
list_input_tables=${chain_name}_origin.transaction_blocks,${chain_name}_origin.blocks_receipt
output_table=${chain_name}.blocks
```

Properties theo dõi:
```
fromBlock = 0
toBlock = 19500000
```

Khi chạy lần tiếp theo, hệ thống sẽ xử lý từ block `19500001` trở đi, đảm bảo cả hai upstream đều đã có dữ liệu trong khoảng đó.

### 5.2 Loại 2: `frequentType = minute`, `hour`, hoặc `day`

**Đặc điểm:**
- Theo dõi dữ liệu bằng **thời gian** (`fromEpochSecond`, `toEpochSecond`)
- Các bảng upstream **có thể có bất kỳ frequentType nào**
- Khi upstream có `frequentType = block`, hệ thống cần một **bảng origin reference** để ánh xạ block_number → block_time

**Khi nào dùng:**
- Bảng tổng hợp theo thời gian (phút, giờ, ngày)
- Bảng analytics cần dữ liệu theo khung thời gian

**Ví dụ — Bảng theo ngày:**

```sql
frequent_type=day
list_input_tables=${chain_name}.blocks,${chain_name}.transactions
output_table=${chain_name}.daily_summary
```

Properties theo dõi:
```
fromEpochSecond = 1721942400    (2024-07-26 00:00:00 UTC)
toEpochSecond = 1722028800      (2024-07-27 00:00:00 UTC)
```

### 5.3 Xử lý upstream block-based cho bảng time-based

Khi bảng có `frequentType` là time-based nhưng upstream có `frequentType` là block, hệ thống cần **chuyển đổi block_number → block_time** để xác định khoảng thời gian tương ứng.

Quy trình:

```
1. Đọc properties của upstream (block-based): fromBlock, toBlock
2. Đọc origin_table (cấu hình trong application.properties, thường là <chain>.blocks)
3. Từ origin_table, xác định block_time tương ứng với fromBlock và toBlock
4. Chuyển đổi thành fromEpochSecond và toEpochSecond
5. Tính toán khoảng thời gian cần xử lý
```

Đây là lý do trong `application.properties` có thuộc tính:

```properties
origin_table=ethereum.blocks
```

Thuộc tính này cho biết bảng reference dùng để ánh xạ block → time.

### 5.4 Nguyên tắc "đủ dữ liệu" cho time-based

Đây là nguyên tắc quan trọng nhất khi xử lý bảng time-based:

> **Để xử lý dữ liệu cho một khoảng thời gian nhất định, tất cả các bảng upstream phải có dữ liệu bao trùm khoảng thời gian đó (vượt ra ngoài cả hai phía).**

Ví dụ cụ thể: Bảng có `frequentType = day` muốn xử lý dữ liệu cho **ngày 2024-07-26**:

| Upstream | Khoảng dữ liệu | Đủ cho ngày 2024-07-26? |
|---|---|---|
| `ethereum.blocks` (block-based) | block → time: 2024-07-25 18:00 → 2024-07-26 18:00 | **Có** — bao trùm cả ngày 26 |
| `ethereum.transactions` (block-based) | block → time: 2024-07-25 20:00 → 2024-07-26 06:00 | **Không** — chỉ đến 06:00 ngày 26, thiếu dữ liệu từ 06:00–24:00 |

Trong trường hợp này, job **không thể** xử lý ngày 2024-07-26 vì upstream `transactions` chưa đủ dữ liệu. Job sẽ đợi cho đến khi cả hai upstream đều có dữ liệu vượt ra ngoài ngày 26.

**Tóm lại:** Nguyên tắc này đảm bảo rằng dữ liệu trong bảng time-based luôn **đầy đủ** — không bao giờ có tình trạng dữ liệu bị thiếu do upstream chưa xử lý xong.

---

## 6. Cơ chế xử lý lỗi và đảm bảo dữ liệu

### 6.1 Job thất bại trong khi ghi dữ liệu

Nếu job bị lỗi trong quá trình ghi dữ liệu (ví dụ: crash, OOM, network error), hệ thống xử lý như sau:

```
Lần chạy hiện tại:
    - Dữ liệu đã được ghi một phần vào bảng (có thể bị corrupt)
    - Properties KHÔNG được cập nhật (vì ghi chưa thành công)

Lần chạy tiếp theo:
    1. Hệ thống đọc properties → phát hiện dữ liệu chưa được xác nhận
    2. Kiểm tra xem bảng có dữ liệu "treo" từ lần chạy trước không
    3. Nếu có → XÓA dữ liệu treo đó trước khi ghi dữ liệu mới
    4. Tiến hành xử lý và ghi dữ liệu từ đầu
```

### 6.2 Tại sao phải xóa dữ liệu cũ trước khi ghi mới

Nguyên tắc quan trọng: **dữ liệu trong bảng phải luôn chính xác**. Nếu lần chạy trước crash giữa chừng, dữ liệu trong bảng có thể ở trạng thái không nhất quán (ví dụ: một partition đã ghi, partition khác chưa). Việc xóa dữ liệu cũ đảm bảo rằng sau khi job chạy thành công, bảng chỉ chứa dữ liệu đã được xác nhận là đúng.

### 6.3 Retry mechanism

Hệ thống hỗ trợ cấu hình retry cho mỗi job:

```properties
max_retry=10           # Số lần thử lại tối đa khi một partition gặp lỗi
wait_miliseconds=100   # Thời gian chờ giữa mỗi lần retry
```

---

## 7. Tóm tắt flow chạy của một job

Dưới đây là flow tổng quát khi một job được chạy:

```
┌─────────────────────────────────────────────────────────┐
│                    JOB BẮT ĐẦU                         │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  1. Đọc application.properties                         │
│     → Lấy chain_name, run_mode, origin_table, ...      │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  2. Đọc properties của bảng OUTPUT                     │
│     → Lấy fromBlock/toBlock hoặc from/toEpochSecond    │
│     → Lấy upstream list (nếu bảng đã tồn tại)         │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  3. Đọc properties của tất cả các bảng UPSTREAM        │
│     → Xác định khoảng dữ liệu khả dụng trên mỗi input │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  4. Tính toán khoảng dữ liệu cần xử lý                │
│     → Giao của khoảng upstream                         │
│     → Mở rộng so với khoảng hiện tại của output        │
│     → Nếu frequentType=time và upstream=block:         │
│       dùng origin_table để map block → time            │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  5. Kiểm tra dữ liệu treo từ lần chạy trước           │
│     → Nếu có → Xóa dữ liệu treo                       │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  6. Xử lý dữ liệu theo partition                      │
│     → Chia thành các partition theo number_block_per_   │
│       partition hoặc khoảng thời gian                   │
│     → Xử lý max_number_partition trong mỗi vòng lặp    │
│     → Lặp tối đa max_time_run vòng                     │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  7. GHI DỮ LIỆU VÀO BẢNG                              │
│     → Nếu thành công: CẬP NHẬT properties              │
│     → Nếu thất bại: KHÔNG cập nhật, lần sau sẽ         │
│       quay lại bước 5 và xử lý lại                     │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                    JOB KẾT THÚC                         │
└─────────────────────────────────────────────────────────┘
```

---

## 8. Ví dụ thực tế

### Pipeline Ethereum — Graph phụ thuộc

```
ORIGIN (frequentType=block, không có upstream)
├── ethereum_origin.transaction_blocks
└── ethereum_origin.blocks_receipt

EXTRACT (frequentType=block)
├── ethereum.blocks
│   └── upstream: origin.transaction_blocks, origin.blocks_receipt
├── ethereum.transactions
│   └── upstream: origin.blocks_receipt
└── ethereum.logs
    └── upstream: origin.blocks_receipt

DECODED (frequentType=block)
└── ethereum_decoded.erc20_evt_transfer
    └── upstream: ethereum.logs

CONTRACT (frequentType=block)
└── ethereum_contract.erc20_tokens
    └── upstream: ethereum_decoded.erc20_evt_transfer

TOKEN (frequentType=block)
└── ethereum_token.erc20_transfer
    └── upstream: ethereum.transactions, ethereum_decoded.erc20_evt_transfer,
                  ethereum_contract.erc20_tokens
```

### Ví dụ tính toán khoảng cho `ethereum.blocks`

**Trạng thái hiện tại:**
```
ethereum_origin.transaction_blocks: fromBlock=0, toBlock=19500000
ethereum_origin.blocks_receipt:     fromBlock=0, toBlock=19500000
ethereum.blocks (output):           fromBlock=0, toBlock=19400000
```

**Khi chạy job `ethereum.blocks`:**
1. Upstream khả dụng: block 0 → 19500000 (cả hai đều có)
2. Output hiện tại: block 0 → 19400000
3. Khoảng cần xử lý: block **19400001 → 19500000**
4. Chia thành partition: mỗi partition 300 block → ~333 partitions
5. Xử lý theo `max_number_partition=1`, lặp `max_time_run=1` → xử lý 1 partition mỗi lần chạy

### Ví dụ tính toán khoảng cho bảng time-based

Giả sử có bảng `ethereum.daily_active_contracts` với `frequentType=day`:

**Trạng thái hiện tại:**
```
ethereum.blocks (upstream, block-based):
    fromBlock=0, toBlock=19500000
    → block_time range: 2015-07-30 → 2024-07-26 18:00

ethereum.decoded.erc20_evt_transfer (upstream, block-based):
    fromBlock=0, toBlock=19450000
    → block_time range: 2015-07-30 → 2024-07-25 12:00

ethereum.daily_active_contracts (output, day-based):
    fromEpochSecond → toEpochSecond: 2015-07-30 → 2024-07-24
```

**Khi chạy job:**
1. Upstream `blocks` có data đến 2024-07-26 18:00
2. Upstream `decoded.erc20_evt_transfer` có data đến 2024-07-25 12:00
3. Output đã xử lý đến 2024-07-24
4. Giao upstream: cả hai đều có data đến **2024-07-25 12:00**
5. Job có thể xử lý các ngày **2024-07-25** (vì đã có đủ data cả ngày từ cả hai upstream)
6. **Không thể** xử lý 2024-07-26 vì `erc20_evt_transfer` mới chỉ đến 12:00 ngày 25 → chưa đủ data cho cả ngày 26

---

## Tham chiếu nhanh

| Thành phần | Vai trò |
|---|---|
| `application.properties` | Cấu hình chung: chain_name, run_mode, number_block_per_partition, origin_table, ... |
| File `.sql` header (`list_input_tables`) | Khai báo upstream của bảng output |
| File `.sql` header (`frequent_type`) | Xác định loại bảng: block hoặc time-based |
| File `.sql` header (`output_table`) | Bảng output duy nhất của job |
| File `.sql` body (`${from}`, `${to}`) | Biến động do hệ thống tính toán, không cần set thủ công |
| Properties `fromBlock/toBlock` | Theo dõi khoảng block (block-based) |
| Properties `fromEpochSecond/toEpochSecond` | Theo dõi khoảng thời gian (time-based) |
| `origin_table` trong application.properties | Bảng reference để map block → time (cho time-based job) |
