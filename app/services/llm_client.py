"""LLM 客户端封装 - 统一调用 OpenAI 兼容 API"""
import json
import re
import logging
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

# 全局客户端实例（懒加载）
_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    """获取或创建 AsyncOpenAI 客户端"""
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_api_base_url,
        )
    return _client


async def chat_completion(
    system_prompt: str,
    user_prompt: str,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    """调用 LLM 获取文本响应"""
    client = get_client()
    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature or settings.llm_temperature,
        max_tokens=max_tokens or settings.llm_max_tokens,
    )
    return response.choices[0].message.content


def _try_repair_json(text: str) -> dict:
    """尝试修复并解析可能被截断或有格式问题的 JSON

    处理常见问题：尾部逗号、未闭合字符串、截断等。
    """
    text = text.strip()

    # Remove markdown fences
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Attempt 1: try to close unclosed strings/objects by removing trailing garbage
    # Find the last valid closing brace/bracket
    depth = 0
    in_string = False
    last_valid_pos = 0
    for i, ch in enumerate(text):
        if ch == '"' and (i == 0 or text[i-1] != '\\'):
            in_string = not in_string
        elif not in_string:
            if ch in '{[':
                depth += 1
            elif ch in '}]':
                depth -= 1
            if depth == 0 and ch in '}]':
                last_valid_pos = i + 1

    if last_valid_pos > 0:
        candidate = text[:last_valid_pos]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # Attempt 2: try appending missing closing brackets
    for suffix in ["}]", "}", "]}", "]"]:
        candidate = text + suffix
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    # Attempt 3: reach into nested objects
    # Try to parse the top-level keys individually
    try:
        # Find top-level key-value pairs
        pairs = {}
        pattern = r'"([^"]+)"\s*:\s*'
        matches = list(re.finditer(pattern, text))
        result = {}
        # Just try parsing the whole thing with repair
        fixed = re.sub(r',\s*}', '}', text)
        fixed = re.sub(r',\s*]', ']', fixed)
        return json.loads(fixed)
    except (json.JSONDecodeError, KeyError):
        pass

    raise ValueError(f"Unable to parse JSON after repair attempts. Raw text (last 200 chars): ...{text[-200:]}")


async def chat_completion_json(
    system_prompt: str,
    user_prompt: str,
    temperature: float | None = None,
    max_tokens: int | None = None,
    max_retries: int = 2,
) -> dict:
    """调用 LLM 获取 JSON 响应（带自动修复和重试）"""
    json_system_prompt = (
        system_prompt
        + "\n\n请严格返回完整的 JSON 格式，确保所有引号、括号正确闭合，不要包含任何 markdown 代码块标记。"
    )

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            result = await chat_completion(
                json_system_prompt,
                user_prompt,
                temperature=temperature or 0.1,  # lower temp on retry
                max_tokens=max_tokens,
            )
            return _try_repair_json(result)
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            logger.warning(f"JSON parse attempt {attempt + 1} failed: {e}")
            if attempt < max_retries:
                user_prompt = (
                    user_prompt
                    + f"\n\n上一条回复的JSON解析失败（{str(e)[:100]}），请确保返回格式正确的完整JSON。"
                )

    raise ValueError(f"JSON parse failed after {max_retries + 1} attempts: {last_error}")
