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
    Tìm câu trả lời FAQ theo câu hỏi hoặc từ khóa.
    Args:
        query — câu hỏi hoặc từ khóa của khách
    Return: {faq_id, question, answer}
    Errors: faq_not_found, query_empty
    """
    normalized_query = (query or "").strip().lower()
    if not normalized_query:
        return {"error": "query_empty", "message": "Vui lòng nhập nội dung cần tìm trong FAQ"}

    best_match = None
    best_score = 0
    query_terms = set(normalized_query.replace("?", " ").replace(",", " ").split())

    for item in FAQ_DB:
        searchable = f"{item['question']} {item['answer']}".lower()
        score = sum(1 for term in query_terms if term in searchable)
        if normalized_query in searchable:
            score += 5
        if score > best_score:
            best_score = score
            best_match = item

    if not best_match or best_score == 0:
        return {"error": "faq_not_found", "message": "Không tìm thấy FAQ phù hợp"}

    return {
        "success": True,
        "faq_id": best_match["id"],
        "question": best_match["question"],
        "answer": best_match["answer"],
    }


TOOLS_P4 = [
    {
        "name": "check_product_availability",
        "description": "Kiểm tra tồn kho sản phẩm, size và màu có sẵn không. Dùng khi khách hỏi còn hàng không, size X còn không.",
        "function": check_product_availability,
    },
    {
        "name": "search_faq",
        "description": "Tìm câu trả lời FAQ/chính sách như đổi trả, phí vận chuyển, thời gian nhận hàng, thanh toán, hàng lỗi.",
        "function": search_faq,
    },
]
