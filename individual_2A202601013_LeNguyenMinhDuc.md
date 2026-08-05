# Member Role Report - Day 9: Multi Agent A2A

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Lê Nguyễn Minh Đức |
| MSSV | 2A202601013 |
| Khóa/Lớp | K3 |
| Vai trò chính | Thành viên 2 - Payment Agent, Policy Rules Engine, Policy Agent |
| Ngày hoàn thành | 2026-08-05 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Payment Agent | `src/agents/payment.py` | `InvestigationRequest`, Data Access Layer | `PaymentFacts` gồm các dòng thanh toán, tổng tiền và candidate evidence | Hoàn thành |
| Deterministic Policy Rules | `src/policy_rules.py` | `OrderSellerFacts`, `PaymentFacts`, `DeliveryFacts` | Kết quả phân định theo `EC_POLICY_V1` | Hoàn thành |
| Policy Agent | `src/agents/policy.py` | `PolicyRequest` | `ResolutionDraft` chuẩn schema | Hoàn thành |
| Unit tests | `tests/test_payment.py`, `tests/test_policy_rules.py`, `tests/test_policy_agent.py` | Mock facts và fixtures | Bộ test Payment/Policy | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
|---|---|---|
| Cấu hình LLM và OpenAI API | Toàn nhóm | Model `gpt-4o-mini` được khai báo trong `src/settings.py`; secret chỉ đọc từ `OPENAI_API_KEY` |

OpenAI không công bố chính thức số tham số của GPT-4o mini. Vì vậy báo cáo không gán model này là `8B`; đây là rủi ro cần được đối chiếu với yêu cầu model `<=10B` của đề trước khi nộp.

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
|---|---|---|---|
| Xử lý các dòng thanh toán | `src/agents/payment.py` | Payment Agent cộng mỗi `payment_value` đúng một lần | `pytest tests/test_payment.py` |
| Triển khai sáu quy tắc | `src/policy_rules.py` | Policy Engine đúng thứ tự ưu tiên | `pytest tests/test_policy_rules.py` |
| Sinh quyết định chuẩn schema | `src/agents/policy.py` | `ResolutionDraft` có issue, root cause, party, refund, action và evidence | `pytest tests/test_policy_agent.py` |

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Phần Payment phải tính chính xác tổng thanh toán từ tất cả payment row mà không nhân `payment_value` với `payment_installments`. Policy phải áp dụng đúng thứ tự sáu luật, làm tròn tiền bằng `Decimal`, xác định đúng bên chịu trách nhiệm, số tiền hoàn và hành động xử lý.

### Cách triển khai

1. `PaymentAgent` lấy toàn bộ payment row từ Data Access Layer, cộng `payment_value` bằng `Decimal`, đếm số dòng và tạo evidence dạng `payment:<order_id>:<payment_sequential>`.
2. `evaluate_policy` áp dụng lần lượt `canceled_order_paid`, `unavailable_order_paid`, `late_delivery_seller`, `late_delivery_logistics`, `valid_split_payment` và `unsupported_late_claim`.
3. Payment reconciliation chấp nhận sai số tối đa `0.10 BRL` giữa tổng payment và tổng item cộng freight.
4. `PolicyAgent` chuyển kết quả luật thành `ResolutionDraft`, giới hạn số entity/evidence/action theo schema và không tự tạo dữ liệu ngoài facts.

### Cách xác minh

```bash
source .venv/bin/activate
python -m pytest -q tests/test_payment.py tests/test_policy_rules.py tests/test_policy_agent.py
python -m pytest -q
```

## 5. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Lê Nguyễn Minh Đức

**Ngày xác nhận:** 2026-08-05
