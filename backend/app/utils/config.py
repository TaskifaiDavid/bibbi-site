from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str
    api_port: int = 8000
    api_host: str = "0.0.0.0"
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: str = ".xlsx"
    
    # Email settings
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    email_use_tls: bool = True
    
    # OpenAI settings
    openai_api_key: str = ""
    openai_model: str = "gpt-4"
    openai_temperature: float = 0.1
    openai_max_tokens: int = 1000
    
    # Redis settings
    redis_url: str = "redis://localhost:6379"
    
    # Database URL for LangChain (constructed from Supabase settings)
    @property
    def database_url(self) -> str:
        """Construct PostgreSQL URL from Supabase URL - LEGACY, kept for compatibility"""
        return self.supabase_url.replace('https://', 'postgresql://postgres:').replace('.supabase.co', '.supabase.co:5432') + '/postgres'
    
    @property
    def langchain_database_url(self) -> str:
        """Dedicated PostgreSQL URL for LangChain chat functionality"""
        # First try the explicit DATABASE_URL from environment
        import os
        from dotenv import load_dotenv
        
        # Ensure .env is loaded
        load_dotenv()
        explicit_url = os.getenv("DATABASE_URL")
        if explicit_url:
            return explicit_url
        
        # Try to construct from available Supabase data if we have them
        try:
            # Extract project reference from Supabase URL
            supabase_host = self.supabase_url.replace("https://", "").replace("http://", "")
            project_ref = supabase_host.split('.')[0]
            
            # Read the actual DATABASE_URL from .env file directly if env loading failed
            env_file_path = os.path.join(os.getcwd(), '.env')
            if os.path.exists(env_file_path):
                with open(env_file_path, 'r') as f:
                    for line in f:
                        if line.startswith('DATABASE_URL='):
                            db_url = line.split('=', 1)[1].strip()
                            if db_url:
                                return db_url
            
            # Final fallback - let the chat system use Supabase REST API instead
            raise ValueError("DATABASE_URL not available, will use Supabase REST API fallback")
            
        except Exception as e:
            # This will trigger the Supabase REST API fallback in the chat system
            raise ValueError(f"DATABASE_URL environment variable is required for LangChain database connection: {str(e)}")
    
    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings():
    return Settings()