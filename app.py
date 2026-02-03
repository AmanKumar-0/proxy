from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from auth.jwt_middleware import jwt_middleware
from metrics.middleware import metrics_middleware
from router import llm_router
from registry.provider_registry import provider_registry


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(BaseHTTPMiddleware, dispatch=metrics_middleware)
app.add_middleware(BaseHTTPMiddleware, dispatch=jwt_middleware)

app.include_router(llm_router)


@app.get("/")
async def root():
    return {
        "service": "AI Proxy Gateway",
        "providers": provider_registry.list_providers()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
