# Stage 1: Build the frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Build the backend and serve the application
FROM python:3.10-slim
WORKDIR /app/backend

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install backend dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./

# Copy frontend build from stage 1
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Expose port (Cloud Run sets this via environment variable)
EXPOSE 8080

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Run the application using gunicorn
# -b 0.0.0.0:$PORT: binds to the port provided by Cloud Run
# --workers 1: one worker is enough for this app
# --threads 4: handle multiple concurrent requests
# --timeout 0: disable timeout for long-running initialization if needed (though we use threads)
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 0 app:app
