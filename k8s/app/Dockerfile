# App tier image — built in step 2.2 with:
#   nerdctl --namespace k8s.io build -t k8s-tutorial-app:0.1.0 ./app
FROM python:3.12-slim

# uv is the package manager — copy the binary from its official image
COPY --from=ghcr.io/astral-sh/uv:0.5.9 /uv /usr/local/bin/uv

WORKDIR /app

# Install locked deps first — layer stays cached while main.py changes
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-cache

COPY main.py ./

EXPOSE 8000
CMD [".venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
