FROM python:3.14-slim-bookworm

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy workspace definition
COPY pyproject.toml uv.lock workspace.toml ./

# Copy source code
COPY components ./components
COPY bases ./bases
COPY projects/banking_demo ./projects/banking_demo
COPY projects/orchestrix_lib ./projects/orchestrix_lib

# Install dependencies and the project
# We use --frozen to ensure we use the exact versions from uv.lock
RUN uv sync --frozen --no-dev --project projects/banking_demo

# Set path to use the virtual environment
ENV PATH="/app/projects/banking_demo/.venv/bin:$PATH"

# Run the application
# Assuming the entry point is defined or we run the module directly
CMD ["python", "-m", "orchestrix.banking.main"]
