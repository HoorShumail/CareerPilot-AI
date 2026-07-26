import pytest
from unittest.mock import AsyncMock, patch
from openai import AuthenticationError, RateLimitError
from src.infrastructure.llm.openai_provider import OpenAIProvider


@pytest.mark.asyncio
async def test_openai_provider_initialization():
    provider = OpenAIProvider(api_key="sk-test-key", base_url="https://api.openai.com/v1", model="gpt-4o-mini")
    assert provider.model == "gpt-4o-mini"
    assert provider.base_url == "https://api.openai.com/v1"


@pytest.mark.asyncio
async def test_openai_provider_generate_success():
    provider = OpenAIProvider(api_key="sk-test-key")
    mock_choice = AsyncMock()
    mock_choice.message.content = '{"result": "success"}'
    mock_response = AsyncMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = AsyncMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
    mock_response._request_id = "req_123"

    with patch.object(provider.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        res = await provider.generate("Test prompt")
        assert res == '{"result": "success"}'
        mock_create.assert_called_once()



@pytest.mark.asyncio
async def test_openai_provider_maps_authentication_error():
    provider = OpenAIProvider(api_key="sk-test-key")
    
    mock_response = AsyncMock()
    mock_response.status_code = 401
    mock_response.headers = {}
    
    auth_err = AuthenticationError(message="Invalid API Key", response=mock_response, body=None)

    with patch.object(provider.client.chat.completions, "create", side_effect=auth_err):
        with pytest.raises(RuntimeError) as exc_info:
            await provider.generate("Test prompt")
        assert "Invalid OpenAI API key" in str(exc_info.value)
