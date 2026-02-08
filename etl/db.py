from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
import sqlite3
from .config import DB_URL, SCHEMA_PATH
from .logging_utils import log_info

_engine = None
_Session = None

def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(DB_URL, echo=False, future=True)
        if DB_URL.startswith('sqlite'):
            # Enable foreign keys for SQLite
            with _engine.connect() as conn:
                conn.execute(text('PRAGMA foreign_keys=ON'))
    return _engine

def get_session() -> Session:
    global _Session
    if _Session is None:
        _Session = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, future=True)
    return _Session()

def init_db(schema_path: str = SCHEMA_PATH):
    engine = get_engine()
    with engine.connect() as conn:
        with open(schema_path, 'r') as f:
            sql = f.read()
        for stmt in sql.split(';'):
            stmt = stmt.strip()
            if stmt:
                try:
                    conn.execute(text(stmt))
                except Exception as e:
                    log_info(f"Skipping statement (may already exist): {stmt[:40]}...", error=str(e))
    log_info("Database initialized.")
