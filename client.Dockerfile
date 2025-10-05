FROM python:3.13-slim

RUN apt-get update \
    && apt-get -y install gcc ffmpeg

WORKDIR /app

COPY client client
RUN pip install --no-cache-dir -r client/requirements.txt

COPY secrets_manager.py secrets_manager.py
COPY parameter_store.py parameter_store.py
CMD ["python3", "-m", "uvicorn", "client.main:app", "--host", "0.0.0.0", "--port", "3001"]