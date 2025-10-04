FROM python:3.13-slim

RUN apt-get update \
    && apt-get -y install gcc ffmpeg

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "-m", "uvicorn", "api:app"]
