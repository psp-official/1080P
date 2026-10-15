FROM python:3.10-slim

# Install system dependencies (FFmpeg and build essentials)
RUN apt-get update && apt-get install -y --no-install-recommends     ffmpeg     build-essential     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose port (Render uses PORT env variable or default 5000)
ENV PORT=5000
EXPOSE 5000

# Run the application using gunicorn or python
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "300", "test_encoder:app"]
