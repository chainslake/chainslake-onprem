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

