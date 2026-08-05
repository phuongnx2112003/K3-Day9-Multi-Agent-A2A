import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

from src.settings import MODEL_NAME

load_dotenv()

_openai_client: Optional[OpenAI] = None


def get_openai_client() -> OpenAI:
    """Create and cache the OpenAI client."""
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "Chưa cấu hình OPENAI_API_KEY trong file .env hoặc biến môi trường!"
            )

        kwargs = {"api_key": api_key}
        base_url = os.getenv("OPENAI_BASE_URL")
        if base_url:
            kwargs["base_url"] = base_url

        _openai_client = OpenAI(**kwargs)
    return _openai_client


def call_llm(
    prompt: str,
    system_prompt: str = "You are a helpful e-commerce support assistant.",
    temperature: float = 0.0,
) -> str:
    """Call GPT-4o mini through the OpenAI Chat Completions API.

    Args:
        prompt: Câu lệnh/nội dung gửi tới LLM.
        system_prompt: Lời nhắc hệ thống định hình vai trò.
        temperature: Độ sáng tạo (mặc định 0.0 để đảm bảo tính nhất quán/reproducibility).

    Returns:
        Nội dung văn bản phản hồi từ LLM.
    """
    client = get_openai_client()
    messages = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    chat_completion = client.chat.completions.create(
        messages=messages,
        model=MODEL_NAME,
        temperature=temperature,
    )

    return chat_completion.choices[0].message.content or ""
