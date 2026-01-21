from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Use PostgreSQL from environment variable, fallback to SQLite for local dev
# Neon/Vercel can use different variable names
DATABASE_URL = (
    os.environ.get("DATABASE_URL") or
    os.environ.get("POSTGRES_URL") or
    os.environ.get("POSTGRES_PRISMA_URL") or
    os.environ.get("POSTGRES_URL_NON_POOLING") or
    "sqlite:///./nhl_screener.db"
)

# Handle Neon/Vercel postgres:// -> postgresql:// conversion
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configure engine based on database type
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    league = Column(String(10), index=True, default="NHL")  # NHL, AHL
    team_id = Column(String(20), index=True)  # Original team ID from API
    abbrev = Column(String(10), index=True)
    name = Column(String(100))
    name_ru = Column(String(100), nullable=True)
    logo_url = Column(String(500), nullable=True)

    home_games = relationship("Game", foreign_keys="Game.home_team_id", back_populates="home_team")
    away_games = relationship("Game", foreign_keys="Game.away_team_id", back_populates="away_team")

    __table_args__ = (
        # Unique constraint on league + abbrev combination
        {"sqlite_autoincrement": True},
    )


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True)
    league = Column(String(10), index=True, default="NHL")  # NHL, AHL
    game_id = Column(String(20), index=True)
    date = Column(DateTime, index=True)
    home_team_id = Column(Integer, ForeignKey("teams.id"))
    away_team_id = Column(Integer, ForeignKey("teams.id"))
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    is_finished = Column(Boolean, default=False)
    season = Column(String(10))

    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_games")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_games")


class DataUpdate(Base):
    __tablename__ = "data_updates"

    id = Column(Integer, primary_key=True)
    updated_at = Column(DateTime, default=datetime.utcnow)
    update_type = Column(String(50))


class ValueBetPrediction(Base):
    __tablename__ = "value_bet_predictions"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Event info
    event_id = Column(String(50), index=True)
    league = Column(String(10), index=True)
    scheduled = Column(DateTime, index=True)

    # Teams
    home_team = Column(String(100))
    home_abbrev = Column(String(10))
    away_team = Column(String(100))
    away_abbrev = Column(String(10))

    # Bet info
    bet_type = Column(String(50))  # home-it-over, away-it-under, match-total-over, etc.
    bet_label = Column(String(100))  # Human readable: "ИТБ Edmonton Oilers"
    line = Column(Float)  # 2.5, 5.5, etc.

    # Odds and value
    odds = Column(Float)
    probability = Column(Float)  # 0-1
    fair_odds = Column(Float)
    value_percentage = Column(Float)  # Value %

    # Result tracking
    is_checked = Column(Boolean, default=False)
    is_won = Column(Boolean, nullable=True)  # NULL = not checked yet
    actual_result = Column(String(20), nullable=True)  # e.g., "3-2", "over", "under"
    checked_at = Column(DateTime, nullable=True)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
