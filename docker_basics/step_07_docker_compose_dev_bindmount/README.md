# Step 7: Docker Compose for Development — Bind Mounts & Live Hot-Reload

In Step 6, we learned how Docker Compose unifies our multi-container architecture. However, during active development, you hit a common frustration: **every time you edit your Python code, you have to run `docker compose up --build` and wait for the image to rebuild.**

This guide shows how developers configure Docker Compose for **instant hot-reloading** using **Bind Mounts**, `command` overrides, and the essential `--host 0.0.0.0` flag.

---

## 🎯 What You Will Learn

1. **Volume vs Bind Mount**: The key differences between Docker Named Volumes and Bind Mounts.
2. **Instant Code Reflection**: How `./app:/app/app` syncs your local files with the running container in real time.
3. **Overriding `CMD` with `command`**: Why the `Dockerfile` specifies production `fastapi run`, while `docker-compose.yml` overrides it with development `fastapi dev`.
4. **The `--host 0.0.0.0` Trap**: Why `fastapi dev` fails inside Docker without explicitly specifying the host.
5. **Zero-Rebuild Development Workflow**: Editing code in VS Code and seeing updates live in your browser without rebuilding images.

---

## 🔍 Named Volume vs Bind Mount: Side-by-Side

| Feature | Named Volume (Step 5 & 6) | Bind Mount (Step 7) |
| :--- | :--- | :--- |
| **Syntax** | `pgdata:/var/lib/postgresql/data` | `./app:/app/app` |
| **Storage Location** | Managed internally by Docker on host | An exact folder/file on your host computer |
| **Primary Purpose** | Persisting database files across restarts | Sharing source code between host and container |
| **Editing Files** | Hidden; not meant for manual editing | Directly edited in your IDE (VS Code, etc.) |
| **Best For** | Production database data (`db` service) | Local development live-reload (`api` service) |

```text
Host Computer (Your IDE)                             Container
┌───────────────────────────┐                     ┌───────────────────────────┐
│ d:/Exatech/.../app/       │    Bind Mount       │ /app/app/                 │
│   ├── main.py  ───────────┼────────────────────►│   ├── main.py             │
│   └── config/db.py        │  (./app:/app/app)   │   └── config/db.py        │
└───────────────────────────┘                     └───────────────────────────┘
     ▲                                                 ▲
     │ Any save here                                   │ Is immediately seen here
```

---

## ⚙️ Anatomy of the Development Compose File

Here is our development configuration in [docker-compose.yml](file:///d:/Exatech/docker_basics/step_07_docker_compose_dev_bindmount/docker-compose.yml):

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
    # 1. BIND MOUNT: Sync your host 'app' folder into the container
    volumes:
      - ./app:/app/app
    # 2. COMMAND OVERRIDE: Run dev server with auto-reload listening on 0.0.0.0
    command: uv run fastapi dev app/main.py --host 0.0.0.0
    env_file:
      - .env
    depends_on:
      - db

volumes:
  pgdata:
```

---

## 💡 Two Key Concepts You Must Understand

### 1. Why `command:` in Compose Overrides `CMD` in Dockerfile

* In [Dockerfile](file:///d:/Exatech/docker_basics/step_07_docker_compose_dev_bindmount/Dockerfile), the default command is:
  ```dockerfile
  CMD ["uv", "run", "fastapi", "run", "app/main.py"]
  ```
  `fastapi run` is meant for **production**: it disables file-watching and optimizes performance.
* In [docker-compose.yml](file:///d:/Exatech/docker_basics/step_07_docker_compose_dev_bindmount/docker-compose.yml), the `command:` setting **directly overrides** the `Dockerfile`'s `CMD`:
  ```yaml
  command: uv run fastapi dev app/main.py --host 0.0.0.0
  ```
  `fastapi dev` activates **WatchFiles**, which continuously monitors code for changes and automatically reloads the server on save.

---

### 2. The Critical `--host 0.0.0.0` Trap

When you run `fastapi dev` on your computer terminal, it starts listening on:
```text
http://127.0.0.1:8000
```

If you run `uv run fastapi dev app/main.py` inside Docker **without `--host 0.0.0.0`**, the server will only listen on the container's own internal loopback interface (`127.0.0.1`):

```text
Browser (Host: localhost:8000)
       │
       │ Port Forwarding (-p 8000:8000)
       ▼
Container Virtual Interface (eth0: 172.x.x.x)
       │
       │ ❌ FAILS! FastAPI is only listening on 127.0.0.1 (lo),
       │          ignoring outside traffic!
       ▼
Container Loopback (127.0.0.1)
```

**The Fix:** Passing `--host 0.0.0.0` instructs FastAPI / Uvicorn:
> *"Listen for incoming network traffic on **all** network interfaces, including Docker's virtual network adapter."*

This allows Docker's port forwarder (`8000:8000`) to route requests from your host browser into the application.

---

## 📦 Step-by-Step Instructions: Testing Live Reload

### Step 1: Ensure `.env` Exists

Make sure your `.env` file is ready:
```bash
cp .env.example .env
```

### Step 2: Start Services in Detached Mode

Start the database and API containers:

```bash
docker compose up -d
```

### Step 3: Stream API Logs

Open a terminal to watch the reload events in real time:

```bash
docker compose logs -f api
```

You should see logs confirming development mode and file watching:
```text
⚡️ Starting FastAPI in development mode
🐍 Using import string: app.main:app
🌐 Server started at http://0.0.0.0:8000
   Documentation at http://0.0.0.0:8000/docs
INFO:     Will watch for changes in these directories: ['/app/app']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Step 4: Open Swagger UI

In your browser, visit:
* [http://localhost:8000/docs](http://localhost:8000/docs)

### Step 5: Edit Code in Your Local Editor (Live Test)

Open `app/main.py` on your computer in VS Code. Add a simple new route at the bottom:

```python
@app.get("/ping")
def ping():
    return {"status": "live-reload-working!"}
```

**Save the file.**

Look at your terminal streaming the logs:
```text
WARNING:  WatchFiles detected changes in 'app/main.py'. Reloading...
INFO:     Started server process
INFO:     Application startup complete.
```

Now refresh your browser at [http://localhost:8000/docs](http://localhost:8000/docs):
* The new `/ping` endpoint appears immediately!
* **No `docker build` needed.**
* **No `docker compose restart` needed.**

---

## 🧹 Clean Up

To stop the containers when you're done:

```bash
# Stop containers (preserves database volume)
docker compose down

# Stop containers AND delete database volume
docker compose down -v
```

---

## 📋 Quick Summary

| Component | Setting | Purpose |
| :--- | :--- | :--- |
| **Code Sync** | `volumes: - ./app:/app/app` | Syncs host source code with container |
| **Command** | `command: uv run fastapi dev ...` | Replaces production server with auto-reloading dev server |
| **Network Host** | `--host 0.0.0.0` | Enables Docker port mapping to reach the server |
