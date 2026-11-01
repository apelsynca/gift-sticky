FROM python:3.14-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.12.15 /uv /uvx /bin/

RUN apt-get update && apt-get install -y --no-install-recommends libcairo2

ADD . /app

WORKDIR /app

RUN uv sync --locked --no-dev

RUN useradd --uid 1000 --no-create-home sticky && chown sticky /app/generations

ENV LITESTAR_APP="sticky.app:app"
ENV PATH="/app/.venv/bin:$PATH"

USER sticky

CMD ["litestar", "run", "--host", "0.0.0.0", "--port", "8000"]
