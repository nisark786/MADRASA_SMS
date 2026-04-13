from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database Configuration - MUST be set via .env file
    DATABASE_URL: str
    
    # Database Connection Pool Configuration
    DB_POOL_SIZE: int = 20                    # Connections to keep in pool
    DB_MAX_OVERFLOW: int = 10                 # Additional connections during peaks
    DB_POOL_TIMEOUT: int = 10                 # Timeout in seconds to get connection
    DB_POOL_RECYCLE: int = 900                # Recycle connections every 15 minutes
    
    # Redis Configuration
    REDIS_URL: str = "redis://redis:6379"
    
    # Security Settings - CRITICAL: Never use default in production
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    
    # Token Expiration
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Frontend URL for CORS
    FRONTEND_URL: str = "http://localhost:5173"
    
    # Rate Limiting (requests per minute)
    LOGIN_RATE_LIMIT: int = 5
    API_RATE_LIMIT: int = 60

    class Config:
        env_file = ".env"
        # Raises error if required env vars are missing
        case_sensitive = True


settings = Settings()
