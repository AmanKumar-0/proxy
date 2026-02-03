import httpx
import os
from providers.base import BaseProvider


class OpenAIProvider(BaseProvider):
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1/chat/completions"
        
        self.capabilities = {
            "gpt-4": {"max_tokens": 8192},
            "gpt-4-turbo": {"max_tokens": 128000},
            "gpt-3.5-turbo": {"max_tokens": 4096}
        }

    async def generate(self, payload, stream):
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        if stream:
            payload["stream_options"] = {"include_usage": True}
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            if stream:
                return await self._handle_streaming(client, headers, payload)
            else:
                return await self._handle_non_streaming(client, headers, payload)

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
                    if data.strip() == "[DONE]":
                        break
                    yield data.encode() + b"\n\n"

    async def count_tokens(self, input_text, output_text):
        import tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")
        input_tokens = len(encoding.encode(input_text))
        output_tokens = len(encoding.encode(output_text or ""))
        return input_tokens, output_tokens

    def get_model_capabilities(self, model):
        if model not in self.capabilities:
            raise ValueError(f"Model not found")
        return self.capabilities[model]
