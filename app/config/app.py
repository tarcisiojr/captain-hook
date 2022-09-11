import os
from pathlib import Path

from pydantic import BaseModel, BaseSettings


class MongoSettings(BaseModel):
    connection_uri: str


class AppSettings(BaseSettings):
    mongo: MongoSettings

    class Config:
        env_nested_delimiter = "__"
        env_file = Path(f"{os.path.dirname(__file__)}/../../{os.getenv('ENV_FILE', '.env')}").resolve()
        env_file_encoding = 'utf-8'


settings = AppSettings()