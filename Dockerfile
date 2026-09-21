FROM python:3.14-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.12.15 /uv /uvx /bin/

RUN apt-get update && apt-get install -y --no-install-recommends libcairo2

ADD . /app

WORKDIR /app

RUN uv sync --locked

CMD ["uvicorn", "sticky.app:app", "--host", "0.0.0.0", "--port", "8000"]
