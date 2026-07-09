from app.db import engine
from app.models.base import Base
from app.models.repository import Repository
from app.models.pull_request import PullRequest
from app.models.analysis_run import AnalysisRun
from app.models.finding import Finding

Base.metadata.create_all(engine)
print("tables created")