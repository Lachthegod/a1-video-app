
FROM python:3.11-slim

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

EXPOSE 3001

CMD ["uvicorn", "client:app", "--host=0.0.0.0", "--port=3001"]