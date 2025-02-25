from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase

from app.models import UrlModel


class Base(DeclarativeBase):
    pass


class Url(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    link = Column(Text, nullable=False)
    short_link = Column(String(7), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    def to_model(self) -> UrlModel:
        return UrlModel(
            link=self.link,
            short_link=self.short_link,
            created_at=self.created_at
        )

    @classmethod
    def from_model(cls, model: UrlModel):
        return Url(
            link=model.link,
            short_link=model.short_link,
        )

    def __repr__(self):
        return f"Url(id={self.id}, link={self.link}, short_link={self.short_link}, created_at={self.created_at})"  # noqa
