FROM python:3.11-slim

RUN apt-get update \
    && apt-get -yy install gcc ffmpeg

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "worker.py"]
