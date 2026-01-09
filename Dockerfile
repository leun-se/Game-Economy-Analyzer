# Start with a tiny version of Linux that has Python installed
FROM python:3.10-slim

# Create a folder inside the container called 'app'
WORKDIR /app

# Copy requirements first (caching trick for speed)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy pipeline.py from computer and put it in the container
COPY pipeline.py .

# What to do when the container turns on
CMD ["python", "pipeline.py"]