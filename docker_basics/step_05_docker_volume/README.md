# Step 5: Docker Volumes — Persisting PostgreSQL Data

In Step 4, we connected our containerized FastAPI app with our containerized PostgreSQL database using Docker networking. However, there is a critical problem: **by default, any data written inside a Docker container is completely lost when that container is removed.**

This guide demonstrates that problem firsthand and shows how to permanently persist database data using **Docker Named Volumes**.

---

## 🎯 What You Will Learn

1. **Container Ephemerality**: Why container filesystems are temporary and disposable.
2. **The Data Loss Problem**: Experiencing what happens to database records when a container is recreated without a volume.
3. **Docker Named Volumes**: How Docker manages persistent storage independently of container lifecycles.
4. **Mounting Volumes (`-v`)**: How to map `/var/lib/postgresql/data` to a named volume so your todos survive restarts and deletions.

---

## 🏗️ Architecture: How Storage & Networking Work Together

```text
                      todo-net (User-Defined Network)
FastAPI Container  ─────────────────────────────────────►  PostgreSQL Container
(fastapi-todo-app)        DATABASE_URL=...@pg-todo:5432    (pg-todo)
                                                                 │
                                                        writes data files to
                                                                 ▼
                                                     /var/lib/postgresql/data
                                                                 │
                                                    ┌────────────┴─────────────┐
                                                    │                          │
                                             WITHOUT a volume:          WITH a volume:
                                         Lives inside container     Lives in "pgdata" volume
                                         → DELETED with container   → PERSISTS across containers!
```

---

## 🚀 Project Structure

```text
step_05_docker_volume/
├── .dockerignore        # Excludes virtual environments and local caches
├── .env                 # Database URL pointing to pg-todo
├── .env.example         # Template for environment variables
├── Dockerfile           # Docker build configuration
├── pyproject.toml       # Dependencies and project metadata
├── uv.lock              # Pinned lockfile
├── README.md            # This guide
└── app/
    ├── __init__.py
    ├── main.py          # FastAPI application entrypoint & API routes
    └── config/
        ├── __init__.py
        └── db.py        # Database engine setup (reads DATABASE_URL)
```

---

## 💥 The Problem: What Happens WITHOUT a Volume?

Let's see the issue in action before fixing it.

### 1. Create the network and start Postgres without a volume
```bash
docker network create todo-net

docker run -d \
  --name pg-todo \
  --network todo-net \
  -e POSTGRES_PASSWORD=secret \
  postgres:16
```

### 2. Build and start the FastAPI app
```bash
docker build -t fastapi-todo-image .

docker run -d \
  --name fastapi-todo-app \
  --network todo-net \
  -p 8000:8000 \
  --env-file .env \
  fastapi-todo-image
```

### 3. Add data
Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser:
* Use `POST /todos` to create 2-3 todos (e.g. *"Buy groceries"*, *"Study Docker"*).
* Call `GET /todos` to verify they exist in the database.

### 4. Recreate the Postgres container
Imagine your Postgres container crashed or you need to update it:
```bash
docker rm -f pg-todo

# Start a fresh Postgres container
docker run -d \
  --name pg-todo \
  --network todo-net \
  -e POSTGRES_PASSWORD=secret \
  postgres:16
```

### 5. Check `/docs` again
Go back to [http://localhost:8000/docs](http://localhost:8000/docs) and call `GET /todos`.

> ❌ **Your todos are gone!** You receive an empty list `[]`.
> 
> Because PostgreSQL stored its files inside the old container's ephemeral filesystem, deleting the container erased the entire database.

---

## 🛡️ The Fix: Docker Named Volumes

A **Docker Volume** is dedicated storage created and managed by Docker on the host system, completely separate from any individual container's lifecycle.

### How `-v` Works

```text
-v pgdata:/var/lib/postgresql/data
      ↑                 ↑
 Volume Name     Path inside container
```
Whatever PostgreSQL writes to `/var/lib/postgresql/data` (its default internal storage directory) is saved inside the `pgdata` volume on the host.

---

## 📦 Step-by-Step Instructions: Persisting Data

### Step 1: Clean Up Old Containers
Remove the ephemeral Postgres and FastAPI containers:
```bash
docker rm -f pg-todo fastapi-todo-app
```

### Step 2: Create a Docker Named Volume
Create a dedicated named volume for your database:
```bash
docker volume create pgdata
```

Verify that the volume was created:
```bash
docker volume ls
```

### Step 3: Run PostgreSQL WITH the Volume Mounted
Start PostgreSQL, mounting `pgdata` to `/var/lib/postgresql/data`:

```bash
docker run -d \
  --name pg-todo \
  --network todo-net \
  -v pgdata:/var/lib/postgresql/data \
  -e POSTGRES_PASSWORD=secret \
  postgres:16
```

### Step 4: Run the FastAPI Container
Start your FastAPI container on the same network:

```bash
docker run -d \
  --name fastapi-todo-app \
  --network todo-net \
  -p 8000:8000 \
  --env-file .env \
  fastapi-todo-image
```

### Step 5: Add Todos via Swagger UI
Open [http://localhost:8000/docs](http://localhost:8000/docs) and use `POST /todos` to add tasks:
- `"Learn Docker volumes"`
- `"Persist PostgreSQL database"`

Call `GET /todos` to confirm they are saved.

### Step 6: Test Persistence (Destroy & Recreate Container)
Now, delete the running Postgres container completely:
```bash
docker rm -f pg-todo
```

Start a brand new Postgres container with the exact same volume attached:
```bash
docker run -d \
  --name pg-todo \
  --network todo-net \
  -v pgdata:/var/lib/postgresql/data \
  -e POSTGRES_PASSWORD=secret \
  postgres:16
```

Go back to [http://localhost:8000/docs](http://localhost:8000/docs) and call `GET /todos`.

> ✅ **Your todos are still there!**
> 
> Even though the Postgres container was destroyed and replaced with a new one, all database files remained safe and intact inside the `pgdata` volume.

---

## 🧩 The Three Pillars of Multi-Container Docker

Students should understand the role of each component:

1. **Port Mapping (`-p 8000:8000`)**: Exposes the FastAPI application to your browser.
2. **Docker Network (`--network todo-net`)**: Enables DNS resolution so FastAPI reaches PostgreSQL using `pg-todo`.
3. **Docker Volume (`-v pgdata:...`)**: Ensures data survives container destruction and recreation.

---

## 🧹 Volume Management & Clean Up

### Inspecting Volumes
Inspect where Docker stores the volume on your system:
```bash
docker volume inspect pgdata
```

### Clean Up Containers & Volume
When you are completely finished:
```bash
# Stop and remove containers
docker rm -f fastapi-todo-app pg-todo

# Remove network
docker network rm todo-net

# Remove volume (WARNING: this deletes all persisted database data!)
docker volume rm pgdata
```

---

## 📋 Quick Command Summary

| Task | Command |
| :--- | :--- |
| **Create volume** | `docker volume create pgdata` |
| **List volumes** | `docker volume ls` |
| **Inspect volume details** | `docker volume inspect pgdata` |
| **Run Postgres with volume** | `docker run -d --name pg-todo --network todo-net -v pgdata:/var/lib/postgresql/data -e POSTGRES_PASSWORD=secret postgres:16` |
| **Remove volume** | `docker volume rm pgdata` |
| **Prune all unused volumes** | `docker volume prune` |
