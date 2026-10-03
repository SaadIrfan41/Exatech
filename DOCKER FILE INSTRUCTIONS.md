# Dockerfile Instructions: Every Building Block Explained

A `Dockerfile` is a list of instructions, read top to bottom, that tells Docker how to build an image. Each instruction is a single word in ALL CAPS, followed by what it should do.

This guide walks through every instruction you'll actually use, what it means, and — for the ones that look similar — exactly how they're different, since that's where most confusion happens.

---

## Module 1: `FROM` — the starting point

Every Dockerfile must start with `FROM`. It picks a **base image** to build on top of, instead of starting from nothing.

```dockerfile
FROM python:3.12-slim
```

Think of it as: *"start with a computer that already has this installed."* You can build on top of an official image (like `python`), a minimal one (like `alpine`), or even nothing at all (`FROM scratch`, for advanced cases you won't need yet).

---

## Module 2: `WORKDIR` — set the current folder

```dockerfile
WORKDIR /app
```

Sets the folder that every instruction *after* this one runs from — the same idea as running `cd /app` before your next commands. If the folder doesn't exist yet, Docker creates it automatically.

Without `WORKDIR`, everything runs from `/` (the root of the filesystem), and your `COPY`/`RUN` instructions can end up in confusing places.

---

## Module 3: `COPY` vs `ADD` — getting your files in

Both instructions copy files from your computer into the image. They look almost identical, but they're not the same.

### `COPY` — the simple, predictable one

```dockerfile
COPY . /app
COPY requirements.txt .
```

Copies files or folders from your project into the image. That's it — no surprises, no extra behavior.

### `ADD` — does everything `COPY` does, plus two extra tricks

```dockerfile
ADD archive.tar.gz /app/       # automatically extracts the archive
ADD https://example.com/file.txt /app/   # can download a file from a URL
```

`ADD` can also **automatically unpack** compressed archives (`.tar`, `.tar.gz`, etc.) as it copies them in, and can fetch a file directly from a URL.

### Which one should you actually use?

**Use `COPY` by default, always** — for almost everything you do, `COPY` is what you want. Its behavior is predictable: what you see is exactly what happens. `ADD`'s "magic" extraction behavior can cause confusing, hard-to-debug results if you didn't intend it. Only reach for `ADD` in the rare case where you specifically need to auto-extract a local archive.

```
COPY = "copy this file/folder, exactly, nothing else"
ADD  = "copy this file/folder — but also auto-extract archives, or fetch URLs"
```

---

## Module 4: `RUN` — execute a command while building

```dockerfile
RUN uv sync
```

Runs a command **once, during the build**, and saves the result as part of the image. This is how you install dependencies, create folders, or run any setup command that needs to happen before the image is finished.

Every `RUN` creates a new layer in the image (see the Docker Commands guide for more on layers and caching).

---

## Module 5: `CMD` vs `ENTRYPOINT` — what happens when the container starts

This is the pair that confuses almost everyone at first. Both define what runs when a container **starts** (not while building — that's `RUN`'s job). The difference is about *how replaceable* that command is.

### `CMD` — the default command, easily overridden

```dockerfile
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
```

This is what runs by default. But anyone running your image can completely replace it:

```bash
docker run todo-api:1.0 echo "hello"
```

This ignores the `CMD` entirely and runs `echo "hello"` instead.

### `ENTRYPOINT` — the fixed command, always runs

```dockerfile
ENTRYPOINT ["fastapi", "run", "app/main.py"]
```

This is *not* easily overridden. Anything you add after `docker run image` gets **appended** to it, instead of replacing it:

```bash
docker run todo-api:1.0 --port 9000
# actually runs: fastapi run app/main.py --port 9000
```

### Using them together (the common real-world pattern)

```dockerfile
ENTRYPOINT ["fastapi", "run", "app/main.py"]
CMD ["--host", "0.0.0.0", "--port", "8000"]
```

Here, `ENTRYPOINT` is the fixed program that always runs, and `CMD` supplies the **default arguments** to it — arguments someone can still override at `docker run` time without changing what program actually runs.

**Simple rule of thumb:**
```
Just CMD:               fine for simple images, easiest to override for testing
ENTRYPOINT + CMD:       best when you want the image to always run ONE specific program,
                        but still allow customizing its default arguments
```

For the Todo API throughout this course, plain `CMD` is enough — you won't need `ENTRYPOINT` until you're building images meant to behave like a fixed command-line tool.

---

## Module 6: `ENV` vs `ARG` — variables in a Dockerfile

Both let you use a variable inside the Dockerfile, but they exist at different times.

### `ENV` — available at build time AND inside the running container

```dockerfile
ENV APP_ENV=production
```

This value exists while the image builds, and it's **baked into the image** — meaning any container started from it will also see this environment variable automatically, without you needing to pass it in with `docker run`.

### `ARG` — only available WHILE building, then it's gone

```dockerfile
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim
```

`ARG` values exist only during the build — they're **not** available once a container starts running. You pass them in at build time:

```bash
docker build --build-arg PYTHON_VERSION=3.11 -t todo-api .
```

**When to use which:**
```
ENV → things the running app itself needs (though for real secrets, prefer
      passing them in at "docker run" time with --env-file, not baking them
      into the image — see the Docker Commands guide)
ARG → things that only affect HOW the image gets built (like a version
      number to install), and don't need to exist afterward
```

---

## Module 7: `EXPOSE` — document which port the app uses

```dockerfile
EXPOSE 8000
```

This is purely **documentation** — it tells anyone reading the Dockerfile (and some tools) which port the app is expected to listen on. It does **not** actually open the port; you still need `-p 8000:8000` on `docker run` for the port to be reachable. Skipping `EXPOSE` doesn't break anything, but it's good practice to include it.

---

## Module 8: `VOLUME` — mark a folder as persistent storage

```dockerfile
VOLUME /app/data
```

Marks a folder inside the container as a place where data should live outside the container's own disposable filesystem — Docker will automatically create an anonymous volume for it if one isn't specified at `docker run` time. In practice, most people instead create and name their volumes explicitly at `docker run` (`-v todo-data:/app/data`, as covered in the Docker Commands guide) rather than declaring `VOLUME` in the Dockerfile — but it's worth recognizing when you see it in someone else's Dockerfile.

---

## Module 9: `USER` — who runs the app inside the container

```dockerfile
RUN useradd --create-home appuser
USER appuser
```

By default, everything inside a container runs as `root` — full permissions. `USER` switches to a less-privileged account for anything that runs after it. This is a production security best practice: if the app is ever compromised, the damage is limited by what that user is allowed to do.

---

## Module 10: `LABEL` — metadata about the image

```dockerfile
LABEL maintainer="saad@example.com"
LABEL version="1.0"
LABEL description="Todo API backend"
```

Doesn't affect how the image runs at all — it just attaches searchable information to it, viewable with `docker inspect`. Useful for organizing images once you have many of them, but not essential while learning.

---

## Module 11: `HEALTHCHECK` — let Docker check if the app is actually working

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/ || exit 1
```

Tells Docker how to periodically check whether the app inside the container is actually responding, not just "running." A container can be technically running while the app inside it has crashed or frozen — `HEALTHCHECK` lets tools like `docker ps` show `(healthy)` / `(unhealthy)`, and orchestration tools (like Kubernetes, later in your course) can automatically restart unhealthy containers.

---

## A few advanced instructions (good to recognize, not essential yet)

| Instruction | What it does | Why it's rarely needed as a beginner |
|---|---|---|
| `ONBUILD` | Sets up a trigger instruction that runs later, when *another* Dockerfile builds `FROM` this image | Mainly used when building "base images" meant for others to extend |
| `SHELL` | Changes which shell `RUN` uses to execute commands | The default (`/bin/sh -c`, or `cmd /S /C` on Windows) is fine for almost everything |
| `STOPSIGNAL` | Changes which signal is sent to gracefully stop the container | The default (`SIGTERM`) is correct for the vast majority of apps |

---

## Putting it all together

Here's a Dockerfile using the instructions from this guide, for the Todo API:

```dockerfile
FROM python:3.12-slim

LABEL maintainer="saad@example.com"

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

RUN useradd --create-home appuser
USER appuser

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/ || exit 1

CMD ["uv", "run", "fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
```

Every line maps back to a module above — `FROM` picks the base, `WORKDIR` sets the folder, `COPY` brings files in (ordered for good layer caching), `RUN` installs dependencies and sets up a non-root user, `USER` switches to it, `ENV` sets a runtime variable, `EXPOSE` documents the port, `HEALTHCHECK` lets Docker monitor it, and `CMD` defines what actually runs.

---

## Quick-reference table

| Instruction | Runs when? | Purpose |
|---|---|---|
| `FROM` | Build | Choose the base image to start from |
| `WORKDIR` | Build | Set the current folder for later instructions |
| `COPY` | Build | Copy files/folders in, exactly as-is |
| `ADD` | Build | Like `COPY`, plus auto-extract archives / fetch URLs |
| `RUN` | Build | Execute a command and bake the result into the image |
| `ENV` | Build + Runtime | Set a variable available both while building and when running |
| `ARG` | Build only | Set a variable available only while building |
| `EXPOSE` | Documentation only | Note which port the app listens on |
| `VOLUME` | Runtime | Mark a folder as external, persistent storage |
| `USER` | Build + Runtime | Switch to a less-privileged user |
| `LABEL` | Metadata only | Attach searchable info to the image |
| `HEALTHCHECK` | Runtime | Let Docker check if the app is actually working |
| `CMD` | Runtime | Default command (easily overridden at `docker run`) |
| `ENTRYPOINT` | Runtime | Fixed command (arguments get appended, not replaced) |