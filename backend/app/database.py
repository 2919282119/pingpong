from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "MYSQL_PASSWORD_ENV_VAR",
    "database": "pingpong",
    "port": 3306,
}

DB_URL = (
    f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    f"?charset=utf8mb4"
)

engine = create_engine(DB_URL, pool_pre_ping=True, pool_size=10)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
