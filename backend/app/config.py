from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application Settings"""
    
    # API Keys
    gemini_api_key: str
    landingai_api_key: str = ""
    
    # Snowflake Configuration
    snowflake_account: str = ""
    snowflake_user: str = ""
    snowflake_password: str = ""
    snowflake_warehouse: str = "COMPUTE_WH"
    snowflake_database: str = "FINANCIAL_DATA"
    snowflake_schema: str = "PUBLIC"
    snowflake_role: str = "ACCOUNTADMIN"
    
    # Application
    environment: str = "development"
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# Test settings on import
try:
    settings = get_settings()
    print(f"⚙️  Configuration loaded from .env")
except Exception as e:
    print(f"❌ Configuration error: {e}")
    print(f"   Make sure .env file exists with required settings")