FROM python:slim AS build

ENV POETRY_HOME=/opt/poetry
ENV POETRY_VIRTUALENVS_IN_PROJECT=1
ENV POETRY_VIRTUALENVS_CREATE=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV POETRY_CACHE_DIR=/opt/.cache

RUN pip install poetry

WORKDIR /app

# --- Reproduce the environment ---
# You can comment the following two lines if you prefer to manually install
#   the dependencies from inside the container.
COPY pyproject.toml poetry.lock /app/

# Install the dependencies and clear the cache afterwards.
#   This may save some MBs.
RUN poetry install --no-root && rm -rf $POETRY_CACHE_DIR

# Now let's build the runtime image from the builder.
#   We'll just copy the env and the PATH reference.
FROM python:slim

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY --from=build ${VIRTUAL_ENV} ${VIRTUAL_ENV}

RUN apt update && \
    apt install -y tini && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 5000

WORKDIR /app

COPY *.py /app
COPY app /app/app

ENV FLASK_ENV=production

ENTRYPOINT ["tini", "--"]

CMD ["python", "run.py"]
