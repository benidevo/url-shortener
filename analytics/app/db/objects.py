from datetime import datetime

from app.models import AnalyticsModel, ClickModel
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    analytics_id = Column(Integer, ForeignKey("analytics.id"), nullable=False)
    ip = Column(String, index=True, default="")
    city = Column(String, index=True, default="")
    country = Column(String, index=True, default="")

    def to_model(self):
        return ClickModel(
            ip=self.ip,
            city=self.city,
            country=self.country,
        )

    @classmethod
    def from_model(cls, model: ClickModel):
        return cls(
            ip=model.ip,
            city=model.city,
            country=model.country,
        )

    def __repr__(self):
        return f"Click(id={self.id}, ip={self.ip}, city={self.city}, country={self.country})"  # noqa


class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    short_link = Column(String, index=True, nullable=False)
    updated_at = Column(DateTime, index=True, default=datetime.now)
    clicks = relationship("Click", cascade="all, delete-orphan")

    def to_model(self):
        return AnalyticsModel(
            short_link=self.short_link,
            updated_at=self.updated_at,
            clicks=[click.to_model() for click in self.clicks],
        )

    @classmethod
    def from_model(cls, model: AnalyticsModel):
        return cls(
            short_link=model.short_link,
            updated_at=model.updated_at,
            clicks=[Click.from_model(click) for click in model.clicks],
        )

    def __repr__(self):
        return f"Analytics(id={self.id}, short_link={self.short_link}, updated_at={self.updated_at})"
