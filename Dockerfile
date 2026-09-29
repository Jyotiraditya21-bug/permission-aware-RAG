FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies using uv into a virtual environment
RUN uv venv /opt/venv && \
    uv pip install --python /opt/venv --no-cache -e .

FROM python:3.12-slim AS runtime

# Create a non-root user
RUN useradd -m -s /bin/bash appuser

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy the application source code
COPY src/ ./src/

# Change ownership of the application code
RUN chown -R appuser:appuser /app

# Use the non-root user
USER appuser

# Expose port
EXPOSE 8000

# Ensure the virtual environment's bin directory is in the PATH
ENV PATH="/opt/venv/bin:$PATH"

# Run the FastAPI application using uvicorn
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
