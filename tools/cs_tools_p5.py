"""
cs_tools_p5.py — NGƯỜI 5
Tool 9:  create_support_ticket — tạo ticket hỗ trợ
Tool 10: escalate_to_human    — chuyển cho nhân viên thật
"""
from tools.mock_db import ORDERS, CUSTOMERS, TICKETS, TICKET_COUNTER


def create_support_ticket(order_id: str, issue: str, priority: str = "normal") -> dict:
    """
    Tạo ticket hỗ trợ cho vấn đề của khách.
    Args:
        order_id — mã đơn hàng liên quan
        issue    — mô tả vấn đề
        priority — "low" | "normal" | "high" (mặc định: normal)
    Return: {ticket_id, priority, estimated_response_time}
    Errors: order_not_found, invalid_priority
    """
    if priority not in ("low", "normal", "high"):
        return {"error": "invalid_priority", "message": "priority phải là 'low', 'normal', hoặc 'high'"}

    order = ORDERS.get(order_id.upper())
    if not order:
        return {"error": "order_not_found", "message": f"Không tìm thấy đơn '{order_id}'"}

    customer = CUSTOMERS.get(order["customer_id"], {})
    # Gold tier gets high priority automatically
    if customer.get("tier") == "gold" and priority == "normal":
        priority = "high"

    TICKET_COUNTER["n"] += 1
    ticket_id = f"TKT-{TICKET_COUNTER['n']}"
    TICKETS[ticket_id] = {
        "type": "support",
        "order_id": order_id.upper(),
        "issue": issue,
        "priority": priority,
        "status": "open",
        "customer_id": order["customer_id"],
    }

    response_time = {"low": "48-72 giờ", "normal": "24 giờ", "high": "2-4 giờ"}

    return {
        "success": True,
        "ticket_id": ticket_id,
        "priority": priority,
        "status": "Đã mở",
        "estimated_response_time": response_time[priority],
        "message": f"Ticket {ticket_id} đã được tạo. Nhân viên sẽ phản hồi trong {response_time[priority]}.",
    }


def escalate_to_human(ticket_id: str, reason: str) -> dict:
    """
    Chuyển ticket đến nhân viên hỗ trợ thật khi agent không giải quyết được.
    Args:
        ticket_id — mã ticket cần chuyển
        reason    — lý do cần chuyển (VD: "khách yêu cầu bồi thường", "tình huống phức tạp")
    Return: {ticket_id, assigned_agent, estimated_call_time}
    Errors: ticket_not_found
    """
    if ticket_id not in TICKETS:
        return {"error": "ticket_not_found", "message": f"Không tìm thấy ticket '{ticket_id}'"}

    TICKETS[ticket_id]["status"] = "escalated"
    TICKETS[ticket_id]["escalation_reason"] = reason

    return {
        "success": True,
        "ticket_id": ticket_id,
        "status": "Đã chuyển nhân viên",
        "assigned_agent": "Nguyễn Hỗ Trợ (CS Team)",
        "escalation_reason": reason,
        "estimated_response": "15-30 phút trong giờ hành chính (8h-17h30)",
        "message": "Nhân viên sẽ liên hệ qua email/điện thoại đã đăng ký.",
    }


TOOLS_P5 = [
    {
        "name": "create_support_ticket",
        "description": "Tạo ticket hỗ trợ khi vấn đề cần theo dõi. priority='high' nếu khách VIP hoặc vấn đề nghiêm trọng.",
        "function": create_support_ticket,
    },
    {
        "name": "escalate_to_human",
        "description": "Chuyển vấn đề cho nhân viên thật khi agent không thể giải quyết. Dùng như bước cuối cùng.",
        "function": escalate_to_human,
    },
]
