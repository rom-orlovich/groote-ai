FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git bash ca-certificates gnupg \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g @anthropic-ai/claude-code@latest

# Create non-root user
RUN useradd -m -u 1000 agent && chown -R agent:agent /app

# Setup directories
RUN mkdir -p /home/agent/.claude /home/agent/.local/bin /app/repos \
    && chown -R agent:agent /home/agent /app

ENV PATH="/home/agent/.local/bin:${PATH}"

# Install Cursor CLI
RUN export HOME=/home/agent \
    && curl https://cursor.com/install -fsS | bash \
    && chown -R agent:agent /home/agent/.local /home/agent/.local/share

RUN pip install uv

COPY requirements.txt .
RUN uv pip install --no-cache-dir --system -r requirements.txt

COPY --chown=agent:agent . .

RUN cp -r .claude/agents /home/agent/.claude/agents && \
    cp -r .claude/skills /home/agent/.claude/skills && \
    cp .claude/CLAUDE.md /home/agent/.claude/CLAUDE.md && \
    cp .claude/mcp.json /home/agent/.claude/mcp.json && \
    mkdir -p /home/agent/.cursor && \
    cp -r .claude/agents /home/agent/.cursor/agents && \
    cp -r .claude/skills /home/agent/.cursor/skills && \
    cp .claude/CLAUDE.md /home/agent/.cursor/CLAUDE.md && \
    cp .claude/mcp.json /home/agent/.cursor/mcp.json && \
    chown -R agent:agent /home/agent/.claude /home/agent/.cursor

RUN find . -name "*.sh" -exec sed -i 's/\r$//' {} + && \
    find . -name "*.sh" -exec chmod +x {} +

ENV PORT=9100
ENV CLI_PROVIDER=claude

EXPOSE 9100

# Switch to non-root user
USER agent

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:9100/health || exit 1

CMD ["python", "scripts/start.py"]
