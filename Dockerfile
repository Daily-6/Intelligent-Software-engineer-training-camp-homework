FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY . .

RUN mkdir -p /app/workspace

ENV DEEPSEEK_MODEL=deepseek-v4-flash

EXPOSE 7860

CMD ["sh", "-c", "uvicorn harness.webui.app:app --host 0.0.0.0 --port ${PORT:-7860}"]
