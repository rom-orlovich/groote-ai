FROM node:22-slim AS frontend-build
WORKDIR /frontend

RUN corepack enable && corepack prepare pnpm@latest --activate

COPY frontend/package.json frontend/pnpm-lock.yaml* frontend/.npmrc ./
RUN pnpm install --frozen-lockfile || pnpm install

COPY frontend/ .
RUN pnpm build

FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

COPY src/ .
COPY --from=frontend-build /frontend/dist /frontend/dist

EXPOSE 8015

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8015"]
