import os
import re
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

class ReActAgent:
    """
    SKELETON: A ReAct-style Agent that follows the Thought-Action-Observation loop.
    Students should implement the core loop logic and tool execution.
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        """
        TODO: Implement the system prompt that instructs the agent to follow ReAct.
        Should include:
        1.  Available tools and their descriptions.
        2.  Format instructions: Thought, Action, Observation.
        """
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        return f"""
        You are an agent that uses the ReAct framework to solve complex tasks. 
        You have access to the following tools:
        {tool_descriptions}

        Format your responses as follows:

        Thought: Thinking about what to do next.
        Action: tool_name(arguments)
        Observation: The result from the tool.
        ... (this Thought/Action/Observation can repeat N times)
        Final Answer: The final response to the user.

        Important Rules:
        1. Always provide a Thought before an Action.
        2. If you have enough information, provide a Final Answer immediately.
        3. Use ONLY the tools listed above.
        4. When calling a tool, strictly use the format: tool_name(arguments).

        Example:
        Thought: I need to find the price of an item.
        Action: get_price("iPhone 15")
        Observation: 999
        Thought: I have the price. Now I will provide the final answer.
        Final Answer: The price of iPhone 15 is 999.
        """

    def run(self, user_input: str) -> str:
        
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        
        # Bắt đầu với câu hỏi của người dùng
        current_prompt = f"Question: {user_input}"
        steps = 0

        while steps < self.max_steps:
            # 1. Gọi Gemini để lấy Thought + Action (sử dụng method generate có sẵn)
            result = self.llm.generate(current_prompt, system_prompt=self.get_system_prompt())
            content = result["content"]
            
            # In ra console để người dùng theo dõi quá trình suy nghĩ của Agent
            print(f"\n--- Bước {steps + 1} ---\n{content}")
            
            # Cập nhật prompt với phản hồi của LLM để duy trì ngữ cảnh
            current_prompt += f"\n{content}"
            
            # 2. Kiểm tra xem đã có Câu trả lời cuối cùng chưa
            if "Final Answer:" in content:
                final_response = content.split("Final Answer:")[-1].strip()
                logger.log_event("AGENT_END", {"steps": steps + 1, "status": "success"})
                return final_response

            # 3. Phân tích Action bằng Regex: format tool_name(arguments)
            action_match = re.search(r"Action:\s*(\w+)\((.*)\)", content)
            if action_match:
                tool_name = action_match.group(1)
                tool_args = action_match.group(2).strip("'\"") # Làm sạch tham số
                
                # 4. Thực thi Tool và nhận Observation
                observation = self._execute_tool(tool_name, tool_args)
                print(f"Observation: {observation}")
                
                # 5. Đưa kết quả quan sát ngược lại vào prompt cho bước tiếp theo
                current_prompt += f"\nObservation: {observation}"
            else:
                # Nếu không tìm thấy Action và cũng không có Final Answer, dừng lại để tránh lặp vô tận
                break
            
            steps += 1
            
        logger.log_event("AGENT_END", {"steps": steps})
        return "Xin lỗi, tôi không thể hoàn thành nhiệm vụ trong số bước giới hạn."

    def _execute_tool(self, tool_name: str, args: str) -> str:
        # Logic giả lập các công cụ cho bài demo "The Hook"
        for tool in self.tools:
            if tool['name'] == tool_name:
                if tool_name == "get_item_price":
                    # Giả lập: Nếu là Laptop Gaming thì giá 1000, các thứ khác giá 500
                    return "1000" if "Laptop" in args else "500"
                elif tool_name == "calculate_tax":
                    try:
                        return str(float(args) * 0.1)
                    except:
                        return "Lỗi: Tham số không hợp lệ."
        return f"Tool {tool_name} not found."
