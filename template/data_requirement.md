# Data Requirement

<<Phần thông tin chung, trình bày dạng bảng>>
- Ngày tạo
- Ngày update gần nhất
- Version: mỗi lần thay đổi sẽ nâng lên 1 số, bắt đầu từ số 1

## Summary
<<Phần mô tả tóm tắt>>

## Change log
<<Phần ghi lại tóm tắt các thay đổi sau mỗi lần update>>
- [Version] - [Ngày update]: Tóm tắt nội dung thay đổi

## User Requirement
<<Phần thông tin chính làm rõ yêu cầu của User, cần trả lời các câu hỏi dưới đây>>

- Nhóm câu hỏi để giới hạn phạm vi dữ liệu
    - User cần dữ liệu của chain nào?
    - Dữ liệu cần có từ thời gian nào? 1 năm, 2 năm hay toàn bộ lịch sử của chain
- Nhóm câu hỏi để giới hạn nghiệp vụ:
    - User quan tâm đến mảng nào trong blockchain?
        - Defi
        - NFT
        - Gamefi
        ...
    - User quan tâm đến những token, contract, hoặc giao thức nào cụ thể hay không, nếu có hãy tìm kiếm các thông tin xung quanh trên internet
        - Ví dụ với token, contract thì cần tìm thông tin về tên chính xác, contract address, ngày deploy, ABI 
        - Với giao thức thì cần tìm thông tin về dự án, link tài liệu dự án, github (nếu có), ABI các contract
        - Cần hỏi lại để User confirm những thông tin này
- Nhóm câu hỏi để làm rõ yêu cầu
    - User mong muốn biết điều gì từ dữ liệu?
    - Hình thức trình bày thông tin như thế nào?
        - Dạng bảng: gồm những thông tin nào?
        - Dạng biểu đồ:
            - Gồm những metrics nào
            - Nếu như theo thời gian thì cần xem theo ngày, theo giờ, hay tháng...
    - Tần suất update dữ liệu như thế nào: daily hay hourly hay chỉ cần chạy 1 lần ra kết quả

## Data prototype

<<Từ yêu cầu của người dùng, xây dựng các bảng dữ liệu prototype>>

- [Tên bảng]: Mô tả bảng sẽ đáp ứng yêu cầu gì
| Column 1 | Column 2 | ... |
|---|---|---|
| Ví dụ 1 | Ví dụ 2 | ... |

## Result Analyst
<<Phần này do Data Analyst Agent viết>>

Danh sách link Chart, dashboard trên Metabase


