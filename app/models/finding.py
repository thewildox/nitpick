from sqlalchemy import ForeignKey, String, func, Enum, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

import enum

class Source(enum.Enum):
    RUFF = "ruff"
    BANDIT = "bandit"
    AST = "ast"
    LLM = "llm"

class Finding(Base):
    __tablename__ = "findings"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_run_id: Mapped[int] = mapped_column(ForeignKey("analysis_runs.id"))
    file_path: Mapped[str] = mapped_column(String(255))
    line_number: Mapped[int] = mapped_column(Integer)
    severity: Mapped[str] = mapped_column(String(255))
    source: Mapped[Source] = mapped_column(Enum(Source))
    rule_id: Mapped[str | None] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text())
    suggestion: Mapped[str | None] = mapped_column(Text())