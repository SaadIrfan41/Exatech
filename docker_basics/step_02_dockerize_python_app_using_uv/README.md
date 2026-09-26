# Modern Python Docker Guide: Dockerize with `uv`

A comprehensive, beginner-friendly guide on how to containerize modern Python applications using [Astral's `uv`](https://github.com/astral-sh/uv), lockfiles, and Docker layer caching best practices.

---

## 💡 Why Use `uv` with Docker?

In [Step 1](../step_01_dockerize_basic_python_project/), we ran a bare Python script without third-party libraries. In real-world projects, apps rely on external packages (`requests`, `fastapi`, `cowsay`, etc.).

Traditionally, developers used `pip` with a `requirements.txt`. Today, **`uv`** is the standard for fast, modern Python development:
* ⚡ **10-100x Faster**: Written in Rust, installs packages in milliseconds.
* 🔒 **Reliable & Deterministic**: Uses `pyproject.toml` and `uv.lock` to guarantee the exact same dependencies in production and development.
* 📦 **Standalone Binary**: Astral provides official binaries (`/uv` and `/uvx`) that can be dropped directly into any Docker image without pre-installing pip or curl.
* 🧱 **Optimized Docker Caching**: Separating dependency installation from code copying means Docker caches the dependencies, so rebuilding after code changes takes less than a second!

---

## 🛠️ Prerequisites

Ensure you have Docker installed and running on your system:
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows / macOS)
* `docker-ce` (Linux)
* *(Optional)* [`uv`](https://docs.astral.sh/uv/getting-started/installation/) installed locally if you want to test outside Docker.

---

## 🚀 Project Structure

```text
step_02_dockerize_python_app_using_uv/
├── .dockerignore        # Prevents host venv and temp files from copying into container
├── Dockerfile           # Docker build instructions
├── pyproject.toml       # Project definition and dependencies (PEP 518/621)
├── uv.lock              # Exact pinned versions of all dependencies
└── main.py              # Application entrypoint (using cowsay package)
```

### 1. `pyproject.toml`
Defines the project and its external dependencies (e.g., `cowsay`):
```toml
[project]
name = "step-02-dockerize-python-app-using-uv"
version = "0.1.0"
description = "Dockerized Python app using uv"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "cowsay>=6.1",
]
```

### 2. `main.py`
A simple script utilizing the installed dependency:
```python
import cowsay


def main():
    cowsay.cow("Hello from Dockerized Python App using UV!")


if __name__ == "__main__":
    main()
```

### 3. `.dockerignore`
> [!IMPORTANT]
> **Never copy host virtual environments into a container!**  
> If you create a `.venv` on Windows or macOS, those compiled binaries and paths will **not** work inside a Linux Docker container. The `.dockerignore` file ensures Docker ignores local virtual environments and caches:
```text
.venv
__pycache__
*.pyc
*.pyo
*.pyd
.git
.gitignore
```

### 4. `Dockerfile` Explained
```dockerfile
# 1. Base Image: Use an official lightweight Python 3.12 slim image
FROM python:3.12-slim

# We can install uv using:
# RUN pip install uv
# But it will download uv from the internet using pip and install it in the Python environment, which is slower.
# So instead, we copy the pre-built standalone uv & uvx binaries directly from Astral's official Docker image.
# This is the fastest and recommended way to install uv in Docker (no pip/curl required).

# 2. Install uv: Copy uv & uvx binaries from Astral's official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 3. Set working directory inside the container
WORKDIR /app

# 4. Layer Caching for Dependencies (Docker Best Practice!)
# Copy only pyproject.toml and uv.lock first
COPY pyproject.toml uv.lock ./

# Install project dependencies without installing the project itself yet.
# If you edit your Python code later, Docker re-uses this cached layer and skips 
# re-downloading packages!
RUN uv sync --frozen --no-install-project

# 5. Copy the remaining project files into the container
COPY . /app

# 6. Default command to execute when the container starts
# uv run automatically handles using the virtual environment created in /app/.venv
CMD ["uv", "run", "main.py"]
```

---

## 📦 Step-by-Step Instructions

### Step 1: Build the Docker Image

Build the Docker image and tag (`-t`) it as `uv-python-app`.

```bash
docker build -t uv-python-app .
```

> [!TIP]
> Notice how Docker pulls the `uv` binary, copies `pyproject.toml` and `uv.lock`, and runs `uv sync`. Subsequent builds where you only change `main.py` will be almost instantaneous because Docker will reuse the cached dependency layer!

### Step 2: Verify Built Images

List locally available images to confirm `uv-python-app` is present:

```bash
docker images
```

### Step 3: Run the Container

Run a container from the image. It will execute `main.py` and output our cow message:

```bash
docker run uv-python-app
```

**Expected Output:**
```text
  __________________________________________
| Hello from Dockerized Python App using UV! |
  ==========================================
                                          \
                                           \
                                             ^__^
                                             (oo)\_______
                                             (__)\       )\/\
                                                 ||----w |
                                                 ||     ||
```

---

## 🔍 Managing & Interacting with the Container

### Step 4: Run Container with a Custom Name

Give the container an explicit name for easy reference:

```bash
docker run --name=uv_app_container uv-python-app
```

### Step 5: Run an Interactive Shell (`sh`) Inside the Container

Drop into an interactive command shell inside the container instead of running `main.py`.

```bash
docker run --name=uv_app_container -it uv-python-app sh
```

* **`-i` (interactive)**: Keeps standard input open so you can type commands.
* **`-t` (pseudo-TTY)**: Allocates a terminal prompt.
* **`sh` vs `bash`**: Both are Unix command interpreters. Since Debian/slim images always provide `/bin/sh`, passing `sh` at the end overrides the default `CMD` and places you directly inside `/app` in the container.
* Inside the shell, you can explore the environment:
  ```bash
  # Check current directory
  pwd
  
  # List files inside container
  ls -la
  
  # Check uv version inside container
  uv --version
  
  # Run the application using uv
  uv run main.py
  
  # Exit the container
  exit
  ```

> [!WARNING]
> **Name Conflict Issue**: Once you exit, the container stops but **still exists on your machine**. If you try running `docker run --name=uv_app_container ...` again, Docker will return an error:
> `docker: Error response from daemon: Conflict. The container name "/uv_app_container" is already in use...`
> To reuse that name, you would have to manually delete it first:
> ```bash
> docker rm uv_app_container
> ```

### Step 6: Run with Auto-Removal (`--rm`) for Testing & Repetition

When testing or debugging, you don't want to manually delete containers after every exit. Add the `--rm` flag:

```bash
docker run --name=uv_app_container -it --rm uv-python-app sh
```

* **`--rm` flag**: Automatically deletes and cleans up the container the moment it stops/exits.
* **Use Case**: Allows you to enter the container, test commands, exit, and re-run the same command repeatedly without name conflict errors.

---

## 🧹 Quick Command Summary

| Command | Description |
| --- | --- |
| `docker build -t uv-python-app .` | Builds the image tagged `uv-python-app` |
| `docker images` | Lists all local Docker images |
| `docker run uv-python-app` | Runs the container executing default `CMD` |
| `docker run --name=<name> <image>` | Runs container with a specific custom name |
| `docker run --name=<name> -it <image> sh` | Runs interactive shell inside container |
| `docker run --name=<name> -it --rm <image> sh` | Runs interactive shell and automatically removes container upon exit |
| `docker ps` | Lists currently active/running containers |
| `docker ps -a` | Lists all containers (running and stopped) |
| `docker rm <name>` | Manually removes a stopped container |
| `docker rmi <image>` | Removes a Docker image from local storage |
