# Kế hoạch phân công nhóm - Multi-Agent E-commerce Dispute Resolution

## 1. Mục tiêu

Kế hoạch này phân chia công việc cho nhóm ba thành viên dựa trên kiến trúc trong `architecture.md`. Mục tiêu là triển khai song song tối đa, xác định rõ ownership và chỉ ra các dependency bắt buộc trước khi tích hợp.

Kết quả cuối cùng cần có:

- Pipeline multi-agent xử lý đủ 50 case trong `input/`.
- Đúng sáu agent theo kiến trúc: Coordinator, Order & Seller, Payment, Delivery, Policy và Verifier.
- Đúng 50 file JSON trong `output/`.
- `logging/trace.jsonl` chứa trace của lượt chạy mới nhất.
- `logging/metadata.json` mô tả đúng model, framework và runtime thực tế.
- Source code, test, `architecture.md` và báo cáo cá nhân được commit lên repo.
- File zip chỉ chứa 50 JSON output, không chứa source, `.env`, trace hoặc metadata.

## 2. Phân công chính

| Thành viên | Agent/module sở hữu | Trách nhiệm chính |
|---|---|---|
| Người 1 | Data Access, Order & Seller Agent, Delivery Agent | Đọc/join CSV, điều tra order-item-seller và kiểm tra các mốc giao hàng |
| Người 2 | Payment Agent, Policy Agent | Đối soát thanh toán, áp dụng `EC_POLICY_V1`, tính refund và resolution action |
| Người 3 | Coordinator Agent, Verifier Agent, Batch Runner | Điều phối handoff, kiểm chứng kết quả, chạy 50 case, ghi trace và đóng gói submission |

Mỗi người tự viết unit test cho module mình sở hữu. Người 3 chịu trách nhiệm test tích hợp toàn hệ thống, nhưng lỗi thuộc module nào thì người sở hữu module đó chịu trách nhiệm sửa.

## 3. Giai đoạn 0 - Thống nhất contract

**Thời lượng đề xuất:** 30-45 phút.

**Cách thực hiện:** cả ba người làm cùng nhau. Giai đoạn này chưa thể làm hoàn toàn song song vì mọi module đều phụ thuộc vào contract chung.

Các nội dung phải thống nhất:

- Schema của `InvestigationRequest`.
- Schema của `OrderSellerFacts`, `PaymentFacts` và `DeliveryFacts`.
- Schema của `ResolutionDraft` và `VerificationResult`.
- Cách biểu diễn timestamp, số tiền và provenance.
- Tên module, class và method.
- Model sử dụng phải có tối đa 10B parameters.
- Quy tắc tạo `run_id`, `trace_id` và `message_id`.
- Các event bắt buộc trong `trace.jsonl`.

Người 3 chịu trách nhiệm ghi contract đã thống nhất vào:

```text
src/contracts/messages.py
src/contracts/output_schema.py
```

**Điều kiện hoàn thành:** cả ba thành viên cùng xác nhận schema và có thể dùng cùng một bộ fixture/mock message.

## 4. Giai đoạn 1 - Triển khai song song

Sau khi khóa contract, ba thành viên bắt đầu ba luồng công việc song song.

### 4.1 Người 1 - Data và Delivery

#### Task P1.1 - Data Access Layer

- Load các CSV cần thiết một lần khi tiến trình bắt đầu.
- Xây các index:
  - `orders_by_order_id`
  - `items_by_order_id`
  - `payments_by_order_id`
  - `seller_by_seller_id`
- Cung cấp API truy vấn read-only cho các agent.
- Xử lý order không có item hoặc payment.
- Trả record kèm provenance để dựng evidence.

**File sở hữu:** `src/data_access.py`

**Bàn giao:** API truy vấn và fixture dữ liệu cho Người 2, Người 3.

#### Task P1.2 - Order & Seller Agent

- Tìm order theo `claimed_order_id`.
- Lấy toàn bộ item và seller của order.
- Không giả định một order chỉ có một item hoặc seller.
- Tính `item_total_brl`.
- Tính `freight_total_brl`.
- So sánh `order_delivered_carrier_date` với từng `shipping_limit_date`.
- Tạo candidate evidence cho order, item và seller.
- Trả `OrderSellerFacts` đúng contract.

**File sở hữu:** `src/agents/order_seller.py`

**Phụ thuộc:** contract chung và API của Task P1.1.

#### Task P1.3 - Delivery Agent

- Lấy ngày giao thực tế và ngày giao dự kiến.
- So sánh `order_delivered_customer_date` với `order_estimated_delivery_date`.
- Trả `delivered_late`, `delivered_within_estimate` hoặc trạng thái thiếu timestamp.
- Trả mốc carrier nhận hàng để Policy Agent kết hợp với shipping limit.
- Không suy diễn tracking checkpoint không tồn tại trong dataset.
- Trả `DeliveryFacts` đúng contract.

**File sở hữu:** `src/agents/delivery.py`

**Phụ thuộc:** contract chung và API của Task P1.1.

#### Task P1.4 - Unit tests

- Test order có nhiều item.
- Test order có nhiều seller.
- Test order không có item.
- Test giao trước, đúng và sau estimated date.
- Test carrier nhận trước, đúng và sau shipping limit.
- Test item total và freight total.

**File sở hữu:** `tests/test_data_access.py`, `tests/test_order_seller.py`, `tests/test_delivery.py`.

#### Dependency nội bộ của Người 1

```text
P1.1 Data Access
  ├──> P1.2 Order & Seller Agent
  └──> P1.3 Delivery Agent

P1.2 + P1.3
  └──> P1.4 Unit tests với dữ liệu thật
```

Trong lúc P1.1 chưa hoàn thành, P1.2 và P1.3 vẫn có thể được viết bằng fixture/mock record theo contract chung.

### 4.2 Người 2 - Payment và Policy

#### Task P2.1 - Payment Agent

- Truy xuất toàn bộ payment row theo `order_id`.
- Cộng `payment_value` đúng một lần cho mỗi row.
- Không nhân `payment_value` với `payment_installments`.
- Giữ `payment_sequential` để dựng evidence.
- Tính `payment_total_brl`.
- Đối soát payment với `item_total_brl + freight_total_brl`.
- Chấp nhận sai số tối đa `0.10 BRL`.
- Trả `PaymentFacts` đúng contract.

**File sở hữu:** `src/agents/payment.py`

**Phụ thuộc:** contract chung. Có thể dùng mock Data Access trước, sau đó tích hợp API thật từ P1.1.

#### Task P2.2 - Policy Rules

Cài đặt sáu luật deterministic theo đúng thứ tự ưu tiên:

1. `canceled_order_paid`
2. `unavailable_order_paid`
3. `late_delivery_seller`
4. `late_delivery_logistics`
5. `valid_split_payment`
6. `unsupported_late_claim`

Yêu cầu:

- Dùng `Decimal` cho phép tính tiền.
- Làm tròn output đến hai chữ số thập phân.
- Mỗi case chỉ chọn một `primary_issue`.
- Không để model tự tính refund hoặc tự tạo evidence.

**File sở hữu:** `src/policy_rules.py`

**Phụ thuộc:** chỉ phụ thuộc contract chung; có thể phát triển hoàn toàn bằng mock facts.

#### Task P2.3 - Policy Agent

- Nhận `OrderSellerFacts`, `PaymentFacts` và `DeliveryFacts` đã được Coordinator gộp.
- Chọn `primary_issue` theo đúng thứ tự policy.
- Xác định `case_status`.
- Xác định root cause và responsible party.
- Tính `recommended_refund_brl`.
- Chọn resolution action.
- Chỉ sử dụng candidate evidence có provenance.
- Trả `ResolutionDraft` đúng output schema.

**File sở hữu:** `src/agents/policy.py`

**Phụ thuộc:** Task P2.2 và contract facts. Test với dữ liệu thật phụ thuộc kết quả từ Người 1.

#### Task P2.4 - Unit tests

- Ít nhất một test cho mỗi policy rule.
- Test thứ tự ưu tiên giữa các rule.
- Test split payment hợp lệ.
- Test sai số payment đúng `0.10` và lớn hơn `0.10`.
- Test full refund và freight refund.
- Test làm tròn bằng `Decimal`.
- Test responsible party và action tương ứng từng root cause.

**File sở hữu:** `tests/test_payment.py`, `tests/test_policy_rules.py`, `tests/test_policy_agent.py`.

#### Dependency nội bộ của Người 2

```text
P2.2 Policy Rules
  └──> P2.3 Policy Agent

OrderSellerFacts ──┐
PaymentFacts ──────┼──> P2.3 chạy với dữ liệu thật
DeliveryFacts ─────┘
```

P2.1 và P2.2 có thể bắt đầu ngay sau khi khóa contract. P2.3 được viết và test bằng mock facts, không cần đợi Người 1 hoàn thành.

### 4.3 Người 3 - Điều phối và kiểm chứng

#### Task P3.1 - Contract Models

- Cài đặt schema cho các message handoff.
- Cài đặt output schema.
- Validate enum, type và giới hạn số phần tử.
- Tạo fixtures dùng chung cho Người 1 và Người 2.

**File sở hữu:** `src/contracts/messages.py`, `src/contracts/output_schema.py`.

**Phụ thuộc:** quyết định chung ở Giai đoạn 0.

#### Task P3.2 - Coordinator Agent

- Validate case input.
- Tạo correlation IDs.
- Fan-out tới Order & Seller, Payment và Delivery Agent.
- Cho phép ba investigation agent chạy song song.
- Nhận và gộp ba response theo `case_id` và `order_id`.
- Gọi Policy Agent sau khi đủ facts.
- Gọi Verifier Agent sau khi có `ResolutionDraft`.
- Không tự áp policy hoặc sửa output để vượt verifier.

**File sở hữu:** `src/agents/coordinator.py`

**Phụ thuộc:** P3.1. Có thể dùng mock responses trước khi agent thật hoàn thành.

#### Task P3.3 - Verifier Agent

- Validate output schema.
- Kiểm tra giới hạn entity, evidence, causes, parties và actions.
- Kiểm tra evidence ID đúng định dạng và tồn tại trong CSV.
- Tính lại item, freight, payment và refund.
- Kiểm tra tính nhất quán giữa issue, root cause, party và action.
- Kiểm tra `action_required` khi refund lớn hơn 0.
- Kiểm tra `no_action` khi refund bằng 0.
- Trả `VerificationResult` gồm `valid`, `errors`, `warnings`.

**File sở hữu:** `src/agents/verifier.py`

**Phụ thuộc:** P3.1. Kiểm tra evidence thật phụ thuộc Data Access từ P1.1.

#### Task P3.4 - Batch Runner và Logging

- Quét đúng `EC_001.json` đến `EC_050.json`.
- Tạo `run_id` cho lượt chạy và `trace_id` cho từng case.
- Khởi tạo mới `logging/trace.jsonl`, không append trace cũ.
- Chạy case có isolation; một case lỗi không làm dừng toàn batch.
- Chỉ ghi output sau khi Verifier trả `valid=true`.
- Ghi output theo cách atomic.
- Tạo `logging/metadata.json` từ cấu hình thực tế.
- Kiểm tra đủ 50 output trước khi tạo zip.

**File sở hữu:** `run.py`, `src/tracing.py`, `src/settings.py`.

**Phụ thuộc:** P3.2, P3.3 và pipeline tích hợp hoàn chỉnh.

#### Task P3.5 - Integration tests

- Contract test cho mọi message handoff.
- Verifier test với output đúng và output sai.
- Test case lỗi không làm dừng batch.
- End-to-end test với một case đại diện cho mỗi primary issue.
- Chạy đủ 50 input và kiểm tra đủ 50 output.
- Kiểm tra trace có terminal event cho từng case.
- Kiểm tra zip chỉ chứa 50 JSON output.

**File sở hữu:** `tests/test_contracts.py`, `tests/test_verifier.py`, `tests/test_end_to_end.py`.

#### Dependency nội bộ của Người 3

```text
P3.1 Contract Models
  ├──> P3.2 Coordinator
  └──> P3.3 Verifier

P3.2 + P3.3
  └──> P3.4 Batch Runner
       └──> P3.5 End-to-end tests
```

Coordinator và Verifier có thể được viết bằng mock response trước khi module của Người 1 và Người 2 hoàn thành.

## 5. Các cổng tích hợp bắt buộc

### Gate 1 - Investigation handoff

**Cần hoàn thành:**

- P1.2 Order & Seller Agent.
- P1.3 Delivery Agent.
- P2.1 Payment Agent.
- P3.1 Contract Models.
- Phần fan-out/fan-in của P3.2 Coordinator.

**Kiểm tra:**

- Coordinator gửi cùng `case_id`, `order_id`, `run_id` và `trace_id`.
- Ba agent trả response đúng schema.
- Coordinator không làm mất item, seller hoặc payment row.
- Trace thể hiện ba agent thực sự được gọi riêng biệt.

**Dependency:** Gate 1 phải hoàn thành trước khi Policy Agent chạy với dữ liệu thật.

### Gate 2 - Policy integration

**Phụ thuộc:** Gate 1.

**Cần hoàn thành:**

- P2.2 Policy Rules.
- P2.3 Policy Agent.
- Phần gọi Policy Agent của P3.2 Coordinator.

**Kiểm tra:**

- Mỗi case có đúng một `primary_issue`.
- Các luật được áp dụng đúng thứ tự ưu tiên.
- Refund và action nhất quán.
- Evidence được lấy từ facts có provenance.

**Dependency:** Gate 2 phải hoàn thành trước khi chạy Verifier end-to-end.

### Gate 3 - Verification integration

**Phụ thuộc:** Gate 2.

**Cần hoàn thành:**

- P3.3 Verifier Agent.
- Data Access từ P1.1 để kiểm tra evidence tồn tại.
- Output draft từ P2.3 Policy Agent.

**Kiểm tra:**

- Output sai schema bị chặn.
- Evidence không tồn tại bị chặn.
- Refund sai bị chặn.
- Responsible party hoặc action sai bị chặn.
- Output hợp lệ được trả cho Batch Runner.

### Gate 4 - Chạy đủ 50 case

**Phụ thuộc:** Gate 3.

**Cần hoàn thành:**

- P3.4 Batch Runner và Logging.
- Unit test của cả ba thành viên.
- Integration test quan trọng.

**Các bước:**

1. Khởi tạo output và trace cho lượt chạy mới.
2. Chạy đủ 50 case.
3. Phân lỗi về đúng module sở hữu.
4. Mỗi người sửa lỗi module của mình.
5. Chạy lại toàn bộ 50 case.
6. Kiểm tra terminal trace cho từng case.
7. Kiểm tra đủ `EC_001.json` đến `EC_050.json`.

### Gate 5 - Submission

**Phụ thuộc:** Gate 4 thành công với đủ 50 case.

**Cần kiểm tra:**

- `metadata.json` khai báo đúng model `<=10B`, framework và runtime.
- `architecture.md` phản ánh đúng code cuối cùng.
- Mỗi thành viên có báo cáo cá nhân đúng phần trực tiếp thực hiện.
- Toàn bộ source code đã được commit.
- Git không chứa `.env`, API key hoặc secret.
- Zip chỉ chứa đúng 50 JSON trong `output/`.

## 6. Sơ đồ dependency tổng thể

```text
[Giai đoạn 0: Khóa contracts]
                 │
        ┌────────┼────────┐
        ▼        ▼        ▼
     Người 1   Người 2   Người 3
     Data      Payment   Contracts code
     Order     Policy    Coordinator mock
     Delivery            Verifier + Runner
        │        │        │
        └────────┼────────┘
                 ▼
       Gate 1: Investigation
                 │
                 ▼
          Gate 2: Policy
                 │
                 ▼
       Gate 3: Verification
                 │
                 ▼
         Gate 4: Chạy 50 case
                 │
                 ▼
   Gate 5: Trace + Metadata + Output ZIP
```

## 7. Kế hoạch theo phiên làm việc

| Phiên | Người 1 | Người 2 | Người 3 | Dependency |
|---|---|---|---|---|
| Phiên 0 | Thống nhất contract | Thống nhất contract | Ghi contract | Tất cả cùng làm |
| Phiên 1 | Data Access | Payment + policy rules bằng mock | Contract code + Coordinator mock | Chỉ cần contract |
| Phiên 2 | Order & Seller + Delivery | Policy Agent + unit tests | Verifier + tracing bằng mock | Làm song song |
| Phiên 3 | Tích hợp facts thật | Tích hợp payment/policy thật | Tích hợp Coordinator | Gate 1 |
| Phiên 4 | Sửa lỗi data/domain | Sửa lỗi policy/money | Tích hợp Verifier + runner | Gate 2 và Gate 3 |
| Phiên 5 | Rà totals/timestamp | Rà sáu policy rule | Chạy 50 case + kiểm zip | Gate 4 |
| Phiên 6 | Báo cáo cá nhân | Báo cáo cá nhân | Metadata, tài liệu và báo cáo cá nhân | Pipeline đã ổn định |

## 8. Quy tắc làm việc với Git

Mỗi thành viên dùng branch riêng:

```text
feature/data-investigation
feature/payment-policy
feature/orchestration-verification
```

Thứ tự merge đề xuất:

1. Merge contract models của Người 3.
2. Merge Data Access và investigation agents của Người 1.
3. Merge Payment và Policy của Người 2.
4. Merge Coordinator, Verifier và Batch Runner của Người 3.
5. Chạy integration trên branch chung.
6. Chỉ merge vào `main` khi pipeline đã qua các gate cần thiết.

Quy tắc tránh conflict:

- Người 1 sở hữu `src/data_access.py`, `src/agents/order_seller.py`, `src/agents/delivery.py`.
- Người 2 sở hữu `src/agents/payment.py`, `src/agents/policy.py`, `src/policy_rules.py`.
- Người 3 sở hữu `src/contracts/`, `src/agents/coordinator.py`, `src/agents/verifier.py`, `src/tracing.py`, `run.py`.
- Mỗi người thêm test vào file riêng.
- Không sửa file thuộc ownership của người khác nếu chưa trao đổi.
- Pull/rebase branch chung trước khi tạo pull request hoặc merge.
- Commit nhỏ, message mô tả đúng một thay đổi chính.

## 9. Checklist bàn giao của từng người

### Người 1

- [ ] Data Access đọc đúng các CSV cần thiết.
- [ ] Order & Seller Agent trả đúng facts contract.
- [ ] Delivery Agent trả đúng facts contract.
- [ ] Các phép tính item/freight đã dùng `Decimal`.
- [ ] Unit tests module dữ liệu đã chạy thành công.
- [ ] Đã bàn giao fixture và API cho Người 2, Người 3.
- [ ] Báo cáo cá nhân mô tả đúng phần đã thực hiện.

### Người 2

- [ ] Payment Agent cộng đúng mọi payment row.
- [ ] Không nhân payment với installments.
- [ ] Đã cài đủ sáu policy rule theo đúng thứ tự.
- [ ] Refund, action và responsible party nhất quán.
- [ ] Unit tests cho payment và policy đã chạy thành công.
- [ ] Đã bàn giao `ResolutionDraft` mẫu cho Người 3.
- [ ] Báo cáo cá nhân mô tả đúng phần đã thực hiện.

### Người 3

- [ ] Contract models được cả nhóm thống nhất.
- [ ] Coordinator thể hiện handoff thật giữa các agent.
- [ ] Verifier chặn schema, evidence và refund sai.
- [ ] Batch Runner xử lý đủ 50 case.
- [ ] Trace chỉ chứa lượt chạy mới nhất.
- [ ] Metadata phản ánh đúng runtime thực tế.
- [ ] Zip chỉ chứa đúng 50 JSON output.
- [ ] Báo cáo cá nhân mô tả đúng phần đã thực hiện.

## 10. Definition of Done của cả nhóm

Bài lab chỉ được xem là hoàn thành khi:

- [ ] Có đủ sáu agent và mỗi agent có trách nhiệm riêng.
- [ ] Ba investigation agent chạy song song hoặc trace thể hiện rõ cơ chế fan-out/fan-in.
- [ ] Policy chỉ chạy sau khi nhận đủ facts.
- [ ] Output chỉ được ghi sau khi Verifier thông qua.
- [ ] Có đúng 50 output và tất cả parse được theo schema.
- [ ] Không có evidence ID không tồn tại.
- [ ] Mỗi case có terminal event trong trace.
- [ ] Model được khai báo trong source và có tối đa 10B parameters.
- [ ] Không commit `.env`, API key hoặc secret.
- [ ] Source code đã được commit trước khi tạo submission zip.
- [ ] `architecture.md` và kế hoạch này phản ánh đúng implementation cuối cùng.
