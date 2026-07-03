Đọc file README.md để hiểu bối cảnh dự án
- Tôi cần bảng dữ liệu ethereum_token.erc20_transfer, bảng này có input từ 2 bảng: ethereum.transactions, ethereum_decoded.erc20_evt_transfer
- 2 bảng input sẽ được join với nhau theo block_number, tx_hash (từ transfer) - hash (transactions)
- lấy tất cả các column của bảng transfer, lấy thêm các thông tin sau từ bảng transactions:
    - from: đổi tên thành tx_from
    - to: đổi tên thành tx_to 
    - method_id: đổi tên thành tx_method_id
- Yêu cầu code tuân thủ convention của dự án
- Sau khi dev xong thì để tôi review code trước khi test job bằng cách run thủ công