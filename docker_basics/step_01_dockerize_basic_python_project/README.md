# Simple Docker Image Creation & Container Guide

A step-by-step guide on how to build a simple Python Docker image and run it inside a container using basic Docker commands.

---

## 🛠️ Prerequisites

Ensure you have Docker installed and running on your system:
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows / macOS)
* `docker-ce` (Linux)

---

## 🚀 Getting Started

### 1. Project Structure

Create a project directory with your Python script and a `Dockerfile`:

```text
my-python-app/
├── Dockerfile
└── app.py

```

**Example `app.py`:**

```python
print("Hello from inside the Docker container!")

```

**Example `Dockerfile`:**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY app.py .
CMD ["python", "app.py"]

```

---

## 📦 Step-by-Step Instructions

### Step 1: Build the Docker Image

Build a Docker image from the current directory (`.`) and tag (`-t`) it as `python-class`.

```bash
docker build -t python-class .

```

### Step 2: Verify Built Images

List all locally available Docker images to confirm your image was created.

```bash
docker images

```

### Step 3: Run the Container

Run a new container created from the `python-class` image.

```bash
docker run python-class

```

---

## 🔍 Managing Containers

### Step 4: Check Running Containers

List all currently active (running) containers.

```bash
docker ps
# OR
docker container ls

```

### Step 5: Check All Containers (Including Stopped)

List all containers, including those that have already exited.

```bash
docker ps -a
# OR
docker container ls -a

```

### Step 6: Run Container with a Specific Name

Assign a custom name (`python_class_container`) to your running container for easy reference.

```bash
docker run --name=python_class_container python-class

```

### Step 7: Run an Interactive Container with a Shell (`sh`)

Open an interactive shell session inside the container rather than running the default script (`CMD`).

```bash
docker run --name=python_class_container -it python-class sh
```

* **`-i` (interactive)**: Keeps standard input (STDIN) open, allowing you to enter commands.
* **`-t` (pseudo-TTY)**: Allocates a terminal interface so you get a usable command prompt.
* **What is `sh` / `bash`?**: Both are Unix command-line shells (interpreters). Passing `sh` (or `bash`) at the end overrides the default `CMD` specified in the `Dockerfile` and places you directly into the container's file system so you can explore directories (`ls`, `cd`, `pwd`), check environment variables, and run test commands. `sh` is universally available across virtually all minimal/slim base images (like Alpine or Debian slim), whereas `bash` is feature-rich but may not always be installed in lightweight images.

> [!WARNING]
> **Name Conflict Issue**: When you exit this container, it stops but **remains saved on your machine**. If you attempt to run the command again with `--name=python_class_container`, Docker will throw a conflict error stating that the container name is already in use. You must manually delete it first with `docker rm python_class_container` before reusing that name.

### Step 8: Run with Auto-Removal for Testing & Reusability (`--rm`)

If you want to test a container interactively and run it repeatedly without manually deleting it each time, use the `--rm` flag.

```bash
docker run --name=python_class_container -it --rm python-class sh
```

* **`--rm` flag**: Automatically deletes the container and cleans up its file system the moment it exits.
* **Why use it?**: When testing or debugging containers, you often need to jump in, test something, exit, make adjustments, and jump back in. Without `--rm`, you must remember to run `docker rm` each time before starting a new container with the same name. Adding `--rm` avoids name conflicts and keeps your system free of leftover stopped containers.

---

## 🧹 Quick Command Summary

| Command | Description |
| --- | --- |
| `docker build -t python-class .` | Builds the image with tag `python-class` |
| `docker images` | Lists all local images |
| `docker run python-class` | Executes a container from the image |
| `docker ps` / `docker container ls` | Shows running containers |
| `docker ps -a` / `docker container ls -a` | Shows all containers (running & stopped) |
| `docker run --name=<name> <image>` | Runs container with a specific custom name |
| `docker run --name=<name> -it <image> sh` | Runs interactive shell inside container |
| `docker run --name=<name> -it --rm <image> sh` | Runs interactive shell and automatically removes container upon exit |
| `docker rm <name>` | Manually deletes a stopped container |

