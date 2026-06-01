"""
cs_tools_p3.py — NGƯỜI 3
Tool 5: create_return_request — tạo yêu cầu đổi/trả
Tool 6: calculate_refund      — tính số tiền hoàn lại
"""
from tools.mock_db import ORDERS, TICKETS, TICKET_COUNTER


def create_return_request(order_id: str, reason: str) -> dict:
    """
    Tạo yêu cầu đổi/trả hàng cho đơn hàng.
    Args:
        order_id — mã đơn hàng
        reason   — lý do đổi trả (VD: "hàng bị lỗi", "sai size", "không như mô tả")
    Return: {ticket_id, status, message}
    Errors: order_not_found, reason_empty
    """
    if not reason or len(reason.strip()) < 3:
        return {"error": "reason_empty", "message": "Vui lòng cung cấp lý do đổi trả rõ ràng"}

    order = ORDERS.get(order_id.upper())
    if not order:
        return {"error": "order_not_found", "message": f"Không tìm thấy đơn '{order_id}'"}

    TICKET_COUNTER["n"] += 1
    ticket_id = f"RET-{TICKET_COUNTER['n']}"
    TICKETS[ticket_id] = {
        "type": "return",
        "order_id": order_id.upper(),
        "reason": reason,
        "status": "pending_review",
        "customer_id": order["customer_id"],
    }

    return {
        "success": True,
        "ticket_id": ticket_id,
        "status": "Đang chờ xét duyệt",
        "message": f"Đã tạo yêu cầu đổi trả {ticket_id}. Nhân viên sẽ liên hệ trong 24 giờ.",
        "next_step": "Giữ lại sản phẩm và hộp đựng. Không giặt/sử dụng thêm.",
    }


def calculate_refund(order_id: str, refund_type: str = "full") -> dict:
    """
    Tính số tiền hoàn lại cho khách.
    Args:
        order_id    — mã đơn hàng
        refund_type — "full" (hoàn toàn bộ) hoặc "partial" (hoàn 70%)
    Return: {original_amount, refund_amount, fee, note}
    Errors: order_not_found, invalid_refund_type
    """
    order = ORDERS.get(order_id.upper())
    if not order:
        return {"error": "order_not_found", "message": f"Không tìm thấy đơn '{order_id}'"}

    if refund_type not in ("full", "partial"):
        return {"error": "invalid_refund_type", "message": "refund_type phải là 'full' hoặc 'partial'"}

    original = order["total"]
    if refund_type == "full":
        refund = original
        fee = 0
        note = "Hoàn 100% do lỗi từ phía shop"
    else:
        fee = int(original * 0.30)
        refund = original - fee
        note = "Hoàn 70% — khách đổi ý (áp dụng phí 30%)"

    return {
        "success": True,
        "order_id": order_id.upper(),
        "original_amount": f"{original:,}đ",
        "refund_amount": f"{refund:,}đ",
        "fee_deducted": f"{fee:,}đ",
        "note": note,
        "processing_time": "3-5 ngày làm việc",
    }


TOOLS_P3 = [
    {
        "name": "create_return_request",
        "description": "Tạo yêu cầu đổi/trả hàng. Dùng sau khi đã xác nhận đơn đủ điều kiện đổi trả.",
        "function": create_return_request,
    },
    {
        "name": "calculate_refund",
        "description": "Tính số tiền khách được hoàn lại. refund_type='full' nếu lỗi shop, 'partial' nếu khách đổi ý.",
        "function": calculate_refund,
    },
]
