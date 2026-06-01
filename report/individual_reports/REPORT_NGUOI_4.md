# Individual Report — Lab 3

- **Tên**: [Phạm Thị Bích Ngọc-2A202600575]
- **Ngày**: 2026-06-01

---

## I. Technical Contribution (15đ)

**Modules tôi implement:** `src/tools/cs_tools_p1.py`

**Tool 1: `get_order_status`**
Tra trạng thái đơn hàng (pending/shipping/delivered/cancelled). Nhận `order_id`, tra trong mock DB, trả về trạng thái tiếng Việt.

**Tool 2: `get_order_details`**
Lấy chi tiết đơn: tên sản phẩm, số lượng, tổng tiền, thông tin khách hàng.

**Code highlight:**

```python
def get_order_status(order_id: str) -> dict:
    order = ORDERS.get(order_id.upper())
    if not order:
        return {"error": "order_not_found", ...}
    ...
```

---

## II. Debugging Case Study (10đ)

**Vấn đề tìm thấy trong log:**

```json
{
  "event": "PARSE_ERROR",
  "data": { "raw": "Action: get_order_status(ORD-001)" }
}
```

**Nguyên nhân:** Agent gọi tool mà không có dấu ngoặc kép cho argument — parser regex không match.

**Cách sửa:** Cập nhật system prompt thêm ví dụ rõ hơn: `Action: get_order_status(order_id="ORD-001")`

---

## III. Personal Insights (10đ)

1. **Reasoning:** Chatbot đoán trạng thái đơn hàng dựa trên training data — hoàn toàn sai. Agent gọi tool → có số liệu thật → đáng tin.
2. **Khi agent tệ hơn chatbot:** Câu hỏi đơn giản "chính sách đổi trả thế nào?" — chatbot trả lời ngay, agent mất 2 bước gọi `search_faq` không cần thiết.
3. **Observation ảnh hưởng:** Sau khi `get_order_status` trả về "delivered", agent mới quyết định gọi tiếp `check_return_policy` — đây là dynamic decision thực sự.

---

## IV. Future Improvements (5đ)

- **Async tool calls:** Gọi song song nhiều tool thay vì tuần tự → giảm latency 40-60%
- **Tool caching:** Cache kết quả `get_order_status` trong session → tránh gọi lại cùng tool 2 lần
- **Confidence scoring:** Thêm điểm tin cậy vào mỗi Thought → agent biết khi nào nên escalate
