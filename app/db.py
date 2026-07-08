from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_engine(settings.database_url)          # 1. connection manager: knows the address, pools connections
SessionLocal = sessionmaker(bind=engine)               # 2. session factory: stamps out workspaces, each wired to the engine
def get_db():                                          # 3. the handout pattern: yields a session, guarantees it closes
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()