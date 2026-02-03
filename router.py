from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import tiktoken
from registry.provider_registry import provider_registry
from metrics.middleware import record_token_usage

try:
    token_encoding = tiktoken.get_encoding("cl100k_base")
except:
    token_encoding = None

llm_router = APIRouter(prefix="/v1")


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str
    messages: List[Message]
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000


class ChatResponse(BaseModel):
    id: str
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]


@llm_router.post("/chat/completions")
async def chat_completions(request: Request, chat_request: ChatRequest):
    
    if "/" not in chat_request.model:
        raise ValueError("Model format should be 'provider/model-name'")
    
    provider_name, model_name = chat_request.model.split("/", 1)
    
    request.state.provider = provider_name
    request.state.model = model_name
    
    provider_class = provider_registry.get(provider_name)
    provider = provider_class()
    
    payload = {
        "model": model_name,
        "messages": [msg.dict() for msg in chat_request.messages],
        "stream": chat_request.stream,
        "temperature": chat_request.temperature,
        "max_tokens": chat_request.max_tokens
    }
    
    if chat_request.stream:
        return await handle_streaming_request(provider, payload, provider_name, model_name)
    else:
        return await handle_non_streaming_request(provider, payload, provider_name, model_name)


async def handle_non_streaming_request(provider, payload, provider_name, model_name):
    response = await provider.generate(payload, stream=False)
    
    if token_encoding:
        input_text = " ".join([f"{m.get('role', '')}: {m.get('content', '')}" 
                               for m in payload.get("messages", [])])
        input_tokens = len(token_encoding.encode(input_text))
        
        output_text = ""
        if isinstance(response, dict):
            if "choices" in response and response["choices"]:
                output_text = response["choices"][0].get("message", {}).get("content", "")
            elif "content" in response:
                content = response["content"]
                output_text = content[0].get("text", "") if isinstance(content, list) else str(content)
        
        output_tokens = len(token_encoding.encode(output_text)) if output_text else 0
        record_token_usage(provider_name, model_name, input_tokens, output_tokens)
    
    return response


async def handle_streaming_request(provider, payload, provider_name, model_name):
    stream = await provider.generate(payload, stream=True)
    
    async def stream_generator():
        output_chunks = []
        
        try:
            async for chunk in stream:
                chunk_text = extract_text_from_chunk(chunk)
                if chunk_text:
                    output_chunks.append(chunk_text)
                yield chunk
            
            if token_encoding:
                input_text = " ".join([f"{m.get('role', '')}: {m.get('content', '')}" 
                                      for m in payload.get("messages", [])])
                input_tokens = len(token_encoding.encode(input_text))
                
                output_text = "".join(output_chunks)
                output_tokens = len(token_encoding.encode(output_text)) if output_text else 0
                
                record_token_usage(provider_name, model_name, input_tokens, output_tokens)
                
        except Exception as e:
            error_msg = f'data: {{"error": "{str(e)}"}}\n\n'
            yield error_msg.encode()
    
    return StreamingResponse(stream_generator(), media_type="text/event-stream")


@llm_router.get("/health")
async def health_check():
    return {"status": "healthy"}


@llm_router.get("/models")
async def list_models():
    models = {}
    for provider_name in provider_registry.providers.keys():
        capabilities = provider_registry.model_capabilities.get(provider_name, {})
        models[provider_name] = capabilities
    
    return {"models": models}


def extract_text_from_chunk(chunk):
    try:
        import json
        
        if isinstance(chunk, bytes):
            chunk = chunk.decode('utf-8')
        
        if isinstance(chunk, str) and chunk.startswith("data: "):
            data_str = chunk[6:].strip()
            if data_str and data_str != "[DONE]":
                data = json.loads(data_str)
                
                if "choices" in data and data["choices"]:
                    delta = data["choices"][0].get("delta", {})
                    return delta.get("content", "")
                
                if "delta" in data:
                    return data["delta"].get("text", "")
        
        return ""
    except:
        return ""
