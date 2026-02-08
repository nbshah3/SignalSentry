FROM python:3.11-slim as base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY . .

RUN if [ -f pyproject.toml ]; then pip install --upgrade pip && pip install .; \
    elif [ -f requirements.txt ]; then pip install --upgrade pip && pip install -r requirements.txt; \
    else pip install --upgrade pip; fi

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
