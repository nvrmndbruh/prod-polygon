from pydantic_settings import BaseSettings


# класс для загрузки конфигурации из переменных окружения
class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ENVIRONMENTS_PATH: str = "/app/environments"
    LXD_URL: str = "https://host.docker.internal:8443"
    LXD_CERT: str = "/app/lxd-certs/lxd-client.crt"
    LXD_KEY: str = "/app/lxd-certs/lxd-client.key"

    class Config:
        env_file = ".env"


settings = Settings()