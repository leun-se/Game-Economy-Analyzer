# Start with a tiny version of Linux that has Python installed
FROM python:3.10-slim

# Create a folder inside the container called 'app'
WORKDIR /app

# Install Java (OpenJDK 17) and basic system tools
# Combine into one command to keep image small
RUN apt-get update && \
    apt-get install -y default-jre default-jdk && \
    apt-get clean

# Copy requirements first (caching trick for speed)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy pipeline.py from computer and put it in the container
COPY . .

# Run immediately during the build
RUN javac LootGenerator.java

# What to do when the container turns on
CMD ["python", "pipeline.py"]