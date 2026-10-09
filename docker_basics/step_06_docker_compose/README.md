# Step 6: Docker Compose — Multi-Container Orchestration

In Steps 4 and 5, you ran the FastAPI Todo API and PostgreSQL together manually. That required:
- Manually creating a network (`docker network create todo-net`)
- Manually creating a volume (`docker volume create pgdata`)
- Starting PostgreSQL with numerous CLI flags
- Building the FastAPI image
- Starting the FastAPI container with numerous CLI flags
- Manually cleaning up everything in reverse order

In this step, we combine **networking, volumes, environment variables, and multi-container orchestration** into a single file: `docker-compose.yml`.

---

## 🎯 What You Will Learn

1. **The Problem with Manual Multi-Container Workflows**: Why running containers by hand does not scale.
2. **What Docker Compose Is**: Defining and running multi-container Docker applications with declarative YAML.
3. **Anatomy of `docker-compose.yml`**: Breaking down `services`, `build`, `image`, `ports`, `environment`, `env_file`, `volumes`, and `depends_on`.
4. **Automatic Networking**: How Docker Compose creates a private network automatically and sets service names (like `db`) as DNS hostnames.
5. **Managing Application Lifecycles**: How to start, monitor, and stop the entire application with single commands (`docker compose up` / `docker compose down`).

---

## 🏗️ Architecture

```text
Host Machine
┌────────────────────────────────────────────────────────────────────────┐
│ Browser (http://localhost:8000)                                        │
│         │                                                              │
│         ▼                                                              │
│ Docker Compose Managed Network                                         │
│ ┌───────────────────────────┐         ┌──────────────────────────────┐ │
│ │ Service: api (FastAPI)    │         │ Service: db (Postgres)       │ │
│ │                           │         │                              │ │
│ │ Port: 8000 (mapped)       │         │ Internal Port: 5432          │ │
│ │ DATABASE_URL=             │────────►│                              │ │
│ │ ...@db:5432/postgres      │   DNS   │ Writes data to:              │ │
│ └───────────────────────────┘         └──────────────┬───────────────┘ │
│                                                      ▼                 │
│                                           Volume: pgdata               │
│                                           (Persisted on Host)          │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Project Structure

```text
step_06_docker_compose/
├── .dockerignore        # Excludes virtual environments and local caches
├── .env                 # Database credentials (DATABASE_URL=...@db:5432/...)
├── .env.example         # Template for environment variables (committed to git)
├── docker-compose.yml   # Multi-container Compose definition
├── Dockerfile           # Docker build configuration for the FastAPI service
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

## 📄 Anatomy of `docker-compose.yml`

Here is our complete `docker-compose.yml`:

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: secret
    volumes:
      - pgdata:/var/lib/postgresql/data

  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db

volumes:
  pgdata:
```

### Breaking It Down Piece by Piece:

### 1. `services:`
Defines the containers to run. We have two services:
- `db`: The PostgreSQL database container.
- `api`: Our FastAPI application container.

These service names (`db` and `api`) double as **network hostnames**.

### 2. `image:` vs `build:`
- `image: postgres:16` tells Compose to pull the official PostgreSQL 16 image from Docker Hub.
- `build: .` tells Compose to build our custom image from the local `Dockerfile` in this directory.

### 3. `ports:`
Maps host port 8000 to container port 8000 (`"host:container"`), making the FastAPI app reachable from your browser at `http://localhost:8000`. Notice that `db` does not expose any host ports, keeping it secure and private inside the internal Docker network.

### 4. `environment:` vs `env_file:`
- `environment:` sets environment variables directly in the YAML file (e.g., `POSTGRES_PASSWORD: secret`).
- `env_file:` loads variables from our local `.env` file (e.g., `DATABASE_URL`). This keeps secrets out of the compose file.

### 5. `volumes:`
- Declared at the top level at the bottom of the file (`volumes: pgdata:`): Tells Docker to manage a named volume called `pgdata`.
- Mounted under the `db` service (`- pgdata:/var/lib/postgresql/data`): Mounts that volume to Postgres's data directory for persistent storage.

### 6. `depends_on:`
Tells Compose to start the `db` service before starting the `api` service.

### 7. Automatic Networking
Docker Compose **automatically creates a user-defined bridge network** for all services in the file. 

Because of this:
- No manual `docker network create` is needed.
- The `api` container can connect to PostgreSQL using `db` as the hostname:
  ```env
  DATABASE_URL=postgresql://postgres:secret@db:5432/postgres
  ```

---

## 📦 Step-by-Step Instructions

### Step 1: Configure Environment Variables

Verify that `.env` is present and points to the `db` service:

```bash
# Copy example if .env does not exist
cp .env.example .env
```

Your `.env` should contain:
```env
DATABASE_URL=postgresql://postgres:secret@db:5432/postgres
```

### Step 2: Start All Services

Run one single command to build the image (if not already built), create the network, create the volume, and start both containers in the background:

```bash
docker compose up --build -d
```

### Step 3: Check Status of Services

View the running containers managed by Compose:

```bash
docker compose ps
```

You should see both the `db` and `api` services in the `Up` state.

### Step 4: Follow Container Logs

To view streaming logs from both containers:

```bash
docker compose logs -f
```

To see logs for just the API service:
```bash
docker compose logs -f api
```

*(Press `Ctrl + C` to stop following logs).*

### Step 5: Test the Todo API in Your Browser

Open your browser and navigate to:
* **Interactive Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

1. Use `POST /todos` to add a new task (e.g. `{"title": "Master Docker Compose", "completed": true}`).
2. Use `GET /todos` to confirm the item is stored in the database.

### Step 6: Stop Services (Preserving Database Data)

To stop and remove containers and networks while keeping your database volume safe:

```bash
docker compose down
```

If you run `docker compose up -d` again later, your saved todos will still be there!

### Step 7: Teardown Completely (Including Volumes)

If you want to perform a complete wipe and delete the database volume as well:

```bash
docker compose down -v
```

> [!WARNING]
> The `-v` flag deletes all named volumes attached to the Compose project, permanently erasing all stored database records.

---

## 🧹 Docker Compose Command Reference

| Command | Description |
| :--- | :--- |
| `docker compose up -d` | Start all services in detached (background) mode |
| `docker compose up --build -d` | Rebuild images before starting containers |
| `docker compose down` | Stop and remove containers and networks (preserves volumes) |
| `docker compose down -v` | Stop and remove containers, networks, **and volumes** |
| `docker compose ps` | List status of all project containers |
| `docker compose logs -f` | Stream logs for all services in real time |
| `docker compose logs -f <service>` | Stream logs for a specific service (e.g. `docker compose logs -f api`) |
| `docker compose restart` | Restart all services |
