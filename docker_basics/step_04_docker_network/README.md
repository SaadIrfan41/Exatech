# Step 4: Docker Network — Connecting FastAPI & PostgreSQL Containers

In Step 3, our containerized FastAPI app connected to an external cloud database (Neon DB). In this step, we take the next step: **running PostgreSQL inside its own Docker container and connecting our FastAPI container to it**.

---

## 🎯 What You Will Learn

1. **The `localhost` Trap**: Why one container cannot reach another container using `localhost`.
2. **The Fragility of Container IPs**: Why relying on Docker's default bridge IP addresses fails.
3. **User-Defined Bridge Networks**: How custom Docker networks provide **automatic DNS service discovery** using container names.
4. **Host vs Container Traffic (`-p`)**: Why PostgreSQL does NOT need `-p 5432:5432` when communicating with another container on the same network.

---

## 🏗️ Architecture

```text
Your Computer (Host)
┌────────────────────────────────────────────────────────────────────────┐
│ Browser (http://localhost:8000)                                        │
│          │                                                             │
│   Port Mapping (-p 8000:8000)                                          │
│          ▼                                                             │
│   ┌──────────────────────────────────────────────────────────────┐     │
│   │ Docker User-Defined Network: todo-net                        │     │
│   │                                                              │     │
│   │  ┌───────────────────────┐        ┌───────────────────────┐  │     │
│   │  │ Container:            │        │ Container:            │  │     │
│   │  │ fastapi-todo-app      │        │ pg-todo               │  │     │
│   │  │                       │        │                       │  │     │
│   │  │ DATABASE_URL=         │───────►│ Port 5432             │  │     │
│   │  │ ...@pg-todo:5432...   │  DNS   │ (PostgreSQL database) │  │     │
│   │  └───────────────────────┘        └───────────────────────┘  │     │
│   │                                                              │     │
│   └──────────────────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Project Structure

```text
step_04_docker_network/
├── .dockerignore        # Prevents local caches, envs, and venvs from entering the image
├── .env                 # Local container database URL (DATABASE_URL=...@pg-todo:5432/...)
├── .env.example         # Template for environment variables (committed to git)
├── Dockerfile           # Docker build configuration
├── pyproject.toml       # Project metadata and dependencies
├── uv.lock              # Deterministic lockfile
├── README.md            # This guide
└── app/
    ├── __init__.py
    ├── main.py          # FastAPI application entrypoint & API routes
    └── config/
        ├── __init__.py
        └── db.py        # Database engine setup (reads DATABASE_URL)
```

---

## ❌ Challenge 1: The `localhost` Fallacy

When running PostgreSQL locally on your host machine, you used:
```text
DATABASE_URL=postgresql://postgres:secret@localhost:5432/postgres
```

However, once **FastAPI is running inside a Docker container**, using `localhost` causes:
```text
connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused
```

### Why does this happen?
* **`localhost` means "this current environment"**, not your entire computer.
* Each Docker container has its own private **network namespace** and its own loopback address (`127.0.0.1`).
* Inside the `fastapi-todo-app` container, `localhost:5432` refers to port 5432 of the **FastAPI container itself**, where nothing is listening on 5432!

```text
┌───────────────────────────┐         ┌───────────────────────────┐
│ FastAPI Container         │         │ Postgres Container        │
│                           │         │                           │
│ localhost:5432            │   ❌    │                           │
│ points to THIS container! │───/───► │ Postgres listens here     │
└───────────────────────────┘         └───────────────────────────┘
```

---

## ❌ Challenge 2: Why Default Bridge IP Addresses Are Fragile

Every container started without `--network` gets attached to Docker's default **bridge** network and receives an internal IP address (e.g. `172.17.0.2`):

```bash
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' pg-todo
# Output: 172.17.0.2
```

You *could* set:
```text
DATABASE_URL=postgresql://postgres:secret@172.17.0.2:5432/postgres
```

### Why this is a terrible idea in practice:
1. **IP addresses are dynamic**: When a container is stopped, removed, and recreated, Docker assigns it whatever IP is next in the pool (e.g. `172.17.0.3` or `172.17.0.4`).
2. **Hardcoded IPs break constantly**: As soon as the IP changes, your FastAPI app cannot connect until you manually inspect the container and update your `.env` file.
3. **No automatic DNS**: The default Docker bridge does **NOT** provide DNS name resolution. Containers on the default bridge cannot reach each other by name.

---

## ✅ The Solution: User-Defined Bridge Network & Docker DNS

When you create a **user-defined bridge network**, Docker provides an **embedded DNS server** (`127.0.0.11` inside containers).

On a user-defined network:
- Containers can reach each other simply using their **container names** as hostnames!
- Docker automatically translates `pg-todo` into the current IP address of the Postgres container, even if that IP changes.

```text
FastAPI Container
      │
      │ 1. "Where is pg-todo?"
      ▼
Docker Embedded DNS (127.0.0.11)
      │
      │ 2. Resolves to current IP of pg-todo
      ▼
Postgres Container
```

Therefore, our connection URL in `.env` becomes completely stable:
```text
DATABASE_URL=postgresql://postgres:secret@pg-todo:5432/postgres
```

---

## 💡 Port Mapping (`-p`) vs Container-to-Container Traffic

A common point of confusion is whether PostgreSQL needs `-p 5432:5432`:

| Traffic Flow | Needs `-p`? | Reason |
| :--- | :--- | :--- |
| **Host Browser ➔ FastAPI** | **Yes** (`-p 8000:8000`) | Outside traffic crossing the boundary from host into Docker. |
| **FastAPI ➔ PostgreSQL** | **No** (no `-p` needed) | Both containers share the same internal Docker network (`todo-net`). |

> [!TIP]
> You only need `-p 5432:5432` on PostgreSQL if you want tools on your host machine (like pgAdmin or DBeaver) to connect directly to the database.

---

## 📦 Step-by-Step Instructions

### Step 1: Create a User-Defined Network

Create a custom bridge network called `todo-net`:

```bash
docker network create todo-net
```

Verify that the network exists:
```bash
docker network ls
```

### Step 2: Start the PostgreSQL Container

Run the official PostgreSQL container on `todo-net`:

```bash
docker run -d \
  --name pg-todo \
  --network todo-net \
  -e POSTGRES_PASSWORD=secret \
  postgres:16
```

### Step 3: Configure `.env`

Confirm your `.env` file uses the container name `pg-todo`:

```env
DATABASE_URL=postgresql://postgres:secret@pg-todo:5432/postgres
```

### Step 4: Build the FastAPI Docker Image

From `step_04_docker_network/`:

```bash
docker build -t fastapi-todo-image .
```

### Step 5: Start the FastAPI Container on the Same Network

Run the FastAPI container attached to `todo-net` with port mapping `8000:8000`:

```bash
docker run -d \
  --name fastapi-todo-app \
  --network todo-net \
  -p 8000:8000 \
  --env-file .env \
  fastapi-todo-image
```

### Step 6: Test in Your Browser

Open your browser and navigate to:
* [http://localhost:8000/docs](http://localhost:8000/docs)

1. Use `POST /todos` to create a new task (e.g. `{"title": "Test Docker networking", "completed": false}`).
2. Use `GET /todos` to verify the item is saved and retrieved from the `pg-todo` container!

### Step 7: Clean Up

When you are done testing, stop and remove the containers and the custom network:

```bash
docker rm -f fastapi-todo-app pg-todo
docker network rm todo-net
```

---

## 🧹 Quick Command Summary

| Task | Command |
| :--- | :--- |
| **Create network** | `docker network create todo-net` |
| **Run Postgres on network** | `docker run -d --name pg-todo --network todo-net -e POSTGRES_PASSWORD=secret postgres:16` |
| **Build FastAPI image** | `docker build -t fastapi-todo-image .` |
| **Run FastAPI on network** | `docker run -d --name fastapi-todo-app --network todo-net -p 8000:8000 --env-file .env fastapi-todo-image` |
| **Inspect network containers** | `docker network inspect todo-net` |
| **View app logs** | `docker logs fastapi-todo-app` |
| **Remove containers & network**| `docker rm -f fastapi-todo-app pg-todo && docker network rm todo-net` |
