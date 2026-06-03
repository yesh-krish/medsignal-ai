from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    environment: str = "local"
    rxnorm_base_url: str = "https://rxnav.nlm.nih.gov"
    rxnorm_timeout_seconds: float = 5.0
    openfda_base_url: str = "https://api.fda.gov"
    openfda_timeout_seconds: float = 10.0
    summarizer_model_name: str = "sshleifer/distilbart-cnn-6-6"
    summarizer_task: str = "summarization"
    summarizer_max_input_chars: int = 4000
    summarizer_max_new_tokens: int = 180
    summarizer_min_new_tokens: int = 60
    mlflow_tracking_uri: str = "http://mlflow:5000"
    mlflow_experiment_name: str = "medsignal-label-summarization"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
