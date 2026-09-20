# FastAPI Todo API: Database → Authentication → Docker

This continues straight from where **FastAPI From Zero** left off. At that point, your API worked, but todos were stored in a plain Python list — meaning every time the server restarted, all your data disappeared.

In this guide we fix that, then add real user accounts so each person only sees their own todos, then package the whole thing so it can run anywhere.

```
Where we are:   In-memory list  (data disappears on restart)
Step A:         Real database   (Neon — a hosted Postgres database)
Step B:         User accounts   (login required, todos belong to a user)
Step C:         Docker          (the app runs the same way everywhere)
```

---

# Part A — Database (Neon + SQLModel)

## Step 1 — Why we need a database

Right now, `todos` is just a Python list living in memory:

```python
todos = [
    {"id": 1, "title": "Learn FastAPI"},
]
```

The problem: memory is **temporary**. The moment your server restarts (or crashes, or you redeploy it), that list resets back to whatever was hardcoded in the file. A real app needs the data to **persist** — to survive restarts, and to be shared safely even if multiple requests come in at once.

That's what a database is for: it stores data reliably, outside the lifetime of your running app.

---

## Step 2 — What is Neon?

**Neon** is a managed **Postgres** database that lives in the cloud — you don't install or run a database server yourself. You create a project on Neon's website, and they give you a **connection string**: a single address your app uses to talk to that database over the internet.

```
Your FastAPI app  --connection string-->  Neon (Postgres, hosted in the cloud)
```

This is different from SQLite (a single file on your own machine) — with Neon, the database exists independently of your app, which is exactly how real production apps are set up.

---

## Step 3 — Create a Neon project and get your connection string

1. Go to [neon.tech](https://neon.tech) and create a free account.
2. Create a new project (Neon will also create a default database for you).
3. From your project dashboard, copy the **connection string**. It looks like this:

```
postgresql://<user>:<password>@<host>.neon.tech/<dbname>?sslmode=require
```

Keep this somewhere safe — treat it like a password, because it *is* one.

---

## Step 4 — Store the connection string safely

Never hardcode a database password directly in your code. Instead, we use an **environment variable**.

Install `python-dotenv`:
```bash
uv add python-dotenv
```

Create a file named `.env` in your project root:
```
DATABASE_URL=postgresql://<user>:<password>@<host>.neon.tech/<dbname>?sslmode=require
```

Add `.env` to a `.gitignore` file so it's never committed to version control:
```
.env
```

We'll load this value into our app in Step 7, and we'll add one more secret here in Part B.

---

## Step 5 — Install SQLModel and the Postgres driver

**SQLModel** is a library (built by the same author as FastAPI) that lets you talk to a database using Python, instead of writing raw SQL by hand. Its big advantage for us: one class does double duty — it defines both your database table **and** your API's data shape, so you don't need to write two separate things.

To talk to Postgres specifically, we also need a driver:

```bash
uv add sqlmodel psycopg2-binary
```

---

## Step 6 — Define the Todo model

Create a new file: `app/database.py`

> [!IMPORTANT]
> **Working with folders & packages (`__init__.py`):**
> Whenever you organize your code inside folders (e.g., `app/`, or subfolders like `app/config/`), **always include an `__init__.py` file** (it can be completely empty) in every directory:
>
> ```text
> fastapi_basics/
> ├── app/
> │   ├── __init__.py         <-- Marks 'app' as a package
> │   ├── main.py
> │   ├── database.py
> │   └── config/             <-- If using nested subfolders
> │       ├── __init__.py     <-- Marks 'app.config' as a package
> │       └── db.py
> ├── .env
> └── pyproject.toml
> ```
>
> **Why is this necessary?**
> 1. **Package Recognition:** It tells Python that the directory is a package, enabling absolute imports like `from app.database import ...` or `from app.config.db import ...`.
> 2. **FastAPI CLI Project Root Detection:** When you run `uv run fastapi dev app/main.py`, FastAPI CLI inspects the directory tree for `__init__.py` to find the project root. Without it, you will see `Import error: No module named 'app'`.
> 3. **Avoids IDE Import Errors:** Prevents VS Code / Pyright from showing `Cannot find module ...` warnings.

```python
from sqlmodel import SQLModel, Field

class Todo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    completed: bool = False
```

What this says:
- `Todo(SQLModel, table=True)` — this class is a real database table, not just a plain data shape.
- `id: int | None = Field(default=None, primary_key=True)` — the primary key. It's `None` before the row is saved, and the database fills it in automatically once it's created.
- `title: str` — a required text field.
- `completed: bool = False` — defaults to `False` if not provided.

This replaces the plain dictionaries we used before — `Todo` is now a real database table *and* the shape FastAPI uses to validate incoming data.

(We'll come back and add one more field to this model in Part B, once users exist.)

---

## Step 7 — Connect to the database

Still in `app/database.py`, add:

```python
import os
from dotenv import load_dotenv
from sqlmodel import create_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
```

| Line | Meaning |
|---|---|
| `load_dotenv()` | Reads the `.env` file and makes its values available |
| `os.getenv("DATABASE_URL")` | Pulls the connection string out of the environment, instead of hardcoding it |
| `engine` | The actual connection to your Neon database |
| `pool_pre_ping=True` | Checks if the connection is alive before using it; reconnects automatically if Neon goes to sleep |
| `pool_recycle=300` | Recycles idle connections after 5 minutes to prevent stale SSL timeouts |

Notice we don't need `connect_args={"check_same_thread": False}` anymore — that was an SQLite-only quirk. Postgres doesn't need it.

---

## Step 8 — Create the table

At the bottom of `app/database.py`:

```python
def init_db():
    SQLModel.metadata.create_all(engine)
```

This tells SQLModel: *"look at every model that inherits from `SQLModel` with `table=True`, and create the matching table if it doesn't exist yet."*

We want this to run once, right when the app starts — not scattered somewhere in the middle of the file. FastAPI has a built-in way to do exactly that: **`lifespan`**.

In `main.py`:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)
```

How to read this:
- Everything **before** `yield` runs once, when the app starts up.
- `yield` hands control over to the running app — this is where your API spends most of its life, handling requests.
- Everything **after** `yield` (there's nothing here yet) would run once, when the app shuts down — useful later for things like closing connections cleanly.

This replaces calling `init_db()` loosely at the bottom of the file — now it's tied explicitly to the app's startup, which is what FastAPI expects.

---

## Step 9 — Connect the database to each request

In `main.py`, we need a way to open a database session for each request, and close it when the request is done. Add this:

```python
from sqlmodel import Session
from app.database import engine, Todo

def get_session():
    with Session(engine) as session:
        yield session
```

`yield` here means: *"give this session to the route, let it do its work, then close it automatically afterward"* — the `with` block handles the cleanup for us.

We'll plug this into our routes using `Depends()`, which you'll see next.

---

## Step 10 — Replace the list with real database queries

Now we rewrite each route to talk to the database instead of the list. Compare each one to what it used to look like.

**GET all todos:**
```python
from fastapi import Depends
from sqlmodel import Session, select

@app.get("/todos")
def get_todos(session: Session = Depends(get_session)):
    return session.exec(select(Todo)).all()
```
`Depends(get_session)` runs our `get_session` function and hands the resulting session into `session`. `select(Todo)` builds a query for *"every row in the todos table,"* and `session.exec(...).all()` runs it.

**GET one todo:**
```python
@app.get("/todos/{todo_id}")
def get_todo(todo_id: int, session: Session = Depends(get_session)):
    todo = session.get(Todo, todo_id)
    if todo:
        return todo
    return {"message": "Todo not found"}
```
`session.get(Todo, todo_id)` is a shortcut for *"look this row up directly by its primary key."*

**POST — create a todo:**
```python
@app.post("/todos")
def create_todo(todo: Todo, session: Session = Depends(get_session)):
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo
```
Notice `todo: Todo` — because our model *is* a Pydantic model too, FastAPI automatically validates the incoming request body against it. `session.add()` stages the new row, `session.commit()` actually saves it to Neon, and `session.refresh()` reloads it so we get back the auto-generated `id`.

**PUT — update a todo:**
```python
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
```

**DELETE — remove a todo:**
```python
@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int, session: Session = Depends(get_session)):
    existing = session.get(Todo, todo_id)
    if not existing:
        return {"message": "Todo not found"}
    session.delete(existing)
    session.commit()
    return existing
```

---

## Step 11 — Test it

Run your server. On startup, `lifespan` creates the `todo` table automatically — check your Neon dashboard and you'll see it appear, hosted in the cloud. Then create a few todos via `/docs`, and **stop the server and start it again.** Your todos are still there — because they now live on Neon, not in your app's memory. You can even check the Neon dashboard's table view and see the rows directly.

---

# Part B — User Authentication

Right now, every todo is visible to everyone — there's no concept of "whose todo is this." In this part, we add real user accounts: people register, log in, and only ever see *their own* todos.

## Step 12 — Why we need real user accounts

Before, anyone could read or change any todo — there was no owner. What we want instead:

```
Alice logs in  → sees only Alice's todos
Bob logs in    → sees only Bob's todos
```

To do this we need three things:
1. A **User** table — to store who's registered.
2. A **link** between each Todo and the User who owns it.
3. A way to **prove who's making each request** — so the server knows which user is currently logged in.

That third part is what "authentication" means: proving identity, then using that identity to decide what data you're allowed to see or change.

---

## Step 13 — Install the auth libraries

We need three new things:
- A way to **hash passwords** (never store real passwords in the database).
- A way to **create and check tokens** (proof that someone already logged in).
- A small dependency FastAPI needs to read login form data.

```bash
uv add "passlib[bcrypt]" "python-jose[cryptography]" python-multipart
```

| Library | What it's for |
|---|---|
| `passlib[bcrypt]` | Turns a plain password into a secure hash, and checks passwords against that hash |
| `python-jose[cryptography]` | Creates and verifies **JWT tokens** — a signed, temporary "proof of login" |
| `python-multipart` | Lets FastAPI read the login form (username + password) sent by the browser/docs page |

---

## Step 14 — Store a secret key

A JWT token is *signed* with a secret key, so the server can tell if a token is genuine or has been tampered with. Add this to your `.env` file, alongside `DATABASE_URL`:

```
SECRET_KEY=replace-this-with-a-long-random-string
```

Never share this value or commit it to version control — anyone who has it can forge valid login tokens.

---

## Step 15 — Create the User model

In `app/database.py`, add a new model:

```python
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
```

- `username: str = Field(unique=True, index=True)` — no two users can share a username, and it's indexed so lookups by username are fast.
- `hashed_password: str` — notice this is **not** called `password`. We will never store the real password — only a hashed (scrambled, one-way) version of it. More on this in Step 17.

---

## Step 16 — Connect Todos to Users (a relationship)

Right now, a `Todo` doesn't know who created it. We fix that by adding a **foreign key** — a column that points to a row in another table — plus a `Relationship`, which lets SQLModel move between the two tables easily in Python.

Update both models in `app/database.py`:

```python
from sqlmodel import SQLModel, Field, Relationship

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    todos: list["Todo"] = Relationship(back_populates="owner")


class Todo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    completed: bool = False
    user_id: int | None = Field(default=None, foreign_key="user.id")
    owner: User | None = Relationship(back_populates="todos")
```

What's new:
- `user_id: int | None = Field(default=None, foreign_key="user.id")` — this is the actual database column that stores *which* user owns this todo. It points at the `id` column of the `user` table.
- `owner: User | None = Relationship(back_populates="todos")` — this isn't a real column. It's a convenience: once you have a `Todo`, you can write `todo.owner` in Python and instantly get the full `User` object, without writing a query yourself.
- `todos: list["Todo"] = Relationship(back_populates="todos")` on `User` is the mirror image: `user.todos` gives you every todo that user owns.

```
User (1) ────owns many────> Todo (many)
```

This is called a **one-to-many relationship**: one user can have many todos, but each todo belongs to exactly one user.

---

## Step 17 — Hash passwords

We never store a password as plain text — if the database were ever exposed, every account would be compromised instantly. Instead we store a **hash**: a scrambled version that can be checked, but not reversed back into the original password.

Create `app/auth.py`:

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

- `hash_password("mypassword")` → produces something like `$2b$12$Kx9...` — impossible to turn back into `"mypassword"`.
- `verify_password("mypassword", stored_hash)` → runs the same hashing process on the input and compares the result — `True` if it matches, `False` if it doesn't.

We hash on the way in (registration) and verify on the way in again (login) — the real password is never stored anywhere.

---

## Step 18 — Create the "register" route

We need a small schema for what a registration request looks like. Not every `SQLModel` class needs `table=True` — this one is just a data shape, not a database table:

```python
class UserCreate(SQLModel):
    username: str
    password: str
```

Now the route, in `main.py`:

```python
from app.database import User
from app.auth import hash_password

@app.post("/register")
def register(user_data: UserCreate, session: Session = Depends(get_session)):
    existing = session.exec(
        select(User).where(User.username == user_data.username)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"id": user.id, "username": user.username}
```

Notice the response only ever returns `id` and `username` — never `hashed_password`. Don't leak it back to the client, even hashed.

---

## Step 19 — Create JWT helper functions

A **JWT (JSON Web Token)** is a signed piece of text the server hands out after a successful login. The client stores it and sends it back with every future request as proof: *"I already logged in, here's my token."*

Add this to `app/auth.py`:

```python
import os
from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

- `data` is whatever we want to remember inside the token — typically just the username.
- `"exp"` gives the token an expiry time. After 60 minutes, it stops being valid, and the user must log in again.
- `jwt.encode(...)` signs the token with `SECRET_KEY`. Anyone can *read* a JWT's contents, but only someone with the secret key can create a *valid* one — that's what stops forged tokens.

---

## Step 20 — Create the "login" route

In `main.py`:

```python
from fastapi.security import OAuth2PasswordRequestForm
from app.auth import verify_password, create_access_token

@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    user = session.exec(
        select(User).where(User.username == form_data.username)
    ).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}
```

- `OAuth2PasswordRequestForm` is a built-in FastAPI shape that reads `username` and `password` from a login form — this is also what makes the "Authorize" button in `/docs` work automatically.
- If the username doesn't exist, or the password doesn't match the stored hash, we reject with `401 Unauthorized`.
- `{"sub": user.username}` — `sub` (short for "subject") is the standard JWT field for "who is this token about."
- The response shape (`access_token` + `token_type`) is also a convention every OAuth2 client expects.

---

## Step 21 — Verify tokens automatically (get the current user)

Every protected route needs to answer: *"which user sent this request?"* We write one dependency that does this once, and reuse it everywhere:

```python
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.auth import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    credentials_exception = HTTPException(
        status_code=401, detail="Could not validate credentials"
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = session.exec(select(User).where(User.username == username)).first()
    if user is None:
        raise credentials_exception
    return user
```

- `OAuth2PasswordBearer(tokenUrl="login")` tells FastAPI *"clients get their token from `/login`, and should send it back as `Authorization: Bearer <token>` on every request."*
- `jwt.decode(...)` checks the token's signature (rejecting forged or tampered tokens) and reads out the data we stored — here, the username.
- If anything is wrong — bad signature, expired token, unknown username — we reject with `401`.
- If everything checks out, we return the actual `User` row from the database, ready to use in a route.

---

## Step 22 — Protect the todo routes and scope data to the logged-in user

Now we plug `get_current_user` into every todo route, and use `current_user.id` to keep each person's data separate.

**GET all todos — only the logged-in user's own:**
```python
@app.get("/todos")
def get_todos(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return session.exec(
        select(Todo).where(Todo.user_id == current_user.id)
    ).all()
```

**GET one todo — only if it belongs to this user:**
```python
@app.get("/todos/{todo_id}")
def get_todo(
    todo_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    todo = session.get(Todo, todo_id)
    if not todo or todo.user_id != current_user.id:
        return {"message": "Todo not found"}
    return todo
```

**POST — create a todo, automatically owned by the logged-in user:**
```python
@app.post("/todos")
def create_todo(
    todo: Todo,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    todo.user_id = current_user.id
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo
```
Notice the client never sends `user_id` themselves — we set it from the logged-in user's token. Never trust the client to say who they are; the token already told us.

**PUT and DELETE follow the same pattern** — look the todo up, check `todo.user_id == current_user.id`, and only then allow the change:
```python
@app.put("/todos/{todo_id}")
def update_todo(
    todo_id: int,
    updated: Todo,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    existing = session.get(Todo, todo_id)
    if not existing or existing.user_id != current_user.id:
        return {"message": "Todo not found"}
    existing.title = updated.title
    existing.completed = updated.completed
    session.commit()
    session.refresh(existing)
    return existing


@app.delete("/todos/{todo_id}")
def delete_todo(
    todo_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    existing = session.get(Todo, todo_id)
    if not existing or existing.user_id != current_user.id:
        return {"message": "Todo not found"}
    session.delete(existing)
    session.commit()
    return existing
```

---

## Step 23 — Test the full flow

1. `POST /register` with a username and password → creates a user.
2. `POST /login` with the same credentials → returns an `access_token`.
3. In `/docs`, click **Authorize** and paste in the token (or the username/password, if using the form-based Authorize button) → all requests now include it automatically.
4. `POST /todos` → the new todo is owned by you.
5. `GET /todos` → you only see your own todos.
6. Register a second user, log in as them, and confirm they see an empty list — not the first user's todos.

---

# Part C — Docker

## Step 24 — Why we containerize

Your app currently depends on things installed on *your* machine: Python, `uv`, the right versions of every package. If you send your project to someone else, or deploy it to a server, none of that is guaranteed to be there.

**Docker** solves this by packaging your app together with everything it needs to run — Python, dependencies, your code — into one unit called a **container**, which behaves exactly the same on any machine.

```
Without Docker: "It works on my machine" (but maybe not yours)
With Docker:    It works the same, everywhere
```

Your database doesn't need to be containerized here — Neon is already hosted separately in the cloud. Your container just needs `DATABASE_URL` and `SECRET_KEY` to know where to find it and how to sign tokens.

---

## Step 25 — Export your dependencies

Docker needs a plain list of your dependencies to install inside the container. Generate one from `uv`:

```bash
uv export --format requirements-txt > requirements.txt
```

This creates `requirements.txt`, listing `fastapi`, `sqlmodel`, `psycopg2-binary`, `python-dotenv`, `passlib[bcrypt]`, `python-jose[cryptography]`, `python-multipart`, and anything else you've added.

---

## Step 26 — Write the Dockerfile

A **Dockerfile** is a recipe: step-by-step instructions for building your container. Create a file named `Dockerfile` (no extension) in your project root:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
```

Line by line:

| Instruction | Meaning |
|---|---|
| `FROM python:3.12-slim` | Start from a minimal image that already has Python installed |
| `WORKDIR /app` | Every following command runs inside `/app` in the container |
| `COPY requirements.txt .` | Copy just this file in first (so Docker can cache the install step) |
| `RUN pip install ...` | Install your dependencies inside the container |
| `COPY . .` | Copy the rest of your project files in |
| `EXPOSE 8000` | Document that this container listens on port 8000 |
| `CMD [...]` | The command that runs when the container starts |

Note: your `.env` file should **not** be copied into the image (keep it out via `.dockerignore`). We'll pass both secrets in at runtime instead — see Step 28.

---

## Step 27 — Build the image

An **image** is the packaged result of your Dockerfile — a snapshot you can run anywhere.

```bash
docker build -t todo-api .
```

- `-t todo-api` names the image `todo-api`.
- `.` tells Docker to look for the Dockerfile in the current directory.

---

## Step 28 — Run the container

Since your database now lives on Neon and your secret key lives in `.env`, pass both in at runtime with `--env-file`:

```bash
docker run --env-file .env -p 8000:8000 todo-api
```

- `--env-file .env` loads `DATABASE_URL` and `SECRET_KEY` into the container's environment.
- `-p 8000:8000` connects port 8000 on your machine to port 8000 inside the container.

Visit `http://127.0.0.1:8000/docs` — it's the same API, now running fully inside a container, isolated from anything installed on your own machine, and still talking to the same Neon database.

---

## Recap: the full journey so far

```
In-memory list
   ↓  (Part A)
Neon (Postgres) + SQLModel — data survives restarts, hosted in the cloud
   ↓  (Part B)
Real user accounts — register, log in, JWT tokens, todos scoped per user
   ↓  (Part C)
Docker container — runs identically on any machine
   ↓  (next in your course)
Cloud deployment with Terraform
```

## Quick-reference glossary

| Term | Meaning |
|---|---|
| **Neon** | A managed, cloud-hosted Postgres database — no server to install yourself |
| **Connection string** | The address + credentials your app uses to reach the database |
| **Environment variable** | A value (like a password) kept outside your code, loaded at runtime |
| **`.env` file** | A local file holding environment variables, kept out of version control |
| **ORM** | A library (like SQLModel) that lets you use Python objects instead of raw SQL |
| **Model** | A Python class that represents both a database table and, with SQLModel, the API's data shape |
| **Session** | A temporary connection used to run database operations for one request |
| **`select()`** | Builds a database query — e.g. "select every row from this table" |
| **`Depends()`** | FastAPI's way of injecting something (a DB session, an auth check) into a route |
| **`lifespan`** | A function that runs setup code before the app starts, and cleanup code after it shuts down |
| **Foreign key** | A column that points to a row in another table (e.g. `Todo.user_id` points to `User.id`) |
| **Relationship** | A SQLModel convenience for navigating between related tables in Python (e.g. `user.todos`) |
| **Hashing** | Turning a password into a one-way scrambled value that can be checked but not reversed |
| **JWT** | A signed token proving a user already logged in, sent with each request afterward |
| **`sub`** | The standard JWT field identifying who the token belongs to |
| **401 Unauthorized** | Status code meaning "you didn't prove who you are" |
| **Image** | A packaged snapshot of your app + everything it needs to run |
| **Container** | A running instance of an image |
| **`__init__.py`** | An initialization file placed inside a folder to mark it as a Python package so imports and tools like `fastapi-cli` work smoothly |