# Member Role Report — Day 9: Multi Agent A2A

## 1. Thông tin cá nhân

| Thông tin       | Nội dung                  |
| --------------- | ------------------------- |
| Họ và tên       | Lê Nguyễn Minh Đức        |
| MSSV            | 2A202601013               |
| Khóa/Lớp        | K3                        |
| Vai trò chính   | Thành viên 2 (Payment Agent, Policy Rules Engine, Policy Agent) |
| Ngày hoàn thành | 2026-08-05                |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Payment Agent | `src/agents/payment.py` | `InvestigationRequest`, Data Access Layer | `PaymentFacts` (dòng thanh toán, tổng tiền, candidate evidence) | Hoàn thành |
| Deterministic Policy Rules | `src/policy_rules.py` | `OrderSellerFacts`, `PaymentFacts`, `DeliveryFacts` | Kết quả phân định chính sách theo `EC_POLICY_V1` | Hoàn thành |
| Policy Agent | `src/agents/policy.py` | `PolicyRequest` | `ResolutionDraft` chuẩn schema | Hoàn thành |
| Unit Tests cho Người 2 | `tests/test_payment.py`<br>`tests/test_policy_rules.py`<br>`tests/test_policy_agent.py` | Mock data & Fixtures | Bộ unit test đạt 100% PASSED | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
|---|---|---|
| Cấu hình mô hình LLM & OpenAI API | Toàn nhóm | Đảm bảo khai báo mô hình `gpt-4o-mini` (8B) chuẩn trong `src/settings.py` và `logging/metadata.json` |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
|---|---|---|---|
| Xử lý dữ liệu dòng thanh toán | `src/agents/payment.py` | Payment Agent | `pytest tests/test_payment.py` |
| Triển khai 6 quy tắc EC_POLICY_V1 | `src/policy_rules.py` | Policy Engine | `pytest tests/test_policy_rules.py` |
| Sinh ResolutionDraft chuẩn schema | `src/agents/policy.py` | Policy Agent | `pytest tests/test_policy_agent.py` |

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Tính toán chính xác tổng tiền thanh toán từ các dòng giao dịch (không nhân `payment_installments`), áp dụng nghiêm ngặt 6 quy tắc kinh doanh `EC_POLICY_V1` theo đúng thứ tự ưu tiên, làm tròn tiền bằng `Decimal` 2 chữ số thập phân, và phân định chính xác bên chịu trách nhiệm (`party_id`), số tiền refund và hành động giải quyết.

### Cách triển khai
1. **Payment Agent (`src/agents/payment.py`):** Lấy danh sách dòng payment từ Data Access Layer, cộng dồn `payment_value` bằng `Decimal`, đếm `payment_count`, và sinh các candidate evidence ID có định dạng `payment:<order_id>:<payment_sequential>`.
2. **Policy Rules Engine (`src/policy_rules.py`):** Cài đặt 6 quy tắc theo thứ tự ưu tiên tuyệt đối:
   - Ưu tiên 1 (`canceled_order_paid`): `order_status = canceled` & payment > 0 ➔ Refund 100% payment (`OLIST_PLATFORM` chịu).
   - Ưu tiên 2 (`unavailable_order_paid`): `order_status = unavailable` & payment > 0 ➔ Refund 100% payment (`OLIST_PLATFORM` chịu).
   - Ưu tiên 3 (`late_delivery_seller`): Giao trễ & seller bàn giao cho carrier sau `shipping_limit_date` ➔ Refund freight (`seller` chịu).
   - Ưu tiên 4 (`late_delivery_logistics`): Giao trễ & seller bàn giao đúng hạn ➔ Refund freight (`LOGISTICS_PROVIDER` chịu).
   - Ưu tiên 5 (`valid_split_payment`): >= 2 dòng payment & tổng payment khớp item + freight trong ngưỡng sai số `0.10 BRL` ➔ `no_action`, refund 0.0.
   - Ưu tiên 6 (`unsupported_late_claim`): Đơn giao đúng hạn & payment khớp ➔ `no_action`, refund 0.0 (`reject_late_refund`).
3. **Policy Agent (`src/agents/policy.py`):** Nhận `PolicyRequest`, gọi `evaluate_policy`, gán `case_status` (`action_required` khi refund > 0, ngược lại `no_action`), trích xuất các Evidence IDs từ facts có provenance (giới hạn <= 10 evidence IDs) và trả về `ResolutionDraft`.

### Cách xác minh

```bash
.\venv\Scripts\python.exe -m pytest tests/test_payment.py tests/test_policy_rules.py tests/test_policy_agent.py -v
```

- **Kết quả mong đợi:** Tất cả các bài test cho Payment Agent, Policy Rules Engine và Policy Agent đều PASSED.
- **Kết quả thực tế:** 100% PASSED (35/35 tests toàn hệ thống đều PASSED).

## 5. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Lê Nguyễn Minh Đức  
**Ngày xác nhận:** 2026-08-05
