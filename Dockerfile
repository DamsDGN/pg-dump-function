FROM python:3.13-alpine

ENV PORT=8080

RUN apk add --no-cache postgresql17-client

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]