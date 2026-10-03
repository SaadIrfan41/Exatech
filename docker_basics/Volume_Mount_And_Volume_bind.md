# Docker Volumes, Bind Mounts & Networking

Everything written inside a container normally disappears the moment that container is removed, and every container is isolated from every other container by default. This guide covers both problems, using a real Postgres container and your own FastAPI Todo app throughout — creating data through `/docs` like you normally would, not typing it in by hand.

```
Volume      = storage Docker manages for you, on its own, hidden away
Bind mount  = storage that's just a folder/file on YOUR computer, mapped directly in
Network     = what lets separate containers actually find and talk to each other
```

```
Part 1 — Persistence:  volumes & bind mounts, with FastAPI running on your own machine
Part 2 — Networking:   what changes once FastAPI moves into a container too
```

---

# Part 1 — Persistence: Volumes & Bind Mounts

## Step 1 — Run a Postgres container, and understand ports

```bash
docker run -d --name pg-todo -e POSTGRES_PASSWORD=secret -p 5432:5432 postgres:16
```

Before going further, let's actually understand that `-p 5432:5432` flag — it's easy to copy-paste without knowing what it's doing.

**What is a port?** A port is a numbered "door" a program listens on for incoming network traffic. Postgres, by convention, listens on port `5432`. FastAPI's dev server listens on `8000`. A single machine can run many programs at once, each with its own door number, so traffic knows exactly which program it's meant for.

**Why containers need port mapping at all:** a container is isolated by default — even though Postgres is listening on port `5432` *inside* the container, nothing outside the container can reach it unless you explicitly connect a door on your own machine to that door inside the container. That's what `-p` does:

```
-p 5432:5432
    ↑     ↑
 host   container
 port    port
```

```
Your computer (port 5432)  <───mapped───>  Container (port 5432)
                                                  │
                                            Postgres is listening here
```

You can also map to a *different* port on your side, if `5432` is already taken by something else on your machine:
```bash
-p 5433:5432
```
This means *"reach the container's port 5432 through port 5433 on my machine instead"* — the container itself is unaffected; only how you reach it from outside changes.

Without `-p` at all, Postgres would be running, healthy, and completely unreachable from outside the container — a very common first mistake.

---

## Step 2 — Get the connection string and use it in FastAPI

With the container above running (and reachable via port `5432` on your machine), the connection string looks exactly like the Neon one did — just pointing at your own machine instead of Neon's servers:

```
DATABASE_URL=postgresql://postgres:secret@localhost:5432/postgres
```

- `postgres` (before the `:secret`) — the default username Postgres creates
- `secret` — the password we set with `-e POSTGRES_PASSWORD=secret`
- `localhost:5432` — your own machine, on the port we just mapped
- `postgres` (at the end) — the default database name Postgres creates automatically

Update your `.env` file with this value, then restart your FastAPI dev server so it picks up the change:

```bash
uv run fastapi dev app/main.py
```

Nothing else in your app changes — `create_engine(DATABASE_URL)` doesn't know or care whether it's talking to Neon or a container on your own machine.

---

## Step 3 — Add data the normal way: through `/docs`

Open `http://127.0.0.1:8000/docs`, and use `POST /todos` to create a couple of todos, just like you always have. Then confirm they're there with `GET /todos`.

This is the important part to notice: **your FastAPI app has no idea Postgres is running inside a container.** As far as your app is concerned, it's just talking to a database at `localhost:5432` — completely unaware of Docker at all.

---

## Step 4 — See what happens WITHOUT a volume

Remove the container and start a fresh one, using the exact same command as Step 1:

```bash
docker rm -f pg-todo
docker run -d --name pg-todo -e POSTGRES_PASSWORD=secret -p 5432:5432 postgres:16
```

Now go back to `/docs` and call `GET /todos` again.

**Your todos are gone — an empty list.** Nothing changed in your FastAPI app or your `.env` file. The database itself was recreated from nothing, because Postgres had been storing its data files inside the old container's filesystem, and that filesystem was deleted along with the container.

---

## Step 5 — Fix it with a named volume

A **volume** is storage that Docker manages for you, completely separate from any one container's lifecycle.

```bash
docker volume create pgdata
docker rm -f pg-todo
docker run -d --name pg-todo -e POSTGRES_PASSWORD=secret -p 5432:5432 -v pgdata:/var/lib/postgresql/data postgres:16
```

`-v pgdata:/var/lib/postgresql/data` means: *"whatever Postgres writes to `/var/lib/postgresql/data` (its own internal data folder) should actually live in the `pgdata` volume, not inside the container."*

Go back to `/docs`, create a couple of todos again with `POST /todos`, confirm them with `GET /todos`. Now repeat the "destroy and recreate" test from Step 4, but keep the `-v pgdata:...` flag this time:

```bash
docker rm -f pg-todo
docker run -d --name pg-todo -e POSTGRES_PASSWORD=secret -p 5432:5432 -v pgdata:/var/lib/postgresql/data postgres:16
```

Call `GET /todos` in `/docs` one more time.

**Your todos are still there.** The container was destroyed and rebuilt from scratch, but the actual data lived safely inside `pgdata` the entire time.

```bash
docker volume ls              # see all volumes
docker volume inspect pgdata  # see details Docker tracks about it
```

---

## Step 6 — How it all fits together

```
                     localhost:5432
FastAPI (uv run)  ───────────────────►  Postgres container
(runs on your                            (port 5432, mapped to
 own machine)                             your machine via -p)
                                                  │
                                          writes data to
                                                  ▼
                                    /var/lib/postgresql/data
                                                  │
                                     ┌────────────┴─────────────┐
                                     │                           │
                              WITHOUT a volume:          WITH a volume:
                          lives inside the container   lives in "pgdata",
                          → destroyed with it            outside the container
                                                          → survives it
```

Three separate things are working together here, and it's worth students being able to name each one:
1. **The port mapping (`-p`)** — lets your FastAPI app (outside Docker) reach Postgres (inside Docker) at all.
2. **The connection string (`DATABASE_URL`)** — tells your app *where* and *how* to connect.
3. **The volume (`-v`)** — decides whether the data behind that connection survives a container being destroyed and recreated.

Get any one of the three wrong, and something breaks in a different way: wrong port mapping → app can't connect at all; wrong connection string → wrong credentials/host; no volume → connects fine, but data quietly vanishes on restart.

---

## Bind mounts: a different problem entirely

Volumes solve *data* persistence. A **bind mount** solves a different problem: seeing your *own code* changes reflected inside a container without rebuilding it every time.

```bash
docker run -d -p 8000:8000 --name todo-dev -v "$(pwd)/app:/app/app" todo-api:1.0 uv run fastapi dev app/main.py --host 0.0.0.0
```

`-v "$(pwd)/app:/app/app"` maps the `app/` folder *on your computer* directly into the container — not a copy, the same files. Edit `main.py`, save it, and (since we're running `fastapi dev`, which watches for changes) the running container picks it up immediately.

**Note:** our production `CMD` normally runs `fastapi run`, which does *not* auto-reload — that's intentional for stability in production. The command above overrides it with `fastapi dev` specifically so the bind mount's benefit (instant reflected changes) is actually visible.

---

## Volume vs bind mount, side by side

| | Volume | Bind mount |
|---|---|---|
| **Who manages the storage location** | Docker | You (it's a folder you chose) |
| **Where it lives** | Hidden away, inside Docker's own storage area | Anywhere on your computer — you pick the path |
| **Typical use** | Database data, anything the app owns entirely | Your source code, config files you're actively editing |
| **Portability** | Works the same on any machine, since Docker manages it | Depends on that exact host path existing |
| **Best for** | Production data that must persist | Local development, live-editing code |

**Simple rule of thumb:**
```
Data the APP owns and manages (a database's files)  → volume
Files YOU are actively editing on your own machine   → bind mount
```

---

## What happens if you use neither

- **A database container with no volume** — every restart, redeploy, or crash-and-recreate wipes all your data, exactly as Step 4 demonstrated. In production, this is catastrophic; in development, it's just annoying every time you need to `docker rm` and rebuild.
- **An app container with no bind mount, during development** — every single code change means: stop container → rebuild image → start container again. Multiply that by every small fix, and development slows to a crawl.

---

---

# Part 2 — Networking: Connecting Containers

Everything in Part 1 assumed FastAPI runs directly on your own machine (`uv run fastapi dev ...`), reaching Postgres through `localhost:5432` because of the port mapping from Step 1. Here's what changes once FastAPI *itself* also moves into a container.

## Step 7 — What `localhost` actually means

**`localhost` means "this environment I'm currently running inside" — it is not a fixed, universal address.**

While FastAPI ran directly on your machine, `localhost` meant *your machine* — so `localhost:5432` correctly reached the Postgres container, because its port was mapped out to your machine in Step 1.

```
Your machine
┌───────────────────────────┐
│  FastAPI (uv run)          │
│      │ localhost:5432      │
│      ▼                     │
│  Postgres container :5432  │
│  (reachable via -p)        │
└───────────────────────────┘
```

## Step 8 — Containerize FastAPI too, and `localhost` breaks

Now put FastAPI inside its own container as well:

```bash
docker run -d --name todo-dev --env-file .env -p 8000:8000 todo-api:1.0
```

With `DATABASE_URL` still pointing at `localhost:5432`, the app fails to connect — something like:
```
connection to server at "localhost" (::1), port 5432 failed: Connection refused
```

**Why:** FastAPI is no longer running on your machine — it's running inside its own Linux container, with its *own* isolated `localhost`. Each container has its own network namespace, so one container's `localhost` is never another container:

```
┌─────────────────────┐       ┌─────────────────────┐
│ FastAPI container    │       │ Postgres container   │
│                      │       │                      │
│ localhost            │       │ localhost            │
│    ↓                 │       │    ↓                 │
│ FastAPI container     │       │ Postgres container    │
│ itself (NOT Postgres)│       │ itself                │
└─────────────────────┘       └─────────────────────┘
```

`localhost:5432` from inside the FastAPI container means *"port 5432 of the FastAPI container"* — which has nothing listening on it at all.

## Step 9 — The default bridge network (works, but fragile)

Every container Docker runs gets connected to a network. If you don't specify one, that's the default **bridge** network, and Docker gives each container its own internal IP address on it:

```bash
docker inspect pg-todo
```
```json
"bridge": {
    "IPAddress": "172.17.0.2"
}
```

Containers on this same default network *can* reach each other by IP:
```
DATABASE_URL=postgresql://postgres:secret@172.17.0.2:5432/postgres
```

This works — but it's fragile. Remove and recreate the Postgres container (exactly like Step 4 in Part 1), and Docker can easily hand it a *different* IP next time:
```
pg-todo → 172.17.0.2   (today)
pg-todo → 172.17.0.5   (after recreating the container)
```
Your `.env` would still say `172.17.0.2`, and the app would quietly break. **Don't teach students to hard-code container IPs** — it's worth showing once, specifically so they understand why the next step exists.

## Step 10 — The fix: a user-defined bridge network

Creating your own named network gets you something the default bridge doesn't offer: **automatic DNS, so containers can reach each other by name instead of IP.**

```bash
docker network create todo-net
```

If Postgres is already running, you don't need to recreate it — just attach the existing container to the new network:
```bash
docker network connect todo-net pg-todo
```
This only adds a network connection to the existing container — it does **not** recreate it, rebuild it, or touch its data (the volume from Part 1 is completely unaffected).

For a fresh container, you'd instead just include the network at `docker run` time:
```bash
docker run -d --name pg-todo --network todo-net -e POSTGRES_PASSWORD=secret -v pgdata:/var/lib/postgresql/data postgres:16
docker run -d --name todo-dev --network todo-net --env-file .env -p 8000:8000 todo-api:1.0
```

Now update `.env` to use the Postgres container's **name** instead of an IP:
```
DATABASE_URL=postgresql://postgres:secret@pg-todo:5432/postgres
```

```
FastAPI container
   │
   │ asks Docker DNS: "where is pg-todo?"
   ▼
Docker DNS  ──►  current IP of pg-todo
   │
   ▼
Postgres container
```

Docker keeps that name-to-IP mapping up to date automatically — if `pg-todo` is ever recreated and gets a new IP, `pg-todo` as a hostname still resolves correctly, with nothing to update in `.env`.

**If you see this error:**
```
could not translate host name "pg-todo" to address: Name or service not known
```
it means the FastAPI container itself isn't on `todo-net` — Docker DNS only resolves names for containers sharing the same user-defined network. Double-check both `docker run` commands actually included `--network todo-net`.

## Step 11 — One more distinction: `-p` vs container-to-container traffic

From Part 1, `-p 5432:5432` makes Postgres reachable **from your machine** (e.g. for a GUI tool like pgAdmin, or `localhost:5432` from a host-run app). But **container-to-container traffic on a shared network doesn't need `-p` at all** — FastAPI can reach `pg-todo:5432` directly through Docker's internal network, even if Postgres was started with no `-p` flag whatsoever.

```
Host → container traffic   (needs -p)       e.g. your browser hitting localhost:8000
Container → container traffic (no -p needed) e.g. FastAPI reaching pg-todo:5432
```

## Step 12 — All four scenarios, side by side

| Setup | What goes in `DATABASE_URL` as the host |
|---|---|
| FastAPI and Postgres both running directly on your machine | `localhost` |
| FastAPI containerized, Postgres running directly on your machine | `host.docker.internal` |
| Both containerized, on the default bridge network | Postgres container's IP (fragile — changes on recreate) |
| Both containerized, on a user-defined bridge network | Postgres container's **name** (stable — recommended) |

**Four rules to leave students with:**
1. `localhost` means *"this environment/container,"* never a fixed universal address.
2. Each container has its own network namespace — one container's `localhost` is never another container.
3. Containers on the default bridge can reach each other by IP, but that IP isn't stable — avoid relying on it.
4. Put related containers on a **user-defined bridge network** and talk to each other by **container name** — this is the recommended approach, and it's exactly what `docker network create` + `docker network connect` (or `--network` at `docker run` time) gets you.

---

## Bonus: handing Postgres a setup script with a bind mount

```bash
docker run -d \
  -e POSTGRES_PASSWORD=secret \
  -p 5432:5432 \
  -v "$(pwd)/init.sql:/docker-entrypoint-initdb.d/init.sql" \
  postgres:16
```

Postgres's official image automatically runs any `.sql` file found in `/docker-entrypoint-initdb.d/` the very first time it starts — a bind mount is how you hand it that file from your own project.

---

## Clean up

```bash
docker rm -f pg-todo todo-dev
docker volume rm pgdata
docker network rm todo-net
```

---

## Quick-reference cheat sheet

| Command | What it does |
|---|---|
| `-p host_port:container_port` | Map a port on your machine to a port inside the container |
| `docker volume create name` | Create a named volume |
| `docker volume ls` | List all volumes |
| `docker volume inspect name` | See details about a volume |
| `docker volume rm name` | Delete a volume |
| `-v volume_name:/path/in/container` | Mount a Docker-managed volume |
| `-v /host/path:/path/in/container` | Mount a bind mount (a real folder from your machine) |
| `docker network create name` | Create a user-defined bridge network |
| `docker network connect net container` | Attach an existing container to a network, without recreating it |
| `--network name` (on `docker run`) | Start a new container already attached to that network |
| `docker network ls` | List all networks |
| `docker network inspect name` | See which containers are on a network, and their IPs |