from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request
from fastapi.responses import Response as FastAPIResponse
import time


REQUEST_COUNT = Counter(
    "llm_requests_total",
    "Total number of LLM requests",
    ["provider", "model", "status"]
)

INPUT_TOKENS = Counter(
    "llm_input_tokens_total",
    "Total input tokens processed",
    ["provider", "model"]
)

OUTPUT_TOKENS = Counter(
    "llm_output_tokens_total",
    "Total output tokens generated",
    ["provider", "model"]
)

REQUEST_LATENCY = Histogram(
    "llm_request_duration_seconds",
    "Request latency in seconds",
    ["provider", "model"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

ACTIVE_REQUESTS = Gauge(
    "llm_active_requests",
    "Number of active requests",
    ["provider", "model"]
)

ERROR_COUNT = Counter(
    "llm_errors_total",
    "Total number of errors",
    ["provider", "model", "error_type"]
)


async def metrics_middleware(request: Request, call_next):
    
    if request.url.path == "/metrics":
        metrics = generate_latest()
        return FastAPIResponse(content=metrics, media_type=CONTENT_TYPE_LATEST)
    
    if not request.url.path.startswith("/v1/"):
        return await call_next(request)
    
    provider = getattr(request.state, "provider", "unknown")
    model = getattr(request.state, "model", "unknown")
    
    ACTIVE_REQUESTS.labels(provider=provider, model=model).inc()
    
    start_time = time.time()
    status = "success"
    
    try:
        response = await call_next(request)
        
        if response.status_code >= 400:
            status = "error"
        
        return response
        
    except Exception as e:
        status = "error"
        error_type = type(e).__name__
        ERROR_COUNT.labels(provider=provider, model=model, error_type=error_type).inc()
        raise
        
    finally:
        duration = time.time() - start_time
        REQUEST_COUNT.labels(provider=provider, model=model, status=status).inc()
        REQUEST_LATENCY.labels(provider=provider, model=model).observe(duration)
        ACTIVE_REQUESTS.labels(provider=provider, model=model).dec()


def record_token_usage(provider, model, input_tokens, output_tokens):
    INPUT_TOKENS.labels(provider=provider, model=model).inc(input_tokens)
    OUTPUT_TOKENS.labels(provider=provider, model=model).inc(output_tokens)
