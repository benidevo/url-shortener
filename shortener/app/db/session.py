from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import os

# Initialize engine once at module level
db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise ValueError("DATABASE_URL environment variable not set")

engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
