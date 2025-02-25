from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase

from app.models import AnalyticsModel, ClickModel


class Base(DeclarativeBase):
    pass


class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ip = Column(String, index=True)
    city = Column(String, index=True)
    country = Column(String, index=True)

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
    updated_at = Column(DateTime, index=True)

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
