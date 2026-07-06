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