from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    postgres_url: str
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    voyage_api_key: str
    anthropic_api_key: str
    semantic_scholar_api_key: str = ""
    research_inbox_dir: Path = Path.home() / "research-inbox"
    reports_dir: Path = Path("./reports")
    concept_map_path: Path = Path("./data/concept_map.json")

    model_config = {"env_file": ".env"}


settings = Settings()
