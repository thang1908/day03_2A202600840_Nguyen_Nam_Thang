# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: Customer Support ReAct Team
- **Team Members**: 
2A202600855 - Nguyễn Tiến Huân

2A202600840 - Nguyễn Nam Thắng

2A202600663 - Phạm Huy Cảnh

2A202600810 - Nguyễn Xuân Tới

2A202600575 - Phạm Thị Bích Ngọc

- **Deployment Date**: 2026-06-01

---

## 1. Executive Summary

Nhóm xây dựng một Customer Support ReAct Agent cho các tác vụ hỗ trợ khách hàng như kiểm tra trạng thái đơn hàng, xem chi tiết đơn, đếm đơn theo trạng thái, tra ETA/tracking, trả lời FAQ và xử lý trường hợp đơn hàng không tồn tại. Agent sử dụng pattern `Thought -> Action -> Observation -> Final Answer`, gọi tool thật từ mock database thay vì trả lời bằng suy đoán ngôn ngữ tự nhiên.

- **Chatbot Baseline v1**: 0/7 pass với mock baseline không dùng tool
- **Final Test Suite**: 7 test cases
- **Agent v1 Result**: 4/7 pass, 3 expected failures
- **Agent v2 Result**: 7/7 pass
- **Expected Failures for Analysis**: 0/7 sau cải tiến v2
- **Unexpected Failures**: 0
- **Operational Result**: Test runner ổn định, có trace và log đầy đủ cho baseline, v1 failures, v2 fixes và P5 tool traces.

Kết quả chạy baseline:

```bash
python3 chatbot.py
```

```text
Running chatbot baseline v1 on 7 testcases | real_llm=False
Baseline Summary: 0 passed, 7 failed
Logs: logs/<today>.log
```

Kết quả chạy agent:

```bash
python3 main.py
```

```text
Running 7 testcases | real_llm=False
Summary: 7 passed, 0 expected failures, 0 unexpected outcomes
Logs: logs/<today>.log
```

**Key Outcome**: So với chatbot baseline trả lời trực tiếp, ReAct Agent v2 đáng tin hơn ở các câu hỏi cần dữ liệu cụ thể vì agent gọi tool và dựa trên `Observation`. Ba lỗi v1 được phát hiện từ trace đã được xử lý: normalize `ORD002`, route ETA/tracking sang `get_shipping_info`, và thêm `search_faq` cho chính sách đổi trả.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation

Luồng xử lý chính:

```text
User Question
  -> System Prompt with Tool Descriptions
  -> LLM generates Thought + Action
  -> Agent parses Action
  -> Agent executes registered tool
  -> Tool returns JSON Observation
  -> LLM receives Observation
  -> LLM returns Final Answer in Vietnamese
  -> Logger writes trace and metrics
```

Các module chính:

- `src/agent/agent.py`: triển khai ReAct loop, parse action, execute tool, lưu trace.
- `tools/registry.py`: gom danh sách tool từ các file `cs_tools_p*.py`.
- `tools/cs_tools_p1.py`: chứa các tool đơn hàng đang hoạt động.
- `tools/cs_tools_p2.py`: chứa tool vận chuyển `get_shipping_info`.
- `tools/cs_tools_p4.py`: chứa tool FAQ `search_faq`.
- `tools/cs_tools_p5.py`: chứa tool tạo ticket và chuyển nhân viên thật.
- `src/telemetry/logger.py`: ghi structured log dạng JSON vào `logs/YYYY-MM-DD.log`.
- `src/telemetry/metrics.py`: ghi token, latency và cost estimate.
- `chatbot.py`: baseline v1 trả lời trực tiếp, không gọi tool, dùng để so sánh với Agent v2.
- `main.py`: FastAPI app và CLI test runner.

### 2.2 Tool Definitions (Inventory)

| Tool Name | Input Format | Use Case | Status |
| :--- | :--- | :--- | :--- |
| `get_order_status` | `order_id: str` | Kiểm tra trạng thái đơn hàng, ngày đặt, ngày giao nếu có | Implemented |
| `get_order_details` | `order_id: str` | Lấy sản phẩm, số lượng, tổng tiền, thông tin khách hàng | Implemented |
| `count_orders` | `status: str = None`, `customer_id: str = None` | Đếm đơn hàng theo trạng thái hoặc khách hàng | Implemented |
| `get_shipping_info` | `order_id: str` | Lấy hãng vận chuyển, tracking, ETA | Implemented in v2 |
| `search_faq` | `query: str` | Trả lời chính sách đổi trả, phí ship, thanh toán | Implemented in v2 |
| `create_support_ticket` | `order_id: str`, `issue: str`, `priority: str` | Tạo ticket hỗ trợ | Implemented |
| `escalate_to_human` | `ticket_id: str`, `reason: str` | Chuyển cho nhân viên thật | Implemented |

### 2.3 LLM Providers Used

- **Primary for app runtime**: OpenAI provider via `DEFAULT_PROVIDER=openai`.
- **Secondary**: Gemini provider via `DEFAULT_PROVIDER=gemini`.
- **Local option**: `LocalProvider` using llama-cpp model path.
- **Evaluation provider**: `TestCaseLLMProvider` in `main.py`, used for deterministic local testcase runs without API key.

The deterministic mock provider is not a production LLM. It is used to test the ReAct parser, tool execution, trace logging and failure reporting repeatably.

---

## 3. Telemetry & Performance Dashboard

Final test run:

- **Log Source**: `logs/2026-06-01.log`
- **Chatbot Baseline Run Started At**: `2026-06-01T17:34:07`
- **Agent v2 Run Started At**: `2026-06-01T17:35:11`
- **Chatbot Baseline Passed**: 0/7
- **Total Test Cases**: 7
- **Passed**: 7
- **Expected Failed**: 0
- **Unexpected Failed**: 0
- **Average Steps per Task**: 2.00
- **P50 Latency**: 0 ms with mock provider
- **Max Latency**: 0 ms with mock provider
- **Total Mock Tokens**: 562
- **Average Mock Tokens per Task**: 80.29
- **Total Cost Estimate**: 0.00562 using the repository's mock cost formula

Important note: latency and cost are not production values because the final test run used `TestCaseLLMProvider`. They are still useful for checking whether telemetry events are emitted correctly.

### Test Result Table

| Case | Intent | Result | Steps | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `order_status_shipping` | Check status for `ORD-002` | PASS | 2 | Correctly called `get_order_status`. |
| `order_details_delivered` | Get details for `ORD-001` | PASS | 2 | Correctly called `get_order_details`. |
| `count_delivered_orders` | Count delivered orders | PASS | 2 | Correctly called `count_orders(status="delivered")`. |
| `missing_order` | Handle invalid `ORD-999` | PASS | 2 | Returned tool error honestly. |
| `malformed_order_id_no_hyphen` | Infer `ORD002` as `ORD-002` | PASS | 2 | V2 normalizes order id. |
| `shipping_eta_tracking` | Ask ETA/tracking for `ORD-002` | PASS | 2 | V2 called `get_shipping_info`. |
| `faq_return_policy` | Ask return policy FAQ | PASS | 2 | V2 called `search_faq`. |

---

## 4. Root Cause Analysis (RCA) - v1 Failures to v2 Fixes

### Case Study 1: Malformed Order ID

- **Input**: `Đơn ORD002 của tôi đang ở đâu?`
- **Expected**: Agent should normalize `ORD002` into `ORD-002`, then call `get_order_status(order_id="ORD-002")`.
- **v1 Actual**: Agent answered: `Bạn vui lòng cung cấp mã đơn hàng để tôi kiểm tra.`
- **Root Cause**: Current order-id extraction only recognizes tokens beginning with `ORD-`. It does not normalize common user typos such as missing hyphen.
- **v2 Fix**: Added normalization so `ORD002`, `ord002`, and `ORD 002` map to canonical `ORD-002` before tool execution. The deterministic evaluator also emits the canonical order id.
- **v2 Result**: PASS. Trace shows `Action: get_order_status(order_id="ORD-002")`.

### Case Study 2: Shipping ETA Not Available

- **Input**: `Đơn ORD-002 dự kiến giao ngày nào?`
- **Expected**: Answer should include ETA `2026-06-02` and tracking `GHTK789012`.
- **v1 Actual**: Agent answered only: `Đơn ORD-002 hiện là Đang giao hàng, ngày đặt 2026-05-30.`
- **Observation**: The tool call returned order status, not shipping details.
- **Root Cause**: `get_shipping_info` existed in `tools/cs_tools_p2.py`, but the deterministic evaluator routed ETA questions to `get_order_status`, so the agent never used the shipping observation.
- **v2 Fix**: Added ETA/tracking intent routing to `get_shipping_info(order_id)`.
- **v2 Result**: PASS. Final answer includes `GHTK789012` and `2026-06-02`.

### Case Study 3: FAQ Policy Not Answered

- **Input**: `Chính sách đổi trả như thế nào?`
- **Expected**: Answer should mention `Đổi trả trong 7 ngày` and `nguyên tag`.
- **v1 Actual**: Agent asked for an order id instead of answering the FAQ.
- **Root Cause**: `FAQ_DB` exists in mock data, but there was no registered FAQ retrieval tool and no FAQ intent path in the evaluator.
- **v2 Fix**: Implemented `search_faq(query)` in `tools/cs_tools_p4.py`, registered it through `TOOLS_P4`, and added FAQ routing in the evaluator.
- **v2 Result**: PASS. Final answer includes `Đổi trả trong 7 ngày` and `nguyên tag`.

---

## 5. Ablation Studies & Experiments

### Experiment 1: Agent v1 vs Agent v2

| Version | Cases | Result | Insight |
| :--- | :--- | :--- | :--- |
| Agent v1 | 7 | 4 PASS, 3 XFAIL | Worked on canonical order/status questions, failed on malformed id, ETA/tracking, and FAQ. |
| Agent v2 | 7 | 7 PASS | Fixed all three v1 failures using normalization, better routing, and FAQ retrieval. |

**Result**: Strict product-readiness score improved from 57.1% to 100% on the current local suite.

### Experiment 2: Chatbot vs Agent

| Case | Chatbot Baseline v1 Result | Agent v2 Result | Winner |
| :--- | :--- | :--- | :--- |
| Check `ORD-002` status | FAIL: cannot access order system | PASS: calls `get_order_status` and returns exact status | Agent |
| Check `ORD-999` | FAIL: cannot verify missing order | PASS: returns `order_not_found` from tool | Agent |
| Ask delivered order count | FAIL: cannot count internal records | PASS: calls `count_orders(status="delivered")` | Agent |
| Ask return policy | FAIL with safe mock: cannot verify internal FAQ | PASS: calls `search_faq` | Agent |
| Ask ETA/tracking | FAIL: cannot access shipping data | PASS: calls `get_shipping_info` | Agent |

### Experiment 3: Deterministic Mock vs Real LLM

| Provider | Strength | Weakness |
| :--- | :--- | :--- |
| `TestCaseLLMProvider` | Repeatable tests, no API key, stable logs | Does not measure real model reasoning quality |
| OpenAI/Gemini provider | Real model behavior, useful for demo | Requires API key, output may vary, costs money |
| Local provider | Can run offline | Requires model file and local compute |

---

## 6. Production Readiness Review

- **Security**: Validate all tool inputs before execution. Do not expose raw internal errors to users. Add allowlists for tool names and strict schemas for arguments.
- **Guardrails**: Keep `max_steps` to prevent infinite loops. Log `tool_not_found`, `tool_argument_error`, `max_steps`, and parser failures as first-class error categories.
- **Observability**: Continue writing JSON logs for `AGENT_START`, `LLM_METRIC`, `AGENT_END`, and `TESTCASE_RESULT`. Add run IDs so traces across multiple requests can be grouped.
- **Reliability**: Move test cases into a separate JSON/YAML file and run them in CI. Use `XFAIL` only for newly discovered issues with clear owners and target fixes.
- **Scaling**: When tool count grows, use tool routing or retrieval so the prompt does not include every tool. For complex flows, migrate from a single loop to a graph-based agent workflow.
- **Data Coverage**: Expand shipping, FAQ, return/refund, ticket and escalation tests so every contributor's tool has regression coverage.
- **UX**: Keep normalizing common order id formats and ask a targeted clarification only when normalization is ambiguous.

---

## 7. Next Sprint Plan

| Priority | Task | Expected Impact |
| :--- | :--- | :--- |
| P0 | Move test cases out of `main.py` | Easier test maintenance and cleaner app entrypoint. |
| P0 | Add P2-P5 regression cases | Make every team member's tool visible in final grading evidence. |
| P1 | Add run IDs to logs | Group multi-step traces across UI/API/test runs. |
| P1 | Add UI/API trace persistence | Preserve full user request traces beyond test runner logs. |
| P2 | Add real provider regression run | Compare mock vs OpenAI/Gemini behavior. |
