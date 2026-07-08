from app.db import engine
from app.models.base import Base
from app.models.repository import Repository

Base.metadata.create_all(engine)
print("tables created")