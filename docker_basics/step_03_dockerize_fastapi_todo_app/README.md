# Dockerize a FastAPI & Database App with `uv`

A comprehensive, beginner-friendly guide on how to containerize a real-world **FastAPI Todo application** with database connectivity using **`uv`**, secure environment variable handling, and Docker port mapping.

---

## 🎯 What You Will Learn

1. **Building a Python Web API Image** using `uv` and Docker.
2. **Handling Secrets Safely**: Why database credentials must **never** be hardcoded in a `Dockerfile`, and the 2 safe ways to inject them at runtime.
3. **Port Mapping (`-p`)**: Why `EXPOSE 8000` is not enough and how to connect host machine ports to container ports.
4. **Networking Concepts**: Why FastAPI logs `http://0.0.0.0:8000` but your browser must open `http://localhost:8000`.

---

## 🚀 Project Structure

```text
step_03_dockerize_fastapi_todo_app/
├── .dockerignore        # Prevents host .venv, .env, and caches from entering the image
├── .env                 # Local database credentials (NEVER commit to git or image!)
├── Dockerfile           # Docker build configuration
├── pyproject.toml       # Project metadata and dependencies (fastapi, sqlmodel, psycopg, etc.)
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

In our application, `app/config/db.py` needs a `DATABASE_URL` to connect to PostgreSQL / Neon DB:

```python
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, ...)
```

If `DATABASE_URL` is missing, the app crashes with:
```text
ArgumentError: Expected string or URL object, got None
```

### ❌ Why You Should NEVER Put Secrets in a `Dockerfile`

You might be tempted to add this to your `Dockerfile`:
```dockerfile
# ⚠️ DANGEROUS - DO NOT DO THIS!
ENV DATABASE_URL="postgresql://user:password@ep-cool-db.neon.tech/neondb"
```

**Why this is a major security flaw:**
1. **GitHub Leaks**: If you push the `Dockerfile` to GitHub, your private database credentials and passwords are leaked to the public.
2. **Baked Into Image Layers**: Any person or server that pulls the Docker image can run `docker history` or `docker inspect` and read your passwords in plain text.
3. **Breaks "Build Once, Run Anywhere"**: A Docker image should be an environment-agnostic template. If the database URL is hardcoded inside the image, you have to rebuild the entire image from scratch whenever your database or password changes.

---

### ✅ The 2 Safe Ways to Supply Environment Variables at Runtime

Instead of baking credentials into the image, inject them dynamically when starting the container:

#### Method 1: Using `--env-file` (Recommended for Local Dev)
Pass your local `.env` file directly to the container:

```bash
docker run --name=fastapi-todo-container -p 8000:8000 --env-file .env --rm fastapi-todo-image
```
* Docker reads your local `.env` file on your host machine and injects its variables into the container environment.
* The `.env` file remains on your computer and is **never** baked into the image.

#### Method 2: Using `-e` or `--env` (Inline Variables)
Pass individual environment variables directly in the command line:

```bash
docker run --name=fastapi-todo-container -p 8000:8000 -e DATABASE_URL="your_actual_db_connection_url" --rm fastapi-todo-image
```
* Useful in CI/CD pipelines, cloud deployment services (AWS, Google Cloud Run, Render), or when overriding a single value.

---

## 🌐 The Port Mapping Problem (`-p`)

### Why doesn't `EXPOSE 8000` make the app accessible?

In the `Dockerfile`, we have:
```dockerfile
EXPOSE 8000
```
> [!IMPORTANT]
> `EXPOSE 8000` is **only documentation/metadata**! It communicates to developers that the app inside listens on port 8000, but **it does NOT publish or forward the port to your host machine**.

Docker containers run inside an **isolated virtual network bridge**. Without port mapping, the container's port 8000 is completely trapped inside the container's private network.

### The Solution: Map the Ports with `-p`

To connect your host machine's port to the container's port, use `-p <host_port>:<container_port>`:

```bash
-p 8000:8000
```

```
Your Computer (Host)                      Docker Container
┌─────────────────────┐                 ┌─────────────────────┐
│  Browser / Postman  │                 │     FastAPI App     │
│  http://localhost   │                 │     Listening on    │
│      :8000 ─────────┼────────────────►│        :8000        │
└─────────────────────┘   Port Mapping  └─────────────────────┘
                          (-p 8000:8000)
```

If you don't provide `-p 8000:8000`, the container runs successfully, but opening `http://localhost:8000` in your browser will result in `This site can't be reached` / connection refused.

---

## ❓ Why `http://localhost:8000` and NOT `http://0.0.0.0:8000`?

When you start the container, the terminal prints:
```text
🌐 Server started at http://0.0.0.0:8000
   Documentation at http://0.0.0.0:8000/docs
```

When you try opening `http://0.0.0.0:8000` in your browser, **it fails**. But `http://localhost:8000` **works**. Why?

### 1. `0.0.0.0` is a "Listening" Address (Server-Side)
Inside the container, `0.0.0.0` is a meta-address that tells FastAPI / Uvicorn:
> *"Listen for incoming network traffic on **all** network interfaces (Ethernet, Docker virtual bridge, loopback)."*

If FastAPI listened only on `127.0.0.1` inside the container, Docker's network bridge wouldn't be able to forward outside traffic into it. So `0.0.0.0` is required on the server side.

### 2. `localhost` / `127.0.0.1` is a "Destination" Address (Client-Side)
For your web browser:
* `127.0.0.1` (or hostname `localhost`) is the **loopback destination**. It tells your operating system: *"Send this request directly to my own machine."*
* Your operating system directs the request to port `8000`, Docker intercepts it through the `-p 8000:8000` forwarder, and hands it to FastAPI inside the container.

### 3. Why Browsers Reject `0.0.0.0`
* According to internet standards (RFC 1122), `0.0.0.0` is non-routable as a destination IP address.
* The Windows networking stack does not treat `0.0.0.0` as a valid destination for client connections.
* Modern browsers (Chrome, Edge, Firefox) block navigation to `0.0.0.0` for security reasons (Private Network Access policy to prevent CSRF attacks).

| Address | What it does | Browser can open it? |
| :--- | :--- | :--- |
| **`0.0.0.0:8000`** | Tells server to bind & listen on all interfaces | ❌ No |
| **`localhost:8000`** | Routes request to your local computer's port | ✅ Yes |
| **`127.0.0.1:8000`** | IPv4 loopback address to your local computer | ✅ Yes |

---

## 📦 Step-by-Step Instructions

### Step 1: Build the Docker Image

From `step_03_dockerize_fastapi_todo_app/`, build the image:

```bash
docker build -t fastapi-todo-image .
```

### Step 2: Verify the Image

Confirm that the image was built and is stored in your local Docker registry:

```bash
docker images
```

### Step 3: Run the Container with Port Mapping and `.env`

Start the container, publish port `8000`, supply your environment file, and use `--rm` for automatic cleanup on exit:

```bash
docker run --name=fastapi-todo-container -p 8000:8000 --env-file .env --rm fastapi-todo-image
```

### Step 4: Verify in Your Browser

Open your browser and navigate to:
* **Interactive API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Alternative API Docs (ReDoc)**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

You can now test CRUD operations (Create, Read, Update, Delete) on your Todo endpoints directly from Swagger!

### Step 5: Stop the Container

In your terminal where the container is running, press:
```text
Ctrl + C
```
Because of the `--rm` flag, the container will stop and automatically be removed, leaving no leftover container conflicts when you run it next time.

---

## 🧹 Quick Command Summary

| Task | Command |
| :--- | :--- |
| **Build image** | `docker build -t fastapi-todo-image .` |
| **Run with `.env` file & port mapping** | `docker run --name=fastapi-todo-container -p 8000:8000 --env-file .env --rm fastapi-todo-image` |
| **Run with inline variable** | `docker run --name=fastapi-todo-container -p 8000:8000 -e DATABASE_URL="..." --rm fastapi-todo-image` |
| **Explore container shell** | `docker run --name=fastapi-todo-container -it --rm fastapi-todo-image sh` |
| **List running containers** | `docker ps` |
| **List all containers (including stopped)** | `docker ps -a` |
| **Manually delete stopped container** | `docker rm fastapi-todo-container` |
