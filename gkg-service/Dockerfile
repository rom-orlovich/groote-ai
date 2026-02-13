FROM rust:1.75-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://gitlab.com/gitlab-org/rust/knowledge-graph/-/raw/main/install.sh | bash || \
    echo "GKG installation skipped - will use mock mode"

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    git \
    socat \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local/bin/gkg /usr/local/bin/gkg

RUN pip install uv

COPY requirements.txt .
RUN uv pip install --no-cache-dir --system -r requirements.txt

COPY . .

RUN mkdir -p /data/gkg /data/repos

EXPOSE 8003 27495

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
