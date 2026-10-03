from contextlib import asynccontextmanager
from typing import Annotated

from db import Todo, engine, init_db
from fastapi import Depends, FastAPI
from sqlmodel import Session, select


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


@app.get("/todos")
def get_todos(session: SessionDep):
    return session.exec(select(Todo)).all()


@app.get("/todos/{todo_id}")
def get_todo(todo_id: int, session: SessionDep):
    todo = session.get(Todo, todo_id)
    if todo:
        return todo
    return {"message": "Todo not found"}


@app.post("/todos")
def create_todo(todo: Todo, session: SessionDep):
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo


@app.put("/todos/{todo_id}")
def update_todo(todo_id: int, updated: Todo, session: SessionDep):
    existing = session.get(Todo, todo_id)
    if not existing:
        return {"message": "Todo not found"}
    existing.title = updated.title
    existing.completed = updated.completed
    session.commit()
    session.refresh(existing)
    return existing


@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int, session: SessionDep):
    existing = session.get(Todo, todo_id)
    if not existing:
        return {"message": "Todo not found"}
    session.delete(existing)
    session.commit()
    return existing

