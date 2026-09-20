from fastapi import FastAPI,Depends
from contextlib import asynccontextmanager
from app.config.db import init_db,engine, Todo
from sqlmodel import Session, select
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)



def get_session():
    with Session(engine) as session:
        yield session

@app.get("/todos")
def get_todos(session: Session = Depends(get_session)):
    return session.exec(select(Todo)).all()


@app.get("/todos/{todo_id}")
def get_todo(todo_id: int, session: Session = Depends(get_session)):
    todo = session.get(Todo, todo_id)
    if todo:
        return todo
    return {"message": "Todo not found"}

@app.post("/todos")
def create_todo(todo: Todo, session: Session = Depends(get_session)):
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo

@app.put("/todos/{todo_id}")
def update_todo(todo_id: int, updated: Todo, session: Session = Depends(get_session)):
    existing = session.get(Todo, todo_id)
    if not existing:
        return {"message": "Todo not found"}
    existing.title = updated.title
    existing.completed = updated.completed
    session.commit()
    session.refresh(existing)
    return existing

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int, session: Session = Depends(get_session)):
    existing = session.get(Todo, todo_id)
    if not existing:
        return {"message": "Todo not found"}
    session.delete(existing)
    session.commit()
    return existing