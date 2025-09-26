FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY agents/networking /app

RUN uv pip install --system .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "networking.api:app", "--host", "0.0.0.0", "--port", "8000"]
