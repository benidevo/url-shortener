from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, relationship

from app.models import AnalyticsModel, ClickModel


class Base(DeclarativeBase):
    pass


class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    analytics_id = Column(Integer, ForeignKey("analytics.id"), nullable=False)
    ip = Column(String, index=True, default="")
    city = Column(String, index=True, default="")
    country = Column(String, index=True, default="")
    created_at = Column(DateTime, index=True, nullable=False, default=datetime.now)

    def to_model(self) -> ClickModel:
        return ClickModel(  # type: ignore
            ip=self.ip,  # type: ignore
            city=self.city,  # type: ignore
            country=self.country,  # type: ignore
            created_at=self.created_at,  # type: ignore
        )

    @classmethod
    def from_model(cls, model: ClickModel) -> "Click":
        return cls(
            ip=model.ip,
            city=model.city,
            country=model.country,
            created_at=model.created_at,
        )

    def __repr__(self):
        return (
            f"Click(id={self.id}, ip={self.ip}, city={self.city}, "
            f"country={self.country}, created_at={self.created_at})"
        )


class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    short_link = Column(String, index=True, nullable=False)
    updated_at = Column(DateTime, index=True, default=datetime.now)
    clicks = relationship("Click", cascade="all, delete-orphan")

    def to_model(self) -> AnalyticsModel:
        return AnalyticsModel(
            short_link=self.short_link,  # type: ignore[arg-type]
            updated_at=self.updated_at,  # type: ignore[arg-type]
            clicks=[click.to_model() for click in self.clicks],
        )

    @classmethod
    def from_model(cls, model: AnalyticsModel) -> "Analytics":
        return cls(
            short_link=model.short_link,
            updated_at=model.updated_at,
            clicks=[Click.from_model(click) for click in model.clicks],
        )

    def __repr__(self):
        return (
            f"Analytics(id={self.id}, "
            f"short_link={self.short_link}, "
            f"updated_at={self.updated_at})"
        )
