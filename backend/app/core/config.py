from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "Crypto Analysis System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Binance API 配置
    BINANCE_API_KEY: str = ""
    BINANCE_API_SECRET: str = ""
    
    # 数据库配置（暂时不用）
    DATABASE_URL: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()
