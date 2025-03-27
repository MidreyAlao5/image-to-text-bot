# Use an official Python image
FROM python:3.11-slim

# Install dependencies
RUN apt-get update && \
    apt-get install -y tesseract-ocr libtesseract-dev && \
    apt-get clean

# Set work directory
WORKDIR /app

# Copy all project files
COPY . /app

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port (optional)
EXPOSE 8080

# Start the bot
CMD ["python", "main.py"]
