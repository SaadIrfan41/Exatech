# Docker Compose: One File, One Command

You've already run the Todo API and Postgres together by hand — a network, a volume, and two separate `docker run` commands, each with a handful of flags. That worked, but it's worth stopping to notice exactly how much typing it actually took.

---

## Step 1 — The problem with what we've been doing

To get Postgres and the Todo API talking to each other, here's everything we had to run, in order, every single time:

```bash
docker network create todo-net
docker volume create pgdata
docker run -d --name pg-todo --network todo-net \
  -e POSTGRES_PASSWORD=secret \
  -v pgdata:/var/lib/postgresql/data \
  postgres:16
docker build -t todo-api:1.0 .
docker run -d --name todo-dev --network todo-net \
  --env-file .env -p 8000:8000 \
  todo-api:1.0
```

A few real problems with this, worth naming explicitly to students:

- **It's a lot to remember.** Miss one flag (forget `--network todo-net`, say) and the two containers silently can't reach each other — with no obvious error telling you why.
- **It's not shareable.** If you hand this project to a classmate or teammate, they have to either read your notes or guess every flag you used.
- **Starting over is tedious.** Want to wipe everything and start fresh? That's `docker rm -f` on two containers, `docker network rm`, `docker volume rm` — four more commands, in the right order.
- **Nothing describes the *whole* setup in one place.** The relationship between these two containers (which depends on which, which network they share) only exists in your head and your shell history — not written down anywhere.

---

## Step 2 — What Docker Compose actually is

**Docker Compose lets you describe your entire multi-container setup in a single YAML file**, then start the whole thing with one command:

```bash
docker compose up
```

And tear it all down, just as easily:

```bash
docker compose down
```

Everything we typed by hand above — the network, the volume, both containers, their ports, their environment variables — all of it lives in one file called `docker-compose.yml`, sitting right next to your `Dockerfile`. Anyone who gets your project can run the exact same setup with that one command, no flags to remember.

---

## Step 3 — Anatomy of a Compose file, one part at a time

We'll build this up piece by piece, rather than dumping the whole file at once.

### `services:` — the top-level list of containers

```yaml
services:
  db:
    # ...
  api:
    # ...
```

Each entry under `services:` becomes one container when you run `docker compose up`. We're naming ours `db` and `api` — these names matter, because (as you'll see) they double as hostnames the containers use to reach each other.

### `image:` vs `build:` — where does this container come from?

```yaml
services:
  db:
    image: postgres:16
```

`image:` says *"just pull and use this existing image"* — exactly like `docker run postgres:16`, no building required. We use this for Postgres since we're not writing our own Postgres image, just using the official one.

```yaml
services:
  api:
    build: .
```

`build: .` says *"build an image from the Dockerfile in this folder first"* — the Compose equivalent of running `docker build .` yourself. We use this for our Todo API since we have our own Dockerfile.

### `ports:` — the same port mapping you already know

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
```

Exactly the same idea as `-p 8000:8000` on `docker run` — `"host:container"`.

### `environment:` and `env_file:` — passing in configuration

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: secret
```

`environment:` sets variables directly in the file — equivalent to `-e POSTGRES_PASSWORD=secret`.

```yaml
services:
  api:
    build: .
    env_file:
      - .env
```

`env_file:` instead loads variables from an existing `.env` file — equivalent to `--env-file .env`. Use this when you already have secrets in a `.env` file (like we do for `DATABASE_URL`), so you're not retyping them into the Compose file itself.

### `volumes:` — same idea, in two places

Volumes show up in two spots in a Compose file. First, declared once at the very bottom of the file:

```yaml
volumes:
  pgdata:
```

This is the Compose equivalent of `docker volume create pgdata` — just declaring that this named volume exists.

Then, used inside a specific service:

```yaml
services:
  db:
    image: postgres:16
    volumes:
      - pgdata:/var/lib/postgresql/data
```

Same meaning as `-v pgdata:/var/lib/postgresql/data` on `docker run` — Postgres's data folder is backed by that volume, not the container's own disposable filesystem.

### `depends_on:` — controlling startup order

```yaml
services:
  api:
    build: .
    depends_on:
      - db
```

Tells Compose: *"start `db` before starting `api`."* Without this, Compose might start both containers at roughly the same time, and your API could try to connect to a database that isn't ready yet.

(Worth a quick caveat for students: `depends_on` only waits for the *container* to start, not for Postgres to actually be ready to accept connections — those aren't quite the same moment. For this course, your `DATABASE_URL`-based connection with SQLModel generally tolerates that gap fine, but it's good to know this exists as a limitation.)

### Networking — the part Compose does FOR you automatically

Here's the nicest part: **Compose automatically creates a shared network for every service in the file** — you never need a `docker network create` command, and you never need a `networks:` section unless you want something more advanced than the default.

Even better: **every service can already reach every other service by its service name**, because of how we named things under `services:`. If our `api` service needs to reach `db`, it just uses `db` as the hostname — exactly like `pg-todo` worked as a hostname once both containers shared our manually-created `todo-net` network before. Compose just does that step for us automatically.

That means our connection string inside `.env` changes from:
```
DATABASE_URL=postgresql://postgres:secret@localhost:5432/postgres
```
to:
```
DATABASE_URL=postgresql://postgres:secret@db:5432/postgres
```
`db` is simply the service name we chose above — not `localhost`, because the API is no longer running on your own machine, it's running inside its own container talking to another container.

---

## Step 4 — Putting it all together

Here's the complete `docker-compose.yml`, combining every piece above:

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

Compare this to the six manual commands from Step 1 — same setup, same network behavior, same persisted volume, same port mapping, same environment variables, but now written down once, in one place, in a format anyone on the team can read and reuse.

---

## Step 5 — The commands you'll actually use

```bash
docker compose up
```
Builds (if needed) and starts every service, with logs streaming live in your terminal.

```bash
docker compose up -d
```
Same thing, but detached — runs in the background and gives you your terminal back (just like `-d` on `docker run`).

```bash
docker compose down
```
Stops and removes every container Compose created — but **keeps** named volumes (like `pgdata`) by default, so your database data survives.

```bash
docker compose down -v
```
Same as above, but also deletes the volumes — a true full reset, back to nothing. Use this when you deliberately want to wipe your data.

```bash
docker compose ps
```
Lists the containers Compose is managing (like `docker ps`, but scoped to this project).

```bash
docker compose logs -f api
```
Follows the logs of just the `api` service — same idea as `docker logs -f`, just targeting one service by name instead of a container name/ID.

```bash
docker compose exec api bash
```
Gets you an interactive shell inside the running `api` service — same idea as `docker exec -it`.

```bash
docker compose build
```
Rebuilds any service with a `build:` key (like `api`), without starting anything — useful after changing your Dockerfile.

---

## Quick-reference cheat sheet

| Compose key / command | Equivalent manual command | Meaning |
|---|---|---|
| `services:` | — | One entry = one container |
| `image:` | `docker run <image>` | Use an existing image as-is |
| `build: .` | `docker build .` | Build from the local Dockerfile |
| `ports:` | `-p host:container` | Port mapping |
| `environment:` | `-e KEY=value` | Set variables directly in the file |
| `env_file:` | `--env-file .env` | Load variables from a `.env` file |
| `volumes:` (in a service) | `-v name:/path` | Mount a volume into this service |
| `volumes:` (top-level) | `docker volume create` | Declare a named volume exists |
| `depends_on:` | — | Control which service starts first |
| *(automatic)* | `docker network create` | Compose creates a shared network for you |
| `docker compose up -d` | several `docker run` commands | Start everything |
| `docker compose down` | several `docker rm -f` commands | Stop and remove everything (keeps volumes) |
| `docker compose down -v` | + `docker volume rm` | Stop, remove, and wipe volumes too |

---

## The one sentence to leave students with

> Everything you already know how to do by hand with `docker run`, `docker network`, and `docker volume` still happens exactly the same way under the hood — Compose just writes it down once, in one file, so you (and everyone else on the project) stop retyping it.