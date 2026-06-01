import ast
import inspect
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker

class ReActAgent:
    """
    ReAct-style Agent that follows the Thought-Action-Observation loop.
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []
        self.tool_map = {tool["name"]: tool["function"] for tool in tools}

    def get_system_prompt(self) -> str:
        """
        Build the system prompt that instructs the model to use ReAct.
        """
        tool_descriptions = "\n".join(
            [
                f"- {tool['name']}{inspect.signature(tool['function'])}: {tool['description']}"
                for tool in self.tools
            ]
        )
        return f"""
You are a Vietnamese customer support AI assistant.
You can answer simple questions directly, but for order, shipping, return,
refund, product availability, FAQ, ticket, or escalation questions, use tools.

Available tools:
{tool_descriptions}

Use this exact format:
Thought: short reasoning about the next step.
Action: tool_name(arg_name="value", optional_arg="value")

After an Observation is provided, continue with another Thought/Action if needed.
When you have enough information, end with:
Final Answer: answer to the customer in Vietnamese.

Rules:
- Use only one Action per turn.
- Do not invent tool results.
- Do not write Observation yourself.
- If required information is missing, ask the customer for that information in Final Answer.
- If a tool argument is optional and the user did not provide it, omit that argument. For count or summary questions, use all database records when customer_id is missing.
""".strip()

    def run(self, user_input: str) -> str:
        """
        Run the agent and return only the final answer.
        """
        return self.run_with_trace(user_input)["answer"]

    def run_with_trace(self, user_input: str) -> Dict[str, Any]:
        """
        Run the ReAct loop and return final answer plus trace steps for the UI.
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})

        prompt = f"Question: {user_input}\n"
        trace: List[Dict[str, Any]] = []
        final_answer: Optional[str] = None

        for step_number in range(1, self.max_steps + 1):
            result = self.llm.generate(prompt, system_prompt=self.get_system_prompt())
            content = result.get("content", "").strip()

            tracker.track_request(
                provider=result.get("provider", "unknown"),
                model=self.llm.model_name,
                usage=result.get("usage", {}),
                latency_ms=result.get("latency_ms", 0),
            )

            step: Dict[str, Any] = {
                "step": step_number,
                "thought": self._extract_label(content, "Thought"),
                "llm_output": content,
            }

            final_answer = self._extract_final_answer(content)
            if final_answer:
                step["final_answer"] = final_answer
                trace.append(step)
                logger.log_event("AGENT_END", {"steps": step_number, "status": "final_answer"})
                self.history.append({"question": user_input, "answer": final_answer, "trace": trace})
                return {"answer": final_answer, "trace": trace}

            action = self._parse_action(content)
            if not action:
                final_answer = content or "Xin lỗi, tôi chưa tạo được câu trả lời phù hợp."
                step["final_answer"] = final_answer
                trace.append(step)
                logger.log_event("AGENT_END", {"steps": step_number, "status": "no_action"})
                self.history.append({"question": user_input, "answer": final_answer, "trace": trace})
                return {"answer": final_answer, "trace": trace}

            tool_name, args, action_text = action
            observation = self._execute_tool(tool_name, args)
            step.update(
                {
                    "action": action_text,
                    "tool_name": tool_name,
                    "tool_args": args,
                    "observation": observation,
                }
            )
            trace.append(step)

            prompt += f"\n{content}\nObservation: {observation}\n"

        final_answer = "Tôi chưa đủ thông tin để kết luận sau số bước xử lý cho phép. Bạn vui lòng cung cấp thêm chi tiết hoặc mã đơn hàng."
        trace.append({"step": self.max_steps + 1, "final_answer": final_answer})
        logger.log_event("AGENT_END", {"steps": self.max_steps, "status": "max_steps"})
        self.history.append({"question": user_input, "answer": final_answer, "trace": trace})
        return {"answer": final_answer, "trace": trace}

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """
        Execute a registered tool by name and return a JSON observation string.
        """
        func = self.tool_map.get(tool_name)
        if not func:
            return json.dumps({"error": "tool_not_found", "message": f"Tool '{tool_name}' không tồn tại"}, ensure_ascii=False)

        try:
            signature = inspect.signature(func)
            if "_positional" in args:
                result = func(*args["_positional"])
            else:
                accepted_args = {name: value for name, value in args.items() if name in signature.parameters}
                result = func(**accepted_args)
            return json.dumps(result, ensure_ascii=False)
        except TypeError as exc:
            return json.dumps({"error": "tool_argument_error", "message": str(exc)}, ensure_ascii=False)
        except Exception as exc:
            logger.error(f"Tool execution failed: {tool_name}")
            return json.dumps({"error": "tool_execution_error", "message": str(exc)}, ensure_ascii=False)

    def _parse_action(self, text: str) -> Optional[Tuple[str, Dict[str, Any], str]]:
        action_line = self._extract_label(text, "Action")
        if not action_line:
            return None

        action_text = action_line.strip()
        try:
            expression = ast.parse(action_text, mode="eval").body
            if isinstance(expression, ast.Call) and isinstance(expression.func, ast.Name):
                tool_name = expression.func.id
                args: Dict[str, Any] = {}
                positional = [self._literal_eval(arg) for arg in expression.args]
                if positional:
                    args["_positional"] = positional
                for keyword in expression.keywords:
                    if keyword.arg:
                        args[keyword.arg] = self._literal_eval(keyword.value)
                return tool_name, args, action_text
        except SyntaxError:
            pass
        except ValueError:
            pass

        match = re.match(r"^([a-zA-Z_]\w*)\s*(?:\((.*)\))?$", action_text)
        if not match:
            return None

        tool_name = match.group(1)
        raw_args = (match.group(2) or self._extract_label(text, "Action Input") or "").strip()
        args = self._parse_raw_args(tool_name, raw_args)
        return tool_name, args, action_text

    def _parse_raw_args(self, tool_name: str, raw_args: str) -> Dict[str, Any]:
        if not raw_args:
            return {}

        try:
            parsed = ast.literal_eval(raw_args)
            if isinstance(parsed, dict):
                return parsed
            return {"_positional": [parsed]}
        except (SyntaxError, ValueError):
            pass

        signature = inspect.signature(self.tool_map[tool_name]) if tool_name in self.tool_map else None
        first_param = next(iter(signature.parameters), None) if signature else None
        if first_param:
            return {first_param: raw_args.strip("\"'")}
        return {"_positional": [raw_args.strip("\"'")]}

    def _literal_eval(self, node: ast.AST) -> Any:
        try:
            return ast.literal_eval(node)
        except (ValueError, SyntaxError):
            if isinstance(node, ast.Name):
                return node.id
            return ast.unparse(node)

    def _extract_final_answer(self, text: str) -> Optional[str]:
        match = re.search(r"Final Answer\s*:\s*(.*)", text, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            return None
        answer = match.group(1).strip()
        return answer or None

    def _extract_label(self, text: str, label: str) -> Optional[str]:
        match = re.search(
            rf"{re.escape(label)}\s*:\s*(.+?)(?=\n[A-Za-z ]+\s*:|\Z)",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not match:
            return None
        return match.group(1).strip()
