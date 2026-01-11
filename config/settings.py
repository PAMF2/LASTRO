from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configurações globais da aplicação"""
    
    # Geral
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    timezone: str = "America/Sao_Paulo"
    
    # APIs de IA
    google_api_key: str  # Google Gemini API Key
    
    # WhatsApp (Twilio)
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_whatsapp_number: str
    
    # Redis (opcional)
    redis_host: Optional[str] = None
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # Database
    database_url: str
    
    # Webhooks
    zap_webhook_secret: Optional[str] = None
    vivareal_webhook_secret: Optional[str] = None
    olx_webhook_secret: Optional[str] = None
    
    # Google Calendar
    google_calendar_credentials_path: str = "./config/google_calendar_credentials.json"
    
    # Configurações do sistema
    max_messages_per_day: int = 5
    lead_response_threshold_hours: int = 24
    vigilante_check_interval_minutes: int = 5
    
    # Sentry
    sentry_dsn: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
