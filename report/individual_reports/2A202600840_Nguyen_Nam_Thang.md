# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Thang Nguyen
- **Student ID**: 2A202600840
- **Date**: 2026-06-01

---

## I. Technical Contribution (15 Points)

Trong lab này, tôi phụ trách baseline chatbot, ReAct loop, test runner và phần cải tiến Agent v2 dựa trên failure trace. Mục tiêu là chứng minh rõ quá trình: chatbot baseline thất bại, Agent v1 chạy được nhưng còn lỗi, sau đó Agent v2 sửa lỗi bằng dữ liệu từ log.

- **Modules Implemented / Updated**:
  - `chatbot.py`: Chatbot Baseline v1, trả lời trực tiếp, không gọi tool.
  - `src/agent/agent.py`: ReAct loop, trace từng bước và normalize `order_id` trong tool arguments.
  - `main.py`: test runner deterministic, evaluator cho Agent v2, ghi `TESTCASE_RESULT`.
  - `tools/cs_tools_p1.py`: tool đơn hàng `get_order_status`, `get_order_details`, `count_orders`.
  - `tools/cs_tools_p4.py`: bổ sung `search_faq(query)` để trả lời FAQ từ `FAQ_DB`.

- **Code Highlights**:
  - `src/agent/agent.py`: `run_with_trace()` trả `answer` và `trace` cho UI/log.
  - `src/agent/agent.py`: `_execute_tool()` normalize `order_id`, giúp `ORD002` trở thành `ORD-002`.
  - `main.py`: `TestCaseLLMProvider` route ETA/tracking sang `get_shipping_info`.
  - `main.py`: `TestCaseLLMProvider` route câu hỏi chính sách sang `search_faq`.
  - `tools/cs_tools_p4.py`: `search_faq()` dùng keyword matching trên `FAQ_DB`.

---

## Test Results

Commands:

```bash
.venv/bin/python -B chatbot.py
.venv/bin/python -B main.py
```

Latest log source:

```text
logs/2026-06-01.log
```

| Version | Result | Notes |
| :--- | :--- | :--- |
| Chatbot Baseline v1 | 0/7 pass | Không có tool, không xác minh được dữ liệu nội bộ. |
| ReAct Agent v1 | 4/7 pass, 3 XFAIL | Fail ở `ORD002`, ETA/tracking, FAQ đổi trả. |
| ReAct Agent v2 | 7/7 pass | Sửa cả 3 lỗi v1 bằng normalization, routing và FAQ tool. |

Agent v2 final run:

```text
Running 7 testcases | real_llm=False
Summary: 7 passed, 0 expected failures, 0 unexpected outcomes
```

Agent v2 testcase table:

| Testcase | Result | Tool / Fix |
| :--- | :--- | :--- |
| `order_status_shipping` | PASS | `get_order_status` |
| `order_details_delivered` | PASS | `get_order_details` |
| `count_delivered_orders` | PASS | `count_orders(status="delivered")` |
| `missing_order` | PASS | Structured `order_not_found` handling |
| `malformed_order_id_no_hyphen` | PASS | Normalize `ORD002` -> `ORD-002` |
| `shipping_eta_tracking` | PASS | `get_shipping_info` |
| `faq_return_policy` | PASS | `search_faq` |

Telemetry summary for latest v2 mock run:

- Started at: `2026-06-01T17:35:11`
- Total testcases: 7
- Passed: 7
- Expected failures: 0
- Average steps per testcase: 2.00
- Total mock tokens: 562
- Estimated mock cost: 0.00562

---

## II. Debugging Case Study (10 Points)

- **Problem Description**:

Agent v1 failed three cases after the happy path worked:

| Failure | v1 Behavior | Root Cause |
| :--- | :--- | :--- |
| `ORD002` | Asked user for order id again | Extractor only recognized `ORD-` format. |
| ETA/tracking | Returned only order status | Evaluator routed ETA question to `get_order_status`. |
| FAQ return policy | Asked for order id | No FAQ tool or FAQ route existed. |

- **Log Source**:

`logs/2026-06-01.log`, event `TESTCASE_RESULT`.

v1 failure trace for ETA showed:

```text
Action: get_order_status(order_id="ORD-002")
Observation: {"status_vn": "Đang giao hàng", "order_date": "2026-05-30"}
Final Answer: Đơn ORD-002 hiện là Đang giao hàng, ngày đặt 2026-05-30.
```

Expected answer needed `GHTK789012` and `2026-06-02`, so the trace proved the wrong tool was selected.

- **Solution**:

Agent v2 fixed the trace root causes:

```text
Action: get_shipping_info(order_id="ORD-002")
Observation: {"carrier": "GHTK", "tracking_code": "GHTK789012", "estimated_delivery_date": "2026-06-02"}
Final Answer: Đơn ORD-002 đang được giao bởi GHTK, mã tracking GHTK789012, dự kiến giao ngày 2026-06-02.
```

For FAQ:

```text
Action: search_faq(query="Chính sách đổi trả như thế nào?")
Observation: {"answer": "Đổi trả trong 7 ngày kể từ ngày nhận hàng. Sản phẩm còn nguyên tag, chưa qua sử dụng."}
Final Answer: Đổi trả trong 7 ngày kể từ ngày nhận hàng. Sản phẩm còn nguyên tag, chưa qua sử dụng.
```

For malformed order ids, `ORD002` is normalized to `ORD-002` before tool execution.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**:

Chatbot baseline chỉ trả lời trực tiếp nên không thể xác minh đơn hàng, tracking hoặc FAQ nội bộ. ReAct Agent tốt hơn vì tách rõ `Thought`, `Action`, `Observation`, sau đó final answer dựa trên dữ liệu thật từ tool.

2. **Reliability**:

Agent v1 vẫn có thể fail nếu chọn sai tool hoặc thiếu tool. Điều quan trọng là trace cho biết chính xác lỗi nằm ở đâu. Sau khi xem trace, Agent v2 không sửa bằng đoán prompt chung chung mà sửa đúng routing, normalization và tool coverage.

3. **Observation**:

Observation là bằng chứng hệ thống. Với ETA, observation từ `get_shipping_info` chứa `GHTK789012` và `2026-06-02`, nên final answer đáng tin hơn câu trả lời tự suy đoán. Với FAQ, observation từ `search_faq` giữ câu chữ chính sách nội bộ.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Tách testcase khỏi `main.py` sang JSON/YAML để thêm case mà không sửa code.
- **Safety**: Thêm xác nhận user trước các tool có tác động trạng thái như tạo ticket, hoàn tiền hoặc escalation.
- **Performance**: Ghi thêm run id, duration theo testcase và token theo từng step.
- **Reliability**: Thêm regression tests cho toàn bộ tool P2-P5, không chỉ 7 case chính.
- **Production Readiness**: Khi dùng LLM thật, thêm retry có kiểm soát nếu model trả sai format `Action`.
