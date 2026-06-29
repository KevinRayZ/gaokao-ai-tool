"""配置管理"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置，从 .env 文件或环境变量读取"""

    # API 配置
    app_name: str = "高考志愿填报AI分析工具"
    app_version: str = "0.1.0"
    debug: bool = False

    # LLM API 配置
    llm_api_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 8000

    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8000

    # 用量限制配置
    daily_request_limit: int = 100  # 全局每日最大请求次数（防滥用上限）
    rate_limit_per_minute: int = 5  # 每分钟最大请求次数

    # 付费配置
    admin_key: str = "change-me-in-env"  # 管理员接口密钥，务必在 .env 中修改
    price_per_analysis: str = "19.9"     # 每次分析价格（元），用于前端展示
    contact_wechat: str = "rayz1000"     # 联系微信，用于前端展示

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
