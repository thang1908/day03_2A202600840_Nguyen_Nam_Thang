import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.agent.agent import ReActAgent
from tools.registry import ALL_TOOLS


load_dotenv()

app = FastAPI(title="Customer Support ReAct Agent")
_agent: Optional[ReActAgent] = None


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    trace: list[Dict[str, Any]]


def create_llm_provider():
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


def get_agent() -> ReActAgent:
    global _agent
    if _agent is None:
        _agent = ReActAgent(llm=create_llm_provider(), tools=ALL_TOOLS, max_steps=6)
    return _agent


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return HTML


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="message không được để trống")

    try:
        result = get_agent().run_with_trace(message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ChatResponse(answer=result["answer"], trace=result["trace"])


HTML = """
<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Customer Support ReAct Agent</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f4f6f8;
      --surface: #ffffff;
      --line: #d9e0e7;
      --text: #18212f;
      --muted: #637083;
      --accent: #087f5b;
      --accent-dark: #06684b;
      --warn: #b42318;
      --code: #111827;
      --chip: #eef8f4;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .app {
      display: grid;
      grid-template-columns: minmax(0, 1.05fr) minmax(340px, 0.95fr);
      gap: 16px;
      height: 100vh;
      padding: 16px;
    }

    .pane {
      min-width: 0;
      min-height: 0;
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .header {
      height: 58px;
      padding: 0 18px;
      border-bottom: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex: 0 0 auto;
    }

    h1, h2 {
      margin: 0;
      font-size: 16px;
      font-weight: 700;
      letter-spacing: 0;
    }

    .status {
      border: 1px solid #badbcc;
      background: var(--chip);
      color: #0f5132;
      border-radius: 999px;
      padding: 5px 10px;
      font-size: 12px;
      white-space: nowrap;
    }

    .messages, .trace {
      min-height: 0;
      flex: 1 1 auto;
      overflow: auto;
      padding: 18px;
    }

    .messages {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .msg {
      max-width: min(760px, 88%);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px 14px;
      line-height: 1.45;
      white-space: pre-wrap;
      word-break: break-word;
    }

    .user {
      align-self: flex-end;
      background: #eaf4ff;
      border-color: #bdd7f2;
    }

    .assistant {
      align-self: flex-start;
      background: #fbfcfd;
    }

    .composer {
      border-top: 1px solid var(--line);
      padding: 12px;
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 10px;
      flex: 0 0 auto;
    }

    textarea {
      width: 100%;
      min-height: 46px;
      max-height: 150px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      font: inherit;
      line-height: 1.35;
      outline: none;
    }

    textarea:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(8, 127, 91, 0.12);
    }

    button {
      min-width: 92px;
      border: 0;
      border-radius: 8px;
      background: var(--accent);
      color: #fff;
      font-weight: 700;
      font: inherit;
      cursor: pointer;
      padding: 0 16px;
    }

    button:hover { background: var(--accent-dark); }
    button:disabled { opacity: 0.55; cursor: not-allowed; }

    .trace {
      display: flex;
      flex-direction: column;
      gap: 12px;
      background: #fbfcfd;
    }

    .step {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      padding: 12px;
    }

    .step-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 10px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
    }

    .field {
      margin: 8px 0 0;
      font-size: 13px;
      line-height: 1.45;
      word-break: break-word;
    }

    .label {
      display: block;
      color: var(--muted);
      font-weight: 700;
      margin-bottom: 4px;
    }

    code, pre {
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      color: var(--code);
    }

    pre {
      margin: 4px 0 0;
      padding: 10px;
      border-radius: 8px;
      background: #f3f5f7;
      overflow: auto;
      white-space: pre-wrap;
    }

    .empty {
      color: var(--muted);
      line-height: 1.5;
      max-width: 420px;
    }

    .error {
      color: var(--warn);
      border-color: #f5c2c7;
      background: #fff5f5;
    }

    @media (max-width: 900px) {
      .app {
        height: auto;
        min-height: 100vh;
        grid-template-columns: 1fr;
      }

      .pane {
        min-height: 48vh;
      }

      .composer {
        grid-template-columns: 1fr;
      }

      button {
        height: 44px;
      }
    }
  </style>
</head>
<body>
  <main class="app">
    <section class="pane">
      <div class="header">
        <h1>Customer Support Agent</h1>
        <span class="status" id="status">Ready</span>
      </div>
      <div class="messages" id="messages">
        <div class="msg assistant">Xin chào. Bạn có thể hỏi về đơn hàng, vận chuyển, đổi trả, hoàn tiền, tồn kho hoặc chính sách hỗ trợ.</div>
      </div>
      <form class="composer" id="form">
        <textarea id="input" placeholder="Ví dụ: Đơn ORD-002 của tôi đang ở đâu?" autocomplete="off"></textarea>
        <button id="send" type="submit">Gửi</button>
      </form>
    </section>

    <aside class="pane">
      <div class="header">
        <h2>ReAct Trace</h2>
      </div>
      <div class="trace" id="trace">
        <div class="empty">Trace sẽ xuất hiện sau mỗi câu hỏi.</div>
      </div>
    </aside>
  </main>

  <script>
    const form = document.getElementById('form');
    const input = document.getElementById('input');
    const send = document.getElementById('send');
    const statusEl = document.getElementById('status');
    const messages = document.getElementById('messages');
    const trace = document.getElementById('trace');

    function addMessage(role, text, error = false) {
      const el = document.createElement('div');
      el.className = `msg ${role}${error ? ' error' : ''}`;
      el.textContent = text;
      messages.appendChild(el);
      messages.scrollTop = messages.scrollHeight;
    }

    function renderTrace(steps) {
      trace.innerHTML = '';
      if (!steps || !steps.length) {
        trace.innerHTML = '<div class="empty">Không có trace.</div>';
        return;
      }

      for (const item of steps) {
        const step = document.createElement('div');
        step.className = 'step';
        step.innerHTML = `
          <div class="step-title"><span>Step ${item.step}</span><span>${item.tool_name || 'final'}</span></div>
          ${item.thought ? field('Thought', item.thought) : ''}
          ${item.action ? field('Action', item.action) : ''}
          ${item.observation ? field('Observation', pretty(item.observation), true) : ''}
          ${item.final_answer ? field('Final Answer', item.final_answer) : ''}
        `;
        trace.appendChild(step);
      }
      trace.scrollTop = trace.scrollHeight;
    }

    function field(label, value, code = false) {
      const content = code ? `<pre>${escapeHtml(value)}</pre>` : escapeHtml(value);
      return `<div class="field"><span class="label">${label}</span>${content}</div>`;
    }

    function pretty(value) {
      try {
        return JSON.stringify(JSON.parse(value), null, 2);
      } catch (_) {
        return value;
      }
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
    }

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const message = input.value.trim();
      if (!message) return;

      addMessage('user', message);
      input.value = '';
      send.disabled = true;
      statusEl.textContent = 'Thinking';

      try {
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message })
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || 'Request failed');
        }
        addMessage('assistant', data.answer);
        renderTrace(data.trace);
      } catch (error) {
        addMessage('assistant', error.message, true);
      } finally {
        statusEl.textContent = 'Ready';
        send.disabled = false;
        input.focus();
      }
    });

    input.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        form.requestSubmit();
      }
    });
  </script>
</body>
</html>
"""
