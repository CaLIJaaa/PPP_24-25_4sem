from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_URL = "sqlite:///./library.db"

engine = create_engine(
    DB_URL, connect_args={"check_same_thread": False} # для sqlite + fastapi
)
DbSess = sessionmaker(autocommit=False, autoflush=False, bind=engine)

OrmBase = declarative_base()

# отдает сессию бд
def get_db():
    db = DbSess()
    try:
        yield db
    finally:
        db.close() 