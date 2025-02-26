from app.config import Settings, get_settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Config: Settings = get_settings()
db_url = Config.DATABASE_URL

if not db_url:
    raise ValueError("DATABASE_URL environment variable not set")

engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
