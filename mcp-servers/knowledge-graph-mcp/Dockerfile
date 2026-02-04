FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY requirements.txt .
RUN uv pip install --no-cache-dir --system -r requirements.txt

COPY . .

ENV KG_PORT=9005
ENV KG_KNOWLEDGE_GRAPH_URL=http://knowledge-graph:4000

EXPOSE 9005

CMD ["python", "main.py"]
