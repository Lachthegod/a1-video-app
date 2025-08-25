FROM python:3.11-slim

# Install system dependencies for MariaDB and FFmpeg
RUN apt-get update \
    && apt-get -yy install libmariadb3 libmariadb-dev gcc ffmpeg

WORKDIR /usr/src/app

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 3000

# Start the FastAPI app
CMD ["python3", "-m", "uvicorn", "app:app", "--host=0.0.0.0", "--port=3000"]
