FROM pypy:slim AS build

ENV POETRY_HOME=/opt/poetry
ENV POETRY_VIRTUALENVS_IN_PROJECT=1
ENV POETRY_VIRTUALENVS_CREATE=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# system deps only if you need to compile wheels; many projects don't
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      curl \
      ca-certificates \
      build-essential \
      libffi-dev libssl-dev pkg-config \
   && rm -rf /var/lib/apt/lists/*

RUN pip install poetry

WORKDIR /app

# --- Reproduce the environment ---
# You can comment the following two lines if you prefer to manually install
#   the dependencies from inside the container.
COPY pyproject.toml poetry.lock /app/
# Install project deps into .venv using PyPy
RUN poetry install --no-root --no-interaction --no-ansi

# copy your source (no re-resolution needed)
COPY *.py /app
COPY app /app/app

# Now let's build the runtime image from the builder.
#   We'll just copy the env and the PATH reference.
FROM pypy:slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends tini && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 5000

WORKDIR /app

COPY --from=build /app/.venv /app/.venv
COPY --from=build /app /app

ENV PATH="/app/.venv/bin:${PATH}" \
    FLASK_ENV=production

ENTRYPOINT ["tini", "--"]

CMD ["python","run.py"]
