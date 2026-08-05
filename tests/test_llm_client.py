import os
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import src.llm_client as llm_client


@pytest.fixture(autouse=True)
def reset_openai_client(monkeypatch):
    monkeypatch.setattr(llm_client, "_openai_client", None)


def test_get_openai_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        llm_client.get_openai_client()


def test_get_openai_client_uses_environment(monkeypatch):
    constructor = Mock(return_value=object())
    monkeypatch.setattr(llm_client, "OpenAI", constructor)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.test/v1")

    first_client = llm_client.get_openai_client()
    second_client = llm_client.get_openai_client()

    assert first_client is second_client
    constructor.assert_called_once_with(
        api_key="test-key",
        base_url="https://example.test/v1",
    )


def test_call_llm_uses_gpt_4o_mini(monkeypatch):
    client = Mock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="OK"))]
    )
    monkeypatch.setattr(llm_client, "get_openai_client", lambda: client)

    response = llm_client.call_llm(
        prompt="Reply with OK.",
        system_prompt="Be concise.",
        temperature=0.0,
    )

    assert response == "OK"
    client.chat.completions.create.assert_called_once_with(
        messages=[
            {"role": "system", "content": "Be concise."},
            {"role": "user", "content": "Reply with OK."},
        ],
        model="gpt-4o-mini",
        temperature=0.0,
    )


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="Yêu cầu OPENAI_API_KEY để chạy live API test",
)
def test_call_llm_live():
    response = llm_client.call_llm(
        prompt="Trả lời ngắn gọn chữ 'OK' nếu bạn nhận được tin nhắn này."
    )
    assert response is not None
    assert len(response.strip()) > 0
