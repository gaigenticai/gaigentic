# ---- Builder stage ----
FROM python:3.11-slim AS builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ---- Final image ----
FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y netcat && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy built dependencies
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Ensure the entrypoint script is executable
RUN chmod +x start.sh

# Expose FastAPI default port
EXPOSE 8001

# Start the app
CMD ["./start.sh"]
