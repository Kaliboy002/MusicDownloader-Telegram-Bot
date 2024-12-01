# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install FFmpeg and other dependencies for Selenium (if necessary)
RUN apt-get update && \
    apt-get install -y ffmpeg \
    wget \
    libx11-dev \
    libgdk-pixbuf2.0-0 \
    libglib2.0-0 \
    libnss3 \
    libxss1 \
    libappindicator3-1 \
    libindicator7 \
    chromium-driver

# Install dependencies from requirements.txt
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV NAME World

# Run main.py when the container launches
CMD ["python", "main.py"]
