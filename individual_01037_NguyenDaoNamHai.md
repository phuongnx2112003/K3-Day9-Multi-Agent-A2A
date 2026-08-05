# Member Role Report — Day 9: Multi Agent A2A

## 1. Thông tin cá nhân

| Thông tin       | Nội dung                  |
| --------------- | ------------------------- |
| Họ và tên       | Nguyễn Đào Nam Hải        |
| MSSV            | 2A202601037               |
| 5 số cuối MHV   | 01037                     |
| Khóa/Lớp        | K3                        |
| Vai trò chính   | Thành viên 3 (Coordinator, Verifier, Batch Runner & Observability) |
| Ngày hoàn thành | 2026-08-05                |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Contracts & Schemas | `src/contracts/messages.py`<br>`src/contracts/output_schema.py`<br>`src/contracts/fixtures.py` | Đề bài & Quy tắc Handoff | Pydantic Models & Mock Fixtures dùng chung cho cả nhóm | Hoàn thành |
| Verifier Agent (Quality Gate) | `src/agents/verifier.py` | `VerificationRequest`, `ResolutionDraft`, Facts, DAL | `VerificationResult` (Kiểm tra Schema, Decimal Totals, Status/Refund consistency & Grounded Evidence) | Hoàn thành |
| Coordinator Agent (Orchestration) | `src/agents/coordinator.py` | `CaseInput` từ Batch Runner | Async Fan-out (OrderSeller, Payment, Delivery), Policy Call, Verifier Gate & Per-Agent Tracing | Hoàn thành |
| Batch Runner & Observability | `run.py`<br>`src/tracing.py`<br>`src/settings.py`<br>`src/llm_client.py` | 50 file `input/EC_xxx.json` | 50 output JSON, `trace.jsonl`, `metadata.json` (dynamic commit SHA), Groq LLM Client & `submission_output.zip` | Hoàn thành |
| Unit & Integration Tests | `tests/test_contracts.py`<br>`tests/test_verifier.py`<br>`tests/test_end_to_end.py`<br>`tests/test_llm_client.py` | Mock data & Real Data Pipeline | Bộ test kiểm thử tự động 36/36 tests PASSED | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
|---|---|---|
| Thiết kế Handoff Contracts & Fixtures | Thành viên 1 & Thành viên 2 | Cung cấp sẵn mock data giúp TV1 & TV2 viết test độc lập ngay từ Giai đoạn 0 |
| Khởi tạo LLM Client & Cấu hình Groq | Toàn nhóm | Đóng gói `src/llm_client.py` tích hợp Groq API (`llama-3.1-8b-instant`), cài đặt `.env` mẫu an toàn |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
|---|---|---|---|
| Khóa Handoff Contracts | `src/contracts/messages.py` | Pydantic Schemas | `pytest tests/test_contracts.py` |
| Triển khai Quality Gate Verifier | `src/agents/verifier.py` | Quality Gate kiểm tra 7 lớp quy tắc | `pytest tests/test_verifier.py` |
| Triển khai Orchestrator Coordinator | `src/agents/coordinator.py` | Async Fan-out & Granular Agent Tracing | `pytest tests/test_end_to_end.py` |
| Triển khai LLM Client | `src/llm_client.py` | Kết nối Groq API cho `llama-3.1-8b-instant` | `pytest tests/test_llm_client.py` |
| Triển khai Batch Runner & Submission Zip | `run.py` | Cô lập lỗi từng case, tạo 50 JSON & ZIP chứa đúng 50 file | `python run.py` |

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Xây dựng trục điều phối (Orchestrator), quản lý hợp đồng tin nhắn (Handoff Contracts), kiểm định chất lượng độc lập (Quality Gate Verifier), tự động lấy Git Commit SHA động, cô lập lỗi từng case và tự động hóa quy trình chạy 50 cases đảm bảo không bị đụng độ file rác.

### Cách triển khai
1. **Pydantic Contract Models:** Chuẩn hóa toàn bộ cấu trúc tin nhắn giữa các Agent.
2. **Quality Gate Verifier:** Kiểm tra giới hạn số phần tử, kiểm tra sự tồn tại của ID đối soát với facts/DAL (Grounded Evidence), đối soát tài chính bằng Decimal arithmetic, và kiểm tra tính nhất quán giữa `case_status` và `recommended_refund_brl`.
3. **Async Coordinator & Per-Agent Tracing:** Sử dụng `asyncio.gather` thực hiện fan-out song song 3 Agent điều tra, gộp facts và bảo toàn correlation IDs (`trace_id`, `run_id`), đồng thời ghi log chi tiết cho từng Agent (`order_seller_agent`, `payment_agent`, `delivery_agent`, `policy_agent`, `verifier_agent`).
4. **Batch Runner & Zip Validation:** Chạy 50 case có bọc `try...except` cô lập lỗi từng case, ghi file atomic write (`.tmp` -> replace) và đóng gói tệp ZIP submission chỉ chứa đúng 50 file `EC_*.json`.
5. **Dynamic Commit SHA:** Tự động gọi `git rev-parse HEAD` trong `src/tracing.py` để ghi SHA thực tế vào `logging/metadata.json`.

### Cách xác minh

```bash
.\.venv\Scripts\pytest tests/ -v
.\.venv\Scripts\python run.py
```

- **Kết quả mong đợi:** Tất cả 36 bài test cho Contracts, Verifier, LLM Client và End-to-End đều PASSED (100%). Chạy `run.py` thành công 50/50 cases và nén file ZIP chứa đúng 50 JSON.
- **Kết quả thực tế:** 36/36 PASSED, 50/50 cases succeeded.

## 5. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Đào Nam Hải  
**Ngày xác nhận:** 2026-08-05
