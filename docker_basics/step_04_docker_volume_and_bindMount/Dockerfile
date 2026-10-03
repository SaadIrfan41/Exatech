FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./



RUN uv sync --frozen --no-install-project

COPY . .

EXPOSE 8000

# CMD ["uv", "run", "fastapi", "run", "main.py"]
ENTRYPOINT ["uv", "run", "fastapi", "run", "main.py"]