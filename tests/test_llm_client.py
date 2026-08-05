import pytest
import os
from src.llm_client import call_llm


@pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="Yêu cầu GROQ_API_KEY để chạy test API")
def test_call_llm_success():
    response = call_llm(prompt="Trả lời ngắn gọn chữ 'OK' nếu bạn nhận được tin nhắn này.")
    assert response is not None
    assert len(response.strip()) > 0
