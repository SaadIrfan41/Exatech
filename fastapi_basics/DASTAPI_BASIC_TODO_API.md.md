# FastAPI From Zero: Building a Todo API

A step-by-step guide to building your own backend API. No prior API experience needed — we go one idea at a time, and every idea is used immediately in code.

**Don't try to memorize everything at once.** Each step builds on the one before it.

---

## What we're building

By the end, you'll have a small backend that can:

```
GET     /todos        → get all todos
GET     /todos/1      → get one todo
POST    /todos        → create a todo
PUT     /todos/1      → update a todo
DELETE  /todos/1      → delete a todo
```

We'll store todos in a plain Python list in memory (no database yet) — because first we need to understand how the API itself works. The database comes later.

```
FastAPI Application → Python list → Todo data
```

---

## Step 1 — What is an API?

**API = Application Programming Interface.** It's how one program talks to another.

```
Browser --"Give me my todos"--> Backend
Browser <--"Here are the todos"-- Backend
```

The browser never touches your Python code directly — it talks to your API, and the API talks to the code.

**A simple way to picture it — a restaurant:**

```
You → Waiter → Kitchen → Waiter → You
```

You don't walk into the kitchen and cook yourself. You tell the waiter what you want, the waiter relays it to the kitchen, and brings the food back. The API is the waiter between the frontend and the backend.

---

## Step 2 — Request and response

A **request** is a message asking the server to do something:
```
GET /todos   →  "Server, give me the todos."
POST /todos  →  "Server, create a new todo."
```

A **response** is what the server sends back:
```json
[
  { "id": 1, "title": "Learn FastAPI" },
  { "id": 2, "title": "Build Todo App" }
]
```

---

## Step 3 — Routes and HTTP methods

A **route** is an address in your API — it tells the server: *"when a request comes to this address, run this code."*

A route has two parts: an **HTTP method** + a **path**.

```
GET /todos
 ↑     ↑
method  path
```

The four methods you'll use constantly:

| Method | Purpose | Think of it as |
|---|---|---|
| GET | Read data | "Give me something" |
| POST | Create data | "Create something" |
| PUT | Update data | "Change something" |
| DELETE | Delete data | "Remove something" |

For our Todo app:
```
GET     /todos       → get todos
POST    /todos       → create todo
PUT     /todos/1     → update todo #1
DELETE  /todos/1     → delete todo #1
```

Notice `GET /todos` and `POST /todos` share the same path but different methods — they're still two different, separate endpoints.

---

## Step 4 — Set up the project

We'll use **uv** to manage the project and its dependencies.

```bash
uv init . --no-package
```
`.` = create the project here. `--no-package` = this isn't a Python package meant to be installed elsewhere, just an app.

Now install FastAPI:
```bash
uv add "fastapi[standard]"
```

Create a folder called `app/` with a file inside it called `main.py`. Your project should look like this:

```
todo-api/
├── app/
│   └── main.py
├── pyproject.toml
├── uv.lock
└── README.md
```

`main.py` is where our whole API lives.

---

## Step 5 — Create and run your first FastAPI app

In `app/main.py`:

```python
from fastapi import FastAPI

app = FastAPI()
```

- `from fastapi import FastAPI` — import the FastAPI class.
- `app = FastAPI()` — create your application. Think of `app` as *"our API."*

Run it:
```bash
uv run fastapi dev ./app/main.py
```

You should see:
```
Uvicorn running on http://127.0.0.1:8000
```

Open that address in your browser. Nothing to see yet — we haven't created a route.

---

## Step 6 — Your first route

Update `main.py`:

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def home():
    return {"message": "Hello World"}
```

Open `http://127.0.0.1:8000/` — you'll get:
```json
{ "message": "Hello World" }
```

**How to read this:**
```
GET /  →  home()  →  {"message": "Hello World"}
```

`@app.get("/")` tells FastAPI: *"when a GET request hits `/`, run the function below it."* `/` is the **root path** — the base address of your server.

---

## Step 7 — GET: reading data

`GET` is used to retrieve/read data. Let's give ourselves some data to read.

```python
from fastapi import FastAPI

app = FastAPI()

todos = [
    {"id": 1, "title": "Learn FastAPI"},
    {"id": 2, "title": "Build Todo API"},
]


@app.get("/")
def home():
    return {"message": "Hello World"}


@app.get("/todos")
def get_todos():
    return todos
```

Visit `http://127.0.0.1:8000/todos` and you'll get the full list back as JSON.

`/todos` is a **static route** — the path never changes. (Other examples: `/users`, `/about`, `/products`.)

---

## Step 8 — Getting *one* todo (dynamic routes)

What if we only want todo #1, not the whole list? We don't want to write a separate function for every possible ID:

```python
@app.get("/todos/1")   # bad - not scalable
@app.get("/todos/2")   # bad - not scalable
```

Instead, we use a **dynamic route** — a part of the path that can change:

```python
@app.get("/todos/{todo_id}")
def get_todo(todo_id: int):
    for todo in todos:
        if todo["id"] == todo_id:
            return todo
    return {"message": "Todo not found"}
```

`{todo_id}` is called a **path parameter**. If you request `/todos/1`, FastAPI passes `todo_id = 1` into your function automatically.

The `: int` after `todo_id` tells FastAPI to expect a number — `/todos/5` works, `/todos/hello` gets rejected automatically. That validation is free, built into FastAPI.

---

## Step 9 — POST: creating data

`POST` is used to create new data. Note that `GET /todos` and `POST /todos` use the *same path* but are different endpoints because the method is different.

Data sent to create something is called the **request body**:

```
POST /todos
Body: { "title": "Learn Docker" }
```

```python
@app.post("/todos")
def create_todo(todo: dict):
    new_todo = {
        "id": len(todos) + 1,
        "title": todo["title"]
    }
    todos.append(new_todo)
    return new_todo
```

Send a POST request with `{"title": "Learn Docker"}` and the server appends it to the list, then returns the new todo.

---

## Step 10 — PUT: updating data

`PUT` updates something that already exists. Since we need to say *which* todo to update, we combine it with a path parameter:

```
PUT /todos/1
Body: { "title": "Learn FastAPI and Docker" }
```

```python
@app.put("/todos/{todo_id}")
def update_todo(todo_id: int, todo: dict):
    for item in todos:
        if item["id"] == todo_id:
            item["title"] = todo["title"]
            return item
    return {"message": "Todo not found"}
```

---

## Step 11 — DELETE: removing data

```
DELETE /todos/1   →  "Delete todo number 1."
```

```python
@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    for index, todo in enumerate(todos):
        if todo["id"] == todo_id:
            deleted_todo = todos.pop(index)
            return deleted_todo
    return {"message": "Todo not found"}
```

---

## Step 12 — You now have CRUD

**CRUD** = Create, Read, Update, Delete — the four basic operations almost every API needs.

| CRUD | HTTP | Route | Purpose |
|---|---|---|---|
| Create | POST | `/todos` | Create a todo |
| Read | GET | `/todos` | Get all todos |
| Read | GET | `/todos/{id}` | Get one todo |
| Update | PUT | `/todos/{id}` | Update a todo |
| Delete | DELETE | `/todos/{id}` | Delete a todo |

---

## Step 13 — Query parameters (filtering results)

You've already met **path parameters** (`/todos/{todo_id}`) — they identify *which* resource. **Query parameters** are different: they come after a `?` and filter/customize the result.

```
/todos?completed=true
```

**The distinction that matters:**
```
Path parameter  → "Which resource?"          e.g. /todos/10
Query parameter → "How should I filter it?"  e.g. /todos?completed=true
```

Example — search todos by title:

```python
@app.get("/todos")
def get_todos(search: str | None = None):
    if search is None:
        return todos

    results = []
    for todo in todos:
        if search.lower() in todo["title"].lower():
            results.append(todo)
    return results
```

Now `GET /todos` still returns everything, but `GET /todos?search=fastapi` returns only matching titles. `search: str | None = None` means the parameter is optional — the route works with or without it.

You can have more than one query parameter, separated by `&`:
```
/todos?search=fastapi&limit=5
```
```python
@app.get("/todos")
def get_todos(search: str | None = None, limit: int | None = None):
    ...
```

---

## Step 14 — Free automatic documentation

While your server is running, open:
```
http://127.0.0.1:8000/docs
```

FastAPI generates an interactive page (Swagger UI) listing every route you've built, and lets you test them directly in the browser — no extra code required.

---

## Step 15 — The complete Todo API

Putting it all together:

```python
from fastapi import FastAPI

app = FastAPI()

todos = [
    {"id": 1, "title": "Learn FastAPI"},
    {"id": 2, "title": "Build Todo API"},
]


@app.get("/")
def home():
    return {"message": "Todo API is running"}


@app.get("/todos")
def get_todos(search: str | None = None, limit: int | None = None):
    results = todos

    if search:
        results = [
            todo for todo in results
            if search.lower() in todo["title"].lower()
        ]

    if limit:
        results = results[:limit]

    return results


@app.get("/todos/{todo_id}")
def get_todo(todo_id: int):
    for todo in todos:
        if todo["id"] == todo_id:
            return todo
    return {"message": "Todo not found"}


@app.post("/todos")
def create_todo(todo: dict):
    new_todo = {
        "id": len(todos) + 1,
        "title": todo["title"]
    }
    todos.append(new_todo)
    return new_todo


@app.put("/todos/{todo_id}")
def update_todo(todo_id: int, todo: dict):
    for item in todos:
        if item["id"] == todo_id:
            item["title"] = todo["title"]
            return item
    return {"message": "Todo not found"}


@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    for index, todo in enumerate(todos):
        if todo["id"] == todo_id:
            deleted_todo = todos.pop(index)
            return deleted_todo
    return {"message": "Todo not found"}
```

---

## Step 16 — The big picture

Don't think of FastAPI as magic. Underneath, this is always what's happening:

```
Client
  | HTTP Request (e.g. GET /todos/2)
  v
FastAPI  → finds the matching route
  v
Python function  → reads/modifies data
  v
Python list  → the result
  v
FastAPI  → sends back an HTTP Response
  v
Client
```

Example trace:
```
GET /todos/2 → @app.get("/todos/{todo_id}") → get_todo(todo_id=2) → find todo with id 2 → return it
```

---

## Quick-reference glossary

| Term | Meaning |
|---|---|
| **API** | A way for applications to talk to a backend |
| **Request** | A message sent to the server |
| **Response** | The data the server sends back |
| **Route** | An address that maps a request to Python code |
| **HTTP Method** | What we want to do — GET / POST / PUT / DELETE |
| **Static route** | Fixed path, e.g. `/todos` |
| **Dynamic route** | Path with a changing part, e.g. `/todos/{todo_id}` |
| **Path parameter** | A value inside the path — identifies *which* resource |
| **Query parameter** | An optional value after `?` — filters/customizes the result |
| **Request body** | Data sent along with POST/PUT requests |
| **CRUD** | Create (POST), Read (GET), Update (PUT), Delete (DELETE) |

---

## What comes next

Don't jump straight to databases, authentication, Docker, or Kubernetes. Once this sequence feels solid, you're ready to move on:

```
Pydantic models → Error handling → Database → Authentication → Docker → Cloud deployment
```

The real goal isn't memorizing FastAPI syntax — it's understanding **what happens when a client sends an HTTP request to your backend.** Once that's clear, everything else on top of FastAPI gets much easier.