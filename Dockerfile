# Use an official Python image. Choose a version compatible with your code.
# python:3.11-slim is often a good choice for Render.
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies needed by Playwright
# Add 'apt-get update' before installing packages
# Use '-y' to automatically confirm installations
# Add 'rm -rf /var/lib/apt/lists/*' at the end to clean up
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libxss1 \
    libasound2 \
    libdbus-glib-1-2 \
    libxtst6 \
    xvfb \
    libgtk-3-0 \
    libgraphene-1.0-0 \
    libgstreamer-gl1.0-0 \
    gstreamer1.0-codecparsers \
    libenchant-2-2 \
    libsecret-1-0 \
    libmanette-0.2-0 \
    libgles2 \
    # Clean up APT cache to reduce image size
    && rm -rf /var/lib/apt/lists/*

# Copy your requirements file
COPY requirements.txt .

# Install Python dependencies AND Playwright browsers
# Combine these into one RUN layer for better caching
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install chromium

# Copy the rest of your application code
COPY . .

# Expose the port your app runs on (uvicorn default is 8000)
EXPOSE 8000

# Command to run your application using uvicorn
# Use --host 0.0.0.0 to bind to all network interfaces
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]