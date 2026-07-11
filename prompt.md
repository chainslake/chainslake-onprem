Đọc file README.md để hiểu bối cảnh dự án
- Tôi cần bảng dữ liệu ethereum_token.erc20_transfer, bảng này có input từ 2 bảng: ethereum.transactions, ethereum_decoded.erc20_evt_transfer
- 2 bảng input sẽ được join với nhau theo block_number, tx_hash (từ transfer) - hash (transactions)
- lấy tất cả các column của bảng transfer, lấy thêm các thông tin sau từ bảng transactions:
    - from: đổi tên thành tx_from
    - to: đổi tên thành tx_to 
    - method_id: đổi tên thành tx_method_id
- Yêu cầu code tuân thủ convention của dự án
- Sau khi dev xong thì để tôi review code trước khi test job bằng cách run thủ công

===

Đọc file README.md để hiểu bối cảnh dự án
- Trong data warehouse hiện tại đang có bảng ethereum_token.erc20_transfer, tuy nhiên hiện tại bảng này chưa có thông tin về token_symbol tôi muốn bạn sửa code job của bảng này để bổ sung thêm input từ bảng ethereum_contract.erc20_tokens (join thông qua contract_address)
- Kết quả thêm symbol và decimals từ erc20_tokens vào bảng erc20_transfer, ngoài ra tính lại value theo công thức sau:
    value = value * 10 ^ -decimals
- Yêu cầu code tuân thủ convention của dự án
- Sau khi dev xong thì để tôi review code trước khi test job bằng cách run thủ công

===

- Tôi đã viết 1 script python get_example_table.py để lấy ra 1 bản ghi từ 1 bảng dữ liệu trong data warehouse để phục vụ mục đích lấy schema và example từ 1 bảng, tôi cần bạn viết thêm cho tôi một số script nữa như sau:
    - Script drop 1 bảng dữ liệu, yêu cầu khi gọi script này sẽ cần người dùng confirm việc xóa
    - Script thực thi 1 câu truy vấn trên data warehouse:
        - cần kiểm tra nếu câu truy vấn nếu có thay đổi (xóa, sửa) thì sẽ bị chặn không được thực hiện
        - câu truy vấn yêu cầu phải có limit số bản ghi trả về
- Sau khi làm xong hãy viết cho tôi 1 file README.md hướng dẫn sử dụng cho cả 3 script (bao gồm script get_example_table.py)

===

Đọc file README.md để hiểu bối cảnh dự án
- Tôi muốn một Data Agent có thể giúp tôi maintain dự án này, có khả năng tự động học hỏi, làm giàu kỹ năng theo thời gian. Hãy viết cho tôi một AGENT_INSTRUCTION.md để làm điểm bắt đầu cho Agent này.
- Ngoài các thư mục thuộc dự án này, Agent được quản lý thêm 2 thư mục nữa:
    - script: Đây là thư mục chứa các python script .py và 1 file index.md chứa thông tin mô tả ngắn gọn về mỗi script trong thư mục
        - Trong quá trình làm việc, nếu Agent thấy rằng có nhiệm vụ nào đó lặp lại hoặc cần những tool đặc biệt (ví dụ call api...) nó sẽ tự động viết script python đó để sử dụng, sau đó đưa mô tả ngắn gọn về tool đó vào file index.md để lần sau chỉ cần đọc file index.md là có thể tái sử dụng lại script này mà không cần viết lại. 
    - skill: Đây là nơi chứa skill hay chính là kinh nghiệm của Agent trong quá trình làm việc, mỗi skill là 1 file .md và có 1 file index.md chứa mô tả ngắn gọn về tất cả các skill
        - Trong quá trình sử dụng, người dùng sẽ viết prompt để yêu cầu agent thực thi nhiệm vụ, sau khi thực thi xong nhiệm vụ thành công, Agent sẽ chủ động viết lại skill cho nhiệm vụ đó, để lần sau khi người dùng yêu cầu, Agent có thể thực hiện ngay mà không cần hướng dẫn của người dùng nữa
- toàn bộ script và skill đều do Agent chủ động và tự động viết mà không cần sự yêu cầu trực tiếp từ người dùng, múc đích là để Agent tự làm giàu tool và kỹ năng từ đó phục vụ người dùng tốt hơn.

===

Đọc file AGENT_INSTRUCTION.md để nắm được bối cảnh
- Nhiệm vụ của bạn là giúp tôi xây dựng một data pipeline mới cho BNB chain, làm tương tự như ethereum
- Để BNB chain có thể hoạt động được thì bạn cần phải tìm được danh sách RPC để đưa vào file chainslake-run/.env (tương tự như ETHEREUM_RPCS)
    - Cách làm như sau:
        - Lấy danh sách các rpc free từ trang: https://chainlist.org/rpcs.json
        - Lấy danh sách RPC ở chain name: BNB Smart Chain Mainnet
        - với mỗi RPC cần kiểm tra xem RPC đó có đáp ứng được yêu cầu sử dụng hay không bằng cách call thử các api sau:
            - API lấy latest block
            ```sh
            curl -X POST "<<RPC cần kiểm tra>>" \
                -H "Content-Type: application/json" \
                -d '{
                "jsonrpc": "2.0",
                "method": "eth_blockNumber",
                "params": [],
                "id": 1
            }'
            ```
            output cần trả về ví dụ như sau:
            ```json
            {
                "jsonrpc": "2.0",
                "id": 1,
                "result": "0x15536ee"
            }
            ```
            - API lấy transaction_blocks (dùng cho bảng _origin.transaction_blocks), lấy result từ bước trên để gọi api
            ```sh     
            curl -X POST "<<RPC cần kiểm tra>>" \
            -H "Content-Type: application/json" \
            -d '{
            "jsonrpc": "2.0",
            "method": "eth_getBlockByNumber",
            "params": [
                "0x15536ee",
                true
            ],
            "id": 1
            }'
            ```
            Verify kết quả trả về có format như sau:
            ```json
            {
                "result": {
                    var number: String,
                    var hash: String,
                    var parentHash: String,
                    var nonce: String,
                    var sha3Uncles: String,
                    var logsBloom: String,
                    var transactionsRoot: String,
                    var stateRoot: String,
                    var receiptRoot: String,
                    var miner: String,
                    var mixHash: String,
                    var difficulty: String,
                    var totalDifficulty: String,
                    var extraData: String,
                    var size: String,
                    var gasLimit: String,
                    var gasUsed: String,
                    var timestamp: String,
                    var transactions: Array[{
                        var hash: String,
                        var nonce: String,
                        var blockHash: String,
                        var blockNumber: String,
                        var transactionIndex: String,
                        var from: String,
                        var to: String,
                        var value: String,
                        var gasPrice: String,
                        var gas: String,
                        var input: String,
                        var r: String,
                        var s: String,
                        var type: String
                    }]
                }
            }
            ```
            - API lấy blocks receipt dùng cho bảng origin.blocks_receipt, lấy latest block để gọi api
            ```sh
            curl -X POST "<<RPC cần check>>" \
            -H "Content-Type: application/json" \
            -d '{
            "jsonrpc": "2.0",
            "method": "eth_getBlockReceipts",
            "params": [
                "0x15536ee"
            ],
            "id": 1
            }'
            ```
            Verify kết quả trả về có format như sau:
            ```json
            {
                "result": Array[{
                    var blockHash: String,
                    var blockNumber: String,
                    var contractAddress: String,
                    var cumulativeGasUsed: String,
                    var effectiveGasPrice: String,
                    var from: String,
                    var gasUsed: String,
                    var to: String,
                    var status: String,
                    var transactionHash: String,
                    var transactionIndex: String,
                    var `type`: String,
                    var logsBloom: String,
                    var logs: Array[{
                        var address: String,
                        var topics: Array[String],
                        var data: String,
                        var blockNumber: String,
                        var transactionHash: String,
                        var transactionIndex: String,
                        var blockHash: String,
                        var blockTimestamp: String,
                        var logIndex: String,
                        var removed: Boolean
                    }]
                }]
            }
            ```
    - Các RPC sau khi pass check thì sẽ được đưa vào BNB_RPCS để job sử dụng

=== 

Đọc file AGENT_INSTRUCTION.md để nắm được bối cảnh
- Hãy cài đặt Chainslake data warehouse
- hãy giúp tôi setup tài khoản admin cho Metabase luôn, 
- Tiếp theo sau đó start workflow của Ethereum (chỉ chạy 1 lần)
- Kiểm tra dữ liệu sau của các bảng sau khi chạy

- Tôi tin rằng bạn đã có nhiều kinh nghiệm khi xử lý nhiệm vụ này, vì vậy hãy viết lại chúng thành script và skill để sử dụng về sau
- Tôi nghĩ rằng mật khẩu và account login vào metabase không nên được hard trực tiếp vào trong script như vậy, hãy bỏ nó vào file .env, đừng quên cho vào .gitignore để không đẩy thông tin nhạy cảm lên git

===

Đọc file AGENT_INSTRUCTION.md để nắm được bối cảnh
- Tôi muốn bạn viết cho tôi một số tool query để hỗ trợ maintain cho datawarehouse như sau:
    - tool kiểm tra properties của bảng:
        - Cách thực hiện: gọi query sql sử dụng engine spark: "show tblproperties <tên bảng>"
        - Kết quả sẽ cho biết các thuộc tính của bảng này, trong đó có các thuộc tính quan trọng sau:
            - isLock: Cho biết bảng có đang bị khóa không (giá trị 1 hoặc 0), đảm bảo tại 1 thời điểm chỉ có 1 job được ghi data vào bảng, nếu 1 job ghi vào bảng đang log sẽ báo lỗi Table is Lock
            - frequenceType: frequenceType của bảng, có thể nhận 1 trong các giá trị: block, hour, minute, day
            - fromBlock, toBlock: Nếu frequenceType là block thì sẽ có 2 giá trị này, 
                - cho biết bảng đang có data từ block nào đến block nào
                - các giá trị này chỉ được update xuống nếu việc ghi thành công (đảm bảo dữ liệu chính xác cho downstream sử dụng)
                - các job downstream sẽ dựa vào fromBlock và toBlock để tính toán giá trị from, to phù hợp khi chạy
            - fromEpochSecond, toEpochSecond: tính năng tương tự như fromBlock, toBlock nhưng dùng cho các bảng có frequenceType là minute, hour, day. sử dụng đơn vị giây (Second) thay vì block
    - tool mở khóa bảng:
        - Cách thực hiện: gọi sql sử dụng engine spark: "alter table <tên bảng> set tblproperties (isLock=0)"
        - Lưu ý:
            - tool được sử dụng khi job ghi dữ liệu vào bảng bị lỗi, khi chạy lại báo lỗi Table is Lock (do bảng chưa được mở khóa ở lần chạy trước)
            - chỉ sử dụng tool này khi biết chắc chắn không còn job nào đang ghi dữ liệu vào bảng

===

Đọc file AGENT_INSTRUCTION.md để nắm được bối cảnh
- Tôi cần upload file data/eth_etf_address.csv vào data warehouse, các bước làm như sau:
    - Tạo 1 schema mới với tên là ext_upload (nếu chưa có) sử dụng query engine spark:
        SQL: `create schema ext_upload`
    - Copy file vào node01 sau đó sử dụng hdfs put (bên trong docker node01) để đẩy nó lên hdfs
        script: `hdfs dfs -put eth_etf_address.csv /user/hive/warehouse/ext_upload.db/eth_etf_address/`
    - Tạo table, sử dung SQL với engine spark:
       ```sql
       CREATE EXTERNAL TABLE ext_upload.eth_etf_address (
            issuer STRING,
            address STRING,
            etf_ticker STRING,
            track_inflow STRING,
            track_outflow STRING,
            inverse_values STRING
        )
        ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
        WITH SERDEPROPERTIES (
            "separatorChar" = ",",
            "quoteChar"     = "\""
        )
        STORED AS TEXTFILE
        LOCATION 'hdfs:///user/hive/warehouse/ext_upload.db/eth_etf_address/';
       ``` 
    - query thử bảng xem đã được chưa
- Sau khi xong thì viết lại skill, script để tái sử dụng
- vì thư mục chainslake đã được mount vào trong node01 rồi, nên có thể bỏ qua bước copy vào node01
- thay vào đó hãy tạo 1 thư mục mới là ext_upload trong thư mục chainslake, để người dùng bỏ file họ muốn upload lên vào đó