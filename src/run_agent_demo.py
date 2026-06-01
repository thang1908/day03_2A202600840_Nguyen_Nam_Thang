import os
import sys

# Thêm thư mục gốc vào sys.path để Python nhận diện được package 'src'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from src.core.gemini_provider import GeminiProvider
from src.agent.agent import ReActAgent

def main():
    load_dotenv()
    
    # 1. Setup Provider (Sử dụng Gemini thay cho Local để demo hiệu quả hơn)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: Vui lòng bổ sung GEMINI_API_KEY vào file .env")
        return

    provider = GeminiProvider(model_name="gemini-2.5-flash", api_key=api_key)
    
    # 2. Định nghĩa các công cụ giả lập (Tools) cho Demo
    # Trong thực tế, các tools này sẽ nằm trong src/tools/
    tools = [
        {
            "name": "get_item_price",
            "description": "Lấy giá của một sản phẩm. Input: tên sản phẩm (string)."
        },
        {
            "name": "calculate_tax",
            "description": "Tính thuế cho một số tiền. Input: số tiền (float)."
        }
    ]
    
    # 3. Khởi tạo Agent
    agent = ReActAgent(llm=provider, tools=tools)
    
    # 4. Scenario: Truy vấn đa bước (Multi-step query)
    user_query = "Hãy tìm giá của 'Laptop Gaming' và tính tổng chi phí sau khi cộng thêm 10% thuế."
    
    print("--- DEMO: AGENT VS MULTI-STEP QUERY ---")
    print(f"Câu hỏi: {user_query}\n")
    
    print("\n--- BẮT ĐẦU CHẠY AGENT ---")
    response = agent.run(user_query)
    print(f"Kết quả Agent: {response}")
    
    print("\n--- KẾT LUẬN (THE HOOK) ---")
    print("Chatbot thông thường sẽ cố gắng đoán kết quả hoặc nói 'Tôi không biết'.")
    print("Agent sẽ phân tích: Cần gọi 'get_item_price' -> Nhận kết quả -> Gọi 'calculate_tax'.")

if __name__ == "__main__":
    main()