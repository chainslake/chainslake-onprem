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

===

- Đọc file AGENT_INSTRUCTION.md để nắm được bối cảnh
- Hiện tại tôi đang thấy rằng các script và skill để làm tương tác với airflow đang được thực hiện thông qua call HTTP request, tôi nghĩ rằng đây không phải là cách tối ưu dành cho agent, tôi muốn bạn review và sửa lại để sử dụng Airflow CLI

===

- Đọc file AGENT_INSTRUCTION.md để nắm được bối cảnh
- Thực hiện setup metabase
- Tôi muốn thực hiện việc nâng cấp metabase lên phiên bản mới nhất, để Agent có thể sử dụng metabase cli, bạn có thể xóa database metabase cũ trong postgres và tạo lại database mới và set up lại từ đầu sử dụng metabase cli
- update lại skill và script sử dụng metabase cli

=== 

- Tôi muốn bạn viết một skill mới để thực hiện việc cấu hình các tham số cho job hoặc pipeline
- Đây là một nhiệm vụ khó, tuy nhiên rất quan trọng nên bạn cần hiểu rõ và viết lại rõ ràng.
- Nhắc lại về một số tham số cấu hình quan trọng của job:
    - number_block_per_partition: số block cho mỗi partition
    - max_number_partition: Số partition được xử lý trong mỗi vòng lặp
    - max_time_run: Số vòng lặp trong 1 lần chạy job
- Các tham số này có thể được cấu hình trong file application.properties, hoặc cấu hình trực tiếp trong file .sh của job thông qua config, ví dụ: --conf "spark.app_properties.max_number_partition=24", nếu có cả ở 2 nơi thì job sẽ ưu tiên sử dụng giá trị trong file .sh
- Cách chọn tham số:
    - number_block_per_partition:
        - sẽ được chọn riêng cho mỗi chain sao cho mỗi partition sẽ có lượng data khoảng 1 giờ dữ liệu (cần lấy nhiều hơn 1 chút). Có thể tính toán con số này dựa vào các thông tin lấy được từ Internet, tuy nhiên sau đó cần tính toán lại dựa trên block_number và block_time bằng cách count số block trong 1 giờ từ bảng transaction_blocks (lưu ý cần đảm bảo có đủ data trong 1 giờ)
        - Cách tốt nhất là khi setup mới 1 chain, hãy lấy giá trị number_block_per_partition theo thông tin từ Internet, sau đó set max_number_partition và max_time_run rồi chạy job 1 đến 2 lần, sau đó thực hiện tính toán lại số number_block_per_partition cho chính xác (nhớ là cần lấy nhiều hơn 1 chút lý tưởng là 5%, vì số block mỗi giờ của chain thường không cố định).
    - max_number_partition:
        - tham số này cho biết có bao nhiêu partitions được xử lý trong 1 vòng lặp, con số này cần được điều chỉnh để phù hợp với lượng tài nguyên (số thread và lượng memory cung cấp) được cung cấp cho job đó
        - Tài nguyên sẽ được cấp phát dựa vào 2 tham số sau đây của job:
            --master local[2] \ số threads càn nhiều thì sẽ càng có nhiều partitions được xử lý đồng thời
            --driver-memory 4g \ memory cung cấp cần phải nhiều hơn dung lượng data đọc (nếu có) + dung lượng data ghi của job
        - Để tính được memory cần dùng cho job, bạn cần tính xem 1 partition dữ liệu trên bảng có dung lượng bao nhiêu, bằng cách sử dụng câu SQL sau:
            `describe detail <tên bảng>` Sau đó tìm sizeInBytes để biết kích thước thực tế của bảng
        - Lưu ý quan trọng: Đối với các job sử dụng frequent_type là day thì max_number_partition phải >= 24 
    - max_time_run: cho biết số vòng lặp trong 1 lần chạy dữ liệu, hợp lý nhất là chọn sao cho 1 lần chạy xử lý được 1 ngày dữ liệu
- Cấu hình DAG
    - start_date: hãy đặt bằng ngày bắt đầu của chain, ví dụ với Ethereum là ngày 30/07/2015
    - is_paused_upon_creation=True: Để DAG luôn off khi khởi động
    - catchup=False: Để DAG sẽ ko tự động chạy các ngày history
- Lưu ý: Nếu người dùng yêu cầu có data từ 
- Mặc định chúng ta sẽ cấu hình run_mode của cả pipeline là backward, tức là chạy ngược từ hiện tại về quá khứ, sau khi đã đủ dữ liệu đến ngày người dùng cần thì cần chuyển lại cấu hình này về forward. Tuy nhiên thay vì chuyển run_mode thành forward cho tất cả các job trên pipeline thì bạn chỉ cần thay đổi cấu hình này tại job đầu tiên trong pipeline tức là job _origin.transaction_blocks vì khi job này đã bị dừng chạy ngược, các job phía sau dù có backward cũng không thể chạy tiếp về quá khứ được nữa (vì ko có data). Lưu ý rằng cấu hình backward sẽ cho phép job chạy cả tiến và lùi, trong khi forward chỉ cho phép chạy tiến.
- Khi thêm 1 job mới vào DAG, giả sử lúc này DAG đã hoàn thành chạy dữ liệu về quá khứ, như vậy job mới thêm vào phải tự chạy về quá khứ, bạn hãy sử dụng Airflow CLI để chạy backfill cho riêng job mới này.
    
===

Hãy viết cho tôi phần hướng dẫn cài đặt thành 1 skill, để Agent không cần đọc file docker/README.md nữa (vì đây là doc dành cho người dùng)

===

Hãy config giúp tôi để mỗi lần mở opencode lên thì toàn bộ log OPENCODE_LOG_LEVEL=TRACE sẽ được ghi ra file opencode.log của thư mục này 

===

- Tôi muốn chỉnh sửa lại skill Configure Job/Pipeline Parameters như sau:
    - tại bước 4: Cấu hình `start_date` trên DAG
        - Cấu hình start_date mặc định là thời điểm 2 năm kể từ ngày hiện tại
        - phải bổ sung thêm cấu hình catchup=False để DAG không tự động chạy lại từ ngày start_date, vì đã có bước 6 để chạy backfill rồi

=== 

Tôi muốn bạn bổ sung thêm mục Use case trong AGENT_INSTRUCTION.md, để hướng dẫn nhanh cho Agent biết cần gọi các skill nào trong các tình huống sử dụng cụ thể, Use case cũng sẽ được Agent tự động update trong quá trình sử dụng. Sau đây là 1 số Use case:
    - Bắt đầu:
        - Kiểm tra xem hệ thống đã được cài đặt hay chưa? nếu chưa thì hỏi người dùng xem có muốn cài đặt ngay không
        - Nếu đã cài đặt rồi thì kiểm tra xem hệ thống đã được bật lên chưa, toàn bộ service đã hoạt động đầy đủ chưa, nếu chưa thì hỏi người dùng có muốn bật hệ thống lên không
    - Cài đặt hệ thống:
        - Sử dụng skill: Cài đặt Chainslake On-Premises
        - Sau khi cài đặt và khởi động xong thì cho người dùng biết đang có những chain nào đang có sẵn
        - Hỏi người dùng xem họ muốn chạy chain nào hoặc muốn setup một chain mới hay không
    - Setup một chain mới:
        - Sử dụng skill: Add New Chain Pipeline (cần hỏi người dùng xem họ muốn setup chain nào)
        - Sử dụng skill: Configure Job/Pipeline Parameters 
            - Xác định các tham số cấu hình cần thiết cho chain mới

===

- Tôi cần bạn viết một script mới để lấy thông tin hiện trạng về các bảng dữ liệu đang có trong warehouse để cho vào thư mục catalog của dự án này
- Các bước làm như sau:
    - Lấy danh sách tất cả các bảng trong warehouse
        - vì không có câu lệnh SQL nào có thể lấy được hết tất cả bảng nên script cần thực thi 2 câu truy vấn sau
            - `show schemas`: Lấy danh sách tất cả schema trong warehouse (cần bỏ qua schema default)
            - `show tables in [schema_name]`: Lấy danh sách tất cả table trong schema
    - Với mỗi table script cần lấy các thông tin sau:
        - schema của bảng (danh sách column và type) và ví dụ dữ liệu, hãy sử dụng script có sẵn
        - thông tin thuộc tính của bảng, sử dụng script có sẵn
            - Các thuộc tính cần lấy bao gồm:   
                - frequentType
                - fromBlock
                - toBlock
                - fromEpochSecond
                - toEpochSecond
                - listInputTables: cho biết danh sách bảng upstream của bảng này
                - sqlSource: SQL transform của bảng (nếu có)
                - abi: ABI sử dụng trong bảng (nếu có)
        - Các thông tin sizing của bảng
            - số lượng bản ghi hiện tại: sử dụng `select count(*) from [table_name]` để đếm số bản ghi
            - ngày tạo, ngày update, dung lượng (sizeInBytes), số file: Sử dụng `describe detail [table_name]` để lấy
    - Tổng hợp thông tin của mỗi bảng thành 1 tài liệu với tên file là [schema].[table_name].md sử dụng mẫu tại table_template.md
    - Tổng hợp tất cả thông tin về upstream và downstream của tất cả các bảng để tạo 1 tài liệu với tên là lineage.md (cũng đặt trong thư mục catalog) trong tài liệu này thể hiện sự phụ thuộc (lineage) của tất cả các bảng dưới dạng graph trực quan 

- Chúng ta đang có 1 script build_catalog dùng để tạo tài liệu catalog markdown cho toàn bộ bảng trong data warehouse, bao gồm metadata, schema, ví dụ dữ liệu và lineage graph. Tôi muốn bạn sửa script này để cập nhật thêm thông tin vào phần schema cho mỗi tài liệu như sau:
    - Hiện tại bảng trong phần schema đang có Column | Type | Example tôi muốn bổ sung thêm 2 cột nữa sau Type:
        - Index: nhận giá trị là số, bắt đầu từ 1, cho biết thứ tự đánh index của column đó, để có thông tin này cần lấy từ thuộc tính của bảng ra thông tin: delta.dataSkippingNumIndexedCols, thông tin này cho biết có bao nhiêu column được đánh index tính từ column đầu tiên. Nếu column ko được đánh index thì để trống.
        - Partition: để giá trị là x nếu bảng được partition theo column này, để trống với các column còn lại. Danh sách các column được partition có khi gọi truy vấn `describe detail [table_name]` lấy thông tin partitionColumns 
            
===

- Tôi muốn biến Agent hiện tại thành một nhóm Agent hoạt động như một data team thực sự trong đó:
    - Business Analyst Agent
    - Data Architect Agent
    - Developer Agent
    - Tester Agent
    - DataOps Agent
    - Data Analyst Agent
- Hãy tư vấn cho tôi nên triển khai như thế nào với opencode, viết kế hoạch chi tiết triển khai ra file agent_build_plan.md

- Tôi muốn bổ sung thêm 1 vài ý như sau:
    - Tôi muốn các agent sẽ có 1 Thư mục tài liệu chia sẻ chung cho mỗi bài toán mà các agent cùng xử lý
    - Thư mục tài liệu này sẽ do Team lead agent tạo ra trong thư mục docs (nếu thấy cần thiết)
    - Trong thư mục docs còn có một file index.md chứa thông tin mô tả ngắn gọn về mỗi Thư mục tài liệu, để lần sau khi người dùng hỏi đến, nó có thể xác định ngay Thư mục tài liệu cho bài toán đó
    - Đối với các agent khác:
        - Business Analyst Agent:
            - Đây là Agent làm việc trực tiếp với User để tìm hiểu về nhu cầu dữ liệu của User
            - Yêu cầu đối với Agent:
                - Có hiểu biết về lĩnh vực blockchain, dữ liệu blockchain đặc biệt là dữ liệu onchain
                - Có khả năng giao tiếp với User, đặt câu hỏi để từng bước làm rõ nhu cầu của User
            - Nhiệm vụ của Agent
                - Giao tiếp với User để viết tài liệu Data_Requirement.md trong Thư mục tài liệu chung, sử dụng template template/data_requirement.md
                - Tài liệu có thể được update nhiều lần trong suốt quá trình làm việc.
                - Tài liệu sau khi viết xong cần được User review và confirm
                - Nếu trong các lần làm việc sau đó có chỉnh sửa và thay đổi, Agent cần cập nhật lại ngày update và change log cho tài liệu
            - Output của Agent:
                - Data_Requirement.md mô tả về yêu cầu của User
        - Data Architect Agent
            - Agent có nhiệm vụ thiết kế các bảng dữ liệu trong Data warehouse
            - Input của Agent:
                - Thư mục catalog chứa mô tả của tất cả các bảng hiện có trong Data warehouse
                - Thư mục tài liệu chứa file Data_Requirement.md
            - Yêu cầu đối với Agent:
                - Có hiểu biết về toàn bộ các bảng dữ liệu hiện có của Data warehouse thông qua việc đọc mô tả của bảng trong thư mục catalog, trong thư mục này mỗi bảng có 1 file .md (tên file chính là tên bảng) mô tả chi tiết các thông tin về bảng đó, file lineage.md có thông tin về mối quan hệ phụ thuộc giữa các bảng.
                - Nắm rõ quy tắc đặt tên bảng của dự án
                - Có thể đọc hiểu yêu cầu và thiết kế các bảng dữ liệu mới hoặc thay đổi thiết kế bảng dữ liệu đang có để đáp ứng được nhu cầu của người dùng
                - Khi thiết kế Agent cần:
                    - Ưu tiên sự ổn định của hệ thống, hạn chế thay đổi trên những bảng đang có sẵn vì nếu có thay đổi trên những bảng này sẽ cần xóa bảng đi và chạy lại do đó cần đánh giá về chi phí dựa vào kích thước hiện tại của bảng (càng lớn thì chi phí càng cao)
                    - Nếu xây dựng bảng mới thì bảng mới ngoài việc đáp ứng yêu cầu thì cần có có khả năng tái sử dụng tốt nếu có thể
            - Các skill và script mà Agent được dùng:
                - Script build_catalog khi cần lấy thông tin bảng mới nhất
                - Có thể gọi script query trên data warehouse
            - Nhiệm vụ của Agent:
                - Viết tài liệu thiết kế bảng theo mẫu giống như các tài liệu đang có trong thư mục catalog. 
                    - Với các bảng đã có mà muốn chỉnh sửa thì copy tài liệu của bảng đó từ thư mục catalog sang sau đó chỉnh sửa trên tài liệu copy này
                    - Với các bảng cần tạo mới thì tạo tài liệu mới theo mẫu giống như các tài liệu đang có trong thư mục catalog, lưu ý cần có đầy đủ thông tin ở các mục như:
                        - Trạng thái: cần có frequentType để biết tần suất update của bảng 
                        - Lineage: để biết bảng sẽ đọc dữ liệu từ những bảng nào, và sẽ là input cho cho bảng nào sau nó (nếu có)
                        - Schema: để biết các column của bảng, type và ví dụ (có thể thực thi câu query ở phần SQL Transform để có thông tin này)
                        - SQL tranform: Logic SQL transform để tạo ra bảng
                        - ABI: ABI contract được sử dụng (nếu có)
                - Trong trường hợp Agent nhận thấy rằng các bảng hiện tại là đủ để đáp ứng yêu cầu, nó có thể trả lại mà không có bất kỳ thay đổi nào
            - Output của Agent:
                - Thư mục tài liệu sau khi đã được bổ sung thêm thiết kế của các bảng cần làm hoặc cần chỉnh sửa (nếu có)
        
        - Developer Agent:
            - Agent có nhiệm vụ phát triển các job để tạo ra các bảng theo thiết kế 
            - Đầu vào của Agent:
                - Thư mục tài liệu sau khi đã được Data Architect thiết kế. Lưu ý nếu không có bảng nào được thiết kế mới thì Agent này có thể kết thúc ngay.
            - Yêu cầu của Agent:
                - Có khả năng đọc hiểu tài liệu thiết kế từ Data Architect
                - Nắm rõ cấu trúc thư mục, convention của dự án 
                - Biết cách tạo job, sql, cấu hình job và run job thông qua docker
            - Nhiệm vụ của Agent:
                - Thực hiện dev các bảng theo thiết kế của Data Architect bao gồm SQL, jobs, ABI (không add job vào pipeline, không sửa DAG)
                - Khi đặt tên file và tên bảng cần thêm hậu tố _dev để đánh dấu rằng đây là các bảng đang phát triển.
                - Trường hợp là bảng cũ (update logic bảng), dev phải clone code và file .sh của bảng cũ sang file mới, đặt tên bảng output có hậu tố _dev
                - job mới cũng không được đọc trực tiếp từ bảng đang có trên hệ thống, thay vào đó dev cần thực hiện shallow clone bảng input sang bảng mới có hậu tố _dev, điều này giúp tránh tối đa việc ảnh hưởng đến các bảng đang chạy trên product
                - Sau khi xong dev thực hiện việc chạy thử job trực tiếp qua docker, lưu ý cần cấu hình lại job trong file .sh để chạy 1 lượng nhỏ data, thường là 1 giờ hoặc 1 ngày (vì có thể file sẽ lấy cấu hình chung của workflow trong application.properties gây chậm và tốn tài nguyên)
                - Sau khi job chạy thành công dev tiến hành update vào tài liệu thiết kế bảng của Architect (thêm 1 mục mới là Development) trong đó mô tả input và output của job, script để chạy job
            - Output của Agent: 
                - code, script của các job cho các bảng cần bổ sung hoặc sửa
                - Chạy thử thành công 1 lần
                - Cấp nhật thông tin chạy vào tài liệu thiết kế của Architect
    Tôi muốn bổ sung tiếp như sau:
        - Tester Agent
            - Agent có nhiệm vụ kiểm thử kết quả của các job
            - Đầu vào của Agent
                - Thư mục tài liệu sau khi đã được Data Architect thiết kế, và Dev đã bổ sung file development.md trong thư mục tài liệu
            - Yêu cầu của Agent
                - Có khả năng đọc hiểu tài liệu thiết kế từ Data Architect
                - Hiểu rõ cách thức hoạt động chung của job thông qua việc đọc tài liệu guide_book.md
                - Viết được test case cho từng bảng theo mẫu có trong file template/TestCase.md
            - Các bước thực hiện
                - Tạo 1 thư mục mới với tên là test trong Thư mục tài liệu chung
                - Từ các thông tin thiết kế có trong tài liệu, Agent xây dựng file test case cho mỗi bảng theo mẫu trong template/TestCase.md, mỗi bảng làm 1 file riêng với tên file là tên bảng.
                - Tiến hành test theo test case đã xây dựng, lưu ý sử dụng các thông tin mà dev đã viết trong file development.md, chỉ sử dụng các bảng có surfix _dev mà dev đã chuẩn bị sẵn
                - Tester có thể chỉnh sửa dữ liệu, thay đổi thuộc tính bảng trên các bảng _dev để phục vụ mục đích test
                - Cập nhật kết quả test vào file test case
            - Output của Agent:
                - Trong thư mục tài liệu chung mỗi bảng đã thiết kế đều có file test case với kết quả đã được ghi đầy đủ 
        - Trong quá trình phát triển Team lead agent có vai trò điều phối công việc giữa Developer và Tester, Team lead sẽ lấy ra những Test case chưa pass và gửi lại cho Developer xử lý, sau khi Dev sửa xong sẽ yêu cầu Tester test lại, vòng lặp sẽ kết thúc sau khi tất cả các test case đều đã pass hoặc đủ 3 vòng lặp (nếu điều này xảy ra Team lead cần thông báo lại cho người dùng để xử lý)
        
    Tôi muốn bổ sung tiếp như sau:
        - DataOps Agent
            - Ngoài nhiệm vụ về vận hành monitor, Agent này còn có nhiệm vụ cấu hình và triển khai các bảng đã phát triển 
            - Yêu cầu của Agent:
                - Có khả năng đọc hiểu tài liệu Data Requirement, tài liệu thiết kế trong thư mục tài liệu
                - Nắm rõ cấu trúc thư mục, convention của dự án 
                - Hiểu rõ cách thức hoạt động chung của job thông qua việc đọc tài liệu guide_book.md, để có thể cấu hình job chạy đúng đắn
            - Input của Agent:
                - Thư mục tài liệu sau khi đã hoàn thành qua vòng lặp DEV-TEST
            - Nhiệm vụ của Agent:
                - Chạy thử các bảng dữ liệu trong 1 khoảng thời gian nhỏ (5 ngày)
                    - Sửa lại tên bảng và tên các bảng input, các file code, .sh về tên đúng (bỏ đuôi _dev), nếu sau khi bỏ đuôi _dev mà trùng tên với file đang có (trường hợp bảng đã có nhưng có update) thì overwrite lại file code cũ bằng file code, sau đó update lại properties fromBlock, toBlock hoặc fromEpochSecond, toEpochSecond để bảng có thể chạy lại từ đầu (lưu ý không được xóa bảng) cách update như sau:
                        - Nếu bảng chạy backward:
                            - update fromBlock = toBlock + 1 (cấu hình như thế này sẽ giúp lần chạy tiếp theo bảng sẽ chạy lại từ toBlock về trước)
                            - hoặc update fromEpochSecond = toEpochSecond cho trường hợp Time-base
                        - Nếu bảng chạy forward:
                            - update toBlock = fromBlock - 1
                            - hoặc update toEpochSecond = fromEpochSecond
                    - Dọn dẹp: Xóa các bảng dữ liệu đuôi _dev có liên quan
                    - Tạo 1 file UAT.md trong Thư mục tài liệu chung để lên cấu hình cho UAT, tham khảo template/UAT.md, để trống phần result
                    - Cấu hình các job theo config trong UAT.md
                    - Trigger thủ công các job này theo đúng thứ tự lineage mà Architect đã thiết kế, nếu job chạy lỗi do thiếu tài nguyên thì cần điều chỉnh lại tham số phù hợp (VD: giảm max_number_partition và tăng max_time_run sẽ giúp giảm lượng tài nguyên cần để chạy job) nếu lỗi logic thì trả lại cho Team lead
                    - Sau khi các job chạy xong, thu thập các thông tin về thời gian chạy, khoảng data chạy, kích thước output để cập nhật vào file UAT.md
                    - Điều chỉnh lại cấu hình cho các job để mỗi lần run chạy được 1 ngày dữ liệu, sau đó bổ sung job vào DAG theo đúng thiết kết lineage
            - Output của Agent:
                - Các job được triển khai thành công, mỗi bảng có 5 ngày dữ liệu để phục vụ UAT
                - Thông tin của các job được update trong file UAT.md trong thư mục tài liệu chung
        - Data Analyst Agent
            - Agent có nhiệm vụ xây dựng kết quả phân tích trên Metabase dựa trên những bảng có sẵn trong Data warehouse
            - Input của Agent:
                - Thư mục catalog chứa mô tả của tất cả các bảng hiện có trong Data warehouse
                - Thư mục tài liệu chứa file Data_Requirement.md
            - Yêu cầu đối với Agent:
                - Có thể đọc hiểu yêu cầu và viết truy vấn, xây dựng các biểu đồ phân tích trên Metabase
                - Có hiểu biết về toàn bộ các bảng dữ liệu hiện có trong Data warehouse thông qua các tài liệu trong thư mục catalog
                - Câu truy vấn khi viết cần vừa đảm bảo đúng logic và tối ưu hóa, sử dụng thông tin Index và Partition của bảng để tối ưu truy vấn
                - Luôn thực hiện việc lọc để giảm bớt dữ liệu cần đọc từ bảng trước khi thực hiện các phép tính toán và join
                - Đảm bảo mỗi câu truy vấn trả về kết quả trong thời gian dưới 10s, nếu kích thước bảng quá lớn cần bổ sung thêm các bộ lọc để giới hạn dữ liệu (dù không có trong yêu cầu), chẳng hạn bổ sung thêm bộ lọc về thời gian (block_date)
            - Các skill và script mà Agent được dùng:
                - metabase-cli: dùng để thao tác với Metabase, cần sử dụng Database Trino = id 3
                - Có thể gọi script query trên data warehouse
            - Nhiệm vụ của Agent
                - Input của Agent là Thư mục tài liệu, Agent sẽ đọc file Data_Requirement.md trong Thư mục tài liệu để nắm được yêu cầu
                - Viết truy vấn và xây dựng biểu đồ phân tích trên Metabase theo đúng yêu cầu trong tài iệu Data_Requirement
                - Lấy link kết quả và update vào phần Result Analyst trong tài liệu Data_Requirement.md
            - Output của Agent:
                - Thư mục tài liệu chứa file Data_Requirement.md sau khi đã được thêm link kết quả trong Resul Analyst

===

Viết cho tôi một guide_book.md để giúp người dùng và Agent có thể hiểu rõ hơn về cơ chế hoạt của các job trong hệ thống Chainslake, từ đó giúp cấu hình một cách chính xác. Tôi sẽ viết những ý chính, bạn sẽ giúp tôi viết lại rõ ràng

- Mỗi job đều chỉ đẩy dữ liệu vào duy nhất 1 bảng
- Trong 1 bảng, ngoài dữ liệu được lưu trữ trong bảng còn có các thông tin properties, trong đó các thuộc tính như fromBlock, toBlock, fromEpochSecond, toEpochSecond cho biết khoảng dữ liệu hiện tại trong bảng. Khi job được run, nó sẽ sử dụng những thông tin này để tính toán khoảng dữ liệu cần xử lý trong lần run đó. Chỉ sau khi dữ liệu đã được ghi thành công (trong 1 vòng lặp) các thông tin này mới được update vào properties của bảng, nếu job fail trong quá trình ghi, thì ở lần chạy sau, job sẽ kiểm tra lại thông tin properties và tiến hành xóa dữ liệu (nếu có) trước khi khi ghi dữ liệu mới vào, điều này giúp cho dữ liệu trong bảng luôn được đảm bảo chính xác.
- Mỗi bảng dữ liệu đều có một danh sách bảng input được gọi là upstream, trừ các bảng origin (bảng đầu nguồn), các bảng input được khai báo trong thuộc tính list_input_tables và sẽ được set trong properties của bảng. Khi job run, ngoài việc lấy thông tin properties của chính bảng output, nó cũng sẽ lấy thông tin properties của các bảng input để biết dữ liệu trong các bảng input đã được xử lý đến đâu rồi, từ đó tính toán ra khoảng dữ liệu mà nó có thể xử lý trong lần chạy hiện tại.
- Các bảng input có thể có dữ liệu trong các khoảng khác nhau, do đó job sẽ tính toán sao cho khoảng dữ liệu mà nó sẽ xử lý sẽ có đủ data của tất cả các bảng input trong cả trường hợp chạy backward và forward.
- Về mặt kỹ thuật, bảng được chia thành 2 loại chính:
    - frequentType là block:
        - loại bảng này sử dụng fromBlock, toBlock để theo dõi dữ liệu trong bảng
        - input của loại bảng này cũng phải có frequentType là block
    - frequentType là minute, hour hoặc day
        - loại bảng này sử dụng fromEpochSecond và toEpochSecond để theo dõi dữ liệu trong bảng
        - input của loại bảng này có thể có frequenType là tất cả các loại, trong trường hợp input có frequentType là block thì job sẽ sử dụng thông tin từ bảng origin_table (được cấu hình trong application.properties, thường là dùng bảng .blocks) để xác định block_time từ block_number
        - Job khi xử lý loại bảng này sẽ tuân thủ nguyên tắc: phải có đủ data từ các bảng input mới xử lý. Ví dụ bảng có type là day, thì để có thể xử lý cho ngày A, thì các bảng input phải có dữ liệu từ trước ngày A đến sau ngày A (đảm bảo ngày A đủ dữ liệu)
    
=== 

- Hiện tại tôi thấy rằng script build_catalog khi xử lý phần transform_sql_source đang bỏ qua header, hãy sửa lại để có cả phần header đầy đủ 

=== 

- Dựa vào thông tin của bảng ethereum_token.erc20_transfer có trong thư mục catalog
- Dựa vào guide_book.md để hiểu cơ chế hoạt động của job trong hệ thống
- hãy viết cho tôi tài liệu Test case cho bảng này vào file tempate/TestCase.md, tôi sẽ sử dụng tài liệu này làm chuẩn cho phần Test

===

Tôi muốn biết khối lượng giao dịch của các token trên sàn dex mỗi ngày

===

Tôi muốn tạo 1 skill mới để tạo job lấy thông tin từ contract. Hãy xem ví dụ từ job ethereum/contract/erc20_tokens.sh, job này sử dụng sql evm_contract/erc20_tokens.sql, nhiệm vụ của job này là tạo ra bảng ethereum_contract.erc20_tokens chứa thông tin gồm name, symbol, decimals của tất cả các contract erc20. Input của job này là bảng ethereum_decoded.erc20_evt_transfer chứa tất cả các event giao dịch erc20 transfer. Bằng cách sử dụng select dictinct và kiểm tra điều kiện ${if table_existed}, logic sẽ đảm bảo rằng contract_address trong bảng không bị lặp lại. Tại mỗi lần chạy các contract mới được thêm vào sẽ sử dụng một function call được khai báo trong biến register_evm_call, tên function chính là tên của file abi, trong file abi đã có khai báo sẵn các function mà có thể gọi được của contract erc20 như name, symbol, decimals, từ đó trong sql có thể gọi các function này cho từng contract mới để lấy thông tin

=== 

Từ 2 skill add-contract-decode-job, add-contract-info-job hãy giúp tôi bổ sung thêm 1 phần mới vào guide_book.md mô tả cơ chế hoạt động 2 config pre_decode_tables và register_evm_call

===

Vấn đề 1: register_evm_call đã hỗ trợ gọi với nhiều tham số đúng như phương án đề xuất
Vấn đề 2: Đồng ý
Vấn đề 3: Đồng ý
Vấn đề 4: Loại bỏ create_block_number vì không cần thiết
Vấn đề 5: Đồng ý
Vấn đề 6: Đồng ý

===

Tôi muốn giới hạn lại quyền đọc, ghi, thực thi của các agent trong nhóm data agent team như sau:
    - Các agent trong nhóm này chỉ được sử dụng các script, query, skill đã có sẵn, không phát triển các script, query skill mới (việc phát triển các script, query, skill mới là do Agent build thực hiện)
    - Sử dụng các skill có sẵn, chọn đúng skill cho nhiệm vụ để tránh phải đọc code quá nhiều không cần thiết
    - docs và template là các thưc mục chung mà nhóm data agent có thể truy cập, file guild_book.md cũng là file mà các agent có thể đọc nếu cần
    - Ngoài các thư mục dùng chung thì các Agent chỉ được làm việc trong các thư mục giới hạn sau:
        - BA: Làm việc với user và viêt tài liệu trong thư mục docs, không truy cập vào bất kỳ nơi nào khác
        - data-architect: được truy cập thư mục catalog, thực thi script build_catalog
        - developer, dataops: làm việc trong thư mục chainslake, được dùng tất cả các script, query và skill
        - tester, data-analyst: được dùng tất cả các script, query và 
        
===

Tôi muốn sửa lại guide_book.md mục 9. pre_decode_tables và register_evm_call cho phép có thể khai báo nhiều bảng cần decode và nhiều ABI (cách nhau bới dấu , và không có dấu cách). Khi gọi các function được đăng ký trong register_evm_call nếu function có nhiều parameter thì các parameter của nó chỉ cần nối vào sau function_name và cách nhau bới dấu cách. Hãy sửa lại guide_book cho tôi

=== 

Hiện tại tôi thấy rằng permission cho mỗi agent vẫn chưa thực sự tốt, các agent khi được gọi đến thường đọc rất nhiều file không liên quan trước khi thực sự bắt tay vào công việc, trong khi đó thì các skill đã được xây dựng sẵn thì mãi sau mới được gọi đến để sử dụng, tôi muốn bạn review lại tất cả permission của các agent và đề xuất cho tôi phương án cải thiện theo định hướng sau:
- Các agent được dùng script, query, skill theo đúng nhiệm vụ mà chúng được giao, ưu tiên sử dụng skill có sẵn thay vì đọc lại code
- Chỉ agent build có quyền phát triển các script, query, hoặc skill mới các agent khác chỉ có thể sử dụng
- Khi 1 agent được khởi tạo nó chỉ cần biết rõ nó là ai, nhiệm vụ gì thay vì đưa tất cả context của dự án vào gây loãng
- khi khởi động tôi muốn mặc định agent Team leader sẽ được chọn thay vì Build như hiện tại (Build chỉ được gọi khi cần phát triển skill, script, query mới, hoặc cần những điều chỉnh chính sách chung)

hãy áp dụng 1, 2, 3, 5
với số 4 không cho phép developer tester gọi trực tiếp docker, vì đã có script run_job rồi

===

Tôi đã thử nghiệm sử dụng nhóm Agent để làm bài toán đầu tiên, tuy nhiên tôi nhận thấy có một số vấn đề sau:
    - Các Agent thay vì tập trung vào nhiệm vụ được giao thì chúng lại tự động đọc rất nhiều thông tin không cần thiết, điều này có thể do lượng thông tin đưa vào context chung của các Agent chưa tốt
    - Các Agent sử dụng các công cụ, skill, query, script chưa phù hợp dẫn đến các hành vi xử lý lòng vòng, phức tạp thậm chí tự động can thiệp vào các file không liên quan đến nhiệm vụ

Vì vậy tôi muốn review lại để cải thiện tốt hơn, hãy bắt đầu với AGENT.md, đây là prompt chung của tất cả các Agent, bạn có ý tưởng gì để cải thiện không?

Vì đây là prompt chung cho các Agent nên tôi muốn nó phải thật ngắn gọn chỉ giữ lại những gì chung nhất, loại bỏ tất cả các mời gọi đọc file khác không cần thiết. Các thông tin cần có bao gồm:
    - Lời giới thiệu bối cảnh ngắn gọn có thể dùng cho mọi agent. Ví dụ: Bạn là 1 Agent trong nhóm Data Agent Team của Chainslake gồm có: ...
    - Mô tả chung về nhiệm vụ: Nhiệm vụ của bạn là thực hiện một công đoạn cụ thể trong quy trình để xử lý bài toán cho người dùng
    - Các Agent trong team gồm có: Liệt kê danh sách Agent, mỗi Agent có 1 câu mô tả ngắn gọn (đủ để mọi Agent trong team đều ít nhất biêt Agent khác làm việc gì)
    - Mô tả về quy trình xử lý bài toán: Chỉ cần mô tả từng bước một cách khai quát, ai làm việc gì không cần chi tiết
    - Luật chung cho tất cả các Agent, ví dụ:
        - Bạn sẽ được cấp phép sử dụng các skill, tool (script, query), tài liệu đi kèm và không gian làm việc với quyền hạn xác định 
        - Bám sát nhiệm vụ được giao, sử dụng skill, hướng dẫn và tool được cấp phép để thực hiện nhiệm vụ

===

Hiện tại tôi thấy rằng vai trò của của dataops và developer trong 1 số trường hợp bị chồng lấn lẫn nhau, vì vậy tôi muốn gộp 2 agent này thành 1 agent tên là data-engineer. Agent data-engineer sẽ có đầy đủ các skill và quyền như dataops và developer, quy trình hiện tại của developer trong việc phát triển job mới sẽ được viết lại thành 1 skill cho agent data-engineer. Các quy trình như add contract decoded, add contract info, add new chain pipeline đã có skill rồi thì không cần đi qua quy trình phát triển phực tạp (từ BA -> Architect -> dev -> test) mà data-engineer có thể thực hiện ngay theo skill 