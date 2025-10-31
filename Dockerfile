# Dockerfile for Deep Research MCP Server
# Multi-stage build for optimized production image

# ============================================================================
# Stage 1: Build stage with full Python toolchain and uv
# ============================================================================
FROM python:3.13-slim as builder

# Set environment variables for build optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
RUN pip install uv

# Set work directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install Python dependencies using uv
RUN uv sync --frozen --no-dev

# ============================================================================
# Stage 2: Runtime stage with minimal dependencies
# ============================================================================
FROM python:3.13-slim as runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app:$PYTHONPATH"

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    pandoc \
    texlive-latex-base \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-latex-extra \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /bin/bash appuser

# Set work directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv

# Copy application code
COPY --chown=appuser:appgroup . .

# Create required directories with proper permissions
RUN mkdir -p /app/outputs /app/logs /app/data \
    && chown -R appuser:appgroup /app

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Switch to non-root user
USER appuser

# Expose port for MCP server
EXPOSE 8000

# Default command - can be overridden
CMD ["python", "mcp_server.py"]

# ============================================================================
# Build arguments for customization
# ============================================================================
ARG BUILD_VERSION=latest
ARG BUILD_DATE
ARG VCS_REF

# Metadata labels
LABEL maintainer="Deep Research MCP Team" \
      version="${BUILD_VERSION}" \
      description="Multi-agent deep research system with MCP server" \
      org.opencontainers.image.title="Deep Research MCP" \
      org.opencontainers.image.description="Multi-agent deep research system" \
      org.opencontainers.image.version="${BUILD_VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.source="https://github.com/your-org/deep-research-mcp" \
      org.opencontainers.image.revision="${VCS_REF}"