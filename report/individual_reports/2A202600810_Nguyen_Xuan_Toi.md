# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Toi Nguyen
- **Student ID**: [Điền MSSV]
- **Date**: 2026-06-01

---

## I. Technical Contribution (15 Points)

Trong phần lab này, tôi phụ trách nhóm tool hỗ trợ sau bán hàng trong `tools/cs_tools_p5.py`. Mục tiêu của phần này là giúp ReAct Agent không chỉ tra cứu dữ liệu đơn hàng, mà còn có thể tạo ticket hỗ trợ và chuyển vấn đề cho nhân viên thật khi cần xử lý ngoài khả năng tự động.

- **Modules Implemented**:
  - `tools/cs_tools_p5.py`: triển khai `create_support_ticket()` và `escalate_to_human()`.
  - `tools/registry.py`: `TOOLS_P5` đã được import vào `ALL_TOOLS`, nên hai tool P5 có thể được ReAct Agent gọi thông qua action parser.

- **Code Highlights**:
  - `tools/cs_tools_p5.py:7`: import `ORDERS`, `CUSTOMERS`, `TICKETS`, `TICKET_COUNTER` từ mock database để ticket dùng cùng dữ liệu với toàn hệ thống.
  - `tools/cs_tools_p5.py:10`: `create_support_ticket(order_id, issue, priority="normal")` tạo ticket mới cho vấn đề của khách.
  - `tools/cs_tools_p5.py:22`: validate priority, chỉ cho phép `low`, `normal`, `high`.
  - `tools/cs_tools_p5.py:25`: kiểm tra đơn hàng tồn tại trước khi tạo ticket, tránh tạo ticket cho mã đơn sai.
  - `tools/cs_tools_p5.py:31`: khách `gold` được tự động nâng priority từ `normal` lên `high`.
  - `tools/cs_tools_p5.py:53`: `escalate_to_human(ticket_id, reason)` chuyển ticket sang trạng thái escalated và gán nhân viên hỗ trợ.
  - `tools/cs_tools_p5.py:76`: khai báo `TOOLS_P5` với description để LLM biết khi nào nên dùng hai tool này.

- **Documentation**:

Hai tool P5 tham gia ReAct loop theo flow: model sinh `Action`, agent parse action, gọi function trong `tool_map`, nhận JSON `Observation`, rồi model dùng observation để tạo `Final Answer`. Với `create_support_ticket`, observation chứa `ticket_id`, `priority`, `estimated_response_time`. Với `escalate_to_human`, observation chứa `assigned_agent`, `estimated_response`, và lý do escalation.

---

## Test & Trace Evidence

Tôi đã chạy lại test suite chuẩn và chatbot baseline:

```bash
.venv/bin/python -B chatbot.py
.venv/bin/python -B main.py
```

Kết quả:

```text
Chatbot Baseline v1: 0 passed, 7 failed
ReAct Agent v2: 7 passed, 0 expected failures, 0 unexpected outcomes
```

Log source:

```text
logs/2026-06-01.log
```

Các testcase mặc định trong `main.py` hiện kiểm thử các intent đơn hàng/FAQ/shipping, nhưng chưa có testcase riêng cho P5. Vì vậy tôi chạy thêm một trace riêng qua `ReActAgent` với mock provider để xác minh hai tool P5 được gọi đúng trong ReAct loop. Log event dùng để kiểm tra là `P5_TRACE_RESULT`.
### P5 Trace 1: Create Support Ticket

Input:

```text
Khách báo đơn ORD-001 bị lỗi, hãy tạo ticket hỗ trợ.
```

Trace chính:

```text
Thought: Cần tạo ticket hỗ trợ để theo dõi khiếu nại của khách.
Action: create_support_ticket(order_id="ORD-001", issue="khách báo sản phẩm bị lỗi sau khi nhận hàng", priority="normal")
Observation: {"success": true, "ticket_id": "TKT-101", "priority": "high", "status": "Đã mở", "estimated_response_time": "2-4 giờ"}
Final Answer: Ticket TKT-101 đã được tạo. Nhân viên sẽ phản hồi trong 2-4 giờ. Mức ưu tiên: high.
```

Kết luận: tool tạo ticket thành công. Vì `ORD-001` thuộc khách hàng `gold`, priority được nâng từ `normal` lên `high`, đúng logic đã triển khai.

### P5 Trace 2: Escalate To Human

Input:

```text
Hãy chuyển ticket TKT-101 cho nhân viên thật.
```

Trace chính:

```text
Thought: Cần chuyển ticket cho nhân viên hỗ trợ thật.
Action: escalate_to_human(ticket_id="TKT-101", reason="khách yêu cầu nhân viên xử lý trực tiếp")
Observation: {"success": true, "ticket_id": "TKT-101", "status": "Đã chuyển nhân viên", "assigned_agent": "Nguyễn Hỗ Trợ (CS Team)", "estimated_response": "15-30 phút trong giờ hành chính (8h-17h30)"}
Final Answer: Ticket TKT-101 đã được chuyển cho Nguyễn Hỗ Trợ (CS Team).
```

Kết luận: tool escalation hoạt động đúng khi ticket tồn tại và trả về đầy đủ thông tin nhân viên phụ trách.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**:

Một rủi ro quan trọng của tool tạo ticket là agent có thể tạo ticket cho mã đơn không tồn tại hoặc dùng priority sai format. Nếu không validate, hệ thống sẽ sinh dữ liệu hỗ trợ rác và khiến nhân viên xử lý nhầm.

- **Log Source**:

Log `P5_TRACE_RESULT` trong `logs/2026-06-01.log` cho thấy action `create_support_ticket` được gọi với `order_id="ORD-001"` và observation trả ticket `TKT-101`. Log này chứng minh agent không tự bịa ticket mà lấy kết quả từ tool.

- **Diagnosis**:

P5 tool cần tự bảo vệ dữ liệu ở tầng function, không phụ thuộc hoàn toàn vào LLM. LLM có thể truyền `priority` không hợp lệ, mã đơn sai, hoặc ticket id không tồn tại. Vì vậy tool phải trả lỗi có cấu trúc như `invalid_priority`, `order_not_found`, `ticket_not_found`.

- **Solution**:

`create_support_ticket()` kiểm tra priority và order id trước khi ghi vào `TICKETS`. `escalate_to_human()` kiểm tra `ticket_id` tồn tại trước khi chuyển trạng thái. Cách này giúp observation rõ ràng để ReAct Agent có thể trả lời trung thực thay vì tự suy đoán.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**:
Chatbot thường chỉ trả lời trực tiếp, nên với yêu cầu "tạo ticket" nó có thể nói đã tạo ticket dù không có dữ liệu thật. ReAct Agent tốt hơn vì có bước `Action` gọi `create_support_ticket`, sau đó dùng `Observation` để trả đúng `ticket_id` và thời gian phản hồi.

2. **Reliability**:

Agent có thể kém chatbot nếu intent routing chưa tốt hoặc prompt không chọn đúng tool. Ví dụ nếu user mô tả vấn đề quá mơ hồ mà không có mã đơn, agent cần hỏi lại thay vì gọi tool sai. Vì vậy tool description và validation trong function đều quan trọng.

3. **Observation**:

Observation là bằng chứng hệ thống đã thực hiện hành động thật. Trong trace P5, observation cho biết `TKT-101` được tạo và priority là `high`; final answer chỉ diễn giải lại dữ liệu này. Điều này đáng tin hơn câu trả lời trực tiếp không có tool.

---

## IV. Future Improvements (5 Points)

- **Scalability**:

Lưu ticket vào database thật thay vì dictionary trong memory, thêm trạng thái lifecycle như `open`, `in_progress`, `resolved`, `closed`.

- **Safety**:

Thêm xác nhận của user trước các action quan trọng như escalation hoặc tạo ticket priority `high`, đồng thời sanitize nội dung `issue` để tránh ghi dữ liệu nhạy cảm.

- **Performance**:

Tách testcase P5 vào test suite chính để chạy tự động trong CI, gồm case tạo ticket thành công, invalid priority, order not found, escalate success và ticket not found.

- **Observability**:

Thêm `run_id` hoặc `ticket_id` vào log event để nối được toàn bộ trace từ câu hỏi của khách đến ticket được tạo và escalation sau đó.