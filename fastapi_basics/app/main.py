from fastapi import FastAPI

app = FastAPI()

todos = [
    {"id": 1, "title": "Learn FastAPI"},
    {"id": 2, "title": "Build Todo API"},
]


@app.get("/")
def read_root():
    return {"Hello": "World"}


# @app.get("/todos")
# def get_todos():
#     return todos

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    for index, todo in enumerate(todos):
        if todo["id"] == todo_id:
            deleted_todo = todos.pop(index)
            return deleted_todo
    return {"message": "Todo not found"}

@app.get("/todos")
def get_todos(search: str | None = None):
    if search is None:
        return todos

    results = []
    for todo in todos:
        if search.lower() in todo["title"].lower():
            results.append(todo)
    return results