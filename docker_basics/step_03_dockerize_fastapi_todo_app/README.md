# Step 3: Dockerize FastAPI & Connect to Neon DB (Cloud PostgreSQL)

A comprehensive guide on containerizing a **FastAPI Todo application** using **`uv`** and connecting it to an external cloud database (**Neon PostgreSQL**), with secure environment variable management and Docker port mapping.

---

## 🎯 What You Will Learn

1. **Building a Python Web API Docker Image** using `uv`.
2. **Connecting to a Cloud Database (Neon DB)** from inside a Docker container.
3. **Handling Secrets Safely**: Why database credentials must **never** be hardcoded in a `Dockerfile`, and how to inject them securely at runtime using `.env` and `--env-file`.
4. **Port Mapping (`-p`)**: Why `EXPOSE 8000` is not enough and how to map host ports to container ports.
5. **Networking Concepts**: Why FastAPI listens on `0.0.0.0:8000` inside the container while your browser navigates to `http://localhost:8000`.

---

## 🏗️ Architecture

```text
Your Computer (Host)                             Cloud (Neon)
┌───────────────────────────────┐               ┌───────────────────────┐
│ Browser (http://localhost:8000)│               │                       │
│              │                │               │                       │
│       Port Mapping            │   Internet    │   Neon PostgreSQL     │
│        (-p 8000:8000)         │ (DATABASE_URL)│       Database        │
│              ▼                │──────────────►│                       │
│    ┌───────────────────┐      │               │                       │
│    │ Docker Container  │      │               │                       │
│    │ FastAPI App (uv)  │      │               │                       │
│    │ Listening :8000   │      │               │                       │
│    └───────────────────┘      │               │                       │
└───────────────────────────────┘               └───────────────────────┘
```

---

## 🚀 Project Structure

```text
step_03_dockerize_fastapi_todo_app/
├── .dockerignore        # Prevents host .venv, .env, and caches from entering the image
├── .env                 # Local database credentials (ignored by git, never in image)
├── .env.example         # Template for environment variables (committed to git)
├── Dockerfile           # Docker build configuration
├── pyproject.toml       # Project metadata and dependencies (fastapi, sqlmodel, psycopg2, etc.)
├── uv.lock              # Pinned lockfile for deterministic builds
├── README.md            # This guide
└── app/
    ├── __init__.py
    ├── main.py          # FastAPI application entrypoint & API routes
    └── config/
        ├── __init__.py
        └── db.py        # Database engine setup (reads DATABASE_URL)
```

---

## 🔐 The Environment Variable Problem: Handling Secrets

In our application, `app/config/db.py` reads `DATABASE_URL` to connect to Neon PostgreSQL:

```python
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
```

If `DATABASE_URL` is missing, the application crashes with:
```text
ArgumentError: Expected string or URL object, got None
```

### ❌ Why You Should NEVER Put Secrets in a `Dockerfile`

You might be tempted to write:
```dockerfile
# ⚠️ DANGEROUS - DO NOT DO THIS!
ENV DATABASE_URL="postgresql://neondb_owner:password@ep-sample.neon.tech/neondb?sslmode=require"
```

**Why this is a major security flaw:**
1. **GitHub Leaks**: If you push the `Dockerfile` to GitHub, your private database credentials and passwords are leaked to the public.
2. **Baked Into Image Layers**: Any person or machine pulling the Docker image can run `docker history` or `docker inspect` and extract your credentials in plain text.
3. **Breaks "Build Once, Run Anywhere"**: A Docker image should be environment-agnostic. If credentials are baked in, you must rebuild the entire image whenever your database URL or password changes.

---

### ✅ The 2 Safe Ways to Supply Environment Variables at Runtime

Instead of baking credentials into the image, inject them dynamically when starting the container:

#### Method 1: Using `--env-file` (Recommended for Local Development)
Pass your local `.env` file directly to the container:

```bash
docker run --name fastapi-todo-app -p 8000:8000 --env-file .env --rm fastapi-todo-image
```
* Docker reads the `.env` file on your host machine and injects its variables into the container environment.
* The `.env` file remains on your computer and is **never** copied into the image.

#### Method 2: Using `-e` or `--env` (Inline Variables)
Pass individual environment variables directly on the command line:

```bash
docker run --name fastapi-todo-app -p 8000:8000 -e DATABASE_URL="postgresql://..." --rm fastapi-todo-image
```
* Useful in CI/CD pipelines, cloud deployment services (AWS ECS, Google Cloud Run, Render), or to temporarily override a value.

---

## 🌐 The Port Mapping Problem (`-p`)

### Why doesn't `EXPOSE 8000` make the app accessible?

In the `Dockerfile`, we have:
```dockerfile
EXPOSE 8000
```
> [!IMPORTANT]
> `EXPOSE 8000` is **only documentation/metadata**! It communicates to developers and tools that the application inside listens on port 8000. It **does NOT publish or forward the port to your host machine**.

Containers run inside an **isolated virtual network bridge**. Without port mapping, container port 8000 is completely trapped inside the container's private network.

### The Solution: Map the Ports with `-p`

To connect your host machine's port to the container's port, use `-p <host_port>:<container_port>`:

```bash
-p 8000:8000
```

```text
Your Computer (Host)                      Docker Container
┌─────────────────────┐                 ┌─────────────────────┐
│  Browser / Postman  │                 │     FastAPI App     │
│  http://localhost   │                 │     Listening on    │
│      :8000 ─────────┼────────────────►│        :8000        │
└─────────────────────┘   Port Mapping  └─────────────────────┘
                          (-p 8000:8000)
```

If you omit `-p 8000:8000`, the container runs successfully, but opening `http://localhost:8000` in your browser will result in `This site can't be reached` / Connection Refused.

---

## ❓ Why `http://localhost:8000` and NOT `http://0.0.0.0:8000`?

When the container starts, the logs say:
```text
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Opening `http://0.0.0.0:8000` in your browser fails. But `http://localhost:8000` works. Why?

### 1. `0.0.0.0` is a "Listening" Address (Server-Side)
Inside the container, `0.0.0.0` is a meta-address that tells FastAPI / Uvicorn:
> *"Listen for incoming network traffic on **all** network interfaces (Ethernet, Docker virtual bridge, loopback)."*

If FastAPI listened only on `127.0.0.1` inside the container, Docker's network bridge wouldn't be able to forward outside traffic into it.

### 2. `localhost` / `127.0.0.1` is a "Destination" Address (Client-Side)
For your web browser:
* `127.0.0.1` (or hostname `localhost`) is the loopback destination on your host machine.
* Your operating system directs the request to port `8000`, Docker intercepts it through the `-p 8000:8000` forwarder, and hands it to FastAPI inside the container.

---

## 📦 Step-by-Step Instructions

### Step 1: Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in your actual Neon PostgreSQL connection string:
   ```env
   DATABASE_URL=postgresql://neondb_owner:your_password@ep-sample-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

### Step 2: Build the Docker Image

From the `step_03_dockerize_fastapi_todo_app` directory:

```bash
docker build -t fastapi-todo-image .
```

### Step 3: Run the Container

Run the container with port forwarding and your `.env` file:

```bash
docker run --name fastapi-todo-app -p 8000:8000 --env-file .env --rm fastapi-todo-image
```

### Step 4: Verify in Your Browser

Open your browser and navigate to:
* **Interactive API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Alternative API Docs (ReDoc)**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

Test the endpoints:
1. `POST /todos` — Add a new todo (e.g. `{"title": "Learn Docker basics", "completed": false}`).
2. `GET /todos` — Verify the todo is retrieved from Neon DB!

### Step 5: Stop the Container

In your terminal, press:
```text
Ctrl + C
```
Because of the `--rm` flag, the container stops and is automatically removed.

---

## 🧹 Quick Command Summary

| Task | Command |
| :--- | :--- |
| **Build image** | `docker build -t fastapi-todo-image .` |
| **Run container with `.env`** | `docker run --name fastapi-todo-app -p 8000:8000 --env-file .env --rm fastapi-todo-image` |
| **Run container with inline env** | `docker run --name fastapi-todo-app -p 8000:8000 -e DATABASE_URL="..." --rm fastapi-todo-image` |
| **List running containers** | `docker ps` |
| **Stop container** | `docker stop fastapi-todo-app` |
