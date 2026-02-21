import os

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
DATABASE_URL = os.getenv("DATABASE_URL")
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL")


def _parse_cors_origins(raw_value: str) -> list[str]:
    origins = [origin.strip().rstrip("/") for origin in raw_value.split(",")]
    return [origin for origin in origins if origin]


CORS_ORIGINS = _parse_cors_origins(
    os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
)
