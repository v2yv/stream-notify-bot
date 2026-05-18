FROM python:3.12-slim

RUN groupadd --gid 1000 botuser \
    && useradd --uid 1000 --gid botuser --shell /bin/bash --create-home botuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot/ ./bot/

RUN mkdir -p /app/data /app/logs \
    && chown -R botuser:botuser /app/data /app/logs

USER botuser

CMD ["python", "bot/main.py"]
