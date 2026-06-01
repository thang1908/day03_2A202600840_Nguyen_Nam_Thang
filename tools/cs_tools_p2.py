"""Customer support tools for user."""
from datetime import datetime, date, timedelta
from tools.mock_db import ORDERS, PRODUCTS, SHIPPING


def get_shipping_info(order_id: str) -> dict:
    """
    Lấy thông tin vận chuyển: hãng ship, mã tracking, trạng thái.
    Args:   order_id — mã đơn hàng
    Return: {carrier, tracking_code, status, last_update}
    Errors: order_not_found, no_shipping_info (đơn chưa được lấy hàng)
    """
    order = ORDERS.get(order_id.upper())
    if not order:
        return {"error": "order_not_found", "message": f"Không tìm thấy đơn '{order_id}'"}

    shipping = SHIPPING.get(order_id.upper())
    if not shipping:
        return {"error": "no_shipping_info", "message": "Đơn hàng chưa có thông tin vận chuyển"}

    status_map = {
        "waiting_pickup": "Chờ lấy hàng",
        "in_transit":     "Đang trên đường giao",
        "delivered":      "Đã giao thành công",
    }
    return {
        "success": True,
        "order_id": order_id.upper(),
        "carrier": shipping["carrier"],
        "tracking_code": shipping["tracking"] or "Chưa có mã tracking",
        "status": status_map.get(shipping["status"], shipping["status"]),
        "last_update": shipping["last_update"] or "Chưa cập nhật",
        "estimated_delivery_date": shipping.get("estimated_delivery_date") or "Chưa có dự kiến",
    }


def check_return_policy(order_id: str) -> dict:
    """
    Kiểm tra khách có đủ điều kiện đổi/trả hàng không.
    Args:   order_id — mã đơn hàng
    Return: {eligible, reason, days_remaining, return_deadline}
    Errors: order_not_found, not_delivered (chưa nhận hàng không trả được)
    """
    order = ORDERS.get(order_id.upper())
    if not order:
        return {"error": "order_not_found", "message": f"Không tìm thấy đơn '{order_id}'"}

    if order["status"] != "delivered":
        return {"error": "not_delivered", "message": "Đơn hàng chưa được giao, chưa thể yêu cầu đổi trả"}

    product = PRODUCTS.get(order["product_id"], {})
    return_days = product.get("return_days", 7)

    delivered = datetime.strptime(order["delivered_date"], "%Y-%m-%d").date()
    today = date.today()
    days_passed = (today - delivered).days
    days_remaining = return_days - days_passed

    if days_remaining > 0:
        return {
            "success": True,
            "eligible": True,
            "days_remaining": days_remaining,
            "return_deadline": str(delivered + timedelta(days=return_days)),
            "message": f"Còn {days_remaining} ngày để đổi/trả hàng",
        }
    else:
        return {
            "success": True,
            "eligible": False,
            "days_remaining": 0,
            "message": f"Đã quá {return_days} ngày chính sách đổi trả. Không thể thực hiện.",
        }


def count_expected_deliveries(delivery_date: str = "tomorrow", customer_id: str = None) -> dict:
    """
    Đếm số đơn dự kiến khách nhận vào một ngày cụ thể.
    Args:
        delivery_date — "today", "tomorrow" hoặc ngày dạng YYYY-MM-DD
        customer_id   — mã khách hàng tuỳ chọn, nếu muốn lọc theo khách cụ thể
    Return: {delivery_date, count, orders}
    Errors: invalid_date
    """
    target_date = _parse_delivery_date(delivery_date)
    if not target_date:
        return {
            "error": "invalid_date",
            "message": "delivery_date phải là 'today', 'tomorrow' hoặc ngày dạng YYYY-MM-DD",
        }

    normalized_customer_id = customer_id.upper() if customer_id else None
    matched_orders = []
    for order_id, shipping in SHIPPING.items():
        order = ORDERS.get(order_id)
        if not order or order["status"] in ("delivered", "cancelled"):
            continue

        if normalized_customer_id and order["customer_id"] != normalized_customer_id:
            continue

        if shipping.get("estimated_delivery_date") == target_date.isoformat():
            matched_orders.append(
                {
                    "order_id": order_id,
                    "status": order["status"],
                    "carrier": shipping["carrier"],
                    "tracking_code": shipping["tracking"] or "Chưa có mã tracking",
                    "estimated_delivery_date": shipping["estimated_delivery_date"],
                }
            )

    return {
        "success": True,
        "delivery_date": target_date.isoformat(),
        "customer_id": normalized_customer_id or "all",
        "count": len(matched_orders),
        "orders": matched_orders,
        "message": f"Có {len(matched_orders)} đơn dự kiến giao vào ngày {target_date.isoformat()}",
    }


def _parse_delivery_date(value: str):
    value = (value or "tomorrow").strip().lower()
    if value in ("today", "hom nay", "hôm nay"):
        return date.today()
    if value in ("tomorrow", "ngay mai", "ngày mai"):
        return date.today() + timedelta(days=1)

    weekday_aliases = {
        "monday": 0,
        "thu hai": 0,
        "thứ hai": 0,
        "tuesday": 1,
        "thu ba": 1,
        "thứ ba": 1,
        "wednesday": 2,
        "thu tu": 2,
        "thứ tư": 2,
        "thursday": 3,
        "thu nam": 3,
        "thứ năm": 3,
        "friday": 4,
        "thu sau": 4,
        "thứ sáu": 4,
        "saturday": 5,
        "thu bay": 5,
        "thứ bảy": 5,
        "sunday": 6,
        "chu nhat": 6,
        "chủ nhật": 6,
    }

    for phrase, weekday in weekday_aliases.items():
        if phrase in value:
            today = date.today()
            days_until = (weekday - today.weekday()) % 7
            if "next" in value or "tuan sau" in value or "tuần sau" in value:
                days_until = days_until or 7
                if days_until < 7:
                    days_until += 7
            elif days_until == 0:
                days_until = 7
            return today + timedelta(days=days_until)

    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


TOOLS_P2 = [
    {
        "name": "get_shipping_info",
        "description": "Lấy thông tin vận chuyển: hãng ship, mã tracking, trạng thái giao hàng. Dùng khi khách hỏi hàng đang ở đâu.",
        "function": get_shipping_info,
    },
    {
        "name": "check_return_policy",
        "description": "Kiểm tra đơn hàng có đủ điều kiện đổi/trả không. Dùng trước khi tạo yêu cầu đổi trả.",
        "function": check_return_policy,
    },
    {
        "name": "count_expected_deliveries",
        "description": "Đếm số đơn dự kiến được giao/khách nhận vào một ngày. Dùng khi khách hỏi hôm nay/ngày mai/thứ hai tuần sau nhận được bao nhiêu đơn. delivery_date có thể là 'today', 'tomorrow', 'thứ hai tuần sau' hoặc YYYY-MM-DD; customer_id là tuỳ chọn. Nếu không có customer_id thì đếm toàn bộ database.",
        "function": count_expected_deliveries,
    },
]
