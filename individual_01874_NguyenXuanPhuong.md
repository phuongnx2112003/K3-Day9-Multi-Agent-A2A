# Member Role Report - Day 9: Multi Agent A2A

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Nguyễn Xuân Phượng |
| MSSV | 2A202601874 |
| Khóa/Lớp | K3 |
| Vai trò chính | Thành viên 1 - Data Access, Order & Seller Agent, Delivery Agent |
| Ngày hoàn thành | 2026-08-05 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Data Access Layer | `src/data_access.py` - `DataAccessLayer` | Bốn CSV orders, items, payments và sellers | Các index read-only theo order/seller ID | Hoàn thành |
| Timestamp utility | `src/datetime_utils.py` - `parse_olist_timestamp` | Timestamp dạng chuỗi hoặc giá trị rỗng | `datetime` hoặc `None`, không đổi múi giờ | Hoàn thành |
| Order & Seller Agent | `src/agents/order_seller.py` - `OrderSellerAgent.process` | `InvestigationRequest`, Data Access Layer | `OrderSellerFacts` | Hoàn thành |
| Delivery Agent | `src/agents/delivery.py` - `DeliveryAgent.process` | `InvestigationRequest`, Data Access Layer | `DeliveryFacts` | Hoàn thành |
| Behavioral tests | `tests/test_data_access.py`, `tests/test_order_seller.py`, `tests/test_delivery.py` | Dataset Olist thu nhỏ và contract chung | 13 test cho phần Thành viên 1 | Hoàn thành |
| Test fixtures | `tests/member1_fixtures.py` | Thư mục tạm do pytest cung cấp | Dataset nhiều item/seller, giao trễ, đúng hạn và canceled | Hoàn thành |

Output của phần này được bàn giao cho:

- Payment Agent dùng `item_total_brl` và `freight_total_brl` để reconciliation.
- Policy Agent dùng trạng thái order, seller handoff và delivery facts để chọn policy.
- Coordinator Agent gọi hai investigation agent trong bước fan-out.
- Verifier Agent dùng facts và evidence candidates để kiểm tra output cuối.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
|---|---|---|
| Thiết lập môi trường Python | Cả nhóm | Tạo `.venv`, `requirements.txt`, `.gitignore`, `.env.example`; `pip check` không phát hiện dependency lỗi |
| Rà contract chung | Thành viên 2 và 3 | Xác nhận `OrderSellerFacts` và `DeliveryFacts` tương thích với fixtures đã khóa ở Giai đoạn 0 |
| Kiểm tra dữ liệu thật | Pipeline tích hợp | Hai agent xử lý read-only đủ 50 order chính thức, không có exception |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
|---|---|---|---|
| Load và index dữ liệu nguồn | `DataAccessLayer.load_data` | 99,441 orders, 98,666 order có item, 99,440 order có payment và 3,095 sellers | Chạy script load DAL trên thư mục `data/` |
| Điều tra order và seller | `OrderSellerAgent.process` | Item/seller facts, item total, freight total, seller late handoff và evidence candidates | `pytest tests/test_order_seller.py` |
| Điều tra delivery | `DeliveryAgent.process` | Mốc carrier/customer/estimate và hai cờ `delivered_late`, `delivered_within_estimate` | `pytest tests/test_delivery.py` |
| Kiểm tra các edge case | Bộ test Thành viên 1 | 13/13 behavioral tests đạt | Lệnh pytest theo module |
| Regression toàn repo | Thư mục `tests/` | 25/25 tests đạt tại thời điểm xác minh | `python -m pytest -q` |
| Kiểm tra 50 input thật | `input/EC_001.json` đến `EC_050.json` | 34 delivered, 8 canceled, 8 unavailable; 16 giao trễ, 9 seller handoff trễ và 8 order không có item | Script read-only gọi hai agent cho 50 case |

Một output cụ thể của phần việc là `OrderSellerFacts` cho mỗi order. Artifact này chứa toàn bộ item theo đúng thứ tự `order_item_id`, seller liên quan, tổng tiền hàng, tổng freight, cờ handoff trễ theo item/seller và evidence ID có thể dựng trực tiếp từ CSV. Cùng với `DeliveryFacts`, đây là đầu vào đã kiểm chứng để Policy Agent phân biệt `late_delivery_seller`, `late_delivery_logistics` và `unsupported_late_claim`.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Mỗi case chỉ cung cấp `claimed_order_id` và nội dung khiếu nại. Phần tôi phụ trách phải biến order ID thành facts đáng tin cậy từ nhiều CSV, bao gồm trạng thái order, tất cả item/seller, tổng tiền hàng và freight, mốc seller bàn giao cho carrier, ngày giao thực tế và ngày giao dự kiến. Các facts phải hỗ trợ order nhiều item/seller, order không có item và timestamp bị thiếu mà không suy diễn dữ liệu không tồn tại.

### Cách triển khai

`DataAccessLayer` kiểm tra sự tồn tại và required columns của bốn CSV trước khi publish dữ liệu. Dữ liệu được load một lần bằng pandas rồi index theo `order_id` hoặc `seller_id`. Item được sắp xếp theo `order_item_id`, payment được sắp xếp theo `payment_sequential`. Giá trị pandas NA được chuyển thành `None` trước khi đi qua contract. Các getter trả `deepcopy` để agent không thể thay đổi index dùng chung.

`OrderSellerAgent` lấy order và toàn bộ item, dùng `Decimal` để cộng `price` và `freight_value`, sau đó làm tròn hai chữ số. Với từng item, agent so sánh `order_delivered_carrier_date > shipping_limit_date`; kết quả được giữ ở cấp item và tổng hợp theo seller. Evidence chỉ được tạo cho order, item và seller thực sự tồn tại trong DAL.

`DeliveryAgent` so sánh trực tiếp timestamp trong CSV, không chuyển múi giờ. Khi đủ ngày giao thực tế và ngày giao dự kiến, agent đặt đúng một trong hai cờ giao trễ hoặc trong hạn. Nếu thiếu ngày giao, cả hai cờ đều là `False` để Policy Agent không hiểu nhầm rằng order canceled/unavailable đã được giao đúng hạn.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input | `InvestigationRequest` gồm `case_id`, `order_id`, `opened_at`, nội dung yêu cầu; bốn CSV Olist ở chế độ read-only |
| Output | `OrderSellerFacts` và `DeliveryFacts` theo schema trong `src/contracts/messages.py` |
| Module phụ thuộc | `src/settings.py`, `src/contracts/messages.py`, `src/evidence.py`, `src/datetime_utils.py` |
| Module sử dụng output | Coordinator Agent, Payment Agent, Policy Agent và Verifier Agent |
| Điều kiện lỗi cần xử lý | Thiếu file/cột CSV, primary key trùng, order không tồn tại, timestamp sai format, giá tiền không hợp lệ, order không có item hoặc thiếu ngày giao |

### Cách xác minh

```bash
source .venv/bin/activate
python -m pytest -q tests/test_data_access.py tests/test_order_seller.py tests/test_delivery.py
python -m pytest -q
python -m compileall -q src tests run.py
```

- **Kết quả mong đợi:** 13 test phần Thành viên 1 và toàn bộ test repo đều đạt; source compile thành công.
- **Kết quả thực tế:** `13 passed` cho ba module sở hữu và `25 passed` cho toàn repo tại thời điểm xác minh.
- **Artifact:** `tests/member1_fixtures.py` và ba file behavioral test; không chứa secret.

Kiểm tra bổ sung đã load dataset thật và gọi song song `OrderSellerAgent`, `DeliveryAgent` cho đủ 50 input. Kết quả thực tế là `validated_cases=50`, không có exception.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Nếu mỗi agent đọc và lọc toàn bộ CSV cho từng case, 50 case sẽ lặp lại I/O và có nguy cơ mỗi agent chuẩn hóa dữ liệu khác nhau.
- **Các phương án đã cân nhắc:** đọc CSV ở mỗi lần xử lý case; hoặc load một lần, tạo index dùng chung theo key và chỉ cung cấp API read-only.
- **Phương án đã chọn:** load/index một lần trong `DataAccessLayer`, validate schema trước khi publish và trả `deepcopy` qua getter.
- **Lý do:** giảm I/O lặp lại, giữ một nguồn dữ liệu chuẩn giữa các agent, xử lý lookup theo order ID trực tiếp và ngăn agent vô tình làm thay đổi state dùng chung. Các cột ID/zip được đọc dạng string để không mất số 0 ở đầu; số tiền được cộng bằng `Decimal` trong agent để bảo đảm quy tắc làm tròn.
- **Bằng chứng quyết định phù hợp:** DAL load thành công 99,441 orders và hai agent xử lý đủ 50 case chính thức không lỗi; test xác nhận sửa object trả về không làm thay đổi record trong index.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng:** skeleton của Delivery Agent luôn trả `delivered_within_estimate=True`, kể cả order canceled/unavailable không có `order_delivered_customer_date`.
- **Bước tái hiện:** truy vấn các case như `EC_003` hoặc `EC_005`; dữ liệu nguồn có ngày giao thực tế bằng `None`, trong khi skeleton vẫn đánh dấu giao trong hạn.
- **Nguyên nhân gốc:** giá trị delivery status ban đầu bị hard-code, chưa được tính từ timestamp nguồn và chưa phân biệt `False` với trạng thái không đủ dữ liệu để so sánh.
- **Cách xử lý:** parse riêng ba timestamp; chỉ thực hiện phép so sánh khi cả ngày giao thực tế và estimated date cùng tồn tại. Nếu thiếu một trong hai, `delivered_late=False` và `delivered_within_estimate=False`.
- **Cách xác minh sau khi sửa:** test `test_missing_delivery_date_is_not_assumed_on_time` đạt; kiểm tra 50 case tìm thấy 8 order không có item và không phát sinh lỗi timestamp.
- **Điều học được:** không nên dùng giá trị mặc định mang ý nghĩa nghiệp vụ khi dữ liệu nguồn đang thiếu; trạng thái “không đủ dữ liệu để so sánh” phải khác với “đã giao đúng hạn”.

## 7. Hiểu biết về luồng end-to-end

### 1. Dữ liệu đi từ input đến output như thế nào?

Batch Runner đọc từng `EC_xxx.json`, tạo `run_id` và `trace_id`, rồi gửi `InvestigationRequest` cho Coordinator. Coordinator fan-out song song tới Order & Seller, Payment và Delivery Agent. Sau khi nhận đủ ba facts, Coordinator gửi dữ liệu đã gộp cho Policy Agent. Policy Agent chọn issue, root cause, party, refund, action và tạo `ResolutionDraft`. Verifier kiểm tra schema, evidence, số tiền và tính nhất quán trước khi Batch Runner ghi `output/EC_xxx.json`.

### 2. Vì sao investigation facts phải tách khỏi policy decision?

Investigation Agent chỉ mô tả dữ liệu quan sát được như order status, timestamps, totals và seller handoff. Policy Agent mới chịu trách nhiệm ánh xạ facts sang `primary_issue`. Cách tách này giúp kiểm thử từng phần độc lập, tránh agent điều tra tự kết luận vượt phạm vi và cho phép Verifier tính lại quyết định từ cùng facts.

### 3. Payment reconciliation được thực hiện như thế nào?

Payment Agent cộng mỗi `payment_value` đúng một lần cho từng payment row, không nhân với installments. Tổng payment được so với `item_total_brl + freight_total_brl` trong sai số tối đa `0.10 BRL`. Có ít nhất hai payment row và tổng tiền khớp mới đủ điều kiện cho `valid_split_payment`, sau khi các policy ưu tiên cao hơn đã được loại trừ.

### 4. Verifier khác Policy Agent ở điểm nào?

Policy Agent tạo quyết định; Verifier là quality gate độc lập. Verifier kiểm tra evidence có tồn tại, ID đúng format, totals/refund tính đúng, giới hạn schema được tuân thủ và issue/root cause/party/action nhất quán. Output chỉ được ghi nếu Verifier trả `valid=true`.

### 5. Hệ thống được xem là hoàn thành dựa trên artifact nào?

Hệ thống phải có đúng 50 output JSON hợp lệ, trace terminal cho đủ 50 case, metadata phản ánh đúng model/runtime, source code và test đã commit, và submission zip chỉ chứa 50 file output. Unit test của từng module là điều kiện cần; kết quả end-to-end cùng trace/evidence mới chứng minh toàn pipeline hoạt động đúng.

## 8. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Xuân Phượng

**Ngày xác nhận:** 2026-08-05
