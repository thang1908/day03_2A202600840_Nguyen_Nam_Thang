import argparse
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional

from dotenv import load_dotenv

from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


load_dotenv()


@dataclass(frozen=True)
class BaselineTestCase:
    name: str
    question: str
    expected_keywords: List[str]
    note: str = ""


TEST_CASES = [
    BaselineTestCase(
        name="order_status_shipping",
        question="Đơn ORD-002 của tôi đang ở đâu?",
        expected_keywords=["ORD-002", "Đang giao hàng", "2026-05-30"],
    ),
    BaselineTestCase(
        name="order_details_delivered",
        question="Cho tôi xem chi tiết đơn ORD-001",
        expected_keywords=["ORD-001", "Áo thun basic", "1,500,000đ"],
    ),
    BaselineTestCase(
        name="count_delivered_orders",
        question="Hiện có bao nhiêu đơn đã giao thành công?",
        expected_keywords=["2", "delivered"],
    ),
    BaselineTestCase(
        name="missing_order",
        question="Kiểm tra giúp tôi đơn ORD-999",
        expected_keywords=["Không tìm thấy", "ORD-999"],
    ),
    BaselineTestCase(
        name="malformed_order_id_no_hyphen",
        question="Đơn ORD002 của tôi đang ở đâu?",
        expected_keywords=["ORD-002", "Đang giao hàng"],
        note="Baseline không có tool hoặc normalizer để kiểm tra mã đơn sai format.",
    ),
    BaselineTestCase(
        name="shipping_eta_tracking",
        question="Đơn ORD-002 dự kiến giao ngày nào?",
        expected_keywords=["2026-06-02", "GHTK789012"],
        note="Baseline không truy cập được dữ liệu vận chuyển.",
    ),
    BaselineTestCase(
        name="faq_return_policy",
        question="Chính sách đổi trả như thế nào?",
        expected_keywords=["Đổi trả trong 7 ngày", "nguyên tag"],
        note="Baseline có thể trả lời chung chung nhưng không bảo đảm đúng FAQ nội bộ.",
    ),
]


class ChatbotBaseline:
    """
    Minimal v1 chatbot baseline.

    This intentionally does not receive tool descriptions and does not execute
    tools. It answers directly from the model so the lab can compare direct
    chatbot behavior against the ReAct agent.
    """

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def run(self, user_input: str) -> str:
        result = self.llm.generate(user_input, system_prompt=self.get_system_prompt())
        tracker.track_request(
            provider=result.get("provider", "unknown"),
            model=self.llm.model_name,
            usage=result.get("usage", {}),
            latency_ms=result.get("latency_ms", 0),
        )
        return result.get("content", "").strip()

    def get_system_prompt(self) -> str:
        return """
You are a Vietnamese customer support chatbot.
Answer directly and politely in Vietnamese.
You do not have access to internal order, shipping, stock, refund, or FAQ tools.
If the customer asks for private or database-backed information that you cannot
verify, say that you cannot verify it and ask them to contact support or provide
official lookup access.
Do not invent order status, tracking numbers, prices, or internal policy text.
""".strip()


class BaselineMockLLMProvider(LLMProvider):
    """
    Deterministic local mock for the direct chatbot baseline.
    It simulates a safe chatbot that has no tool access.
    """

    def __init__(self):
        super().__init__(model_name="baseline-mock")

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        content = self._answer(prompt)
        return {
            "content": content,
            "provider": "mock",
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(content.split()),
                "total_tokens": len(prompt.split()) + len(content.split()),
            },
            "latency_ms": 0,
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        yield self.generate(prompt, system_prompt=system_prompt)["content"]

    def _answer(self, question: str) -> str:
        normalized = question.lower()

        if "chính sách" in normalized or "đổi trả" in normalized:
            return (
                "Tôi chưa có quyền truy cập FAQ nội bộ để xác minh chính sách đổi trả. "
                "Bạn vui lòng kiểm tra trang chính sách chính thức hoặc liên hệ bộ phận hỗ trợ."
            )

        if "ord" in normalized or "đơn" in normalized:
            return (
                "Tôi chưa có quyền truy cập hệ thống đơn hàng nên không thể xác minh trạng thái, "
                "chi tiết, tracking hoặc ngày giao dự kiến cho yêu cầu này."
            )

        return "Tôi có thể hỗ trợ thông tin chung, nhưng không thể tra cứu dữ liệu nội bộ."


def create_llm_provider() -> LLMProvider:
    provider = os.getenv("DEFAULT_PROVIDER", "openai").lower()
    model = os.getenv("DEFAULT_MODEL", "").strip()

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your_openai_api_key_here":
            raise RuntimeError("OPENAI_API_KEY chưa được cấu hình trong .env")
        from src.core.openai_provider import OpenAIProvider

        return OpenAIProvider(model_name=model or "gpt-4o", api_key=api_key)

    if provider in ("google", "gemini"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            raise RuntimeError("GEMINI_API_KEY chưa được cấu hình trong .env")
        from src.core.gemini_provider import GeminiProvider

        return GeminiProvider(model_name=model or "gemini-1.5-flash", api_key=api_key)

    if provider == "local":
        model_path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")
        from src.core.local_provider import LocalProvider

        return LocalProvider(model_path=model_path)

    raise RuntimeError(f"DEFAULT_PROVIDER không hợp lệ: {provider}")


def run_baseline(use_real_llm: bool = False, strict: bool = False) -> int:
    chatbot = ChatbotBaseline(llm=create_llm_provider() if use_real_llm else BaselineMockLLMProvider())
    started_at = datetime.now().isoformat(timespec="seconds")
    results = []

    logger.log_event(
        "CHATBOT_BASELINE_RUN_START",
        {"started_at": started_at, "total": len(TEST_CASES), "use_real_llm": use_real_llm},
    )

    print(f"Running chatbot baseline v1 on {len(TEST_CASES)} testcases | real_llm={use_real_llm}")
    for index, test_case in enumerate(TEST_CASES, start=1):
        print(f"\n[{index}/{len(TEST_CASES)}] {test_case.name}")
        print(f"Question: {test_case.question}")

        try:
            answer = chatbot.run(test_case.question)
            passed = all(keyword.lower() in answer.lower() for keyword in test_case.expected_keywords)
            status = "PASS" if passed else "FAIL"
            print(f"Answer: {answer}")
            print(f"Status: {status}")
            if test_case.note:
                print(f"Note: {test_case.note}")

            payload = {
                "name": test_case.name,
                "question": test_case.question,
                "expected_keywords": test_case.expected_keywords,
                "answer": answer,
                "status": status,
                "passed": passed,
                "note": test_case.note,
            }
            logger.log_event("CHATBOT_BASELINE_RESULT", payload)
            results.append(payload)
        except Exception as exc:
            payload = {
                "name": test_case.name,
                "question": test_case.question,
                "expected_keywords": test_case.expected_keywords,
                "status": "ERROR",
                "passed": False,
                "error": str(exc),
                "note": test_case.note,
            }
            logger.log_event("CHATBOT_BASELINE_RESULT", payload)
            results.append(payload)
            print(f"Status: ERROR - {exc}")

    pass_count = sum(1 for item in results if item["passed"])
    fail_count = len(results) - pass_count
    summary = {
        "started_at": started_at,
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "total": len(results),
        "passed": pass_count,
        "failed": fail_count,
        "use_real_llm": use_real_llm,
    }
    logger.log_event("CHATBOT_BASELINE_RUN_END", summary)
    print(f"\nBaseline Summary: {pass_count} passed, {fail_count} failed")
    print("Logs: logs/<today>.log")
    return 1 if strict and fail_count else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run chatbot baseline v1 testcases.")
    parser.add_argument(
        "--use-real-llm",
        action="store_true",
        help="Use DEFAULT_PROVIDER from .env instead of the deterministic baseline mock.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return a non-zero exit code if any baseline testcase fails.",
    )
    args = parser.parse_args()
    return run_baseline(use_real_llm=args.use_real_llm, strict=args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
