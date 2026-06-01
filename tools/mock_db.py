"""
mock_db.py — Dữ liệu giả lập cho Customer Support
Dùng chung bởi tất cả cs_tools_p*.py
"""

ORDERS = {
    "ORD-001": {"status": "delivered", "customer_id": "C001", "product_id": "P001", "quantity": 2, "total": 1_500_000, "order_date": "2026-05-25", "delivered_date": "2026-05-28"},
    "ORD-002": {"status": "shipping",  "customer_id": "C002", "product_id": "P002", "quantity": 1, "total": 850_000,   "order_date": "2026-05-30", "delivered_date": None},
    "ORD-003": {"status": "pending",   "customer_id": "C003", "product_id": "P003", "quantity": 3, "total": 450_000,   "order_date": "2026-06-01", "delivered_date": None},
    "ORD-004": {"status": "cancelled", "customer_id": "C001", "product_id": "P004", "quantity": 1, "total": 2_200_000, "order_date": "2026-05-20", "delivered_date": None},
    "ORD-005": {"status": "delivered", "customer_id": "C004", "product_id": "P001", "quantity": 1, "total": 750_000,   "order_date": "2026-05-10", "delivered_date": "2026-05-13"},
}

PRODUCTS = {
    "P001": {"name": "Áo thun basic",       "price": 750_000,   "stock": 45, "sizes": ["S","M","L","XL"], "colors": ["trắng","đen","xanh"], "return_days": 7},
    "P002": {"name": "Quần jeans slim fit", "price": 850_000,   "stock": 12, "sizes": ["28","30","32","34"], "colors": ["xanh","đen"], "return_days": 7},
    "P003": {"name": "Tất cotton (3 đôi)", "price": 150_000,   "stock": 200,"sizes": ["free"], "colors": ["trắng","đen"], "return_days": 3},
    "P004": {"name": "Áo khoác bomber",     "price": 2_200_000, "stock": 5,  "sizes": ["M","L","XL"], "colors": ["đen","nâu"], "return_days": 7},
    "P005": {"name": "Váy midi floral",     "price": 650_000,   "stock": 0,  "sizes": ["S","M"], "colors": ["hoa"], "return_days": 7},
}

CUSTOMERS = {
    "C001": {"name": "Nguyễn Thị An",  "email": "an@gmail.com",   "phone": "0901234567", "tier": "gold"},
    "C002": {"name": "Trần Văn Bình",  "email": "binh@gmail.com", "phone": "0912345678", "tier": "silver"},
    "C003": {"name": "Lê Thị Cúc",    "email": "cuc@gmail.com",  "phone": "0923456789", "tier": "bronze"},
    "C004": {"name": "Phạm Văn Dũng",  "email": "dung@gmail.com", "phone": "0934567890", "tier": "silver"},
}

SHIPPING = {
    "ORD-001": {"carrier": "GHN", "tracking": "GHN123456", "status": "delivered", "last_update": "2026-05-28 14:30", "estimated_delivery_date": "2026-05-28"},
    "ORD-002": {"carrier": "GHTK", "tracking": "GHTK789012", "status": "in_transit", "last_update": "2026-05-31 09:00", "estimated_delivery_date": "2026-06-02"},
    "ORD-003": {"carrier": "ViettelPost", "tracking": None, "status": "waiting_pickup", "last_update": None, "estimated_delivery_date": "2026-06-04"},
}

FAQ_DB = [
    {"id": 1, "question": "Chính sách đổi trả như thế nào?", "answer": "Đổi trả trong 7 ngày kể từ ngày nhận hàng. Sản phẩm còn nguyên tag, chưa qua sử dụng."},
    {"id": 2, "question": "Phí vận chuyển tính thế nào?",    "answer": "Miễn phí ship đơn từ 500k. Dưới 500k phí 30.000đ."},
    {"id": 3, "question": "Bao lâu thì nhận được hàng?",     "answer": "Nội thành 1-2 ngày. Tỉnh thành 3-5 ngày làm việc."},
    {"id": 4, "question": "Thanh toán bằng phương thức nào?","answer": "COD, chuyển khoản, Momo, VNPay, thẻ tín dụng."},
    {"id": 5, "question": "Hàng bị lỗi thì làm thế nào?",   "answer": "Liên hệ trong 48h kể từ khi nhận hàng. Gửi ảnh lỗi qua email. Được đổi hàng mới miễn phí."},
]

TICKETS = {}
TICKET_COUNTER = {"n": 100}
