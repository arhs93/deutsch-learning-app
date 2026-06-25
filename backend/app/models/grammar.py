import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class GrammarPattern(Base):
    __tablename__ = "grammar_patterns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"))
    pattern_type: Mapped[str] = mapped_column(String, nullable=False)
    pattern_name: Mapped[str] = mapped_column(String, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    rule_summary: Mapped[str] = mapped_column(Text, nullable=False)
    example_from_doc: Mapped[str] = mapped_column(Text, nullable=False)
    example_translation: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    occurrences: Mapped[int] = mapped_column(Integer, default=1)
    ai_analysis: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["Document"] = relationship(back_populates="grammar_patterns")
    exercises: Mapped[list["Exercise"]] = relationship(back_populates="grammar_pattern")
