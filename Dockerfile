# Use a Python base image
FROM python:3.10-slim

# Install OpenJDK 17 (Java) and required utilities
RUN apt-get update && \
    apt-get install -y openjdk-17-jre-headless && \
    apt-get clean;

# Set working directory
WORKDIR /app

# Copy all files into the container
COPY . .

# Install Python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Run the bot script
CMD ["python", "bot.py"]
