FROM python:3.11-slim

ENV POETRY_VERSION=1.8.3
RUN pip install --no-cache-dir poetry==${POETRY_VERSION}

WORKDIR /app
COPY pyproject.toml /app/
# If lock provided, copy as well to enable caching
# COPY poetry.lock /app/
RUN poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-ansi

COPY app /app/app

EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

