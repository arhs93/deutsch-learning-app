import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class VocabularyItem(Base):
    __tablename__ = "vocabulary_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    german_word: Mapped[str] = mapped_column(String, nullable=False)
    lemma: Mapped[str | None] = mapped_column(String, nullable=True)
    translation_en: Mapped[str] = mapped_column(String, nullable=False)
    part_of_speech: Mapped[str | None] = mapped_column(String, nullable=True)
    gender: Mapped[str | None] = mapped_column(String, nullable=True)
    plural_form: Mapped[str | None] = mapped_column(String, nullable=True)
    difficulty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    frequency_in_doc: Mapped[int] = mapped_column(Integer, default=1)
    example_sentence: Mapped[str | None] = mapped_column(Text, nullable=True)
    example_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    cefr_level: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["Document"] = relationship(back_populates="vocabulary_items")
    flashcards: Mapped[list["Flashcard"]] = relationship(back_populates="vocabulary_item")
    exercises: Mapped[list["Exercise"]] = relationship(back_populates="vocabulary_item")
