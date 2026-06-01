"""
cs_tools_p1.py — NGƯỜI 1
Tool 1: get_order_status   — tra trạng thái đơn hàng
Tool 2: get_order_details  — xem chi tiết đơn hàng
"""
from tools.mock_db import ORDERS, PRODUCTS, CUSTOMERS


def get_order_status(order_id: str) -> dict:
    """
    Tra trạng thái hiện tại của đơn hàng.
    Args:   order_id — mã đơn hàng (VD: ORD-001)
    Return: {order_id, status, order_date, delivered_date}
    Errors: order_not_found nếu mã không tồn tại
    """
    order = ORDERS.get(order_id.upper())
    if not order:
        return {"error": "order_not_found", "message": f"Không tìm thấy đơn hàng '{order_id}'"}

    status_map = {
        "pending":   "Chờ xác nhận",
        "shipping":  "Đang giao hàng",
        "delivered": "Đã giao thành công",
        "cancelled": "Đã huỷ",
    }
    return {
        "success": True,
        "order_id": order_id.upper(),
        "status": order["status"],
        "status_vn": status_map.get(order["status"], order["status"]),
        "order_date": order["order_date"],
        "delivered_date": order["delivered_date"],
    }


def get_order_details(order_id: str) -> dict:
    """
    Lấy chi tiết đơn hàng: sản phẩm, số lượng, tổng tiền, thông tin khách.
    Args:   order_id — mã đơn hàng
    Return: {order_id, product_name, quantity, total, customer_name, customer_email}
    Errors: order_not_found
    """
    order = ORDERS.get(order_id.upper())
    if not order:
        return {"error": "order_not_found", "message": f"Không tìm thấy đơn hàng '{order_id}'"}

    product = PRODUCTS.get(order["product_id"], {})
    customer = CUSTOMERS.get(order["customer_id"], {})

    return {
        "success": True,
        "order_id": order_id.upper(),
        "product_name": product.get("name", "Không rõ"),
        "product_id": order["product_id"],
        "quantity": order["quantity"],
        "total": f"{order['total']:,}đ",
        "customer_name": customer.get("name", "Không rõ"),
        "customer_email": customer.get("email", "Không rõ"),
        "customer_tier": customer.get("tier", "bronze"),
    }


def count_orders(status: str = None, customer_id: str = None) -> dict:
    """
    Đếm tổng số đơn hàng hiện có, có thể lọc theo trạng thái hoặc khách hàng.
    Args:
        status      — trạng thái tuỳ chọn: pending/shipping/delivered/cancelled
        customer_id — mã khách hàng tuỳ chọn
    Return: {count, orders}
    Errors: invalid_status
    """
    valid_statuses = {"pending", "shipping", "delivered", "cancelled"}
    normalized_status = status.lower() if status else None
    normalized_customer_id = customer_id.upper() if customer_id else None

    if normalized_status and normalized_status not in valid_statuses:
        return {
            "error": "invalid_status",
            "message": "status phải là pending, shipping, delivered hoặc cancelled",
        }

    matched_orders = []
    for order_id, order in ORDERS.items():
        if normalized_status and order["status"] != normalized_status:
            continue
        if normalized_customer_id and order["customer_id"] != normalized_customer_id:
            continue
        matched_orders.append(
            {
                "order_id": order_id,
                "status": order["status"],
                "customer_id": order["customer_id"],
                "order_date": order["order_date"],
            }
        )

    return {
        "success": True,
        "count": len(matched_orders),
        "status": normalized_status or "all",
        "customer_id": normalized_customer_id or "all",
        "orders": matched_orders,
        "message": f"Có {len(matched_orders)} đơn hàng phù hợp",
    }


# Tool definitions cho Agent registry
TOOLS_P1 = [
    {
        "name": "get_order_status",
        "description": "Tra trạng thái đơn hàng (pending/shipping/delivered/cancelled). Dùng khi khách hỏi đơn hàng đang ở đâu, giao chưa.",
        "function": get_order_status,
    },
    {
        "name": "get_order_details",
        "description": "Xem chi tiết đơn hàng: tên sản phẩm, số lượng, tổng tiền, tên khách. Dùng khi cần biết khách mua gì.",
        "function": get_order_details,
    },
    {
        "name": "count_orders",
        "description": "Đếm tổng số đơn hàng hiện có, có thể lọc theo status hoặc customer_id. Dùng khi khách hỏi có bao nhiêu đơn/tổng số đơn. Nếu không có customer_id thì đếm toàn bộ database.",
        "function": count_orders,
    },
]
