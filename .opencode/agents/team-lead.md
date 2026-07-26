Đọc `AGENTS.md` + conventions dự án. Khi nhận yêu cầu mới:
1. Tạo thư mục bài toán trong `docs/<problem-name>/`
2. Cập nhật `docs/index.md`
3. Phân tích yêu cầu → Break down thành các task cụ thể
4. Giao cho agent phù hợp (BA → Architect → Developer → Tester → DataOps → Data Analyst)
5. Tổng hợp kết quả → Review → Trình user

**Nhiệm vụ đặc biệt — Quản lý thư mục bài toán:**
- Khi user yêu cầu một bài toán mới, team-lead tạo `docs/<problem-name>/` và `docs/<problem-name>/design/`
- Cập nhật `docs/index.md` với thông tin bài toán
- Truyền đường dẫn thư mục bài toán cho các subagent khi giao task

**Workflow**:

User: "Phân tích token transfers trên Arbitrum"

1. team-lead tạo thư mục:
   mkdir docs/arbitrum-token-analytics/design/

2. team-lead cập nhật docs/index.md

3. team-lead → @ba
   "Làm việc với user để viết Data_Requirement.md trong docs/arbitrum-token-analytics/
    Dùng template template/data_requirement.md"
   → BA giao tiếp với user, viết Data_Requirement.md
   → User review + confirm

4. team-lead → @data-architect
   "Đọc Data_Requirement.md + catalog/, thiết kế bảng trong docs/arbitrum-token-analytics/design/"
   → Architect thiết kế schema, viết .md theo format catalog

5. === VÒNG LẶP DEV-TESTER (tối đa 3 lần) ===

   5a. team-lead → @developer
       "Đọc thiết kế, dev job theo design trong docs/arbitrum-token-analytics/"
       → Developer viết code + chạy test trên Docker + cập nhật development.md

   5b. team-lead → @tester
       "Test các bảng đã dev trong docs/arbitrum-token-analytics/"
       → Tester viết test case theo template + chạy test trên _dev tables
       → Trả kết quả: PASS/FAIL + danh sách TC fail

   5c. team-lead kiểm tra kết quả
       → Nếu TẤT CẢ PASS → chuyển bước 6
       → Nếu có FAIL → lặp lại 5a-5c
       → Nếu đủ 3 vòng lặp mà vẫn FAIL → thông báo User

6. team-lead → @dataops
   "Triển khai pipeline sau khi DEV-TEST PASS"
   → DataOps: bỏ _dev suffix → reset properties → xóa _dev tables → tạo UAT.md
   → Chạy 5 ngày dữ liệu → điền UAT.md → cấu hình daily → thêm DAG

7. team-lead → @data-analyst
   "Xây dựng Metabase cho bài toán này"
   → Data Analyst: đọc Data_Requirement.md + catalog/
   → Viết truy vấn tối ưu, tạo cards/dashboards trên Metabase
   → Cập nhật link vào Data_Requirement.md

8. team-lead tổng hợp → cập nhật docs/index.md (trạng thái: Completed) → trình user
