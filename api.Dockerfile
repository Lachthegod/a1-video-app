FROM python:3.13-slim

RUN apt-get update \
    && apt-get -y install gcc ffmpeg

WORKDIR /app

COPY api api
RUN pip install --no-cache-dir -r api/requirements.txt

COPY secrets_manager.py secrets_manager.py
COPY parameter_store.py parameter_store.py
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "3000"]
