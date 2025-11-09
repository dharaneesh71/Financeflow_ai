from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path

# Determine the project root directory (2 levels up from backend/app/config.py)
# This ensures we find .env at the project root regardless of working directory
CONFIG_FILE_DIR = Path(__file__).parent.resolve()  # backend/app/
ENV_FILE = CONFIG_FILE_DIR / ".env"

class Settings(BaseSettings):
    """Application Settings"""
    
    # API Keys
    gemini_api_key: str = ""
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
    upload_dir: str = "./uploads"
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else ".env",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,  # Allow both field name and alias
    )

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# Test settings on import
try:
    settings = get_settings()
    # Report which .env file was found/used
    if ENV_FILE.exists():
        print(f"⚙️  Configuration loaded from .env file at: {ENV_FILE}")
    else:
        # Check if .env exists in current working directory
        cwd_env = Path(".env")
        if cwd_env.exists():
            print(f"⚙️  Configuration loaded from .env file at: {cwd_env.absolute()}")
        else:
            print(f"⚠️  .env file not found at {ENV_FILE} or current directory")
            print(f"   Using environment variables and defaults")
            print(f"   Expected .env location: {ENV_FILE}")
except Exception as e:
    print(f"❌ Configuration error: {e}")
    print(f"   Make sure .env file exists with required settings")