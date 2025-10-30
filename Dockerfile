FROM python:3.12-slim

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install the application dependencies.
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache --no-dev

# Copy the application into the container.
COPY . /app

# Run the application.
# CMD ["/app/.venv/bin/uvicorn", "app.app:init_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-use-colors", "--proxy-headers", "--forwarded-allow-ips", "*"]
CMD ["/app/.venv/bin/gunicorn", "app.app:init_app()", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--preload", "--proxy-protocol", "--forwarded-allow-ips", "*", "--access-logfile", "-", "--error-logfile", "-"]