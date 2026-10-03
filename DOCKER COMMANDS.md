# Docker Commands: From Image to Container

This is a reference guide for the everyday Docker commands — building images, running containers, managing tags, and cleaning up. Keep this open in a tab while you work; you won't memorize all of this on the first pass, and you don't need to.

**One core idea before anything else:**

```
Image      = a blueprint (a packaged snapshot of your app + everything it needs)
Container  = a running house built from that blueprint
```

You build **one image**, and can run **many containers** from it — each one an independent, running copy. Building the image again doesn't affect containers already running from an older version.

---

## Module 1: Building an image

### `docker build`

Turns a `Dockerfile` into an image.

```bash
docker build -t todo-api:1.0 .
```

- `-t todo-api:1.0` — **tags** (names) the image. Format is always `name:tag`.
- `.` — tells Docker to look for the `Dockerfile` in the current folder, and to use everything in this folder as what gets copied in.

If you don't give it a tag at all:
```bash
docker build .
```
The image still builds, but it gets no name — you'd have to refer to it by a random ID, which is inconvenient. Always tag your builds.

---

## Module 2: Understanding tags

A **tag** is just a label on an image — usually used for versioning.

```
todo-api:1.0
  ↑        ↑
 name      tag
```

If you don't specify a tag, Docker silently uses `latest`:
```bash
docker build -t todo-api .
# is the same as:
docker build -t todo-api:latest .
```

**Common tag conventions:**
```
todo-api:latest      → whatever was built most recently
todo-api:1.0          → a specific version
todo-api:dev          → a development build
python:3.12-slim      → an official image, version 3.12, "slim" variant
```

**Important habit to teach:** `latest` is convenient for learning, but in real projects it's risky — it doesn't tell you *which* version is actually running. If you deploy `latest` today and rebuild it next week, anyone still using the tag `latest` now gets a *different* image without realizing anything changed. Use specific version tags (`1.0`, `1.1`, a git commit hash, etc.) once you're doing anything beyond local practice.

You can also add a second tag to an image you've already built, without rebuilding it:

```bash
docker tag todo-api:1.0 todo-api:latest
```
This says: *"todo-api:latest should now point at the same image as todo-api:1.0."* Useful for marking a specific version as "the current one" without a fresh build.

---

## Module 3: Viewing images you have

```bash
docker images
```

Shows every image currently on your machine:

```
REPOSITORY   TAG      IMAGE ID       CREATED         SIZE
todo-api     1.0      a1b2c3d4e5f6   2 minutes ago   215MB
python       3.12     f6e5d4c3b2a1   3 weeks ago     1.02GB
```

| Column | Meaning |
|---|---|
| REPOSITORY | The image's name |
| TAG | The version label |
| IMAGE ID | A unique short ID for this exact build |
| CREATED | How long ago it was built |
| SIZE | How much disk space it takes up |

---

## Module 4: Running a container

### `docker run`

Creates and starts a new container from an image.

```bash
docker run -d -p 8000:8000 --name my-todo-app todo-api:1.0
```

Let's break down every part:

| Flag | Meaning |
|---|---|
| `-d` | **Detached** — run in the background, giving you your terminal back immediately |
| `-p 8000:8000` | **Port mapping**: `host_port:container_port`. Connects port 8000 on your machine to port 8000 inside the container |
| `--name my-todo-app` | Gives the container a name you can refer to later, instead of a random one Docker would generate |
| `todo-api:1.0` | Which image to run |

**Other flags you'll use constantly:**

```bash
docker run -it ubuntu bash
```
- `-it` — combines two things: `-i` (keep input open so you can type) and `-t` (give you a proper terminal-like display). Together, this is what lets you get an *interactive* session inside a container, instead of it just running and exiting immediately.

```bash
docker run --rm todo-api:1.0
```
- `--rm` — automatically delete the container once it stops. Great for quick one-off tests where you don't want leftover stopped containers piling up.

```bash
docker run --env-file .env -p 8000:8000 todo-api:1.0
```
- `--env-file .env` — loads environment variables (like a database URL or secret key) from a file into the container, instead of hardcoding them into the image.

```bash
docker run -e DATABASE_URL=postgres://... todo-api:1.0
```
- `-e KEY=value` — sets a single environment variable directly on the command line, without needing a whole `.env` file.

---

## Module 5: Viewing and managing running containers

### `docker ps` — "What's currently running?"

```bash
docker ps
```

```
CONTAINER ID   IMAGE          COMMAND              STATUS         PORTS                    NAMES
9f8e7d6c5b4a   todo-api:1.0   "fastapi run ..."    Up 2 minutes   0.0.0.0:8000->8000/tcp   my-todo-app
```

By default, `docker ps` only shows **running** containers. To also see stopped ones:
```bash
docker ps -a
```

### `docker logs` — "What has this container printed?"

```bash
docker logs my-todo-app
```

Shows everything the app inside the container has printed since it started — errors, startup messages, request logs.

```bash
docker logs -f my-todo-app
```
`-f` follows the logs live, exactly like `tail -f` on a log file — new lines appear as they happen.

### `docker exec` — "Let me get inside a running container"

```bash
docker exec -it my-todo-app bash
```

Opens an interactive terminal *inside* an already-running container — useful for poking around, checking if a file exists, or debugging something live. `exit` to leave it (this doesn't stop the container, just your session inside it).

### Stopping, starting, and removing containers

```bash
docker stop my-todo-app       # Gracefully stop a running container
docker start my-todo-app      # Start it again (keeps its previous state)
docker restart my-todo-app    # Stop then start, in one command
docker rm my-todo-app         # Delete a stopped container permanently
```

**Note:** `docker stop` doesn't delete anything — the container still exists, just not running. `docker rm` is the one that actually removes it. You can't `rm` a container that's still running unless you add `-f` (force):
```bash
docker rm -f my-todo-app
```

---

## Module 6: Managing images

```bash
docker rmi todo-api:1.0
```
Deletes an image. Fails if a container (even a stopped one) still depends on it — remove the container first.

```bash
docker pull python:3.12-slim
```
Downloads an image from a registry (by default, Docker Hub) without running it — useful for pre-fetching a base image, or grabbing someone else's published image.

```bash
docker push yourusername/todo-api:1.0
```
Uploads your image to a registry so others (or your production server) can pull it. Requires being logged in (`docker login`) and the image being tagged with your registry username first.

---

## Module 7: Cleaning up

Docker doesn't delete anything automatically — stopped containers, old images, and unused networks all pile up over time.

```bash
docker container prune    # Remove ALL stopped containers
docker image prune        # Remove unused (dangling) images
docker system prune       # Remove stopped containers, unused images, and networks all at once
```

Add `-a` to `docker system prune -a` to also remove images that aren't attached to *any* container, not just "dangling" ones — this is more aggressive and will make your next `docker build` or `docker pull` slower, since it has to re-download/rebuild things it just cleared out.

---

## Module 8: Volumes (making data survive)

By default, anything written inside a container disappears when the container is removed. A **volume** is storage that lives outside the container, so data survives even if the container is deleted and recreated.

```bash
docker volume create todo-data
docker run -v todo-data:/app/data todo-api:1.0
```

- `docker volume create todo-data` — creates a named volume.
- `-v todo-data:/app/data` — mounts that volume at `/app/data` inside the container. Anything the app writes there is actually stored in the volume, not inside the disposable container itself.

This is exactly the gap mentioned back when we first containerized the Todo API and its SQLite file — a volume is the real fix for that.

---

## Quick-reference cheat sheet

| Command | What it does |
|---|---|
| `docker build -t name:tag .` | Build an image from a Dockerfile |
| `docker images` | List images on your machine |
| `docker tag old:tag new:tag` | Add another tag to an existing image |
| `docker run -d -p 8000:8000 --name x image` | Start a container in the background |
| `docker run -it image bash` | Start a container with an interactive terminal |
| `docker run --rm image` | Run and auto-delete once it stops |
| `docker ps` | List running containers |
| `docker ps -a` | List all containers, including stopped ones |
| `docker logs -f name` | Follow a container's live output |
| `docker exec -it name bash` | Get a terminal inside a running container |
| `docker stop name` | Stop a running container |
| `docker start name` | Start a stopped container again |
| `docker rm name` | Delete a stopped container |
| `docker rmi image` | Delete an image |
| `docker pull image` | Download an image from a registry |
| `docker push image` | Upload an image to a registry |
| `docker volume create name` | Create a persistent volume |
| `docker system prune` | Clean up unused containers/images/networks |

---

## Try it yourself

Using the `todo-api` image from earlier in the course:

```bash
docker build -t todo-api:1.0 .
docker images
docker run -d -p 8000:8000 --name my-api todo-api:1.0
docker ps
docker logs -f my-api          # Ctrl+C to stop watching (container keeps running)
docker exec -it my-api bash    # look around inside, then type "exit"
docker stop my-api
docker rm my-api
docker rmi todo-api:1.0
```

By the end of that sequence, you've built an image, run it, watched its logs live, gone inside it, and cleaned everything up — the full lifecycle of a container.

---

## What comes next

Running one container by hand is fine for one app. Once you have several containers that need to talk to each other (an API, a database, a cache), typing all these flags by hand every time gets unwieldy — that's what **Docker Compose** is for: describing your whole setup in one file and starting everything with a single `docker compose up`. That's a good next step once these individual commands feel comfortable.