from .utils.config import BaseSettings

class Settings(BaseSettings):
    """
    Declares the configuration schema contracts and fallback defaults 
    for your microservice container.
    """
    APP_NAME: str = "Custom-Microservice-Core"
    APP_VERSION: str = "3.0.0"
    DEBUG_MODE: bool = False
    SERVER_PORT: int = 8000
    
    # Enforces explicit scanning presence
    DATABASE_SECRET_KEY: str = None 

# Instantiate a single global configuration object
settings = Settings()
