FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY requirements.txt .
RUN uv pip install --no-cache-dir --system -r requirements.txt

COPY . .

ENV PORT=9001
ENV GITHUB_API_URL=http://github-api:3001

EXPOSE 9001

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import socket; s = socket.create_connection(('localhost', 9001), timeout=5); s.close()"

CMD ["python", "main.py"]
