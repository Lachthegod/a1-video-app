FROM python:3.11-slim

RUN apt-get update \
    && apt-get -yy install gcc ffmpeg

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

EXPOSE 3000

CMD ["python3", "-m", "uvicorn", "app:app", "--host=0.0.0.0", "--port=3000"]