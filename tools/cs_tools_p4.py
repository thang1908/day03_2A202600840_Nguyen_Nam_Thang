"""
cs_tools_p4.py — NGƯỜI 4
Tool 7: check_product_availability — kiểm tra tồn kho
Tool 8: search_faq                 — tìm kiếm câu hỏi thường gặp
"""
from tools.mock_db import PRODUCTS, FAQ_DB


def check_product_availability(product_id: str, size: str = None, color: str = None) -> dict:
    """
    Kiểm tra tồn kho sản phẩm, có thể lọc theo size và màu sắc.
    Args:
        product_id — mã sản phẩm (VD: P001)
        size       — size cần kiểm tra (tuỳ chọn)
        color      — màu cần kiểm tra (tuỳ chọn)
    Return: {product_name, in_stock, stock_count, available_sizes, available_colors}
    Errors: product_not_found
    """
    product = PRODUCTS.get(product_id.upper())
    if not product:
        return {"error": "product_not_found", "message": f"Không tìm thấy sản phẩm '{product_id}'"}

    result = {
        "success": True,
        "product_id": product_id.upper(),
        "product_name": product["name"],
        "price": f"{product['price']:,}đ",
        "in_stock": product["stock"] > 0,
        "stock_count": product["stock"],
        "available_sizes": product["sizes"],
        "available_colors": product["colors"],
    }

    if size and size.lower() not in [s.lower() for s in product["sizes"]]:
        result["size_note"] = f"Size '{size}' không có sẵn. Các size có: {', '.join(product['sizes'])}"
    elif size:
        result["size_note"] = f"Size '{size}' có sẵn"

    if color and color.lower() not in [c.lower() for c in product["colors"]]:
        result["color_note"] = f"Màu '{color}' không có sẵn. Các màu có: {', '.join(product['colors'])}"
    elif color:
        result["color_note"] = f"Màu '{color}' có sẵn"

    if product["stock"] == 0:
        result["restock_note"] = "Sản phẩm tạm hết hàng. Dự kiến về kho trong 3-5 ngày."

    return result


def search_faq(query: str) -> dict:
    """
    Tìm câu trả lời trong FAQ dựa trên từ khoá.
    Args:   query — câu hỏi hoặc từ khoá (VD: "đổi trả", "phí ship", "thanh toán")
    Return: {results: [{question, answer}]} — tối đa 3 kết quả liên quan
    Errors: no_results nếu không tìm thấy gì liên quan
    """
    if not query or len(query.strip()) < 2:
        return {"error": "query_too_short", "message": "Vui lòng nhập từ khoá tìm kiếm"}

    query_lower = query.lower()
    matches = []
    for faq in FAQ_DB:
        if any(word in faq["question"].lower() or word in faq["answer"].lower()
               for word in query_lower.split()):
            matches.append({"question": faq["question"], "answer": faq["answer"]})

    if not matches:
        return {
            "error": "no_results",
            "message": f"Không tìm thấy FAQ liên quan đến '{query}'. Thử: 'đổi trả', 'ship', 'thanh toán', 'lỗi hàng'",
        }

    return {
        "success": True,
        "query": query,
        "results": matches[:3],
        "total_found": len(matches),
    }


TOOLS_P4 = [
    {
        "name": "check_product_availability",
        "description": "Kiểm tra tồn kho sản phẩm, size và màu có sẵn không. Dùng khi khách hỏi còn hàng không, size X còn không.",
        "function": check_product_availability,
    },
    {
        "name": "search_faq",
        "description": "Tìm kiếm câu hỏi thường gặp theo từ khoá. Dùng khi khách hỏi về chính sách, quy trình, hoặc thông tin chung.",
        "function": search_faq,
    },
]
