from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "sqlite:///./nhl_screener.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
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


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
