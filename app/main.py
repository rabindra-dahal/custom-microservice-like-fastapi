import uvicorn
from .framework import CustomMicroFramework
from .config import settings  # Import the verified global configuration instance

app = CustomMicroFramework()

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
