import uvicorn
from .framework import CustomMicroFramework
from .config import settings  # Import the verified global configuration instance
from .utils.rate_limiter import RateLimiter
from .utils.responses import JSONResponse

# Configure a strict rate limiter constraint layer: Maximum 3 requests every 10 seconds
limiter = RateLimiter(requests_limit=3, window_seconds=10)

app = CustomMicroFramework()

from .utils.rate_limiter import RateLimiter
from .utils.responses import JSONResponse

# Configure a strict rate limiter constraint layer: Maximum 3 requests every 10 seconds
limiter = RateLimiter(requests_limit=3, window_seconds=10)

@app.middleware()
async def ip_rate_limiter_middleware(scope, call_next):
    """
    Intercepts ASGI connection footprints to enforce strict request rate limits.
    Rejects abusive callers with a 429 status code before running any endpoints.
    """
    # 1. Extract the client's network address out of the ASGI client metadata list
    # The ASGI scope structure maps client properties as a tuple array: (ip_string, port_integer)
    client_tuple = scope.get("client")
    client_ip = client_tuple[0] if client_tuple else "127.0.0.1"

    # 2. Check the rate limiter engine
    if not limiter.is_allowed(client_ip):
        print(f"[Rate Limiter] Blocked traffic from abusive IP source: {client_ip}")
        
        # 3. Short-circuit the request pipeline instantly by returning a 429 response tuple
        # We match the framework's internal 5-element execution layout cleanly
        err_response = JSONResponse(
            content={"error": "Too Many Requests", "message": "Slow down! Velocity thresholds breached."},
            status_code=429
        )
        return err_response.status_code, err_response.get_headers(), err_response.render(), None, err_response

    # Proceed down the execution chain if everything is fine
    return await call_next(scope)


@app.get("/api/v1/system/config")
async def fetch_runtime_config():
    """
    Returns the application's active configuration properties, verifying type casting.
    """
    return {
        "application_identity": settings.APP_NAME,
        "environment_profiles": {
            "debug_active": settings.DEBUG_MODE,
            "debug_type": str(type(settings.DEBUG_MODE)),
            "allocated_port": settings.SERVER_PORT,
            "port_type": str(type(settings.SERVER_PORT)),
            "credential_mask": settings.DATABASE_SECRET_KEY[:5] + "******"
        }
    }

if __name__ == "__main__":
    # Dynamically utilize parsed environment variables to launch the ASGI server
    uvicorn.run("app.main:app", host="127.0.0.1", port=settings.SERVER_PORT, reload=settings.DEBUG_MODE)
