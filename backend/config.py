from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import SecretStr
from dotenv import load_dotenv


class Settings(BaseSettings):

    # Project Configuration
    project_name: Optional[str] = None
    project_description: Optional[str] = None

    # Database Configuration
    database_hostname: Optional[str] = None
    database_port: Optional[str] = None
    database_name: Optional[str] = None
    database_password: Optional[str] = None
    database_username: Optional[str] = None

    # Security Configuration
    secret_key: Optional[str] = None
    algorithm: Optional[str] = None
    access_token_expire_minutes: Optional[int] = None

    # Google API Configuration
    google_api_key: Optional[str] = None

    # LLM Configuration
    llm_provider: Optional[str] = None
    llm_api_key: Optional[SecretStr] = None
    llm_api_url: Optional[str] = None
    llm_api_version: Optional[str] = None
    llm_model: Optional[str] = None

    # Embedding Configuration
    embed_model: Optional[str] = None
    embed_api_key: Optional[SecretStr] = None
    embed_api_url: Optional[str] = None
    embed_api_version: Optional[str] = None
    resource_name: Optional[str] = None
   

    # Milvus Configuration
    milvus_host: Optional[str] = None
    milvus_port: Optional[int] = None
    collection_name: Optional[str] = None
    dimension: Optional[int] =None



    class Config:
        env_file = ".env"

settings = Settings()