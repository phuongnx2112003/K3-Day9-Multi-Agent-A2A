import os
from typing import Optional
from dotenv import load_dotenv
from groq import Groq
from src.settings import MODEL_NAME

# Nạp các biến môi trường từ .env
load_dotenv()

_groq_client: Optional[Groq] = None


def get_groq_client() -> Groq:
    """Khởi tạo và trả về Groq client duy nhất (Singleton)."""
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        base_url = os.getenv("GROQ_BASE_URL")
        
        if not api_key:
            raise ValueError(
                "Chưa cấu hình GROQ_API_KEY trong file .env hoặc biến môi trường!"
            )
        
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url

        _groq_client = Groq(**kwargs)
    return _groq_client


def call_llm(
    prompt: str,
    system_prompt: str = "You are a helpful e-commerce support assistant.",
    temperature: float = 0.0,
) -> str:
    """Gọi LLM (Groq API) với model được cấu hình trong settings.py.
    
    Args:
        prompt: Câu lệnh/nội dung gửi tới LLM.
        system_prompt: Lời nhắc hệ thống định hình vai trò.
        temperature: Độ sáng tạo (mặc định 0.0 để đảm bảo tính nhất quán/reproducibility).
        
    Returns:
        Nội dung văn bản phản hồi từ LLM.
    """
    client = get_groq_client()
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
