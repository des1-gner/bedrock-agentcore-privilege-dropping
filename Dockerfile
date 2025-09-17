FROM --platform=linux/arm64 ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# Install gosu
RUN apt-get update && apt-get install -y gosu && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -g 2018 test && useradd -u 2018 -g test -m test

# Create workspace and set permissions
RUN mkdir -p /workspace && chown -R test:test /workspace

WORKDIR /workspace

# Copy and install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

# Copy application
COPY agent.py ./
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

EXPOSE 8080

CMD ["./entrypoint.sh"]