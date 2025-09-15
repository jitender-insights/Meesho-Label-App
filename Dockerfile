# Use Python base image
FROM python:3.10-slim

# Install poppler-utils (needed for pdf2image)
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Run your app 
CMD ["streamlit", "run", "app.py", "--server.port=10000", "--server.address=0.0.0.0"]
