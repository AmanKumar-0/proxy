import httpx
import os
from providers.base import BaseProvider


class ClaudeProvider(BaseProvider):
    
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.base_url = "https://api.anthropic.com/v1/messages"
        
        self.capabilities = {
            "claude-3-opus": {"max_tokens": 200000},
            "claude-3-sonnet": {"max_tokens": 200000},
            "claude-3-haiku": {"max_tokens": 200000}
        }

    async def generate(self, payload, stream):
        
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        claude_payload = self._convert_to_claude_format(payload)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            if stream:
                return await self._handle_streaming(client, headers, claude_payload)
            else:
                return await self._handle_non_streaming(client, headers, claude_payload)

    def _convert_to_claude_format(self, payload):
        return {
            "model": payload.get("model"),
            "messages": payload.get("messages"),
            "max_tokens": payload.get("max_tokens", 1000),
            "temperature": payload.get("temperature", 0.7),
            "stream": payload.get("stream", False)
        }

    async def _handle_non_streaming(self, client, headers, payload):
        response = await client.post(self.base_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

    async def _handle_streaming(self, client, headers, payload):
        async with client.stream("POST", self.base_url, headers=headers, json=payload) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line.strip() and line.startswith("data: "):
                    data = line[6:]
                    yield data.encode() + b"\n\n"

    async def count_tokens(self, input_text, output_text):
        input_tokens = len(input_text) * 10 // 35
        output_tokens = len(output_text or "") * 10 // 35
        return input_tokens, output_tokens

    def get_model_capabilities(self, model):
        if model not in self.capabilities:
            raise ValueError("Model not found")
        return self.capabilities[model]
