from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# host="localhost",dbname="fastapi",user="postgres",password="12345678",row_factory=dict_row

# NOTE: without +psycopg will use version 2 but if put it will use version 3 of psycopg driver

# SQLALCHEMY_DATABASE_URL = "postgresql+psycopg://postgres:12345678@localhost/fastapi"
SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}"

engine = create_engine(SQLALCHEMY_DATABASE_URL) # intial connection with database

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False) # used to create connections with database that connected 

Base = declarative_base() # used in creating model [tables]


# generate database connection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()