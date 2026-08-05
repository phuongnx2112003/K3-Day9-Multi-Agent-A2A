# Member Role Report — Day 9: Multi Agent A2A

## 1. Thông tin cá nhân

| Thông tin       | Nội dung                  |
| --------------- | ------------------------- |
| Họ và tên       | Nguyễn Đào Nam Hải        |
| MSSV            | 2A202601037               |
| Khóa/Lớp        | K3                        |
| Vai trò chính   | Thành viên 3 (Coordinator, Verifier, Batch Runner & Observability) |
| Ngày hoàn thành | 2026-08-05                |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Contracts & Schemas | `src/contracts/messages.py`<br>`src/contracts/output_schema.py`<br>`src/contracts/fixtures.py` | Đề bài & Quy tắc Handoff | Pydantic Models & Mock Fixtures dùng chung cho cả nhóm | Hoàn thành |
| Verifier Agent | `src/agents/verifier.py` | `ResolutionDraft`, Facts | `VerificationResult` (valid=True/False) | Hoàn thành |
| Coordinator Agent | `src/agents/coordinator.py` | `CaseInput` từ Batch Runner | Async Fan-out, Facts Merging & Verifier Gate | Hoàn thành |
| Batch Runner & Observability | `run.py`<br>`src/tracing.py`<br>`src/settings.py` | 50 file `input/EC_xxx.json` | 50 output JSON, `trace.jsonl`, `metadata.json`, submission ZIP | Hoàn thành |
| Unit & Integration Tests | `tests/test_contracts.py`<br>`tests/test_verifier.py`<br>`tests/test_end_to_end.py` | Mock data & Real Pipeline | Bộ test kiểm thử tự động đạt 100% PASSED | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
|---|---|---|
| Thiết kế Handoff Contracts & Fixtures | Thành viên 1 & Thành viên 2 | Cung cấp sẵn mock data giúp TV1 & TV2 viết test độc lập ngay từ Giai đoạn 0 |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
|---|---|---|---|
| Khóa Handoff Contracts | `src/contracts/messages.py` | Pydantic Schemas | `pytest tests/test_contracts.py` |
| Triển khai Quality Gate Verifier | `src/agents/verifier.py` | Verifier Agent | `pytest tests/test_verifier.py` |
| Triển khai Orchestrator Coordinator | `src/agents/coordinator.py` | Async Fan-out Coordinator | `pytest tests/test_end_to_end.py` |
| Triển khai Batch Runner & Submission Zip | `run.py` | 50 outputs & ZIP package | `python run.py` |

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Xây dựng trục điều phối (Orchestrator), quản lý hợp đồng tin nhắn (Handoff Contracts), kiểm định chất lượng độc lập (Quality Gate Verifier) và tự động hóa quy trình chạy 50 cases đảm bảo case isolation và tính chính xác của các bằng chứng (Evidence IDs).

### Cách triển khai
1. **Pydantic Contract Models:** Chuẩn hóa toàn bộ cấu trúc tin nhắn giữa các Agent.
2. **Quality Gate Verifier:** Kiểm tra giới hạn số phần tử, kiểm tra sự tồn tại của ID trong CSV thực tế, đối soát tài chính bằng Decimal arithmetic, và kiểm tra tính nhất quán giữa `case_status` và `recommended_refund_brl`.
3. **Async Coordinator:** Sử dụng `asyncio.gather` thực hiện fan-out song song 3 Agent điều tra, gộp facts và bảo toàn correlation IDs (`trace_id`, `run_id`).
4. **Batch Runner & Zip:** Chạy 50 case độc lập, ghi file atomic write và đóng gói tệp ZIP submission chuẩn hóa.

### Cách xác minh

```bash
.\.venv\Scripts\pytest tests/ -v
```

- **Kết quả mong đợi:** Tất cả các bài test cho Contracts, Verifier và End-to-End đều PASSED.
- **Kết quả thực tế:** 100% PASSED.

## 5. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Đào Nam Hải  
**Ngày xác nhận:** 2026-08-05
