from sqlmodel import SQLModel, Field,create_engine
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)

def init_db():
    SQLModel.metadata.create_all(engine)

class Todo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    completed: bool = False