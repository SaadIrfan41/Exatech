# 1. Base Image: Use an official lightweight Python 3.12 slim image
FROM python:3.12-slim


# We can install uv using:
# RUN pip install uv
# But it will download uv from internet 
# using pip and install it in the /app/.venv/bin directory 
# and it will be slower.
# So instead we are using the official image of uv to copy the uv & uvx binaries from 
# Astral's official image.
# This is the fastest and recommended way to install uv in Docker (no pip/curl required)


# 2. Install uv: Copy uv & uvx binaries from Astral's official image
# This is the fastest and recommended way to install uv in Docker (no pip/curl required)
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
COPY . ./


# 6. Default command to execute when the container starts
CMD ["uv", "run", "main.py"]
