# Use a full Debian-based Python image for better package compatibility
FROM python:3.10-bullseye

# Install OpenJDK 17 (Java)
RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-17-jre-headless && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy all files into the container
COPY . .

# Install Python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Run the bot script
CMD ["python", "bot.py"]
