import jwt
from fastapi import Request
from fastapi.responses import JSONResponse
from config import settings


async def jwt_middleware(request: Request, call_next):
    
    if request.url.path in ["/metrics", "/health", "/"]:
        return await call_next(request)
    
    if not request.url.path.startswith("/v1/"):
        return await call_next(request)
    
    auth_header = request.headers.get("Authorization")
    
    if not auth_header:
        return JSONResponse(
            status_code=401,
            content={"error": "Missing Authorization header"}
        )
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid Authorization header"}
        )
    
    token = parts[1]
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        request.state.user_id = payload.get("user_id")
        request.state.email = payload.get("email")
        
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"error": "Token expired"}
        )
    except jwt.InvalidTokenError:
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid token"}
        )
    
    return await call_next(request)
