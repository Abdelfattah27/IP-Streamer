FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*



ENV POETRY_VERSION=1.8.3
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Configure Poetry to avoid creating virtualenvs inside container
RUN poetry config virtualenvs.create false


COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root --only main


COPY . .

RUN poetry run python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "ip_streamer.asgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--keep-alive", "15", "--timeout", "0"]