FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ .

EXPOSE 8015

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8015"]
